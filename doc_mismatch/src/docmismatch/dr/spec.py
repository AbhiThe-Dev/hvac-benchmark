"""A-priori draw of domain-randomized building specs (see PREREGISTRATION_DR.md).

Every spec dict is a superset of a `sim_spec` topology dict (same keys, so `build_ext._build_envelope` works unchanged) plus the DR keys:
weather transform, SAT strategy / reset, static-pressure reset (fan curve), economizer type + limit, min-OA schedule, equipment efficiencies,
reheat type, distractor faults, telemetry level. Draws are seeded per (suite, index) and never look at any model output.

Suites:  TRAIN: `regime`, `full`, `full_x3`;  TEST (blind): T1_in_range .. T6_compound.
Held out of ALL training suites: SAT strategy `warmest` (zone-demand reset) and `tod_reset` (time-of-day: warmer SAT outside occupied hours); economizers `diff_db`/`diff_enth`; reheat `mixed`; n_ahu = 4 and n_vav > 14;
loops per medium = 3; TEST climates (tampa, palm_springs, arcata, blue_canyon, chicago_amy2013) and weather offsets beyond +-4 K.
"""

from __future__ import annotations

import random

from .. import sim_spec as SS

SPEC_VERSION = 1
TRAIN_CLIMATES = ("sterling_va", "sanfrancisco", "sacramento", "chicago_tmy3", "chicago_amy2012", "golden", "oakland", "los_angeles")
TEST_CLIMATES = ("tampa", "palm_springs", "arcata", "blue_canyon", "chicago_amy2013")
LAYOUTS = [(f, nx, ny) for f in (1, 2, 3) for nx in (2, 3, 4) for ny in (nx, nx + 1, nx + 2) if 6 <= f * nx * ny <= 18]

# operating-regime ranges (train). Wider than the DEV ranges of sim_spec in load, occupancy, setpoint, equipment, infiltration.
REGIME = dict(
    sat=(11.5, 15.5), tile_w=(6.0, 10.0), tile_d=(6.0, 10.0), floor_h=(3.0, 4.0), wwr=(0.15, 0.45), infiltration=(0.0001, 0.0012),
    lights=(4.0, 16.0), equip=(3.0, 20.0), people=(0.02, 0.12), oa_area=(0.0, 0.0010), zone_sigma=(0.10, 0.50),
    occ_start=(5.0, 10.0), occ_end=(16.0, 22.0), night=(0.02, 0.35), weekend=(0.0, 0.60),
    heat_sp=(19.0, 23.0), gap=(1.5, 5.0), min_flow=(0.15, 0.50), heat_sf=(1.05, 1.40), cool_sf=(1.00, 1.40),
    fan_dp=(350.0, 1000.0), hw_t=(60.0, 82.0), hw_dt=(11.0, 25.0), chw_t=(5.5, 9.0), chw_dt=(4.0, 8.0),
    boiler_eff=(0.75, 0.95), chiller_cop=(3.0, 6.0), fan_eff=(0.50, 0.72), night_oa=(0.0, 1.0), min_oa_scale=(0.5, 2.0),
    temp_offset=(-4.0, 4.0), solar_scale=(0.85, 1.15), reset_span=(1.0, 4.0), oa_low=(5.0, 12.0), oa_high=(18.0, 25.0),
    econ_limit_db=(18.0, 26.0), econ_limit_enth=(45000.0, 65000.0), north=(0.0, 90.0),
)
TEST_EXTRA = dict(temp_offset=(-6.0, 6.0), solar_scale=(0.75, 1.25))
SAT_TRAIN, SAT_HELD = ("constant", "oa_reset"), ("warmest", "tod_reset")
ECON_TRAIN, ECON_HELD = ("none", "fixed_db", "fixed_enth"), ("diff_db", "diff_enth")
ECON_OS = dict(none="NoEconomizer", fixed_db="FixedDryBulb", fixed_enth="FixedEnthalpy", diff_db="DifferentialDryBulb", diff_enth="DifferentialEnthalpy")

