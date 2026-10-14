"""The bldg11 scenario demo (live_demo_bldg11/): the building file really carries the points the scenario relies on, the scripted visit runs end to end on the real engine, and the one
finding the build turned up (the shipped joint model cannot see a shared fault on a 49-room handler) is pinned so a change to it shows up here. Skipped without the Mortar Brick file."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "live_demo_bldg11"
TTL = ROOT.parent / "data_cache" / "mortar__bldg11.ttl"
pytestmark = pytest.mark.skipif(not TTL.exists(), reason="needs data_cache/mortar__bldg11.ttl (not part of the repository)")


@pytest.fixture(scope="module")
def demo():
    sys.path.insert(0, str(DEMO))
    import build_building
    import visit
    import world
    return build_building, visit, world


def test_scenario_rooms_have_the_real_points(demo):
    build_building, visit, world = demo
    b, cover = build_building.build_subset()
    points = b["control_system"]["points"]
    claims = b["claims"]
    for c in world.load_scenario()["complaints"]:
        box = claims["vav_zone"][c["room"]]
        assert {"airflow", "damper", "reheat"} <= set(points[box]), (c["room"], box)
        assert "temperature" in points[c["room"]]
    assert "static_pressure" in points["AHU06"] and "static_pressure" in points["AHU05"]
    assert cover["AHU06"]["boxes"] == 49 and cover["AHU05"]["boxes"] == 34


def test_no_point_that_the_brick_file_lacks_is_invented(demo):
    build_building, _, _ = demo
    b, _ = build_building.build_subset()
    keys = {k for p in b["control_system"]["points"].values() for k in p}
    assert keys == {"airflow", "damper", "reheat", "temperature", "static_pressure"}      # no fan_status, no status: the real map has none


def test_adjusted_model_finds_the_shared_cause_and_every_room(demo):
    _, visit, _ = demo
    r = visit.autoplay("adjusted")
    d = r["done"]
    assert d["matches"] == len(d["conclusions"]) == 6
    shared = [t for t in r["trace"] if t.get("shared")]
    assert shared and all(t["check"] == "bas_static" for t in shared)
    assert sum(1 for t in r["trace"] if t.get("check") == "bas_static") == 1            # one static reading speaks for all four AHU06 rooms


def test_shipped_model_cannot_see_a_shared_fault_on_a_large_handler(demo):
    """PINS A KNOWN LIMITATION (README.md): with 4 complaints among 49 rooms the shipped joint model gives low static on AHU06 a prior near zero, never reads the handler and calls the
    four rooms a capacity problem. If this test starts failing because the model changed, update the README, not the assertion."""
    _, visit, _ = demo
    r = visit.autoplay("shipped")
    assert r["prior"]["AHU06"]["low_static"] < 1e-6
    assert not any(t.get("check") == "bas_static" for t in r["trace"])
    assert r["done"]["matches"] < 6


def test_original_demo_building_is_not_affected(demo):
    """The side-by-side demo must not change the engine: the same two-room state prior as the original demo's building (8 rooms per handler) is still non-negligible."""
    import numpy as np
    sys.path.insert(0, str(ROOT / "src"))
    from docmismatch.troubleshoot.v2.joint import JointSettings
    js = JointSettings()
    pc, w = js.p_complain, js.state_prior
    logw = np.log(w) + (8 - 2) * np.log1p(-pc) + 2 * np.log(pc)
    p = np.exp(logw - logw.max())
    p /= p.sum()
    assert p[2] > 0.05


def test_mixed_severity_setting_finds_the_shared_cause_without_a_tuned_number(demo):
    """The general fix (MIX_PROTOCOL.md): a mixture over how many rooms a low-static fault starves, not a number chosen for this building."""
    _, visit, _ = demo
    r = visit.autoplay("mixed")
    assert r["prior"]["AHU06"]["low_static"] > 1e-3 and abs(sum(r["prior"]["AHU06"].values()) - 1.0) < 1e-5
    assert r["done"]["matches"] == 6
    assert sum(1 for t in r["trace"] if t.get("check") == "bas_static") == 1


def test_a_room_the_tool_cannot_settle_gets_a_short_list(demo):
    _, visit, _ = demo
    done = visit.autoplay("mixed")["done"]
    unsettled = [c for c in done["conclusions"] if c["forced"]]
    assert unsettled and all(c["shortlist"] and len(c["shortlist"]["candidates"]) == 2 for c in unsettled)
    assert all(c["shortlist"] is None for c in done["conclusions"] if not c["forced"])
    assert unsettled[0]["shortlist"]["next"]["minutes"] > 0
