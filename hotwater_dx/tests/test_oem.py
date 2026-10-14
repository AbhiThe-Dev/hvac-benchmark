import numpy as np

from hotwater_dx import oem as OE


def row(i, mfr="acme", cause="heater_setpoint_low", check="K01", d="-1", doc="d1", loc="t1", ev="DIRECT", rd="READ_FULL", anchor="outlet temperature low"):
    return dict(claim_id=f"c{i}", manufacturer=mfr, doc_title="t", doc_type="troubleshooting_guide", doc_url=f"http://x/{doc}", doc_rev="", locator=loc, product_class="storage_heater",
                symptom="not_hot_enough", cause_text="x", cause_id=cause, check_text="y", check_id=check, expected_obs="low", expected_dir=d, action="a", evidence=ev, read_status=rd, anchor=anchor)


def cells():
    base = dict(cls="DET_NOT_SEEN", p_sep=0.0, sign=0)
    return {("heater_setpoint_low", "K01"): dict(base, cls="DET_SEEN", p_sep=1.0, sign=-1), ("pump_failed", "K05"): dict(base, cls="DET_SEEN", p_sep=1.0, sign=-1),
            ("crossover", "K05"): dict(base), ("crossover", "K01"): dict(base)}


def test_validation_catches_vocabulary_and_anchor_errors():
    bad = row(1, cause="not_a_cause")
    bad2 = row(2, anchor="one two three four five six seven eight nine")
    bad3 = row(3, ev="DIRECT", anchor="")
    probs = OE.validate([row(0), bad, bad2, bad3, row(0)])
    joined = " ".join(probs)
    assert "cause_id" in joined and "anchor longer" in joined and "without an anchor" in joined and "duplicate" in joined
    assert OE.validate([row(0), row(5, cause="NEW:no_power", check="NEW:verify_power")]) == []


def test_only_direct_fully_read_claims_are_scored_and_duplicates_count_once():
    rows = [row(1), row(2, ev="INFERRED"), row(3, rd="SNIPPET"), row(4), row(5, mfr="other")]
    s = OE.scored(rows)
    assert {r["claim_id"] for r in s} == {"c1", "c5"}                  # c4 duplicates c1; c2 and c3 are never scored
    assert {r["claim_id"] for r in OE.scored(rows, dropped={"c1"})} == {"c4", "c5"}   # dropping c1 leaves its duplicate c4 as the representative


def test_presence_direction_and_corrections():
    rows = [row(1), row(2, mfr="b", d="1", doc="d2"), row(3, mfr="b", cause="crossover", check="K05", d="-1", doc="d3"), row(4, mfr="c", cause="crossover", check="K05", d="-1", doc="d4"),
            row(5, cause="NEW:no_power", check="NONE", doc="d5"), row(6, cause=OE.OUT, check="NONE", doc="d6")]
    a = OE.analyse(rows, cells())
    assert a["n_scored"] == 6 and a["n_mapped"] == 4
    assert abs(a["presence"] - 0.5) < 1e-9                              # two of the four mapped pairs are 'seen' in the matrix
    assert a["n_direction"] == 2 and abs(a["direction"] - 0.5) < 1e-9   # one agrees (-1), one conflicts (+1)
    why = " | ".join(x["why"] for x in a["corrections"])
    assert "direction" in why and "not seen" in why                     # a direction conflict and two manufacturers against a 'not seen' cell
    assert a["new_causes"] == {"NEW:no_power": ["acme"]}


def test_floor_makes_the_scorecard_descriptive():
    a = OE.analyse([row(1)], cells())
    sc = OE.scorecard(a, None)
    assert all(ok is None for k, ok, _ in sc if k in ("O1", "O2", "O3", "O4", "O5", "O6", "O9"))


def test_verification_sample_is_deterministic_and_summary_counts():
    rows = [row(i, doc=f"d{i}", loc=f"t{i}") for i in range(200)]
    s1, s2 = OE.verification_sample(rows), OE.verification_sample(rows)
    assert [r["claim_id"] for r in s1] == [r["claim_id"] for r in s2] and len(s1) == 50
    ver = [dict(claim_id="c1", status="CONFIRMED", cause_id_blind="heater_setpoint_low", check_id_blind="K01"), dict(claim_id="c2", status="NOT_FOUND", cause_id_blind="pump_failed", check_id_blind="K05"),
           dict(claim_id="c3", status="UNREADABLE", cause_id_blind="", check_id_blind="")]
    vs = OE.verification_summary(rows, ver)
    assert vs["readable"] == 2 and vs["confirmed"] == 1 and vs["dropped"] == ["c2"] and abs(vs["cause_agree"] - 0.5) < 1e-9
