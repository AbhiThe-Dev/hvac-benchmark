"""A-priori random draw of the simulation-expansion topology specs (dev_E..dev_H, seal_S1..seal_S4).

Parameters are drawn from FIXED-SEED uniform / categorical draws over the ranges below. Nothing here looks at any
classifier, likelihood model or verifier output; ranges were written before any expansion building was simulated.
The sealed ranges are deliberately wider than the dev ranges in several dimensions (see SEALED_EXTENSIONS); a draw
must satisfy the COVERAGE REQUIREMENTS (a rule about the spec, not about any result); if it does not, the next
deterministic attempt seed is used and the attempt count is recorded in the spec.
"""

from __future__ import annotations

import random

DEV_SEED, SEALED_SEED = 20260921, 20260922

# (floors, nx, ny) layouts; zones = floors*nx*ny
LAYOUTS = [(f, nx, ny) for f in (1, 2, 3) for nx in (2, 3, 4) for ny in (nx, nx + 1, nx + 2) if 6 <= f * nx * ny <= 16]

DEV = dict(
    n_ahu=(1, 2, 3), n_vav=(6, 12), climates=("sterling_va", "sanfrancisco", "sacramento", "chicago_amy2012", "golden"),
    tile_w=(6.0, 10.0), tile_d=(6.0, 10.0), floor_h=(3.0, 4.0), wwr=(0.15, 0.40), infiltration=(0.0002, 0.0006),
    lights=(6.0, 12.0), equip=(5.0, 12.0), people=(0.03, 0.08), oa_area=(0.0, 0.0003), zone_sigma=(0.10, 0.30),
    occ_start=(7.0, 9.0), occ_end=(17.0, 19.0), night=(0.02, 0.10), weekend=(0.0, 0.20),
    heat_sp=(20.0, 22.0), cool_sp=(23.5, 25.5), min_flow=(0.25, 0.40), heat_sf=(1.10, 1.30), cool_sf=(1.05, 1.30),
    fan_dp=(400.0, 800.0), sat=(12.0, 14.0), hw_t=(65.0, 82.0), hw_dt=(11.0, 20.0), chw_t=(6.0, 8.0), chw_dt=(5.0, 7.0),
    max_loops=2, north=(0.0, 90.0),
)
SEALED = dict(
    n_ahu=(1, 2, 3, 4), n_vav=(8, 16), climates=("tampa", "palm_springs", "arcata", "blue_canyon", "chicago_amy2013"),
    tile_w=(5.0, 14.0), tile_d=(5.0, 14.0), floor_h=(2.8, 4.8), wwr=(0.10, 0.60), infiltration=(0.0001, 0.0010),
    lights=(4.0, 16.0), equip=(3.0, 20.0), people=(0.02, 0.12), oa_area=(0.0, 0.0006), zone_sigma=(0.10, 0.50),
    occ_start=(5.0, 9.0), occ_end=(17.0, 22.0), night=(0.02, 0.30), weekend=(0.0, 0.60),
    heat_sp=(19.0, 23.0), cool_sp=(23.0, 26.5), min_flow=(0.15, 0.50), heat_sf=(1.05, 1.40), cool_sf=(1.00, 1.40),
    fan_dp=(350.0, 1000.0), sat=(11.5, 15.5), hw_t=(60.0, 82.0), hw_dt=(11.0, 25.0), chw_t=(5.5, 9.0), chw_dt=(4.0, 8.0),
    max_loops=3, north=(0.0, 90.0),
)
SEALED_EXTENSIONS = [
    "climate: hot-humid (tampa), hot-dry (palm_springs), cool-marine (arcata), mountain (blue_canyon) and a different weather year of chicago (dev uses other climates and AMY 2012)",
    "n_ahu up to 4 (dev max 3)", "n_vav up to 16 (dev max 12)", "plant loops up to 3 per medium (dev max 2)",
    "internal loads (lights/equipment/people), window ratio, infiltration, zone-load spread and setpoints beyond dev ranges",
    "occupancy schedules: earlier start, later end, high night and weekend fractions (near-24/7 use)",
    "zone size / floor height and SAT setpoint spread wider; min-flow fraction and sizing factors wider",
]
DEV_SUFFIX = ("E", "F", "G", "H")
SEALED_SUFFIX = ("S1", "S2", "S3", "S4")


