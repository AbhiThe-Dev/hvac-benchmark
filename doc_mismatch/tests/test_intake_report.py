"""Guards for the intake readiness report: the channel-signal table is exact, statuses follow from what is recorded, dates and quality problems are flagged."""
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _intake_world import CLAIMS, make_building  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import intake_report as R  # noqa: E402
from docmismatch.evidence import _pair_errors, make_context  # noqa: E402
from docmismatch.intake import PointQA  # noqa: E402


def _perturbed(x: np.ndarray, is_temp: bool, rng) -> np.ndarray:
    """a very different series of the same kind: wide random values, and (for flows / powers) a block of zeros so duty-cycle statistics change too"""
    if is_temp:
        return float(np.nanmean(x)) + rng.uniform(-15, 15, len(x))
    y = rng.uniform(0.2, 3.0, len(x)) * abs(float(np.nanmean(x)))
    y[rng.random(len(x)) < 0.3] = 0.0
    return y


# ---------------------------------------------------------------------------------------------- the table is exact
def test_channel_signal_table_is_exactly_what_the_evidence_engine_reads():
    fb = make_building(T=96, seed=3)
    base = fb.base()
    rng = np.random.default_rng(0)
    checked = set()
    for c in fb.claims:
        slot, o, m = c.slot, c.owner, c.member
        if slot not in R.CHANNEL_SIGNALS:
            continue
        ev = dict(fb.ev)
        ctx = make_context(base, ev) if slot == "vav_zone" else None         # keep the building-wide context fixed: only the pair's own series may move
        ref = _pair_errors(base, ev, slot, o, m, slice(None), ctx)
        eq = {"o": o, "m": m}
        expected = {}                                                          # series key -> set of channels that must change
        for k, needs in R.CHANNEL_SIGNALS[slot].items():
            for who, sig in needs:
                sig = R.resolve(sig, fb.equipment[eq[who]]["kind"], fb.equipment[eq[who]].get("function", ""))
                if "|" in sig:                                                # cooling coil: rate_s when it exists, else rate
                    sig = "rate_s" if f"{eq[who]}|rate_s" in ev else "rate"
                expected.setdefault(f"{eq[who]}|{sig}", set()).add(k)
        optional = {f"{eq[who]}|{sig}" for who, sig in R.OPTIONAL_SIGNALS.get(slot, [])}
        for key in [k for k in ev if k.split("|")[0] in (o, m)]:
            ev2 = dict(ev)
            ev2[key] = _perturbed(ev[key], key.split("|")[1] in ("temp", "t_in", "t_dis", "sat", "mat", "t_sup", "t_ret", "t_out", "value", "oat"), rng)
            new = _pair_errors(base, ev2, slot, o, m, slice(None), ctx)
            changed = {k for k in range(3) if not np.isclose(new[k], ref[k], rtol=1e-9, atol=1e-12, equal_nan=True)}
            if key in optional:
                assert changed, f"{slot} {o}->{m}: optional {key} should change the output"
                continue
            assert changed == expected.get(key, set()), f"{slot} {o}->{m}: perturbing {key} changed channels {changed}, table says {expected.get(key, set())}"
            checked.add((slot, key.split("|")[1]))
    assert {s for s, _ in checked} == set(R.CHANNEL_SIGNALS)                  # every connection type was exercised


# ---------------------------------------------------------------------------------------------- readiness
def test_complete_building_is_fully_testable():
    r = R.slot_readiness(make_building(T=96))
    assert {s: d["status"] for s, d in r.items()} == {s: "FULL" for s in r} and len(r) == 10


def test_missing_vav_airflow_blocks_exactly_the_channels_that_read_it():
    r = R.slot_readiness(make_building(T=96, drop=("VAV-1|flow", "VAV-2|flow", "VAV-3|flow")))
    vz = r["vav_zone"]
    assert vz["channels"][0] == 0.0 and vz["channels"][2] == 0.0 and vz["channels"][1] == 1.0 and vz["status"] == "PARTIAL" and vz["supported"] == [1]
    assert vz["missing"][("VAV", "flow", "not recorded")] == 3
    assert r["ahu_vav"]["channels"][1] == 0.0 and r["ahu_vav"]["channels"][0] == 1.0        # ch 0 reads inlet temperature and AHU supply temperature, not flow


