"""Stage 1 of the work-order study (PREREGISTRATION_DR.md Addendum 32): does the text of real work orders carry evidence a search or a language model could use? Real records (FMUCD, CC BY 4.0), streamed and never stored.
  curl -sSL --fail URL | .venv/bin/python doc_mismatch/scripts/76_workorder_screen.py codes --file -    # pass 1: hash the stream, count the code columns (no description text is kept or printed)
(the site refused Python's own HTTP client with a 403, so the stream comes from curl; the URL is workorders.FMUCD_URL)
  curl -sSL --fail URL | .venv/bin/python doc_mismatch/scripts/76_workorder_screen.py sample --file -   # pass 2: seeded sample, written only if the hash is right; prints no description
  .venv/bin/python doc_mismatch/scripts/76_workorder_screen.py check     # coverage of the 12 agent files, labeller agreement, the dispute list (no extractor or keyword output is shown)
  .venv/bin/python doc_mismatch/scripts/76_workorder_screen.py score     # needs adjudicated.json (my rulings on the disputes); writes the report
Nothing here is evidence about the routine's speed or about any building of the user's.
"""
import argparse
import csv
import glob
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import workorder_score as S  # noqa: E402
from docmismatch import workorders as W  # noqa: E402

OUT = ROOT.parent / "results/docmismatch/workorder_screen"