def _u(r: random.Random, lohi, nd=3):
    return round(r.uniform(*lohi), nd)


def _draw_one(r: random.Random, R: dict, tid: str, role: str, climate: str, seed_attempt: int) -> dict:
    n_ahu = r.choice(R["n_ahu"])
    lo, hi = R["n_vav"]
    lay = [L for L in LAYOUTS if lo <= L[0] * L[1] * L[2] <= hi and L[0] * L[1] * L[2] >= 2 * n_ahu]
    floors, nx, ny = r.choice(lay)
    n_vav = floors * nx * ny
    # group sizes: composition of n_vav into n_ahu parts, each >= 2
    sizes = [2] * n_ahu
    for _ in range(n_vav - 2 * n_ahu):
        sizes[r.randrange(n_ahu)] += 1
    # SAT pattern: how alike are the AHUs' setpoints
    pattern = r.choice(("all_twin", "mixed", "all_separate")) if n_ahu >= 2 else "single"
    base = _u(r, R["sat"], 2)
    lo_s, hi_s = R["sat"]
    sat = [base]
    for a in range(1, n_ahu):
        if pattern == "all_twin" or (pattern == "mixed" and a == 1):
            s = base + r.choice((-1, 1)) * r.uniform(0.05, 0.30)      # near-twin: within 0.3 K of AHU 1
        else:
            for _ in range(200):                                       # separated: >= 1.0 K from every earlier AHU
                s = r.uniform(lo_s, hi_s)
                if all(abs(s - x) >= 1.0 for x in sat):
                    break
            else:
                s = sat[-1] + 1.0
        sat.append(s)
    sat = [round(s, 2) for s in sat]
    n_hw = r.randint(1, min(R["max_loops"], n_ahu))
    n_chw = r.randint(1, min(R["max_loops"], n_ahu))

    def loops(n_loops):
        order = list(range(n_loops)) + [r.randrange(n_loops) for _ in range(n_ahu - n_loops)]
        r.shuffle(order)
        return order

    heat = _u(r, R["heat_sp"], 1)
    cool = max(_u(r, R["cool_sp"], 1), heat + 2.0)
    start, end = _u(r, R["occ_start"], 1), _u(r, R["occ_end"], 1)
    return dict(
        id=tid, role=role, climate=climate, n_ahu=n_ahu, n_vav=n_vav, floors=floors, nx=nx, ny=ny,
        tile_w=_u(r, R["tile_w"], 1), tile_d=_u(r, R["tile_d"], 1), floor_h=_u(r, R["floor_h"], 2), north_axis=_u(r, R["north"], 0),
        wwr=_u(r, R["wwr"], 2), infiltration=_u(r, R["infiltration"], 5), lights_wm2=_u(r, R["lights"], 1), equip_wm2=_u(r, R["equip"], 1),
        people_m2=_u(r, R["people"], 3), oa_per_area=_u(r, R["oa_area"], 5), zone_load_sigma=_u(r, R["zone_sigma"], 2),
        zone_shifts=[-1, 0, 1] if r.random() < 0.5 else [0],
        occ=dict(start=start, end=end, night_frac=_u(r, R["night"], 2), weekend_frac=_u(r, R["weekend"], 2)),
        setpoints=dict(heat=heat, cool=cool, heat_setback=round(heat - r.uniform(3, 6), 1), cool_setback=round(cool + r.uniform(2, 5), 1)),
        min_flow_frac=_u(r, R["min_flow"], 2), heat_sizing_factor=_u(r, R["heat_sf"], 2), cool_sizing_factor=_u(r, R["cool_sf"], 2),
        group_mode=r.choice(("block", "stripe")), group_sizes=sizes, sat_pattern=pattern, ahu_sat=sat,
        fan_dp=[_u(r, R["fan_dp"], 0) for _ in range(n_ahu)], economizer=[r.random() < 0.5 for _ in range(n_ahu)],
        n_hw=n_hw, n_chw=n_chw, ahu_hw=loops(n_hw), ahu_chw=loops(n_chw),
        hw_t=[_u(r, R["hw_t"], 1) for _ in range(n_hw)], hw_dt=[_u(r, R["hw_dt"], 1) for _ in range(n_hw)],
        chw_t=[_u(r, R["chw_t"], 1) for _ in range(n_chw)], chw_dt=[_u(r, R["chw_dt"], 1) for _ in range(n_chw)],
        geometry_seed=r.randrange(10**6), seed_attempt=seed_attempt,
    )


