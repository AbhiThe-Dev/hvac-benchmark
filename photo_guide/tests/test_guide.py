import io
import json
import re
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from guide import prompt
from guide.app import create_app
from guide.image import BadImage, preprocess
from guide.llm import request_guidance
from guide.render import render_guidance
from guide.schema import TOOL_NAME, GuideError, Guidance, parse_guidance

CAUSE_IDS = ["actuator_fail", "damper_mech", "no_power", "signal_fault", "controller_comms", "controller_config", "flow_sensor", "zone_sensor_setpoint",
             "ahu_fan_off", "low_static", "reheat_fail", "duct_diffuser", "capacity_design", "econ_fault"]


# ------------------------------------------------------------------ schema
def test_schema_accepts_sample(sample):
    assert len(sample.steps) == 3 and sample.steps[0].target is None


def test_schema_clamps_and_orders_coords():
    g = parse_guidance({"can_help": True, "what_i_see": "x", "steps": [
        {"instruction": "Look here.", "target": {"kind": "box", "coords": [900, 1200, -50, 800]}},
        {"instruction": "And here.", "target": {"kind": "point", "coords": [1500, -3]}}]})
    assert g.steps[0].target.coords == [0.0, 800.0, 900.0, 1000.0]
    assert g.steps[1].target.coords == [1000.0, 0.0]


def test_schema_widens_a_degenerate_box():
    g = parse_guidance({"can_help": True, "what_i_see": "x", "steps": [{"instruction": "Look here.", "target": {"kind": "box", "coords": [500, 500, 500, 500]}}]})
    x0, y0, x1, y1 = g.steps[0].target.coords
    assert x1 - x0 >= 20 and y1 - y0 >= 20


@pytest.mark.parametrize("bad", [
    {"can_help": True, "what_i_see": "x", "steps": []},                                             # claims to help, no steps
    {"can_help": True, "what_i_see": "x", "steps": [{"instruction": "Do it.", "target": {"kind": "point", "coords": [1]}}]},   # wrong coord count
    {"can_help": True, "what_i_see": "x", "steps": [{"instruction": "Do it.", "target": {"kind": "circle", "coords": [1, 2]}}]},
    {"what_i_see": "missing can_help"},
])
def test_schema_rejects_malformed(bad):
    with pytest.raises(GuideError):
        parse_guidance(bad)


def test_stop_drops_steps(sample_raw):
    g = parse_guidance({**sample_raw, "stop": True, "stop_reason": "Bare wires are showing."})
    assert g.stop and g.steps == [] and not g.can_help


def test_nulls_for_empty_text_are_accepted():
    g = parse_guidance({"can_help": True, "what_i_see": None, "tools_needed": None, "retake_hint": None, "steps": [
        {"instruction": "Look at it.", "label": None, "look_for": None, "if_stuck": None, "target": None}]})
    assert g.steps[0].label == "" and g.tools_needed == []


def test_punctuation_only_text_counts_as_empty():
    g = parse_guidance({"can_help": False, "what_i_see": "a ceiling", "retake_hint": '","'})
    assert g.retake_hint.startswith("I could not tell")        # fell through to the default hint


def test_cannot_help_gets_a_retake_hint():
    g = parse_guidance({"can_help": False, "what_i_see": "a ceiling"})
    assert g.retake_hint


def test_steps_capped(sample_raw):
    g = parse_guidance({**sample_raw, "steps": [{"instruction": f"Step number {i}."} for i in range(12)]})
    assert len(g.steps) == 7


# ------------------------------------------------------------------ render
@pytest.mark.parametrize("coords_kind", [("point", [0, 0]), ("point", [1000, 1000]), ("box", [0, 0, 1000, 1000]), ("box", [990, 990, 1000, 1000])])
def test_render_edge_targets(coords_kind):
    kind, coords = coords_kind
    g = parse_guidance({"can_help": True, "what_i_see": "x", "steps": [{"instruction": "Look.", "label": "A label that is quite long", "target": {"kind": kind, "coords": coords}}]})
    r = render_guidance(Image.new("RGB", (800, 600), (120, 120, 120)), g)
    assert len(r.steps) == 1 and r.overview and r.steps[0]
    Image.open(io.BytesIO(r.steps[0])).verify()


