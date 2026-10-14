"""Gates for Addendum 44 (study_missed): the arms are additive, the registry is restored, the matching rule does what the addendum says."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from docmismatch.troubleshoot.v1 import causes as C  # noqa: E402
from docmismatch.troubleshoot.v2 import study_missed as X  # noqa: E402


def test_empty_proposal_equals_fixed_model():
    arms = {"A": X.arm_models([])["A"]}
    arms["B"] = X.proposal_to_model(dict(proposer="e", candidates=[], mode="label_first"))
    arms["B"] = dict(specs=arms["B"]["specs"], shares=arms["B"]["shares"], checks=X.with_profiles(X.K.CATALOGUE, arms["B"]["profiles"]) + tuple(arms["B"]["checks"]))
    res = X.run_cell(0.10, "T3", arms, n=120)
    for r in res:
        assert r["A"] == r["B"]


def test_registry_restored():
    before = set(C.ALL_BY_ID)
    with X.registered(X.hidden_specs()):
        assert "fire_damper_closed" in C.ALL_BY_ID
    assert set(C.ALL_BY_ID) == before


def test_match_modes():
    c = dict(id="return_air_pressure_imbalance", label="Return/exhaust or room pressure imbalance", detail="blocked return (closed fire/transfer damper, undercut door)")
    assert X.match_cause(c, "frozen") == "fire_damper_closed"
    assert X.match_cause(c, "label_first") == "return_blocked"
    assert X.match_cause(dict(id="x", label="unrelated thing", detail="nothing here")) is None


def test_decoy_gets_own_id_and_second_match_is_decoy():
    prop = dict(proposer="q", mode="label_first", candidates=[
        dict(id="a", label="Supply air temperature wrong", detail="", share=0.1), dict(id="b", label="Chilled water failure", detail="", share=0.1), dict(id="c", label="zzz", detail="", share=0.1)])
    m = X.proposal_to_model(prop)
    ids = [s.id for s in m["specs"]]
    assert ids[0] == "sat_off" and ids[1] == "q_b" and ids[2] == "q_c"
    assert abs(m["shares"]["sat_off"] - 0.1 / X.OTHER_MASS) < 1e-12
