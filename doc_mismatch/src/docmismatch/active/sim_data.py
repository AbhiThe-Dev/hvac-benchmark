"""Simulation-expansion topologies: dev / sealed roles (read from the manifest) and the audited SEALED pool loader.

DEV topologies (dev_E..dev_H) may be used like A-D: `pools.load_or_build_sim(tid, rep)`.
SEALED topologies (seal_S1..seal_S4) were generated blind to modelling (see PREREGISTRATION.md and
doc_mismatch/sim_expansion_report.md). Their reading pools may only be loaded through `load_sealed_sim`, which appends a line
(UTC timestamp, calling script, topology, rep, reason) to results/docmismatch/active/sealed_access.log -- the same audit ledger
the real sealed pool uses. Nothing here has ever been fitted, calibrated or scored on a sealed topology.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

from .pools import CACHE, Pool, load_or_build_sim

MANIFEST = CACHE / "sim_manifest.json"
LEDGER = CACHE / "sealed_access.log"


def _roles() -> tuple[list[str], list[str]]:
    m = json.loads(MANIFEST.read_text())
    return list(m["dev_topologies"]), list(m["sealed_topologies"])


DEV_TOPOLOGIES, SEALED_TOPOLOGIES = _roles()


def load_dev_sim(tid: str, rep: int) -> Pool:
    if tid not in DEV_TOPOLOGIES:
        raise ValueError(f"{tid} is not a dev expansion topology (dev: {DEV_TOPOLOGIES}); sealed ones need load_sealed_sim")
    return load_or_build_sim(tid, rep)


def load_sealed_sim(tid: str, rep: int, reason: str) -> Pool:
    """SEALED simulation pool. Load ONLY for the pre-registered final evaluation; every call is logged before the pool is touched."""
    if tid not in SEALED_TOPOLOGIES:
        raise ValueError(f"{tid} is not a sealed expansion topology (sealed: {SEALED_TOPOLOGIES})")
    if not reason or not reason.strip():
        raise ValueError("a non-empty reason is required and is written to the access ledger")
    CACHE.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a") as fh:
        fh.write(f"{datetime.datetime.now(datetime.timezone.utc).isoformat()}\t{Path(sys.argv[0]).name}\t{tid}#r{rep}\t{reason}\n")
    return load_or_build_sim(tid, rep)
