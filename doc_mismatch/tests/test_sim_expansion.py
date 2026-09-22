"""Simulation-expansion invariants (spec/manifest integrity, role separation, sealed-access ledger, graph/cases schema)."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from conftest import RES

ACT = RES / "active"
SPEC, MAN = ACT / "sim_spec.json", ACT / "sim_manifest.json"
pytestmark = pytest.mark.skipif(not (SPEC.exists() and MAN.exists()), reason="run scripts/18_make_sim_spec.py first")


def _man():
    return json.loads(MAN.read_text())


def test_manifest_hash_matches_spec():
    assert _man()["spec_sha256"] == hashlib.sha256(SPEC.read_bytes()).hexdigest()


def test_roles_disjoint_and_match_spec():
    m, spec = _man(), json.loads(SPEC.read_text())
    dev, sealed = set(m["dev_topologies"]), set(m["sealed_topologies"])
    assert len(dev) == 4 and len(sealed) == 4 and not dev & sealed
    assert dev == {t["id"] for t in spec["topologies"] if t["role"] == "dev"}
    assert sealed == {t["id"] for t in spec["topologies"] if t["role"] == "sealed"}
    original = {"sys07_vav_reheat", "sys03_psz_ac", "vav_2ahu_2loops", "vav_3ahu_2loops"}
    assert not (dev | sealed) & original


def test_sealed_ranges_extend_beyond_dev():
    spec = json.loads(SPEC.read_text())
    d, s = spec["ranges"]["dev"], spec["ranges"]["sealed"]
    wider = [k for k in d if isinstance(d[k], list) and len(d[k]) == 2 and (s[k][0] < d[k][0] or s[k][1] > d[k][1])]
    assert len(wider) >= 2
    assert not set(d["climates"]) & set(s["climates"])


def test_generated_topologies_load_and_have_cd_slot_structure():
    from docmismatch.data import SLOTS, load_base
    m = _man()
    specs = {t["id"]: t for t in json.loads(SPEC.read_text())["topologies"]}
    ref = load_base("vav_2ahu_2loops")
    for tid in m["dev_topologies"] + m["sealed_topologies"]:
        assert m["generation"][tid]["status"] == "ok"
        b = load_base(tid)
        assert set(b.slot_edges) == set(ref.slot_edges) and set(b.slot_edges) <= set(SLOTS)
        t = specs[tid]
        assert len(b.ids("AHU")) == t["n_ahu"] and len(b.ids("VAV")) == t["n_vav"] == len(b.ids("Zone"))
        assert len(b.ids("HWL")) == t["n_hw"] and len(b.ids("CHWL")) == t["n_chw"]
        assert b.run["severe"] == 0 and b.run["fatal"] == 0 and b.run["n_hours"] == 8760
        assert not any(np.nanstd(b.ev[k]) < 1e-9 for k in b.ev if k.split("|")[1] in ("flow", "temp") and k.split("-")[0] in ("AHU", "VAV", "Zone"))


def test_case_files_schema_roles_and_frozen_hash():
    m = _man()
    ref = set(json.loads(open(RES / "cases.jsonl").readline())) - {"observable_v1"}
    for name, ids in (("dev_extra", m["dev_topologies"]), ("sealed_sim", m["sealed_topologies"])):
        f = RES / Path(m["cases"][name]["file"]).name
        assert hashlib.sha256(f.read_bytes()).hexdigest() == m["cases"][name]["sha256"], f"{f.name} changed after manifest"
        rows = [json.loads(l) for l in f.open()]
        assert {r["topology_id"] for r in rows} <= set(ids)
        assert all(set(r) == ref for r in rows)  # no extra (e.g. model-derived) annotation
        assert all(r["observable"] in ("true", "false", "ambiguous", "n/a") and isinstance(r["degree_preserving"], bool) for r in rows)
        assert {"hard", "easy", "clean"} <= {r["difficulty"] for r in rows}
        assert len({r["case_id"] for r in rows}) == len(rows)


def test_sealed_loader_logs_access_and_guards_roles(tmp_path, monkeypatch):
    from docmismatch.active import sim_data
    ledger = tmp_path / "sealed_access.log"
    monkeypatch.setattr(sim_data, "LEDGER", ledger)
    calls = []
    monkeypatch.setattr(sim_data, "load_or_build_sim", lambda tid, rep: calls.append((tid, rep)) or "POOL")
    sid, did = sim_data.SEALED_TOPOLOGIES[0], sim_data.DEV_TOPOLOGIES[0]
    assert sim_data.load_sealed_sim(sid, 1, "unit test") == "POOL"
    line = ledger.read_text().strip().split("\t")
    assert len(line) == 4 and line[2] == f"{sid}#r1" and line[3] == "unit test" and calls == [(sid, 1)]
    with pytest.raises(ValueError):
        sim_data.load_sealed_sim(did, 0, "wrong role")
    with pytest.raises(ValueError):
        sim_data.load_sealed_sim(sid, 0, "  ")
    with pytest.raises(ValueError):
        sim_data.load_dev_sim(sid, 0)
    assert len(ledger.read_text().strip().splitlines()) == 1 and calls == [(sid, 1)]  # refused calls neither log nor build


def test_dev_pools_cached_if_built():
    from docmismatch.active.sim_data import DEV_TOPOLOGIES
    built = [(ACT / f"pool_{t}_r{r}.pkl").exists() for t in DEV_TOPOLOGIES for r in (0, 1)]
    if not any(built):
        pytest.skip("dev pools not built")
    assert all(built)
