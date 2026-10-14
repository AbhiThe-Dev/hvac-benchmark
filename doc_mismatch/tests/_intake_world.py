"""A small synthetic building used by the intake tests: every connection type, smooth diurnal series with enough variation to count as informative.
Not a physical simulation -- the numbers only need to be positive, varied and distinct per series."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.intake import Claim, FieldBuilding  # noqa: E402

EQUIPMENT = {
    "ENV": dict(kind="Weather"), "AHU-1": dict(kind="AHU"),
    "VAV-1": dict(kind="VAV"), "VAV-2": dict(kind="VAV"), "VAV-3": dict(kind="VAV"),
    "Zone-1": dict(kind="Zone"), "Zone-2": dict(kind="Zone"), "Zone-3": dict(kind="Zone"),
    "HWL-1": dict(kind="HWL"), "Branch-1": dict(kind="Branch", medium="hot_water"), "Branch-2": dict(kind="Branch", medium="hot_water"),
    "Coil-1": dict(kind="Coil", function="heating", medium="hot_water"), "Coil-2": dict(kind="Coil", function="cooling"), "Coil-3": dict(kind="Coil", function="heating", medium="hot_water"),
    "Pump-1": dict(kind="Pump", medium="hot_water"), "Boiler-1": dict(kind="Boiler", medium="hot_water"),
    "SAT-1": dict(kind="SAT"), "DAT-1": dict(kind="DAT"), "DAT-2": dict(kind="DAT"),
}
# (base level, relative amplitude) per signal family; temperatures use absolute amplitude in K
SIGNAL_LEVEL = {"flow": ("air", 5.0), "t_in": ("temp", 13.0), "t_dis": ("temp", 18.0), "reheat": ("pow", 2000.0), "temp": ("temp", 22.0), "sat": ("temp", 16.0), "mat": ("temp", 16.0),
                "htg": ("pow", 6000.0), "clg": ("pow", 9000.0), "t_sup": ("temp", 70.0), "t_ret": ("temp", 55.0), "t_out": ("temp", 55.0), "rate": ("pow", 3000.0),
                "rate_s": ("pow", 2500.0), "kw": ("pow", 800.0), "value": ("temp", 13.0), "oat": ("temp", 10.0)}
WATER_FLOW = {"HWL-1", "Branch-1", "Branch-2", "Pump-1"}
SIGNAL_SETS = {"Weather": ["oat"], "AHU": ["flow", "sat", "mat", "htg", "clg"], "VAV": ["flow", "t_in", "t_dis", "reheat"], "Zone": ["temp"], "HWL": ["flow", "t_sup", "t_ret"],
               "Branch": ["flow", "t_in", "t_out"], "Coil": ["rate"], "Pump": ["flow", "kw"], "Boiler": ["rate", "t_out"], "SAT": ["value"], "DAT": ["value"]}
CLAIMS = ([Claim("AHU-1", f"VAV-{i}", "ahu_vav", "yes") for i in (1, 2, 3)] + [Claim(f"VAV-{i}", f"Zone-{i}", "vav_zone", "yes") for i in (1, 2, 3)]
          + [Claim("HWL-1", "Branch-1", "loop_branch", "yes"), Claim("HWL-1", "Branch-2", "loop_branch", "no", "HWL-1")]
          + [Claim("Branch-1", "Coil-1", "branch_coil", "yes"), Claim("Branch-2", "Coil-3", "branch_coil", "unknown")]
          + [Claim("HWL-1", "Pump-1", "loop_pump", "yes"), Claim("HWL-1", "Boiler-1", "loop_source", "yes")]
          + [Claim("AHU-1", "Coil-1", "coil_ahu", "yes"), Claim("AHU-1", "Coil-2", "coil_ahu", "yes"), Claim("VAV-1", "Coil-3", "coil_vav", "yes")]
          + [Claim("AHU-1", "SAT-1", "ahu_sat", "yes"), Claim("VAV-1", "DAT-1", "vav_dat", "yes"), Claim("VAV-2", "DAT-2", "vav_dat", "yes")])


def make_series(T: int = 24 * 44, seed: int = 0, drop: tuple = ()) -> dict[str, np.ndarray]:
    """"EQUIPMENT|signal" -> SI series (degC, kg/s, W). `drop` = signal keys or equipment ids to leave out."""
    rng = np.random.default_rng(seed)
    h = np.arange(T)
    out = {}
    for eid, e in EQUIPMENT.items():
        sigs = list(SIGNAL_SETS.get(e["kind"], []))
        if eid == "Coil-2":
            sigs = ["rate", "rate_s"]
        for sig in sigs:
            fam, base = SIGNAL_LEVEL[sig]
            phase, amp = rng.uniform(0, 24), rng.uniform(0.25, 0.5)
            wave = np.sin(2 * np.pi * (h - phase) / 24.0) + 0.4 * np.sin(2 * np.pi * (h - 2 * phase) / 168.0)
            if fam == "temp":
                x = base + 4.0 * amp * wave + rng.normal(0, 0.15, T)
            else:
                lvl = base * (0.4 if eid in WATER_FLOW and sig == "flow" else 1.0)
                x = lvl * (1.0 + amp * wave) * rng.normal(1.0, 0.01, T)
            out[f"{eid}|{sig}"] = np.maximum(x, 0.0) if fam != "temp" else x
    for k in drop:
        for key in list(out):
            if key == k or key.split("|")[0] == k:
                del out[key]
    return out


def make_building(T: int = 24 * 44, seed: int = 0, drop: tuple = (), start: datetime = datetime(2021, 7, 5), context: dict | None = None, claims=None) -> FieldBuilding:
    ev = make_series(T, seed, drop)
    equipment = {k: {"function": "", "medium": "", **v} for k, v in EQUIPMENT.items()}
    return FieldBuilding("synthetic", start, T, equipment, {}, list(CLAIMS if claims is None else claims), ev, {}, context or {})
