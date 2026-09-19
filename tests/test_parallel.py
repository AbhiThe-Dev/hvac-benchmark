"""Checkpointing and parallel execution must never change results: a resumed
or multi-process run has to equal an uninterrupted serial one."""

from __future__ import annotations

import dataclasses
import json
from dataclasses import asdict

import pytest

from hvac_benchmark.config import DEFAULT_CONFIG
from hvac_benchmark.graph.synthetic import make_all_synthetic_graphs
from hvac_benchmark.parallel import ExecOptions, Unit, config_key, run_units
from hvac_benchmark.pipeline import Bundle, compute_availability, run_main_grid
from hvac_benchmark.troubleshooting_pipeline import run_troubleshooting_grid

from conftest import REPO_ROOT

CALLS: list[str] = []


def _square(ontology, x):
    CALLS.append(f"sq{x}")
    return x * x


def _boom(ontology, x):
    raise RuntimeError("boom")


def test_results_preserve_unit_order_and_resume_skips_finished(tmp_path):
    CALLS.clear()
    units = [Unit(f"u{i}", _square, (i,), cost=float(10 - i)) for i in range(5)]
    opts = ExecOptions(workers=1, checkpoint_dir=tmp_path)
    assert run_units(units, None, DEFAULT_CONFIG, opts, "t") == [0, 1, 4, 9, 16]
    assert len(CALLS) == 5

    CALLS.clear()
    assert run_units(units, None, DEFAULT_CONFIG, opts, "t") == [0, 1, 4, 9, 16]
    assert CALLS == []  # everything came from checkpoints


def test_partial_progress_survives_a_failure(tmp_path):
    CALLS.clear()
    opts = ExecOptions(workers=1, checkpoint_dir=tmp_path)
    units = [Unit("a", _square, (2,)), Unit("b", _boom, (3,)), Unit("c", _square, (4,))]
    with pytest.raises(RuntimeError):
        run_units(units, None, DEFAULT_CONFIG, opts, "t")
    assert CALLS == ["sq2"]

    CALLS.clear()
    units[1] = Unit("b", _square, (3,))
    assert run_units(units, None, DEFAULT_CONFIG, opts, "t") == [4, 9, 16]
    assert CALLS == ["sq3", "sq4"]  # 'a' was not recomputed


def test_corrupt_checkpoint_is_recomputed_not_trusted(tmp_path):
    CALLS.clear()
    opts = ExecOptions(workers=1, checkpoint_dir=tmp_path)
    units = [Unit("a", _square, (5,))]
    run_units(units, None, DEFAULT_CONFIG, opts, "t")
    (path,) = list((tmp_path / config_key(DEFAULT_CONFIG)).glob("*.pkl"))
    path.write_bytes(b"not a pickle")
    CALLS.clear()
    assert run_units(units, None, DEFAULT_CONFIG, opts, "t") == [25]
    assert CALLS == ["sq5"]


def test_fresh_ignores_checkpoints(tmp_path):
    CALLS.clear()
    units = [Unit("a", _square, (6,))]
    run_units(units, None, DEFAULT_CONFIG, ExecOptions(checkpoint_dir=tmp_path), "t")
    CALLS.clear()
    run_units(units, None, DEFAULT_CONFIG, ExecOptions(checkpoint_dir=tmp_path, fresh=True), "t")
    assert CALLS == ["sq6"]


def test_different_configs_do_not_share_checkpoints(tmp_path):
    other = dataclasses.replace(DEFAULT_CONFIG, n_seeds=3)
    assert config_key(DEFAULT_CONFIG) != config_key(other)


def _small_setup(ontology):
    cfg = dataclasses.replace(DEFAULT_CONFIG, n_seeds=2, noise_levels=(0.0, 0.05), troubleshooting_severities=(1,),
                              troubleshooting_n_variants=1, troubleshooting_n_seeds_per_variant=1)
    bundles = [Bundle(tg=g, category="real") for g in make_all_synthetic_graphs()[:2]]
    avail = {(b.tg.building_id, r): compute_availability(b.tg, r, ontology) for b in bundles
             for r in ("feeds", "hasPoint", "hasPart")}
    return cfg, bundles, avail


def _dump(results):
    # Trajectories legitimately contain NaN (e.g. precision with no positive
    # predictions), and NaN != NaN once values cross a process boundary, so
    # compare a serialized form in which NaN is a fixed token.
    return [json.dumps(asdict(r), sort_keys=True, default=str) for r in results]


def test_parallel_main_grid_equals_serial_and_resume_equals_both(ontology, tmp_path):
    cfg, bundles, avail = _small_setup(ontology)
    serial = run_main_grid(bundles, ontology, cfg, avail)
    assert serial

    parallel = run_main_grid(
        bundles, ontology, cfg, avail,
        ExecOptions(workers=2, checkpoint_dir=tmp_path, cache_dir=str(REPO_ROOT / "data_cache")),
    )
    assert _dump(parallel) == _dump(serial)

    resumed = run_main_grid(
        bundles, ontology, cfg, avail, ExecOptions(workers=1, checkpoint_dir=tmp_path)
    )
    assert _dump(resumed) == _dump(serial)


def test_parallel_troubleshooting_grid_equals_serial(ontology):
    cfg, bundles, avail = _small_setup(ontology)
    s_results, s_bp = run_troubleshooting_grid(bundles, ontology, cfg, avail)
    p_results, p_bp = run_troubleshooting_grid(
        bundles, ontology, cfg, avail,
        ExecOptions(workers=2, cache_dir=str(REPO_ROOT / "data_cache")),
    )
    assert _dump(p_results) == _dump(s_results)
    assert {k: len(v) for k, v in p_bp.items()} == {k: len(v) for k, v in s_bp.items()}