# suite -> (role, arm membership, topology class, climate set, sat choices, econ choices, reheat choices, distractors, sensor level, regime source)
SUITES: dict[str, dict] = {
    "regime": dict(role="train", n=8, seed=101, topo="small", climates=TRAIN_CLIMATES, sat=SAT_TRAIN, econ=ECON_TRAIN, reheat=("hydronic",), distract=False, sensor="legacy", rng="regime"),
    "full": dict(role="train", n=8, seed=202, topo="full", climates=TRAIN_CLIMATES, sat=SAT_TRAIN, econ=ECON_TRAIN, reheat=("hydronic", "electric"), distract=True, sensor="wide", rng="regime"),
    "full_x3": dict(role="train", n=24, seed=303, topo="full", climates=TRAIN_CLIMATES, sat=SAT_TRAIN, econ=ECON_TRAIN, reheat=("hydronic", "electric"), distract=True, sensor="wide", rng="regime"),
    "T1_in_range": dict(role="test", n=8, seed=1001, topo="small", climates=TRAIN_CLIMATES, sat=("constant",), econ=("none", "fixed_db"), reheat=("hydronic",), distract=False, sensor="estimated", rng="dev"),
    "T2_regime": dict(role="test", n=8, seed=1002, topo="small", climates=TRAIN_CLIMATES, sat=SAT_TRAIN, econ=ECON_TRAIN, reheat=("hydronic",), distract=False, sensor="estimated", rng="regime"),
    "T3_control": dict(role="test", n=8, seed=1003, topo="small", climates=TRAIN_CLIMATES, sat=SAT_HELD, econ=ECON_HELD, reheat=("hydronic",), distract=False, sensor="estimated", rng="regime"),
    "T4_topology": dict(role="test", n=8, seed=1004, topo="held", climates=TRAIN_CLIMATES, sat=SAT_TRAIN, econ=ECON_TRAIN, reheat=("mixed",), distract=False, sensor="estimated", rng="regime"),
    "T5_climate": dict(role="test", n=8, seed=1005, topo="small", climates=TEST_CLIMATES, sat=SAT_TRAIN, econ=ECON_TRAIN, reheat=("hydronic",), distract=False, sensor="estimated", rng="test"),
    "T6_compound": dict(role="test", n=8, seed=1006, topo="held", climates=TEST_CLIMATES, sat=SAT_HELD, econ=ECON_HELD, reheat=("mixed",), distract=False, sensor="estimated", rng="test"),
}
SUITE_ORDER = list(SUITES)
DISTRACTOR_TYPES = ("stuck_sensor", "bias_step", "spikes", "flow_gain_error", "dropout_burst")


def _u(r, lohi, nd=3):
    return round(r.uniform(*lohi), nd)


def _ranges(kind: str) -> dict:
    if kind == "dev":
        d = dict(REGIME)
        d.update(sat=SS.DEV["sat"], infiltration=SS.DEV["infiltration"], lights=SS.DEV["lights"], equip=SS.DEV["equip"], people=SS.DEV["people"],
                 oa_area=SS.DEV["oa_per_area"] if "oa_per_area" in SS.DEV else SS.DEV["oa_area"], zone_sigma=SS.DEV["zone_sigma"], occ_start=SS.DEV["occ_start"],
                 occ_end=SS.DEV["occ_end"], night=SS.DEV["night"], weekend=SS.DEV["weekend"], heat_sp=SS.DEV["heat_sp"], min_flow=SS.DEV["min_flow"],
                 heat_sf=SS.DEV["heat_sf"], cool_sf=SS.DEV["cool_sf"], fan_dp=SS.DEV["fan_dp"], hw_t=SS.DEV["hw_t"], hw_dt=SS.DEV["hw_dt"], chw_t=SS.DEV["chw_t"],
                 chw_dt=SS.DEV["chw_dt"], gap=(2.0, 4.0), temp_offset=(0.0, 0.0), solar_scale=(1.0, 1.0), wwr=SS.DEV["wwr"], floor_h=SS.DEV["floor_h"],
                 boiler_eff=(0.80, 0.85), chiller_cop=(4.0, 4.5), fan_eff=(0.6045, 0.6045), night_oa=(1.0, 1.0), min_oa_scale=(1.0, 1.0))
        return d
    d = dict(REGIME)
    if kind == "test":
        d.update(TEST_EXTRA)
    return d


