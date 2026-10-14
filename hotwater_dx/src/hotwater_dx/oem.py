"""What do manufacturers' own troubleshooting documents say, and does the physics matrix agree? (idea 4 of the robustness brief; documents, not simulation)

Extraction (done by readers of the documents, rules frozen in PREREGISTRATION.md Addendum 9) fills `data/oem_claims.csv`: one row per statement of the form
symptom -> cause -> what to check -> what you would see, as paraphrase with a locator and a very short verbatim anchor; no document text is stored. This module defines the schema and
vocabulary, validates the file, and compares the claims with the matrix of Addendum 1: how many map onto our 17 causes and 23 checks, whether the matrix says the named check can
see the named cause (and in the same direction), which causes and checks manufacturers use that we lack, and which of our causes manufacturers barely mention.
The matrix and the engine are NOT changed by this study; disagreements are candidates for a separately pre-registered correction.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from . import causes as C
from . import checks as K
from .matrix import thresholds_hash
from .provenance import DISCLAIMER

SCHEMA = ("claim_id", "manufacturer", "doc_title", "doc_type", "doc_url", "doc_rev", "locator", "product_class", "symptom", "cause_text", "cause_id", "check_text", "check_id",
          "expected_obs", "expected_dir", "action", "evidence", "read_status", "anchor")
DOC_TYPES = ("installation_operation_manual", "service_manual", "troubleshooting_guide", "technical_bulletin", "design_guide", "submittal_or_data_sheet", "application_note", "other")
PRODUCT_CLASSES = ("storage_heater", "boiler", "indirect_or_hx", "mixing_valve", "recirc_pump", "balancing_valve", "aquastat_or_control", "check_valve", "strainer_or_prv", "expansion_tank", "system_guide", "other")
SYMPTOMS = ("not_hot_enough", "lukewarm", "too_hot", "slow_to_hot", "uneven_between_fixtures", "unstable_or_hunting", "low_flow_or_pressure", "no_hot_water", "noise_or_leak", "other")
EVIDENCE = ("DIRECT", "INFERRED")            # DIRECT = the document itself states the relation; INFERRED = the reader's own reasoning (never scored)
READ = ("READ_FULL", "SNIPPET")              # READ_FULL = the passage text itself was retrieved and read; SNIPPET = search summary only (never scored)
CAUSE_IDS = tuple(c.id for c in C.CAUSES)
CHECK_IDS = tuple(c.id for c in K.CHECKS)
NEW, OUT, NONE = "NEW:", "OUT_OF_SCOPE", "NONE"

OEM_CONFIG = {
    "SCHEMA": SCHEMA, "DOC_TYPES": DOC_TYPES, "PRODUCT_CLASSES": PRODUCT_CLASSES, "SYMPTOMS": SYMPTOMS, "EVIDENCE": EVIDENCE, "READ": READ,
    "CAUSE_IDS": CAUSE_IDS, "CHECK_IDS": CHECK_IDS,
    "SEEN_RULE": "seen = cls == DET_SEEN or (cls in (PARAM, NEEDS_ELIC) and p_sep >= 0.5); direction compared only when seen and the cell sign is not 0 and expected_dir is +1 or -1",
    "SCORED": "evidence == DIRECT and read_status == READ_FULL and not dropped by verification; duplicates (manufacturer, doc_url, cause_id, check_id, locator) count once",
    "FLOOR": {"claims": 60, "manufacturers": 5},         # below this the predictions are descriptive only
    "VERIFY": {"fraction": 0.25, "min": 25, "max": 60, "seed": 20261801},
    "BAR": {"coverage": 0.60, "presence": 0.70, "direction": 0.85, "new_support": 2, "new_count": 2, "thin_max_claims": 1, "thin_causes": 5, "verified": 0.85, "blind_mapping": 0.80},
}


def frozen_hash() -> str:
    from .engine import _strkeys
    return hashlib.sha256(json.dumps(dict(cfg=_strkeys(OEM_CONFIG), matrix=thresholds_hash()), sort_keys=True, default=str).encode()).hexdigest()


# ------------------------------------------------------------------------------------------------ reading and validating the claims file
def read_claims(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return [r for r in csv.DictReader(f) if r.get("claim_id") and not r["claim_id"].startswith("#")]


def validate(rows: list[dict]) -> list[str]:
    problems, seen = [], set()
    for r in rows:
        cid = r.get("claim_id", "?")
        if cid in seen:
            problems.append(f"{cid}: duplicate claim_id")
        seen.add(cid)
        for k in SCHEMA:
            if k not in r:
                problems.append(f"{cid}: missing column {k}")
        if r.get("evidence") not in EVIDENCE:
            problems.append(f"{cid}: evidence {r.get('evidence')!r}")
        if r.get("read_status") not in READ:
            problems.append(f"{cid}: read_status {r.get('read_status')!r}")
        if r.get("symptom") not in SYMPTOMS:
            problems.append(f"{cid}: symptom {r.get('symptom')!r}")
        if r.get("product_class") not in PRODUCT_CLASSES:
            problems.append(f"{cid}: product_class {r.get('product_class')!r}")
        if r.get("doc_type") not in DOC_TYPES:
            problems.append(f"{cid}: doc_type {r.get('doc_type')!r}")
        c = r.get("cause_id", "")
        if not (c in CAUSE_IDS or c == OUT or (c.startswith(NEW) and len(c) > len(NEW))):
            problems.append(f"{cid}: cause_id {c!r}")
        k = r.get("check_id", "")
        if not (k in CHECK_IDS or k == NONE or (k.startswith(NEW) and len(k) > len(NEW))):
            problems.append(f"{cid}: check_id {k!r}")
        if r.get("expected_dir") not in ("1", "-1", "0", "NA", "+1"):
            problems.append(f"{cid}: expected_dir {r.get('expected_dir')!r}")
        if len((r.get("anchor") or "").split()) > 8:
            problems.append(f"{cid}: anchor longer than 8 words")
        if r.get("evidence") == "DIRECT" and not (r.get("anchor") or "").strip():
            problems.append(f"{cid}: DIRECT claim without an anchor")
    return problems


def _dir(x: str) -> int | None:
    return {"1": 1, "+1": 1, "-1": -1}.get(x)


def scored(rows: list[dict], dropped: set[str] = frozenset()) -> list[dict]:
    seen, out = set(), []
    for r in rows:
        if r["evidence"] != "DIRECT" or r["read_status"] != "READ_FULL" or r["claim_id"] in dropped:
            continue
        key = (r["manufacturer"].strip().lower(), r["doc_url"], r["cause_id"], r["check_id"], r["locator"].strip().lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


# ------------------------------------------------------------------------------------------------ comparison with the matrix
def load_cells(path: Path) -> dict:
    m = json.loads(Path(path).read_text())
    return {(c["cause"], c["check"]): c for c in m["cells"]}


def seen(cell: dict) -> bool:
    return cell["cls"] == "DET_SEEN" or (cell["cls"] in ("PARAM", "NEEDS_ELIC") and cell["p_sep"] >= 0.5)


def analyse(rows: list[dict], cells: dict, dropped: set[str] = frozenset()) -> dict:
    S = scored(rows, dropped)
    mfrs = sorted({r["manufacturer"].strip().lower() for r in S})
    mapped = [r for r in S if r["cause_id"] in CAUSE_IDS]
    new_c, new_k = defaultdict(set), defaultdict(set)
    for r in S:
        if r["cause_id"].startswith(NEW):
            new_c[r["cause_id"]].add(r["manufacturer"].strip().lower())
        if r["check_id"].startswith(NEW):
            new_k[r["check_id"]].add(r["manufacturer"].strip().lower())
    by_cause = {c: [r for r in mapped if r["cause_id"] == c] for c in CAUSE_IDS}
    by_check = {k: [r for r in S if r["check_id"] == k] for k in CHECK_IDS}
    pairs = [r for r in mapped if r["check_id"] in CHECK_IDS and (r["cause_id"], r["check_id"]) in cells and K.BY_ID[r["check_id"]].physics_readable]
    rows_cmp, p_ok, d_ok, d_n = [], 0, 0, 0
    for r in pairs:
        cell = cells[(r["cause_id"], r["check_id"])]
        sn = seen(cell)
        d = _dir(r["expected_dir"])
        dir_ok = None
        if sn and cell["sign"] != 0 and d is not None:
            dir_ok = (d == cell["sign"])
            d_n += 1
            d_ok += int(dir_ok)
        p_ok += int(sn)
        rows_cmp.append(dict(claim_id=r["claim_id"], manufacturer=r["manufacturer"], cause=r["cause_id"], check=r["check_id"], cls=cell["cls"], p_sep=cell["p_sep"], matrix_sign=cell["sign"],
                             claim_dir=r["expected_dir"], matrix_sees=sn, direction_agrees=dir_ok, symptom=r["symptom"], expected_obs=r["expected_obs"], doc=r["doc_title"]))
    consensus = defaultdict(set)
    for r in pairs:
        consensus[(r["cause_id"], r["check_id"])].add(r["manufacturer"].strip().lower())
    multi = {k: sorted(v) for k, v in consensus.items() if len(v) >= 2}
    corrections = []
    for (c, k), ms in multi.items():
        cell = cells[(c, k)]
        if cell["cls"] == "DET_NOT_SEEN":
            corrections.append(dict(cause=c, check=k, why="two or more manufacturers say the check reveals the cause; the matrix says it is not seen", manufacturers=ms))
    for x in rows_cmp:
        if x["direction_agrees"] is False:
            corrections.append(dict(cause=x["cause"], check=x["check"], why=f"direction: document says {x['claim_dir']}, matrix says {x['matrix_sign']}", manufacturers=[x["manufacturer"]]))
    return dict(n_scored=len(S), manufacturers=mfrs, n_mapped=len(mapped), coverage=(len(mapped) / len(S) if S else float("nan")),
                new_causes={k: sorted(v) for k, v in new_c.items()}, new_checks={k: sorted(v) for k, v in new_k.items()},
                claims_per_cause={c: len(v) for c, v in by_cause.items()}, mfrs_per_cause={c: len({r["manufacturer"].strip().lower() for r in v}) for c, v in by_cause.items()},
                claims_per_check={k: len(v) for k, v in by_check.items()}, n_pairs=len(pairs), presence=(p_ok / len(pairs) if pairs else float("nan")),
                direction=(d_ok / d_n if d_n else float("nan")), n_direction=d_n, comparison=rows_cmp, consensus=[dict(cause=c, check=k, manufacturers=v) for (c, k), v in sorted(multi.items())],
                corrections=corrections, n_checks_nonphysics=sum(1 for r in S if r["check_id"] in ("K04", "K20")))


# ------------------------------------------------------------------------------------------------ verification sample (blind re-mapping)
def verification_sample(rows: list[dict]) -> list[dict]:
    S = scored(rows)
    v = OEM_CONFIG["VERIFY"]
    n = int(min(max(round(v["fraction"] * len(S)), v["min"]), v["max"], len(S)))
    ids = sorted(r["claim_id"] for r in S)
    pick = set(np.random.default_rng(v["seed"]).choice(len(ids), size=n, replace=False).tolist())
    chosen = {ids[i] for i in pick}
    return [r for r in S if r["claim_id"] in chosen]


def verification_summary(rows: list[dict], ver: list[dict]) -> dict:
    by = {r["claim_id"]: r for r in rows}
    readable = [x for x in ver if x["status"] in ("CONFIRMED", "PARTLY", "NOT_FOUND")]
    conf = [x for x in readable if x["status"] == "CONFIRMED"]
    cause_ok = [x for x in readable if x.get("cause_id_blind") and x["claim_id"] in by and x["cause_id_blind"] == by[x["claim_id"]]["cause_id"]]
    check_ok = [x for x in readable if x.get("check_id_blind") and x["claim_id"] in by and x["check_id_blind"] == by[x["claim_id"]]["check_id"]]
    return dict(n=len(ver), unreadable=sum(1 for x in ver if x["status"] == "UNREADABLE"), readable=len(readable), confirmed=len(conf), partly=sum(1 for x in readable if x["status"] == "PARTLY"),
                not_found=sum(1 for x in readable if x["status"] == "NOT_FOUND"), confirmed_rate=(len(conf) / len(readable) if readable else float("nan")),
                cause_agree=(len(cause_ok) / len(readable) if readable else float("nan")), check_agree=(len(check_ok) / len(readable) if readable else float("nan")),
                dropped=sorted(x["claim_id"] for x in ver if x["status"] == "NOT_FOUND"))


def scorecard(a: dict, vs: dict | None) -> list[tuple[str, bool | None, str]]:
    B, F = OEM_CONFIG["BAR"], OEM_CONFIG["FLOOR"]
    descriptive = a["n_scored"] < F["claims"] or len(a["manufacturers"]) < F["manufacturers"]
    tag = (lambda ok: None if descriptive else bool(ok))  # noqa: E731
    out = []
    out.append(("O1", tag(a["coverage"] >= B["coverage"]), f"{a['n_mapped']} of {a['n_scored']} scored claims ({a['coverage'] * 100:.0f}%) map onto one of our 17 causes (needs >= {B['coverage'] * 100:.0f}%)"))
    out.append(("O2", tag(a["presence"] >= B["presence"]), f"for {a['n_pairs']} claims naming one of our causes and a physical check, the matrix says that check sees that cause in {a['presence'] * 100:.0f}% (needs >= {B['presence'] * 100:.0f}%)"))
    out.append(("O3", tag(a["direction"] >= B["direction"]), f"direction agrees in {a['direction'] * 100:.0f}% of {a['n_direction']} comparable claims (needs >= {B['direction'] * 100:.0f}%)"))
    nc = {k: v for k, v in a["new_causes"].items() if len(v) >= B["new_support"]}
    out.append(("O4", tag(len(nc) >= B["new_count"]), f"{len(nc)} new causes supported by >= {B['new_support']} manufacturers (needs >= {B['new_count']}): " + (", ".join(f"{k} ({len(v)})" for k, v in nc.items()) or "none")))
    nk = {k: v for k, v in a["new_checks"].items() if len(v) >= B["new_support"]}
    out.append(("O5", tag(len(nk) >= B["new_count"]), f"{len(nk)} new checks supported by >= {B['new_support']} manufacturers (needs >= {B['new_count']}): " + (", ".join(f"{k} ({len(v)})" for k, v in nk.items()) or "none")))
    thin = [c for c, n in a["claims_per_cause"].items() if n <= B["thin_max_claims"]]
    out.append(("O6", tag(len(thin) >= B["thin_causes"]), f"{len(thin)} of 17 causes have <= {B['thin_max_claims']} scored claim: " + ", ".join(thin)))
    if vs is None:
        out.append(("O7", None, "verification not run"))
        out.append(("O8", None, "verification not run"))
    else:
        out.append(("O7", bool(vs["confirmed_rate"] >= B["verified"]), f"{vs['confirmed']} of {vs['readable']} verified claims confirmed ({vs['confirmed_rate'] * 100:.0f}%; needs >= {B['verified'] * 100:.0f}%); {vs['partly']} partly, {vs['not_found']} not found, {vs['unreadable']} unreadable"))
        out.append(("O8", bool(vs["cause_agree"] >= B["blind_mapping"]), f"blind re-mapping agrees on the cause for {vs['cause_agree'] * 100:.0f}% and on the check for {vs['check_agree'] * 100:.0f}% of verified claims (needs cause >= {B['blind_mapping'] * 100:.0f}%)"))
    out.append(("O9", tag(len(a["corrections"]) >= 1), f"{len(a['corrections'])} candidate corrections to the matrix (direction conflicts, or two or more manufacturers against a 'not seen' cell)"))
    return out


def write_report(out: Path, a: dict, vs: dict | None, sc: list, rows: list[dict], suffix: str = "", note: str = "") -> None:
    out.mkdir(parents=True, exist_ok=True)
    with open(out / f"oem_comparison{suffix}.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["# " + DISCLAIMER])
        cols = ["claim_id", "manufacturer", "cause", "check", "cls", "p_sep", "matrix_sign", "claim_dir", "matrix_sees", "direction_agrees", "symptom", "expected_obs", "doc"]
        wr.writerow(cols)
        for x in a["comparison"]:
            wr.writerow([x[c] if not isinstance(x[c], float) else f"{x[c]:.3f}" for c in cols])
    L = ["# Manufacturer documents against the physics matrix" + (f" ({note})" if note else ""), "",
         "**Claims extracted from manufacturers' own documents (paraphrase only, no document text stored) compared with a physics-model matrix; the documents are evidence about what manufacturers say, not field evidence about how often causes occur.**", "",
         f"Frozen hash `{frozen_hash()}`. Scored claims: {a['n_scored']} from {len(a['manufacturers'])} manufacturers ({', '.join(a['manufacturers'])}).", "",
         "## Scorecard (rules and predictions frozen before extraction)", "", "| | holds | evidence |", "|---|---|---|"]
    L += [f"| {k} | {'-' if ok is None else ('yes' if ok else 'NO')} | {ev} |" for k, ok, ev in sc]
    L += ["", "## Claims per cause (scored, DIRECT and fully read)", "", "| cause | claims | manufacturers |", "|---|---|---|"]
    for c in CAUSE_IDS:
        L.append(f"| {c} | {a['claims_per_cause'][c]} | {a['mfrs_per_cause'][c]} |")
    L += ["", "## Causes the documents use that our taxonomy lacks", "", "| new cause | manufacturers |", "|---|---|"]
    L += [f"| {k} | {', '.join(v)} |" for k, v in sorted(a["new_causes"].items(), key=lambda kv: -len(kv[1]))] or ["| (none) | |"]
    L += ["", "## Checks the documents use that our catalogue lacks", "", "| new check | manufacturers |", "|---|---|"]
    L += [f"| {k} | {', '.join(v)} |" for k, v in sorted(a["new_checks"].items(), key=lambda kv: -len(kv[1]))] or ["| (none) | |"]
    L += ["", "## Claims per check (scored)", "", "| check | claims |", "|---|---|"] + [f"| {k} ({K.BY_ID[k].name[:50]}) | {n} |" for k, n in a["claims_per_check"].items() if n]
    L += ["", "## Pairs two or more manufacturers agree on (cause, check) and what the matrix says", "", "| cause | check | manufacturers | matrix class |", "|---|---|---|---|"]
    cells = {(x["cause"], x["check"]): x["cls"] for x in a["comparison"]}
    L += [f"| {x['cause']} | {x['check']} | {', '.join(x['manufacturers'])} | {cells.get((x['cause'], x['check']), '?')} |" for x in a["consensus"]] or ["| (none) | | | |"]
    L += ["", "## Candidate corrections to the matrix (not applied)", "", "| cause | check | why | manufacturers |", "|---|---|---|---|"]
    L += [f"| {x['cause']} | {x['check']} | {x['why']} | {', '.join(x['manufacturers'])} |" for x in a["corrections"]] or ["| (none) | | | |"]
    L += ["", "## Disagreements and agreements, claim by claim", "", "| claim | manufacturer | cause | check | matrix class | matrix sees | direction agrees | observation |", "|---|---|---|---|---|---|---|---|"]
    for x in sorted(a["comparison"], key=lambda x: (x["matrix_sees"], str(x["direction_agrees"]))):
        L.append(f"| {x['claim_id']} | {x['manufacturer']} | {x['cause']} | {x['check']} | {x['cls']} | {x['matrix_sees']} | {x['direction_agrees']} | {x['expected_obs'][:90]} |")
    if vs:
        L += ["", "## Verification sample (independent re-reading, blind re-mapping)", "", "```", json.dumps(vs, indent=1), "```"]
    L += ["", "Limits: the documents are mostly about the manufacturer's own product, not about building-level loop causes; a mention in a manual says a cause exists, not how often; extraction is by readers that can err (see verification); "
          "copyright and terms of use of the documents have not been reviewed by a lawyer, so the claims file is an internal research artifact."]
    (out / f"OEM_REPORT{suffix}.md").write_text("\n".join(L) + "\n")
