"""Unit-level parallel execution with on-disk checkpoints.

The benchmark grids decompose into independent units (one per topology and
relation, or per topology). Every trial is seeded and shares no state, so a
unit's output does not depend on which process runs it or when: results are
always reassembled in the original unit order, so a parallel or resumed run
is identical to an uninterrupted serial one.

Each finished unit is written to `<checkpoint_dir>/<config_key>/<unit>.pkl`
(atomically) as soon as it completes. On restart, finished units are loaded
instead of recomputed. The checkpoint directory is namespaced by a hash of the
BenchmarkConfig, so runs with different settings (e.g. `--quick`) never mix.
Checkpoints are local, trusted pickles -- not an exchange format. They are NOT
keyed on source code, so use `fresh=True` (`--fresh`) after changing anything
that affects trial outcomes.
"""

from __future__ import annotations

import hashlib
import logging
import os
import pickle
import re
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

CHECKPOINT_SCHEMA = 1


@dataclass(frozen=True)
class ExecOptions:
    workers: int = 1
    checkpoint_dir: Path | None = None
    cache_dir: str = "data_cache"
    fresh: bool = False


@dataclass(frozen=True)
class Unit:
    """`fn(ontology, *args)` must be a picklable module-level function."""

    key: str
    fn: Callable[..., Any]
    args: tuple
    cost: float = 1.0


_worker_ontology = None


def _init_worker(cache_dir: str) -> None:
    global _worker_ontology
    from .data.cache import FileCache
    from .data.ontology import BrickOntology

    _worker_ontology = BrickOntology.load(FileCache(cache_dir))


def _run_timed(ontology, fn, args):
    t0 = time.time()
    result = fn(ontology, *args)
    return result, time.time() - t0


def _run_in_worker(fn, args):
    return _run_timed(_worker_ontology, fn, args)


def config_key(config: Any) -> str:
    return hashlib.sha256(f"{CHECKPOINT_SCHEMA}|{config!r}".encode()).hexdigest()[:12]


def _unit_path(directory: Path, key: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", key)
    digest = hashlib.sha256(key.encode()).hexdigest()[:8]
    return directory / f"{safe}.{digest}.pkl"


def _write_atomic(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    tmp.write_bytes(pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL))
    os.replace(tmp, path)


def run_units(units: list[Unit], ontology, config: Any, opts: ExecOptions | None, label: str) -> list[Any]:
    """Run `units`, returning their results in the same order as `units`."""
    opts = opts or ExecOptions()
    n = len(units)
    results: list[Any] = [None] * n

    directory: Path | None = None
    if opts.checkpoint_dir is not None:
        directory = Path(opts.checkpoint_dir) / config_key(config)
        directory.mkdir(parents=True, exist_ok=True)

    pending: list[int] = []
    for i, unit in enumerate(units):
        if directory is not None and not opts.fresh:
            path = _unit_path(directory, unit.key)
            if path.exists():
                try:
                    results[i] = pickle.loads(path.read_bytes())
                    continue
                except Exception:  # noqa: BLE001 - a corrupt checkpoint is recomputed, not trusted
                    logger.warning("%s: unreadable checkpoint for %s; recomputing", label, unit.key)
        pending.append(i)

    logger.info(
        "%s: %d units (%d loaded from checkpoints, %d to run, workers=%d)",
        label, n, n - len(pending), len(pending), max(1, opts.workers),
    )
    done = n - len(pending)

    def finish(i: int, result: Any, seconds: float) -> None:
        nonlocal done
        results[i] = result
        if directory is not None:
            _write_atomic(_unit_path(directory, units[i].key), result)
        done += 1
        logger.info("%s: [%d/%d] %s done in %.1fs", label, done, n, units[i].key, seconds)

    if opts.workers <= 1 or len(pending) <= 1:
        for i in pending:
            result, seconds = _run_timed(ontology, units[i].fn, units[i].args)
            finish(i, result, seconds)
    else:
        # Largest first so the long units start early and don't straggle at the end.
        order = sorted(pending, key=lambda i: -units[i].cost)
        with ProcessPoolExecutor(
            max_workers=min(opts.workers, len(pending)),
            initializer=_init_worker,
            initargs=(opts.cache_dir,),
        ) as pool:
            futures = {pool.submit(_run_in_worker, units[i].fn, units[i].args): i for i in order}
            try:
                for future in as_completed(futures):
                    result, seconds = future.result()
                    finish(futures[future], result, seconds)
            except BaseException:
                for future in futures:
                    future.cancel()
                raise
    return results