def _topology(r, kind: str, R: dict):
    """(n_ahu, floors, nx, ny, sizes, n_hw, n_chw)"""
    if kind == "small":
        n_ahu, vlo, vhi, maxl = r.choice((1, 2, 3)), 6, 12, 2
    elif kind == "full":
        n_ahu, vlo, vhi, maxl = r.choice((1, 2, 3)), 6, 14, 2
    else:  # held-out topology: beyond every training range
        n_ahu, vlo, vhi, maxl = 4, 15, 18, 3
    lay = [L for L in LAYOUTS if vlo <= L[0] * L[1] * L[2] <= vhi and L[0] * L[1] * L[2] >= 2 * n_ahu]
    floors, nx, ny = r.choice(lay)
    n_vav = floors * nx * ny
    sizes = [2] * n_ahu
    for _ in range(n_vav - 2 * n_ahu):
        sizes[r.randrange(n_ahu)] += 1
    if kind == "held":
        n_hw, n_chw = r.choice((2, 3)), r.choice((2, 3))
        if max(n_hw, n_chw) < 3:
            n_hw = 3
    else:
        n_hw, n_chw = r.randint(1, min(maxl, n_ahu)), r.randint(1, min(maxl, n_ahu))
    return n_ahu, floors, nx, ny, n_vav, sizes, n_hw, n_chw


TAG = {"regime": "reg", "full": "ful", "full_x3": "fx3"}


