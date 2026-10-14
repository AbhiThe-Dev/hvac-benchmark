"""Guards for the field pool builder: same layout as the simulation pools, evidence identical to a direct engine call, missing / gappy data become NaN not garbage."""
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _intake_world import CLAIMS, EQUIPMENT, make_building  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import intake as I  # noqa: E402
from docmismatch.active.pools import DAYS_PER_WINDOW_PICK, SEASON_OF_WINDOW  # noqa: E402
from docmismatch.data import SLOTS, load_base  # noqa: E402
from docmismatch.evidence import make_context, make_evidence, pair_errors  # noqa: E402
from docmismatch.field_pool import build_field_pool  # noqa: E402

T = 24 * 44


def _day(ev, a):
    return {k: v[a:a + 24] for k, v in ev.items()}


def test_pool_layout_follows_the_simulation_convention():
    fb = make_building(T=T, start=datetime(2021, 7, 5))
    pool = build_field_pool(fb)
    assert pool.n_slices == 7 and list(pool.group) == [0] * 6 + [1]                        # 6 day-slices in window 0 (days 0, 8, ... 40) and the first day of window 1
    oat = fb.ev["ENV|oat"]
    np.testing.assert_allclose(pool.ctx[0, :2], [oat[:24].mean(), oat[:24].max() - oat[:24].min()])
    assert list(pool.season) == [SEASON_OF_WINDOW[4]] * 6 + [SEASON_OF_WINDOW[5]]           # window centres fall on days 206 and 248 of the year (window index 4 and 5 of the simulation year)
    assert set(pool.slots) == set(s for s in SLOTS if s not in ("fan_ahu",))
    sp = pool.slots["vav_zone"]
    assert sp.E.shape == (7, 4, 3, 3) and np.isnan(sp.E[:, 3]).all() and sp.owners == ["VAV-1", "VAV-2", "VAV-3"]


def test_evidence_equals_a_direct_engine_call_on_the_same_day():
    fb = make_building(T=T)
    pool, base = build_field_pool(fb), fb.base()
    days = [d for d in DAYS_PER_WINDOW_PICK]
    for slot, sp in pool.slots.items():
        for i, d in enumerate(days[:3]):
            ev = _day(fb.ev, d * 24)
            ctx = make_context(base, ev) if slot == "vav_zone" else None
            for a, o in enumerate(sp.owners):
                for b, m in enumerate(sp.members):
                    np.testing.assert_allclose(sp.E[i, :3, a, b], pair_errors(base, ev, slot, o, m, slice(None), ctx), rtol=1e-12, atol=1e-12, equal_nan=True, err_msg=f"{slot} {o}->{m} day {d}")


def test_unrecorded_signals_give_nan_channels_not_garbage():
    pool = build_field_pool(make_building(T=T, drop=("AHU-1|flow", "VAV-1|flow", "VAV-2|flow", "VAV-3|flow")))
    assert np.isnan(pool.slots["coil_ahu"].E[:, :3]).all() and np.isnan(pool.slots["ahu_sat"].E[:, :3]).all()      # all three channels read the AHU flow
    vz = pool.slots["vav_zone"].E
    assert np.isnan(vz[:, 0]).all() and np.isnan(vz[:, 2]).all() and np.isfinite(vz[:, 1]).all()                    # only channel 1 avoids the box flow
    assert np.isfinite(pool.slots["loop_pump"].E[:, :3]).all()                                                     # untouched slots are unaffected


def test_short_gaps_are_filled_and_sparse_days_are_masked():
    fb = make_building(T=T)
    clean = build_field_pool(make_building(T=T))
    z = fb.ev["Zone-1|temp"].copy()
    z[5:8] = np.nan                                            # 3 missing hours on day 0: filled by interpolation
    z[192:192 + 15] = np.nan                                   # 15 missing hours on day 8 (only 9 valid): the slice is unusable for this series
    fb.ev["Zone-1|temp"] = z
    pool = build_field_pool(fb)
    vz, ref = pool.slots["vav_zone"], clean.slots["vav_zone"]
    j = vz.members.index("Zone-1")
    assert np.isfinite(vz.E[0, :3, :, j]).all()                                                    # day 0 still computed (E is slice x channel x owner x member), close to the clean value
    np.testing.assert_allclose(vz.E[0, 1, :, j], ref.E[0, 1, :, j], atol=0.15)
    assert np.isnan(vz.E[1, :3, :, j]).all()                                                       # day 8: the zone temperature is unusable -> every channel that reads it is missing
    assert np.isfinite(vz.E[1, :3, :, vz.members.index("Zone-2")]).all()                          # other zones unaffected


def test_truth_documented_and_verified_arrays_hold_only_what_was_checked():
    claims = [I.Claim("VAV-1", "Zone-1", "vav_zone", "yes"), I.Claim("VAV-3", "Zone-2", "vav_zone", "no", "VAV-2"), I.Claim("VAV-3", "Zone-3", "vav_zone", "unknown")]
    pool = build_field_pool(make_building(T=T, claims=claims))
    sp, meta = pool.slots["vav_zone"], pool.field_meta["vav_zone"]
    assert sp.members == ["Zone-1", "Zone-2", "Zone-3"]
    assert list(meta["documented"]) == [0, 2, 2] and list(sp.truth) == [0, 1, -1] and meta["verified"] == ["yes", "no", "unknown"]


