"""Download/cache-failure handling, and a full (small) end-to-end pipeline
run whose output is inspected for the required report language."""

from __future__ import annotations

import dataclasses

import pytest
import requests

from hvac_benchmark.config import DEFAULT_CONFIG
from hvac_benchmark.data.cache import FileCache
from hvac_benchmark.data import fetch as fetch_module
from hvac_benchmark import pipeline as pipeline_module


def test_fetch_raises_after_exhausting_retries(tmp_path, monkeypatch):
    def always_fail(*args, **kwargs):
        raise requests.RequestException("simulated network failure")

    monkeypatch.setattr(fetch_module.figshare, "list_collection_source_articles", always_fail)

    cache = FileCache(tmp_path / "cache")
    with pytest.raises(RuntimeError, match="could not resolve Figshare collection"):
        fetch_module.fetch_all_brick_models(cache, max_retries=2)


def test_load_topologies_falls_back_on_persistent_failure(tmp_path, monkeypatch, ontology):
    def always_fail(cache, max_retries=3):
        raise RuntimeError("simulated: figshare unreachable")

    monkeypatch.setattr(pipeline_module, "fetch_all_brick_models", always_fail)

    cache = FileCache(tmp_path / "cache")
    bundles, provenance_report, _ = pipeline_module.load_topologies(cache, ontology, skip_download=False)

    assert provenance_report["fallback_used"] is True
    assert "simulated" in provenance_report["fallback_reason"]
    # synthetic graphs are still produced even when the real corpus is unreachable
    assert any(b.category == "synthetic" for b in bundles)
    # no real topologies were fabricated from thin air
    assert all(b.category != "real" for b in bundles) or len(bundles) >= 10


@pytest.mark.slow
def test_full_pipeline_smoke(tmp_path):
    """A small but real end-to-end run: real acquisition path (reusing the
    project's populated cache), a couple of seeds, one noise level, no
    ablations -- then check the report's required language and that plots
    were actually written to disk."""
    import shutil

    from conftest import REPO_ROOT

    # Use only the LBNL + ontology files from the project cache. The full
    # cache also holds the 45 MORTAR buildings, several with candidate
    # universes in the thousands, which turns this smoke test into the full
    # (hours-long) benchmark; MORTAR groups whose files are absent are
    # recorded as exclusions, which this test tolerates.
    small_cache = tmp_path / "cache"
    small_cache.mkdir()
    for f in (REPO_ROOT / "data_cache").iterdir():
        if not f.name.startswith("mortar__"):
            shutil.copy(f, small_cache / f.name)

    config = dataclasses.replace(DEFAULT_CONFIG, n_seeds=1, noise_levels=(0.0,))
    results_dir = tmp_path / "results"
    pipeline_module.run_pipeline(
        results_dir=str(results_dir),
        cache_dir=str(small_cache),
        config=config,
        skip_download=True,
        run_ablations_flag=False,
    )

    report_text = (results_dir / "results.md").read_text()
    assert "distinct real topologies" in report_text
    assert "small case-study sample, not a statistically powered benchmark" in report_text
    assert "modeled assumption about unaided search order" in report_text
    assert "No technician search sequences were observed or encoded" in report_text

    assert (results_dir / "provenance.json").exists()
    assert (results_dir / "file_to_building.json").exists()
    assert (results_dir / "exclusions.json").exists()
    assert (results_dir / "config.json").exists()

    plot_files = list((results_dir / "plots").glob("*.png"))
    assert len(plot_files) > 0

    trajectory_files = list((results_dir / "trajectories").glob("*.json"))
    assert len(trajectory_files) > 0
