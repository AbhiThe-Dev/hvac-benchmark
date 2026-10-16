"""python -m guide.cli --check power_24vac photo.jpg --out out/try1   (run from the photo_guide/ folder)"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .image import preprocess, to_jpeg
from .llm import model_name, request_guidance
from .prompt import load_checks, safety_lines
from .render import render_guidance


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("photo", type=Path)
    ap.add_argument("--check", required=True)
    ap.add_argument("--out", type=Path, default=Path("out/cli"))
    ap.add_argument("--note", default="")
    ap.add_argument("--model", default=None)
    a = ap.parse_args(argv)
    checks = load_checks()
    if a.check not in checks:
        raise SystemExit(f"unknown check {a.check!r}; choose from: {', '.join(checks)}")
    c = checks[a.check]
    base = preprocess(a.photo.read_bytes())
    g = request_guidance(c, base, a.note, model=a.model)
    r = render_guidance(base, g)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "photo.jpg").write_bytes(to_jpeg(base))
    (a.out / "overview.jpg").write_bytes(r.overview)
    for i, b in enumerate(r.steps, 1):
        (a.out / f"step_{i}.jpg").write_bytes(b)
    (a.out / "guidance.json").write_text(json.dumps(dict(check=a.check, model=a.model or model_name(), guidance=g.model_dump()), indent=2))

    print(f"CHECK: {c['text']}\n")
    print("SAFETY:\n  " + "\n  ".join(safety_lines(c)) + "\n")
    if g.stop:
        print(f"STOP: {g.stop_reason}")
    elif not g.can_help:
        print(f"CAN'T HELP FROM THIS PHOTO: {g.retake_hint}")
    else:
        print(f"I see: {g.what_i_see}\nYou need: {', '.join(g.tools_needed) or 'nothing extra'}\n")
        for i, s in enumerate(g.steps, 1):
            print(f"{i}. {s.instruction}" + (f"  [{s.label}]" if s.label else "") + ("" if s.target else "  (not marked)"))
            if s.look_for:
                print(f"     look for: {s.look_for}")
        print(f"\nNormal: {g.normal_looks_like}\nAbnormal: {g.abnormal_looks_like}")
    print(f"\nimages in {a.out}")


if __name__ == "__main__":
    main()
