"""Score the guide on labelled photos.  Run from photo_guide/:   ../.venv/bin/python eval/run_eval.py [--model MODEL] [--only NAME]

eval/labels.json:  {"<case id>": {"photo": "photo.jpg", "check": "power_24vac", "expect": "help"|"retake"|"stop" or a list of acceptable ones,
                                  "parts": [{"name": "actuator", "box": [x0, y0, x1, y1]}, ...]}}     (boxes on the same 0-1000 grid, hand-drawn;
                  "photo" defaults to the case id, so one photo can be used with several checks)
Photos live in eval/photos/ (git-ignored). Per photo it records: the model's verdict vs `expect`; for every step that has a mark, whether the
mark's centre lies inside ANY labelled part (a hit means 'on a part that matters', not 'on the right part for that step': read the annotated
images in eval/results/<model>/<photo>/ for that); step length; and unexplained-jargon candidates for a human to judge.
Needs ANTHROPIC_API_KEY. Results go to eval/results/ (git-ignored)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from guide.image import preprocess, to_jpeg  # noqa: E402
from guide.llm import model_name, request_guidance  # noqa: E402
from guide.prompt import load_checks  # noqa: E402
from guide.render import render_guidance  # noqa: E402
from guide.schema import GuideError  # noqa: E402

JARGON = ["vac", "vdc", "actuator", "damper", "terminal", "differential", "static pressure", "setpoint", "k-factor", "bas", "plenum", "transducer", "linkage", "voltage", "continuity"]
MAX_WORDS = 20


def centre(t) -> tuple[float, float]:
    c = t.coords
    return (c[0], c[1]) if t.kind == "point" else ((c[0] + c[2]) / 2, (c[1] + c[3]) / 2)


def inside(pt, box) -> bool:
    return box[0] <= pt[0] <= box[2] and box[1] <= pt[1] <= box[3]


def score(g, label: dict) -> dict:
    verdict = "stop" if g.stop else "help" if g.can_help else "retake"
    marked = [s for s in g.steps if s.target is not None]
    boxes = [p["box"] for p in label.get("parts", [])]
    hits = sum(any(inside(centre(s.target), b) for b in boxes) for s in marked) if boxes else None
    long_steps = [i + 1 for i, s in enumerate(g.steps) if len(s.instruction.split()) > MAX_WORDS]
    jargon = sorted({j for s in g.steps for j in JARGON if re.search(rf"\b{re.escape(j)}\b", s.instruction.lower())})
    expect = label.get("expect", "help")
    expect = [expect] if isinstance(expect, str) else expect
    return dict(verdict=verdict, verdict_ok=verdict in expect, expect=expect, steps=len(g.steps), marked=len(marked), hits=hits,
                hit_rate=None if not marked or hits is None else round(hits / len(marked), 2), long_steps=long_steps, jargon_in_steps=jargon)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    labels = json.loads((HERE / "labels.json").read_text())
    checks = load_checks()
    model = a.model or model_name()
    out_root = HERE / "results" / model
    rows = []
    for case, label in labels.items():
        if a.only and a.only not in case:
            continue
        fname = label.get("photo", case)
        p = HERE / "photos" / fname
        if not p.exists():
            print(f"missing photo {fname}, skipped")
            continue
        base = preprocess(p.read_bytes())
        try:
            g = request_guidance(checks[label["check"]], base, model=model)
        except GuideError as e:
            rows.append(dict(case=case, check=label["check"], error=str(e)))
            continue
        d = out_root / re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(case).stem if "#" not in case else case.replace(".jpg", ""))
        d.mkdir(parents=True, exist_ok=True)
        r = render_guidance(base, g)
        (d / "photo.jpg").write_bytes(to_jpeg(base))
        (d / "overview.jpg").write_bytes(r.overview)
        for i, b in enumerate(r.steps, 1):
            (d / f"step_{i}.jpg").write_bytes(b)
        (d / "guidance.json").write_text(json.dumps(g.model_dump(), indent=2))
        rows.append(dict(case=case, check=label["check"], **score(g, label)))
        print(rows[-1])
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "summary.json").write_text(json.dumps(rows, indent=2))
    ok = [r for r in rows if "verdict_ok" in r]
    marked = sum(r["marked"] for r in ok if r["hits"] is not None)
    hits = sum(r["hits"] for r in ok if r["hits"] is not None)
    print(f"\n{model}: {len(rows)} photos, {sum(r['verdict_ok'] for r in ok)}/{len(ok)} verdicts as expected, errors {len(rows) - len(ok)}; "
          f"marks on a labelled part {hits}/{marked}; steps over {MAX_WORDS} words: {sum(len(r['long_steps']) for r in ok)}")


if __name__ == "__main__":
    main()