def cmd_codes(a):
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    raw = sys.stdin.buffer if a.file == "-" else open(a.file, "rb") if a.file else W.open_url(a.url)
    res = W.code_counts(raw)
    meta = {k: res[k] for k in ("rows", "bad_rows", "bytes", "sha256", "header")}
    meta.update(expected_sha256=W.FMUCD_SHA256, expected_bytes=W.FMUCD_BYTES, hash_ok=res["sha256"] == W.FMUCD_SHA256 and res["bytes"] == W.FMUCD_BYTES, seconds=round(time.time() - t0))
    (OUT / "pass1_meta.json").write_text(json.dumps(meta, indent=1) + "\n")
    for name, cols in (("by_subsystem", ["kind", "SystemCode", "SystemDescription", "SubsystemCode", "SubsystemDescription"]), ("by_university", ["UniversityID", "kind", "SystemCode", "SystemDescription"])):
        with open(OUT / f"pass1_{name}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols + ["orders", "orders_with_description"])
            for k, (n, ne) in sorted(res[name].items()):
                w.writerow(list(k) + [n, ne])
    print(json.dumps({k: v for k, v in meta.items() if k != "header"}))
    if not meta["hash_ok"]:
        sys.exit("HASH MISMATCH: the stream is not the published file; nothing derived from it may be used")


def cmd_sample(a):
    import hashlib
    OUT.mkdir(parents=True, exist_ok=True)
    raw = sys.stdin.buffer if a.file == "-" else open(a.file, "rb") if a.file else W.open_url(a.url)
    res = W.reservoir_sample(raw)
    ok = res["sha256"] == W.FMUCD_SHA256 and res["bytes"] == W.FMUCD_BYTES
    if not ok:
        sys.exit("HASH MISMATCH: the stream is not the published file; no sample written")
    cols = ["sid"] + list(W.KEEP_COLS)
    with open(OUT / "sample_600.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(res["sample"])
    with open(OUT / "sample_inputs.csv", "w", newline="") as f:      # what the extractors and labellers see: the id and the words, nothing else
        w = csv.writer(f)
        w.writerow(["sid", "description"])
        w.writerows([r["sid"], r["WODescription"]] for r in res["sample"])
    meta = {"rows": res["rows"], "bytes": res["bytes"], "sha256": res["sha256"], "hash_ok": ok, "seed": W.SEED, "per_university": W.PER_UNIVERSITY, "eligible_by_university": res["eligible"],
            "sample_size": len(res["sample"]), "frozen_fingerprint": W.prompts_sha256(), "sample_file_sha256": hashlib.sha256((OUT / "sample_600.csv").read_bytes()).hexdigest(),
            "sample_inputs_sha256": hashlib.sha256((OUT / "sample_inputs.csv").read_bytes()).hexdigest()}
    (OUT / "sample_meta.json").write_text(json.dumps(meta, indent=1) + "\n")
    print(json.dumps(meta))


RAW = OUT / "raw"


def load_all():
    """The sample's descriptions and the three agents' files, each checked to cover every order once."""
    rows = list(csv.DictReader(open(OUT / "sample_inputs.csv", newline="")))
    sids, desc = [r["sid"] for r in rows], {r["sid"]: r["description"] for r in rows}
    got = {}
    for role in ("extract", "label1", "label2"):
        got[role] = S.load_jsonl(sorted(glob.glob(str(RAW / f"{role}_c*.jsonl"))))
        S.check_coverage(got[role], sids, role)
    return sids, desc, got


def gates():
    meta = json.loads((OUT / "sample_meta.json").read_text())
    import hashlib
    g = {"G1 the stream was the published file": (meta["hash_ok"], f"sha256 {meta['sha256'][:12]}..."),
         "G2 frozen items unchanged since the sample was drawn": (W.prompts_sha256() == meta["frozen_fingerprint"], f"fingerprint {meta['frozen_fingerprint'][:12]}..."),
         "G3 sample file unchanged": (hashlib.sha256((OUT / "sample_600.csv").read_bytes()).hexdigest() == meta["sample_file_sha256"] and hashlib.sha256((OUT / "sample_inputs.csv").read_bytes()).hexdigest() == meta["sample_inputs_sha256"], "hashes of the two sample files"),
         "G4 sample size": (meta["sample_size"] == 600 and len(meta["eligible_by_university"]) == 12, f"{meta['sample_size']} orders, {len(meta['eligible_by_university'])} universities")}
    return g, meta


def cmd_check(a):
    sids, desc, got = load_all()
    l1, l2 = S.labels(got["label1"]), S.labels(got["label2"])
    ag = S.agreement(l1, l2)
    (OUT / "agreement.json").write_text(json.dumps(ag, indent=1) + "\n")
    d = S.disputes(l1, l2)
    with open(OUT / "disputes.csv", "w", newline="") as f:       # only the two labellers' answers and the words: nothing from the extractor or the keyword search
        w = csv.writer(f)
        w.writerow(["sid", "kind", "labeller1", "labeller2", "labeller1_quote", "labeller2_quote", "description"])
        for s, k in d:
            q = lambda role: (got[role][s].get("quotes") or {}).get(k) or ""
            w.writerow([s, k, l1[s][k], l2[s][k], q("label1"), q("label2"), desc[s]])
    print(json.dumps({"coverage": "all three agents cover all 600 orders", "disputes": len(d), "orders_with_a_dispute": len({s for s, _ in d}), "by_kind": {k: sum(1 for _, kk in d if kk == k) for k in W.KINDS},
                      "agreement": {k: {"agree": v["agree"], "kappa": None if v["kappa"] is None else round(v["kappa"], 2)} for k, v in ag.items()}}))


def p1(x):
    return "n/a" if x is None or x != x else f"{100 * x:.1f}%"


def cmd_score(a):
    g, meta = gates()
    sids, desc, got = load_all()
    l1, l2 = S.labels(got["label1"]), S.labels(got["label2"])
    adj = json.loads((OUT / "adjudicated.json").read_text())
    ref = S.reference(l1, l2, adj)
    uni = {r["sid"]: r["UniversityID"] for r in csv.DictReader(open(OUT / "sample_600.csv", newline=""))}
    eligible = {u: int(n) for u, n in meta["eligible_by_university"].items()}
    ext = S.extraction(got["extract"], desc)
    rows = S.per_order(ref, ext, desc)
    table = S.kind_table(rows, uni, eligible)
    fig = S.stop_figures(rows, uni, eligible)
    ver = S.verdict(fig)
    ag = S.agreement(l1, l2)
    anyd = S.share(rows, uni, eligible, lambda r: r["any_decisive"])
    kwd = S.share(rows, uni, eligible, lambda r: r["kw_any_decisive"])
    L = ["# Stage 1 of the work-order study (Addendum 32): does the text carry evidence?", "",
         "Real records (FMUCD, CC BY 4.0), a seeded sample of 600 unplanned HVAC orders (50 per university, 12 universities). The labels were made by two Claude models and adjudicated by me: **NOT expert-verified**, "
         "and the extractor is a Claude model too, so their errors are correlated. Nothing here says anything about the routine's speed; it only says whether the text carries evidence. Descriptions are terse single records; "
         "the corpus has no room or asset ID and no separate closing note.", "", "## Gates", "", "| gate | result | detail |", "|---|---|---|"]
    L += [f"| {k} | {'PASS' if ok else 'FAIL'} | {d} |" for k, (ok, d) in g.items()]
    if not all(ok for ok, _ in g.values()):
        (OUT / "stage1_report.md").write_text("\n".join(L + ["", "## NO RESULT (a gate failed)"]) + "\n")
        sys.exit("a gate failed")
    L += ["", "## Labeller agreement before adjudication", "", "| kind | both true | agree (of 600) | kappa | labeller 1 true | labeller 2 true |", "|---|---|---|---|---|---|"]
    L += [f"| {k} {W.KIND_NAMES[k]} | {ag[k]['both_true']} | {ag[k]['agree']} | {'n/a' if ag[k]['kappa'] is None else round(ag[k]['kappa'], 2)} | {ag[k]['l1_true']} | {ag[k]['l2_true']} |" for k in W.KINDS]
    L += ["", "## What the text carries, and who finds it", "",
          "Share of orders (equal weight over universities; volume-weighted; lowest and highest university) whose reference label is true, then the keyword search's and the language model's recall and precision against the reference "
          "(the model's precision counts only confirmed statements: reference true AND the quoted words appear in the description).", "",
          "| kind | share (equal) | share (volume) | lowest-highest university | reference true (of 600) | keyword recall | keyword precision | model recall | model precision | model quotes not in the text |", "|---|---|---|---|---|---|---|---|---|---|"]
    for k in W.KINDS:
        t = table[k]
        L.append(f"| {k} {W.KIND_NAMES[k]} | {p1(t['prevalence']['equal'])} | {p1(t['prevalence']['volume'])} | {p1(t['prevalence']['min'])} - {p1(t['prevalence']['max'])} | {t['truth_n']} | {p1(t['kw_recall'])} | {p1(t['kw_precision'])} | {p1(t['ext_recall'])} | {p1(t['ext_precision'])} | {t['ext_unsupported']} |")
    L += ["", f"Orders with at least one of B, C, D (reference): {p1(anyd['equal'])} equal weight, {p1(anyd['volume'])} volume weight; of those the keyword search surfaces the statement in {p1(kwd['equal'])} of all orders (equal weight).", "",
          "## The frozen stop rule", "", "| figure | value | 95% interval | threshold |", "|---|---|---|---|",
          f"| LLM-only share (a confirmed B, C or D statement the keyword search misses), equal weight | {p1(fig['llm_only']['equal'])} | {p1(fig['llm_only_ci'][0])} - {p1(fig['llm_only_ci'][1])} | STOP below 10% |",
          f"| same, volume-weighted | {p1(fig['llm_only']['volume'])} | | (not the rule; flagged if the verdict differs) |",
          f"| lowest - highest university | {p1(fig['llm_only']['min'])} - {p1(fig['llm_only']['max'])} | | |",
          f"| model precision over B, C, D ({fig['confirmed']} confirmed of {fig['statements']} statements) | {p1(fig['precision'])} | {p1(fig['precision_ci'][0])} - {p1(fig['precision_ci'][1])} | STOP below 70% |", "",
          f"**Frozen decision: {'STOP' if ver['stop'] else 'PASS'}**" + (" (" + "; ".join(ver["why"]) + ")" if ver["why"] else "") + ".",
          ("Interval straddles the threshold for: " + ", ".join(ver["straddles"]) + "." if ver["straddles"] else "No interval straddles a threshold."),
          ("The volume-weighted share would give the other verdict on the first criterion." if ver["volume_weight_differs"] else "Volume weights give the same verdict on the first criterion."), "",
          "**Exploratory sensitivity (declared before any output was opened; not the frozen rule).** The adjudication read D generously (an order about an air handler counts as shared equipment, although it tells the technician nothing the routine does not know). LLM-only share, equal weight, counting only some kinds:", "",
          "| kinds counted | LLM-only share |", "|---|---|"]
    for name, kinds in (("B and C (history, mismatch)", ("B", "C")), ("B only", ("B",)), ("C only", ("C",)), ("D only (shared)", ("D",)), ("B, C, D (the frozen figure)", ("B", "C", "D"))):
        L.append(f"| {name} | {p1(S.llm_only_for(rows, uni, eligible, kinds)['equal'])} |")
    L += [""
          "A pass would NOT be a go for the tool: it says nothing about whether history can be tied to the right equipment (the corpus has no room or asset ID), and Stage 2 needs a real building's export and an expert.", "",
          "## By university (LLM-only share, orders of 50)", "", "| university | eligible orders | LLM-only | any B/C/D |", "|---|---|---|---|"]
    anyd_u = anyd["per_university"]
    for u in sorted(fig["llm_only"]["per_university"], key=int):
        L.append(f"| {u} | {eligible[u]} | {p1(fig['llm_only']['per_university'][u])} | {p1(anyd_u[u])} |")
    (OUT / "stage1_report.md").write_text("\n".join(L) + "\n")
    (OUT / "stage1_results.json").write_text(json.dumps({"figures": {k: v for k, v in fig.items()}, "verdict": ver, "table": {k: {kk: vv for kk, vv in t.items()} for k, t in table.items()}}, indent=1, default=str) + "\n")
    print(f"wrote {OUT / 'stage1_report.md'}; decision {'STOP' if ver['stop'] else 'PASS'}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("codes")
    c.add_argument("--url", default=W.FMUCD_URL)
    c.add_argument("--file", help="read this file instead of the URL; '-' reads standard input")
    c.set_defaults(fn=cmd_codes)
    d = sub.add_parser("sample")
    d.add_argument("--url", default=W.FMUCD_URL)
    d.add_argument("--file", help="read this file instead of the URL; '-' reads standard input")
    d.set_defaults(fn=cmd_sample)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    sub.add_parser("score").set_defaults(fn=cmd_score)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