def test_missing_coil_power_makes_every_coil_check_untestable():
    r = R.slot_readiness(make_building(T=96, drop=("Coil-1", "Coil-2", "Coil-3")))
    for slot in ("branch_coil", "coil_ahu", "coil_vav"):
        assert r[slot]["status"] == "NOT TESTABLE", slot


def test_cooling_coil_accepts_either_rate_but_heating_coil_needs_its_own_rate():
    only_total = R.slot_readiness(make_building(T=96, drop=("Coil-2|rate_s",)))["coil_ahu"]           # cooling coil falls back to its total rate
    assert only_total["channels"] == {0: 1.0, 1: 1.0, 2: 1.0}
    no_heating = R.slot_readiness(make_building(T=96, drop=("Coil-1|rate",)))["coil_ahu"]
    assert no_heating["channels"][0] == 0.5                                                             # Coil-1 (heating) unusable, Coil-2 fine


def test_flat_and_sparse_series_are_reported_with_the_right_reason():
    fb = make_building(T=96)
    fb.ev["VAV-2|flow"] = np.full(96, 4.0)
    sparse = fb.ev["VAV-3|flow"].copy()
    sparse[np.arange(96) % 10 != 0] = np.nan
    fb.ev["VAV-3|flow"] = sparse
    miss = R.slot_readiness(fb)["vav_zone"]["missing"]
    assert miss[("VAV", "flow", "flat")] == 1 and miss[("VAV", "flow", "low coverage")] == 1


def test_report_names_what_would_unlock_more_and_carries_the_vav_zone_caveat():
    text = R.report(make_building(T=96, drop=("VAV-1|flow", "VAV-2|flow", "VAV-3|flow", "VAV-1|reheat")))
    assert "VAV `flow` not recorded on 3 unit(s) (needed by ch 0,2)" in text
    assert "cannot tell which box serves which room" in text and "1 box(es) have no `reheat`" in text
    assert "| loop_branch | 2 | 1 | 1 | 0 |" in text and "| branch_coil | 2 | 1 | 0 | 1 |" in text                                                    # documented / verified right / verified wrong / unknown


# ---------------------------------------------------------------------------------------------- dates and quality
def test_alignment_flags_missing_stale_and_ordered_dates():
    ctx = lambda **kw: make_building(T=24 * 44, start=datetime(2021, 7, 5), context=kw)              # trends 2021-07-05 .. 2021-08-18  # noqa: E731
    assert "as_built_date is missing" in R.alignment_flags(ctx())[0]
    assert R.alignment_flags(ctx(as_built_date="2021-06-20")) == []
    stale = R.alignment_flags(ctx(as_built_date="2019-06-01", modifications=[{"date": "2020-03-01", "note": "coil replaced"}]))
    assert len(stale) == 1 and "coil replaced" in stale[0] and "before the start of the trend window" in stale[0]
    assert "no modifications are listed" in R.alignment_flags(ctx(as_built_date="2019-06-01"))[0]
    assert "before the as-built markup" in R.alignment_flags(ctx(as_built_date="2021-09-01"))[0]
    inside = R.alignment_flags(ctx(as_built_date="2021-06-01", modifications=[{"date": "2021-07-20", "note": "valve swap"}]))
    assert "inside the trend window" in inside[0]


def test_quality_flags_list_each_problem_once_per_point():
    fb = make_building(T=48)
    fb.qa = {"a": PointQA("a", n_raw=100, n_out_of_range=5, coverage=0.5, longest_gap_h=100, n_duplicate_ts=2), "b": PointQA("b", n_raw=100, n_valid=100, coverage=1.0)}
    (flag,) = R.quality_flags(fb)
    assert flag.startswith("`a`") and "only 50%" in flag and "longest gap 100 h" in flag and "5 out-of-range" in flag and "2 duplicate" in flag