def draw_building(suite: str, idx: int, attempt: int = 0) -> dict:
    """attempt > 0 = deterministic re-draw used ONLY when the generation-level physics checks reject the previous draw (recorded in the spec as `seed_attempt`)."""
    S = SUITES[suite]
    r = random.Random(f"{SPEC_VERSION}|{suite}|{idx}|{S['seed']}" + (f"|a{attempt}" if attempt else ""))
    R = _ranges(S["rng"])
    n_ahu, floors, nx, ny, n_vav, sizes, n_hw, n_chw = _topology(r, S["topo"], R)
    pattern = r.choice(("all_twin", "mixed", "all_separate")) if n_ahu >= 2 else "single"
    base = _u(r, R["sat"], 2)
    lo_s, hi_s = R["sat"]
    sat = [base]
    for a in range(1, n_ahu):
        if pattern == "all_twin" or (pattern == "mixed" and a == 1):
            s = base + r.choice((-1, 1)) * r.uniform(0.05, 0.30)
        else:
            for _ in range(200):
                s = r.uniform(lo_s, hi_s)
                if all(abs(s - x) >= 1.0 for x in sat):
                    break
            else:
                s = sat[-1] + 1.0
        sat.append(s)
    sat = [round(s, 2) for s in sat]

    def loops(nl):
        order = list(range(nl)) + [r.randrange(nl) for _ in range(n_ahu - nl)]
        r.shuffle(order)
        return order

    heat = _u(r, R["heat_sp"], 1)
    cool = round(min(27.5, heat + _u(r, R["gap"], 1)), 1)
    start, end = _u(r, R["occ_start"], 1), _u(r, R["occ_end"], 1)
    end = max(end, start + 6.0)
    reheat = r.choice(S["reheat"])
    sat_strategy = [r.choice(S["sat"]) for _ in range(n_ahu)]
    econ = [r.choice(S["econ"]) for _ in range(n_ahu)]
    climate = r.choice(S["climates"])
    tid = f"dr_{TAG.get(suite, suite.split('_')[0].lower())}_{idx:02d}"
    spec = dict(
        id=tid, role=S["role"], suite=suite, climate=climate, n_ahu=n_ahu, n_vav=n_vav, floors=floors, nx=nx, ny=ny,
        tile_w=_u(r, R["tile_w"], 1), tile_d=_u(r, R["tile_d"], 1), floor_h=_u(r, R["floor_h"], 2), north_axis=_u(r, R["north"], 0),
        wwr=_u(r, R["wwr"], 2), infiltration=_u(r, R["infiltration"], 5), lights_wm2=_u(r, R["lights"], 1), equip_wm2=_u(r, R["equip"], 1),
        people_m2=_u(r, R["people"], 3), oa_per_area=_u(r, R["oa_area"], 5), zone_load_sigma=_u(r, R["zone_sigma"], 2),
        zone_shifts=[-1, 0, 1] if r.random() < 0.5 else [0],
        occ=dict(start=start, end=end, night_frac=_u(r, R["night"], 2), weekend_frac=_u(r, R["weekend"], 2)),
        setpoints=dict(heat=heat, cool=cool, heat_setback=round(heat - r.uniform(3, 6), 1), cool_setback=round(cool + r.uniform(2, 5), 1)),
        min_flow_frac=_u(r, R["min_flow"], 2), heat_sizing_factor=_u(r, R["heat_sf"], 2), cool_sizing_factor=_u(r, R["cool_sf"], 2),
        group_mode=r.choice(("block", "stripe")), group_sizes=sizes, sat_pattern=pattern, ahu_sat=sat,
        fan_dp=[_u(r, R["fan_dp"], 0) for _ in range(n_ahu)], economizer=[e != "none" for e in econ],
        n_hw=n_hw, n_chw=n_chw, ahu_hw=loops(n_hw), ahu_chw=loops(n_chw),
        hw_t=[_u(r, R["hw_t"], 1) for _ in range(n_hw)], hw_dt=[_u(r, R["hw_dt"], 1) for _ in range(n_hw)],
        chw_t=[_u(r, R["chw_t"], 1) for _ in range(n_chw)], chw_dt=[_u(r, R["chw_dt"], 1) for _ in range(n_chw)],
        geometry_seed=r.randrange(10**6), seed_attempt=attempt,
        # ---- DR keys
        weather=dict(climate=climate, temp_offset=_u(r, R["temp_offset"], 2), solar_scale=_u(r, R["solar_scale"], 3)),
        reheat=reheat, electric_zones=[(r.random() < 0.5) for _ in range(n_vav)] if reheat == "mixed" else None,
        sat_strategy=sat_strategy,
        sat_reset=[dict(oa_low=_u(r, R["oa_low"], 1), oa_high=_u(r, R["oa_high"], 1), span=_u(r, R["reset_span"], 2)) for _ in range(n_ahu)],
        sp_reset=[r.random() < 0.5 for _ in range(n_ahu)],
        econ_type=econ, econ_limit_db=[_u(r, R["econ_limit_db"], 1) for _ in range(n_ahu)], econ_limit_enth=[_u(r, R["econ_limit_enth"], 0) for _ in range(n_ahu)],
        min_oa_scale=_u(r, R["min_oa_scale"], 2), night_oa=(1.0 if R["night_oa"][0] >= 1.0 else round(float(r.random() < 0.5) * _u(r, R["night_oa"], 2), 2)),
        boiler_eff=_u(r, R["boiler_eff"], 3), chiller_cop=_u(r, R["chiller_cop"], 2), fan_eff=_u(r, R["fan_eff"], 3),
        sensor_level=S["sensor"], profile_seed=r.randrange(10**6),
        distractors=[dict(type=r.choice(DISTRACTOR_TYPES), seed=r.randrange(10**6), window=r.choice((None, r.randrange(8))))
                     for _ in range(r.randint(1, 3))] if S["distract"] else [],
        note="SYNTHETIC building (EnergyPlus); not a real building; documentation errors are synthetic and not real-world verified",
    )
    if spec["setpoints"]["cool_setback"] < spec["setpoints"]["cool"]:
        raise AssertionError("bad setpoints")
    return spec


def draw_all() -> dict:
    """The whole spec (all suites). Deterministic; hashed into results/docmismatch/dr/spec_manifest.json before any simulation."""
    out = dict(spec_version=SPEC_VERSION, written_before_simulation=True, suites={}, ranges=dict(dev=_ranges("dev"), regime=_ranges("regime"), test=_ranges("test")),
               held_out=dict(sat=list(SAT_HELD), econ=list(ECON_HELD), reheat=["mixed"], topology="n_ahu=4, n_vav 15-18, 3 loops per medium", climates=list(TEST_CLIMATES),
                             weather_offset="beyond +-4 K (tests up to +-6 K)"),
               train_climates=list(TRAIN_CLIMATES))
    for s in SUITE_ORDER:
        out["suites"][s] = dict(cfg={k: (list(v) if isinstance(v, tuple) else v) for k, v in SUITES[s].items()}, buildings=[draw_building(s, i) for i in range(SUITES[s]["n"])])
    return out