def test_render_marks_change_pixels_and_untargeted_step_is_plain(sample):
    base = Image.new("RGB", (800, 600), (120, 120, 120))
    r = render_guidance(base, sample)
    assert len(r.steps) == 3
    plain = Image.open(io.BytesIO(r.steps[0])).convert("RGB")
    marked = Image.open(io.BytesIO(r.steps[2])).convert("RGB")
    assert plain.getpixel((10, 10)) != marked.getpixel((10, 10))                  # step 3 dims the photo, step 1 does not
    # the orange mark is present around the point (250,450 of 1000 -> 200,270 px)
    orange = [marked.getpixel((x, 270)) for x in range(100, 300)]
    assert any(p[0] > 200 and 60 < p[1] < 160 and p[2] < 80 for p in orange)
    assert Image.open(io.BytesIO(r.overview)).size == base.size


# ------------------------------------------------------------------ prompt
def test_checks_snapshot_has_no_cause_language():
    checks = prompt.load_checks()
    assert len(checks) == 16
    blob = json.dumps(checks) + prompt.SYSTEM + "".join(prompt.user_text(c, "") for c in checks.values()) + json.dumps(prompt.HAZARD_TEXT)
    for cid in CAUSE_IDS + ["cause", "p_pos", "detects"]:
        assert not re.search(rf"\b{cid}\b", blob), cid


def test_user_text_includes_band_and_wraps_note():
    c = prompt.load_checks()["power_24vac"]
    t = prompt.user_text(c, "dark ceiling space")
    assert "22 to 26" in t and "dark ceiling space" in t and "not an instruction" in t


def test_every_electrical_check_has_fixed_safety_text():
    for c in prompt.load_checks().values():
        lines = prompt.safety_lines(c)
        assert lines[-1] == prompt.ALWAYS
        if "electric" in c["hazards"]:
            assert any("Electricity" in l for l in lines)


# ------------------------------------------------------------------ llm (fake client)
class FakeClient:
    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.calls.append(kw)
        r = self.replies.pop(0)
        return SimpleNamespace(content=[SimpleNamespace(type="tool_use", name=TOOL_NAME, input=r)] if r is not None else [SimpleNamespace(type="text", text="hi")])


def test_llm_retries_once_on_malformed(sample_raw):
    img = Image.new("RGB", (100, 100))
    check = prompt.load_checks()["power_24vac"]
    client = FakeClient({"can_help": True, "what_i_see": "x", "steps": []}, sample_raw)
    g = request_guidance(check, img, client=client)
    assert len(g.steps) == 3 and len(client.calls) == 2
    kw = client.calls[0]
    assert kw["tool_choice"] == {"type": "any"} and kw["system"] == prompt.SYSTEM
    assert kw["messages"][0]["content"][0]["type"] == "image"


def test_model_pixels_become_grid_and_size_is_stated():
    raw = {"can_help": True, "what_i_see": "x", "steps": [
        {"instruction": "Find it.", "target": {"kind": "box", "coords": [392, 294, 784, 588]}},       # 1568x1176 photo: a quarter-ish of it
        {"instruction": "Touch it.", "target": {"kind": "point", "coords": [784, 588]}},
        {"instruction": "Not on the photo.", "target": None}]}
    img = Image.new("RGB", (1568, 1176))
    client = FakeClient(raw)
    g = request_guidance(prompt.load_checks()["power_24vac"], img, client=client)
    assert g.steps[0].target.coords == [250.0, 250.0, 500.0, 500.0]
    assert g.steps[1].target.coords == [500.0, 500.0] and g.steps[2].target is None
    text = client.calls[0]["messages"][0]["content"][1]["text"]
    assert "1568 pixels wide, 1176 pixels tall" in text