def _dev_ok(ts):
    multi = [t for t in ts if t["n_ahu"] >= 2]
    return (any(t["n_ahu"] == 1 for t in ts) and any(t["n_ahu"] == 3 for t in ts)
            and any(t["sat_pattern"] in ("all_twin", "mixed") for t in multi) and any(t["sat_pattern"] in ("all_separate", "mixed") for t in multi)
            and any(t["n_hw"] >= 2 or t["n_chw"] >= 2 for t in ts))


def _sealed_ok(ts):
    multi = [t for t in ts if t["n_ahu"] >= 2]
    return (any(t["n_ahu"] == 4 for t in ts) and sum(t["n_vav"] > 12 for t in ts) >= 2
            and any(t["sat_pattern"] in ("all_twin", "mixed") for t in multi) and any(t["sat_pattern"] in ("all_separate", "mixed") for t in multi)
            and any(max(t["n_hw"], t["n_chw"]) >= 3 for t in ts)
            and any(t["occ"]["night_frac"] > 0.10 or t["occ"]["weekend_frac"] > 0.20 for t in ts))


def draw_set(seed: int, R: dict, role: str, suffixes, prefix: str, ok) -> tuple[list[dict], int]:
    for attempt in range(1000):
        r = random.Random(seed + 1000 * attempt)
        clim = r.sample(list(R["climates"]), len(suffixes))     # without replacement: each topology gets its own climate
        ts = [_draw_one(r, R, f"{prefix}_{s}", role, c, attempt) for s, c in zip(suffixes, clim)]
        if ok(ts):
            return ts, attempt
    raise RuntimeError("no draw satisfied the coverage requirements")


def draw_spec() -> dict:
    dev, da = draw_set(DEV_SEED, DEV, "dev", DEV_SUFFIX, "dev", _dev_ok)
    sealed, sa = draw_set(SEALED_SEED, SEALED, "sealed", SEALED_SUFFIX, "seal", _sealed_ok)
    return dict(
        spec_version=1, written_before_simulation=True,
        seeds=dict(dev=DEV_SEED, sealed=SEALED_SEED, dev_attempts=da, sealed_attempts=sa),
        ranges=dict(dev={k: (list(v) if isinstance(v, tuple) else v) for k, v in DEV.items()}, sealed={k: (list(v) if isinstance(v, tuple) else v) for k, v in SEALED.items()}),
        sealed_extensions=SEALED_EXTENSIONS,
        coverage_requirements=dict(
            dev="an n_ahu=1 and an n_ahu=3 building; near-twin (<=0.3 K) AND well-separated (>=1 K) AHU SAT pairs; a building with >=2 loops of some medium",
            sealed="an n_ahu=4 building; >=2 buildings with >12 VAVs; near-twin AND separated SAT pairs; a building with >=3 loops of a medium; a building with night>0.10 or weekend>0.20"),
        topologies=dev + sealed,
    )
