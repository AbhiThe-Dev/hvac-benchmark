"""The first demo (live_demo/, port 8743): two settings of the joint model, Mixed severity (the default) and Shipped, chosen on the intro screen and passed to /api/start. On this building's
8-room handlers the two make the same decisions (live_demo_bldg11/FIRST_DEMO_NOTES.md); these tests check the wiring, not a study result."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "live_demo" / "server.py"


@pytest.fixture(scope="module")
def srv():
    spec = importlib.util.spec_from_file_location("first_demo_server_under_test", SERVER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_default_is_the_mixture_and_shipped_is_the_unmodified_model(srv):
    assert srv.DEFAULT_MODEL == "mixed"
    assert srv.Visit().model.js.low_mix == srv.MIX and srv.Visit("mixed").model.js.low_mix == srv.MIX
    assert srv.Visit("shipped").model.js.low_mix == ()


def test_the_start_route_offers_both_settings_and_reports_what_each_believes(srv):
    r = srv.api_start({})
    assert r["model"] == "mixed" and [m["key"] for m in r["models"]] == ["shipped", "mixed"]
    mixed = r["prior"]["AHU-0"]["low_static"]
    shipped = srv.api_start({"model": "shipped"})["prior"]["AHU-0"]["low_static"]
    assert shipped == pytest.approx(0.0913, abs=1e-3) and mixed == pytest.approx(0.1096, abs=1e-3)       # an 8-room handler: the two start almost the same
    assert abs(sum(r["prior"]["AHU-0"].values()) - 1.0) < 1e-3


def test_an_unknown_setting_is_refused(srv):
    with pytest.raises(ValueError, match="model must be one of"):
        srv.api_start({"model": "tuned"})


def _run(srv, model):
    srv.api_start({"model": model})
    step = srv.VISIT.current_step()
    out = []
    for _ in range(200):
        if step["kind"] == "check":
            step = srv.VISIT.answer("normal" if "normal" in step["words"] else step["words"][-1])
        elif step["kind"] == "question":
            step = srv.VISIT.answer("yes")
        elif step["kind"] == "conclude":
            out.append((step["room"], step["conclusion"], step["forced"]))
            step = srv.VISIT.advance_room()
        elif step["kind"] == "visit_done":
            return out, step
    pytest.fail("the visit never finished")


def test_a_whole_visit_runs_under_both_settings_with_the_same_decisions(srv):
    shipped, done_s = _run(srv, "shipped")
    mixed, done_m = _run(srv, "mixed")
    assert len(shipped) == len(mixed) == 2 and done_s["kind"] == done_m["kind"] == "visit_done"
    assert shipped == mixed                                               # small handler: identical, as measured over 800 simulated visits


def test_the_page_opens_on_mixed_and_has_the_picker():
    html = (ROOT / "live_demo" / "static" / "index.html").read_text()
    assert "model = 'mixed'" in html and "model-pick" in html and "api('/api/start', {model})" in html
    assert "hasModels" in html                                              # an older server sends no setting list: the page then has no picker instead of breaking