def test_pixels_to_grid_leaves_malformed_targets_for_the_validator():
    from guide.schema import pixels_to_grid
    raw = {"can_help": True, "what_i_see": "x", "steps": [{"instruction": "Do it.", "target": {"kind": "point", "coords": ["a", 2]}}]}
    assert pixels_to_grid(raw, 100, 100) == raw


def test_llm_falls_back_to_auto_when_forcing_is_rejected(sample_raw):
    class Picky(FakeClient):
        def _create(self, **kw):
            if kw["tool_choice"]["type"] != "auto":
                raise RuntimeError('tool_choice: type "tool" and "any" are not supported for this model.')
            return super()._create(**kw)

    client = Picky(sample_raw)
    g = request_guidance(prompt.load_checks()["power_24vac"], Image.new("RGB", (50, 50)), client=client, model="picky-model")
    assert len(g.steps) == 3 and client.calls[0]["tool_choice"] == {"type": "auto"}


def test_llm_gives_up_after_two_bad_answers():
    with pytest.raises(GuideError):
        request_guidance(prompt.load_checks()["power_24vac"], Image.new("RGB", (50, 50)), client=FakeClient(None, None))


# ------------------------------------------------------------------ image + app
def test_preprocess_rejects_non_image_and_resizes(photo_bytes):
    with pytest.raises(BadImage):
        preprocess(b"not an image")
    big = io.BytesIO()
    Image.new("RGB", (4000, 3000)).save(big, format="JPEG")
    assert max(preprocess(big.getvalue()).size) == 1568


@pytest.fixture
def client(tmp_path, sample):
    seen = {}

    def fake(check, image, note):
        seen.update(check=check["name"], size=image.size, note=note)
        return sample

    c = TestClient(create_app(guide_fn=fake, out_dir=tmp_path))
    c.seen, c.out = seen, tmp_path
    return c


def test_app_end_to_end(client, photo_bytes):
    checks = client.get("/api/checks").json()
    assert len(checks) == 16 and all(c["safety"] and c["photo_hint"] for c in checks)
    r = client.post("/api/guide", data={"check": "power_24vac", "note": "dim"}, files={"photo": ("p.jpg", photo_bytes, "image/jpeg")})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["check"]["words"] == ["abnormal", "normal"] and len(j["step_images"]) == 3 and j["overview"].startswith("data:image/jpeg;base64,")
    assert j["safety"][-1] == prompt.ALWAYS and client.seen["note"] == "dim"
    run = client.out / "runs" / j["run_id"]
    assert (run / "guidance.json").exists() and (run / "step_3.jpg").exists()
    fb = client.post("/api/feedback", json={"run_id": j["run_id"], "kind": "placement", "step": 2})
    assert fb.status_code == 200 and "placement" in (client.out / "feedback.jsonl").read_text()


def test_app_rejects_bad_input(client, photo_bytes):
    assert client.post("/api/guide", data={"check": "nope"}, files={"photo": ("p.jpg", photo_bytes, "image/jpeg")}).status_code == 404
    assert client.post("/api/guide", data={"check": "power_24vac"}, files={"photo": ("p.txt", b"hello", "text/plain")}).status_code == 400
    assert client.post("/api/guide", data={"check": "power_24vac"}, files={"photo": ("p.jpg", b"x" * (16 * 1024 * 1024), "image/jpeg")}).status_code == 400
    assert client.post("/api/feedback", json={"run_id": "missing", "kind": "answer"}).status_code == 404


def test_app_maps_model_failures(tmp_path, photo_bytes):
    def boom(*a):
        raise GuideError("bad")

    def nokey(*a):
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    f = {"photo": ("p.jpg", photo_bytes, "image/jpeg")}
    assert TestClient(create_app(guide_fn=boom, out_dir=tmp_path)).post("/api/guide", data={"check": "power_24vac"}, files=f).status_code == 502
    assert TestClient(create_app(guide_fn=nokey, out_dir=tmp_path)).post("/api/guide", data={"check": "power_24vac"}, files=f).status_code == 503