def test_outdoor_temperature_is_required():
    with pytest.raises(ValueError, match="outdoor"):
        build_field_pool(make_building(T=T, drop=("ENV",)))


# ---------------------------------------------------------------------------------------------- the real simulated building, through a BAS-style export
def test_simulated_building_survives_export_import_and_gives_the_same_evidence(tmp_path):
    try:
        base = load_base("sys07_vav_reheat")
    except Exception:
        pytest.skip("simulated bases not built (scripts/01_simulate.py)")
    ev = {k: v for k, v in make_evidence(base, 4, seed=1).items() if k.split("|")[1] in I.SIGNALS[base.nodes[k.split("|")[0]]["kind"]]}
    equipment = {i: dict(kind=n["kind"], function={"Heating_Coil": "heating", "Cooling_Coil": "cooling"}.get(n["brick_type"], ""), medium=n.get("medium") or "") for i, n in base.nodes.items()}
    claims = [I.Claim(o, m, slot, "yes") for slot, es in base.slot_edges.items() for o, m in es]
    I.write_export(tmp_path, equipment, ev, claims, datetime(2021, 7, 5), sample_min=60)          # US units, hourly
    fb = I.load_export(tmp_path)
    assert fb.n_hours == 1008 and set(fb.ev) == set(ev)
    for k in ev:
        np.testing.assert_allclose(fb.ev[k], ev[k], rtol=1e-7, atol=1e-7, err_msg=k)
    pool = build_field_pool(fb)
    checked = 0
    for slot, sp in pool.slots.items():
        for i, d in enumerate(DAYS_PER_WINDOW_PICK):
            sl = slice(d * 24, (d + 1) * 24)
            ctx = make_context(base, ev, sl) if slot == "vav_zone" else None
            for a, o in enumerate(sp.owners):
                for b, m in enumerate(sp.members):
                    np.testing.assert_allclose(sp.E[i, :3, a, b], pair_errors(base, ev, slot, o, m, sl, ctx), rtol=1e-6, atol=1e-8, equal_nan=True, err_msg=f"{slot} {o}->{m} day {d}")
                    checked += 1
    assert checked > 500


def test_chunked_export_is_judged_over_days_with_data_and_yields_slices_from_each_chunk():
    from _intake_world import make_series
    ev = make_series(T=24 * 3, seed=5)
    n = 24 * 130
    full = {k: np.concatenate([v, np.full(n - 2 * len(v), np.nan), v]) for k, v in ev.items()}          # 3 days, 100+ days of nothing, 3 days
    fb = make_building(T=n)
    fb.ev = full
    fb.active_days = I.active_day_mask(full, n)
    assert fb.active_days.sum() == 6 and fb.n_chunks == 2
    pool = build_field_pool(fb)
    assert pool.n_slices == 6 and sorted(set(pool.group)) == [0, 3]                                     # 3 day-slices from each chunk; chunk 2 sits in window 3
    assert np.isfinite(pool.slots["vav_zone"].E[:, :3]).any(axis=(1, 2, 3)).all()


# ---------------------------------------------------------------------------------------------- options added for Addendum 17 (defaults must not change behaviour)
def test_slice_days_all_uses_every_day_with_data_and_default_is_unchanged():
    fb = make_building(T=T)
    assert build_field_pool(fb).n_slices == 7                                                             # default: the engine's positions
    pool = build_field_pool(fb, slice_days="all")
    assert pool.n_slices == 44 and list(pool.group).count(0) == 42 and list(pool.group).count(1) == 2     # every day of the 44
    assert len(pool.field_slice_hours) == pool.n_slices and pool.field_slice_hours[:3] == [0, 24, 48]
    with pytest.raises(ValueError, match="slice_days"):
        build_field_pool(fb, slice_days="some")


def test_require_oat_false_builds_without_weather_and_ignores_it_for_day_choice():
    fb = make_building(T=T, drop=("ENV",))
    pool = build_field_pool(fb, require_oat=False)
    assert pool.n_slices == 7 and np.all(pool.ctx[:, :2] == 0.0)
    with pytest.raises(ValueError, match="outdoor"):
        build_field_pool(fb)                                                                                # default still insists on it
    full = build_field_pool(make_building(T=T), require_oat=False)
    assert full.n_slices == 7 and np.any(full.ctx[:, 0] != 0.0)                                            # with a weather series the context is real either way


def test_mask_uninformative_false_returns_raw_channels_where_the_engine_masks_flat_ones():
    fb = make_building(T=T)
    fb.ev["VAV-1|flow"] = np.full(T, 4.0)                                                                  # a flat box flow
    masked = build_field_pool(fb).slots["vav_zone"]
    raw = build_field_pool(fb, mask_uninformative=False).slots["vav_zone"]
    a = masked.owners.index("VAV-1")
    assert np.isnan(masked.E[:, 0, a, :]).all() and np.isfinite(raw.E[:, 0, a, :]).all()                     # default masks channel 0; raw does not
    b = masked.owners.index("VAV-2")
    np.testing.assert_allclose(masked.E[:, 1, b, :], raw.E[:, 1, b, :])                                      # unflat boxes are identical either way
