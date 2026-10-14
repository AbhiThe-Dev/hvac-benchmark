"""Tests of the work-order screen's scoring (Addendum 32). Synthetic labels only."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from docmismatch import workorder_score as S  # noqa: E402
from docmismatch import workorders as W  # noqa: E402


def lab(**kw):
    return {k: bool(kw.get(k, False)) for k in W.KINDS}


def test_norm_and_quote_handling():
    assert S.norm("  AHU-3   Fan\nOFF ") == "ahu-3 fan off"
    assert S.quote_of("null") is None and S.quote_of(None) is None and S.quote_of("") is None and S.quote_of("fan off") == "fan off"


def test_as_bool_takes_only_true():
    assert S.as_bool(True) and S.as_bool("true") and S.as_bool(" True ")
    assert not S.as_bool("false") and not S.as_bool(None) and not S.as_bool("yes") and not S.as_bool(1)


def test_load_and_coverage(tmp_path):
    p = tmp_path / "a.jsonl"
    p.write_text("\n".join(json.dumps({"sid": s, "A": None, "B": None, "C": None, "D": None}) for s in ("S1", "S2")) + "\n\n")
    objs = S.load_jsonl([p])
    S.check_coverage(objs, ["S1", "S2"], "x")
    with pytest.raises(ValueError):
        S.check_coverage(objs, ["S1", "S2", "S3"], "x")
    with pytest.raises(ValueError):
        S.check_coverage(objs, ["S1"], "x")
    (tmp_path / "b.jsonl").write_text(json.dumps({"sid": "S1"}) + "\n" + json.dumps({"sid": "S1"}) + "\n")
    with pytest.raises(ValueError):
        S.load_jsonl([tmp_path / "b.jsonl"])
    (tmp_path / "c.jsonl").write_text("not json\n")
    with pytest.raises(ValueError):
        S.load_jsonl([tmp_path / "c.jsonl"])
    bad = {"S1": {"sid": "S1", "A": None}}
    with pytest.raises(ValueError):
        S.check_coverage(bad, ["S1"], "x")


def test_extraction_requires_the_quote_to_appear_literally():
    desc = {"S1": "AHU-3 fan will not start again", "S2": "hot"}
    objs = {"S1": {"sid": "S1", "A": "AHU-3", "B": "not start  AGAIN", "C": "wrong box", "D": None}, "S2": {"sid": "S2", "A": None, "B": "null", "C": None, "D": None}}
    e = S.extraction(objs, desc)
    assert e["S1"]["A"] == (True, True) and e["S1"]["B"] == (True, True) and e["S1"]["C"] == (True, False) and e["S1"]["D"] == (False, False)
    assert e["S2"]["B"] == (False, False)


def test_kappa_and_agreement_and_disputes():
    assert S.kappa([True, False, True, False], [True, False, True, False]) == 1.0
    assert S.kappa([True, True], [True, True]) is None      # no variation: undefined
    l1 = {"S1": lab(B=True), "S2": lab(), "S3": lab(C=True)}
    l2 = {"S1": lab(B=True), "S2": lab(D=True), "S3": lab()}
    ag = S.agreement(l1, l2)
    assert ag["B"]["agree"] == 3 and ag["D"]["agree"] == 2 and ag["C"]["both_true"] == 0
    assert S.disputes(l1, l2) == [("S2", "D"), ("S3", "C")]


def test_reference_uses_rulings_only_for_disputes_and_refuses_without_them():
    l1 = {"S1": lab(B=True), "S2": lab()}
    l2 = {"S1": lab(B=True), "S2": lab(D=True)}
    with pytest.raises(ValueError):
        S.reference(l1, l2, {})
    ref = S.reference(l1, l2, {"S2": {"D": True}, "S1": {"B": False}})   # a ruling on an agreed item is ignored
    assert ref["S1"]["B"] is True and ref["S2"]["D"] is True and ref["S2"]["B"] is False


def build(n_per=4, universities=("1", "2")):
    """A small world: every order has reference B; the extractor confirms it on all; the keyword search fires on half."""
    desc, uni, ref, ext = {}, {}, {}, {}
    i = 0
    for u in universities:
        for j in range(n_per):
            i += 1
            s = f"S{i:03d}"
            desc[s], uni[s] = ("problem again here" if j % 2 == 0 else "fault as before") + " x", u
            ref[s] = lab(B=True)
            ext[s] = {k: (k == "B", k == "B") for k in W.KINDS}
    return desc, uni, ref, ext


def test_llm_only_counts_confirmed_statements_the_keyword_search_misses():
    desc, uni, ref, ext = build()
    rows = S.per_order(ref, ext, desc)
    assert sum(r["llm_only"] for r in rows.values()) == 4          # 'as before' has no keyword; 'again' does
    assert sum(r["kw_any_decisive"] for r in rows.values()) == 4 and all(r["any_decisive"] for r in rows.values())
    s = S.share(rows, uni, {"1": 1000, "2": 10}, lambda r: r["llm_only"])
    assert s["equal"] == 0.5 and s["min"] == s["max"] == 0.5


def test_unsupported_quotes_and_wrong_kinds_are_not_confirmed():
    desc, uni, ref, ext = build(2)
    ext["S001"]["B"] = (True, False)             # quote not in the text
    ext["S002"]["C"] = (True, True)              # a statement the reference says is absent
    rows = S.per_order(ref, ext, desc)
    assert not rows["S001"]["conf"]["B"] and rows["S001"]["unsupported"]["B"] and not rows["S001"]["llm_only"]
    assert not rows["S002"]["conf"]["C"]
    e, c = S.statement_counts(rows, W.DECISIVE)
    assert e == 4 + 1 and c == 3     # 4 orders x B + S002's C; three B confirmed


def test_volume_weights_differ_from_equal_weights():
    desc, uni, ref, ext = build(2)
    for s in ("S001", "S002"):                       # university 1: both llm-only
        desc[s] = "the same thing"
    rows = S.per_order(ref, ext, desc)
    s = S.share(rows, uni, {"1": 900, "2": 100}, lambda r: r["llm_only"])
    assert s["equal"] == pytest.approx(0.75) and s["volume"] == pytest.approx(0.95)     # university 1: 2 of 2 llm-only; university 2: 1 of 2


def test_kind_table_recall_and_precision():
    desc, uni, ref, ext = build()
    t = S.kind_table(S.per_order(ref, ext, desc), uni, {"1": 10, "2": 10})
    assert t["B"]["truth_n"] == 8 and t["B"]["ext_recall"] == 1.0 and t["B"]["ext_precision"] == 1.0
    assert t["B"]["kw_recall"] == 0.5 and t["B"]["kw_precision"] == 1.0 and t["A"]["ext_precision"] is None and t["A"]["kw_recall"] is None


def test_verdict_rule_and_intervals():
    desc, uni, ref, ext = build(10)
    rows = S.per_order(ref, ext, desc)
    f = S.stop_figures(rows, uni, {"1": 100, "2": 100}, n=200)
    assert f["llm_only"]["equal"] == 0.5 and f["precision"] == 1.0 and f["statements"] == 20
    assert f["llm_only_ci"][0] <= 0.5 <= f["llm_only_ci"][1] and f["precision_ci"] == (1.0, 1.0)
    v = S.verdict(f)
    assert v["stop"] is False and v["why"] == [] and v["straddles"] == []
    f2 = dict(f, llm_only=dict(f["llm_only"], equal=0.05))
    assert S.verdict(f2)["stop"] and "LLM-only" in S.verdict(f2)["why"][0]
    f3 = dict(f, precision=0.6, precision_ci=(0.5, 0.8))
    v3 = S.verdict(f3)
    assert v3["stop"] and "precision" in v3["why"][0] and "precision" in v3["straddles"]
    assert S.verdict(dict(f, precision=None, precision_ci=(float("nan"),) * 2))["stop"]


def test_bootstrap_is_reproducible():
    desc, uni, ref, ext = build(10)
    rows = S.per_order(ref, ext, desc)
    a, b = S.stop_figures(rows, uni, {"1": 1, "2": 1}, n=100), S.stop_figures(rows, uni, {"1": 1, "2": 1}, n=100)
    assert a["llm_only_ci"] == b["llm_only_ci"] and a["precision_ci"] == b["precision_ci"]


def test_llm_only_for_counts_only_the_named_kinds():
    desc, uni, ref, ext = build()
    rows = S.per_order(ref, ext, desc)
    assert S.llm_only_for(rows, uni, {"1": 1, "2": 1}, ("B",))["equal"] == 0.5
    assert S.llm_only_for(rows, uni, {"1": 1, "2": 1}, ("C", "D"))["equal"] == 0.0
