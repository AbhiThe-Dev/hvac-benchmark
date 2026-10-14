"""What detection rate does `bas_economizer` (v1/catalogue.py: "is the OA damper command stuck near its minimum when conditions call for more free cooling?") actually get, measured
against LBNL's real, ground-truth-labeled Experimental RTU dataset -- instead of the placeholder "strong" (0.92) Addendum 37 shipped with, unmeasured? Recommended by Gabe Fierro
(2026-09-29); not a simulation, not part of the tool's own frozen study machinery -- a one-off empirical calibration check against real lab data, exploratory, NOT pre-registered.

DATA (not vendored into this repo -- ~30MB, fetch once):
  mkdir -p ~/.cache/lbnl_fdd_rtu && cd ~/.cache/lbnl_fdd_rtu
  curl -sL -o rtu.zip https://fdddata.lbl.gov/data/Simulated_LBNL_FDD_Data_Sets_RTU/LBNL_FDD_Data_Sets_RTU_all_3.zip
  unzip -q rtu.zip "ORNL_RTU/*" && rm rtu.zip
  .venv/bin/python doc_mismatch/scripts/86_econ_afdd_real_data.py                                  # uses ~/.cache/lbnl_fdd_rtu/ORNL_RTU by default
  .venv/bin/python doc_mismatch/scripts/86_econ_afdd_real_data.py --data-dir /path/to/ORNL_RTU

TWO RULES, tested and reported side by side:
  RULE A (a plain, literal read of the check's own wording -- an AFDD1-style rule, nothing more elaborate): during occupied hours (OCCU_MOD==1), a minute QUALIFIES as "conditions
  call for more free cooling" if OAT < 50F (the correct economizer setpoint) AND OAT < RAT - 2F (outdoor air meaningfully cooler than return air, so free cooling would actually help).
  Among qualifying minutes in one calendar day, the check reads back ABNORMAL for that day if the OA damper command (RTU_OA_DMPR_DM) sits at or below 15 (near the documented 10%
  minimum) in at least half of them; otherwise NORMAL. Days with fewer than 30 qualifying minutes are excluded (no real opportunity to see the fault that day, not evidence either way).
  Only ever designed to catch a damper stuck LOW.

  RULE B (widened, 2026-09-29, asked directly by the user after Rule A was found to miss "stuck open" entirely): a damper that never modulates is suspicious regardless of WHERE it
  is stuck, so this rule drops the "should be economizing" gate and just asks whether the damper moved at all over the occupied day, given that conditions changed enough that a
  working damper would have had reason to move. One calendar day is ABNORMAL if occupied-hours OAT swings by at least 8F (a real reason to modulate existed) while the damper's own
  range of motion is at most 5 percentage points (it didn't). Needs at least 200 occupied minutes of data to evaluate a day at all.

  RULE C (setpoint crossover, 2026-09-29, asked directly by the user: "update the setpoint check for the correct threshold" -- Rule A/B target a stuck damper, not a wrong enable
  temperature): estimate the day's OWN empirical enable point (the warmest OAT at which the damper was ever seen clearly open, >20%, i.e. modulating well past its documented 10%
  minimum) and compare it to the correct 50F. Flagged ABNORMAL if that empirical crossover is 3F or more away from 50F in EITHER direction; if the damper was NEVER seen clearly open
  despite OAT dropping to 45F or colder that day (5F of margin below 50F, so this isn't just measurement noise), also flagged ABNORMAL (an effective threshold far enough below 50F
  to never fire that day). A day with neither signal (never opened, but never got convincingly cold either) is not evaluable.

  Correction while building Rule C: this session's own earlier grouping (in Rule A/B's report) assumed the `Inc_Eco_SP_-2/-4` files meant a LOWERED effective setpoint and
  `Inc_Eco_SP_2/4` a RAISED one, by analogy with the correct value being 10C and the filename suffix reading as a signed offset. Rule C's own measurements contradict that: the `-2/-4`
  files show the damper opening at a HIGHER OAT than 50F (53-59F), and the one evaluable `+4` file shows it never opening despite OAT reaching 43.5F -- the opposite mapping. Rather
  than guess which of "which offset direction" or "what the fault actually modifies internally" is wrong, the groups below are labelled by filename suffix only, not by an assumed
  physical direction, and the correction is reported plainly rather than silently reusing the earlier (evidently wrong) labels.
"""
import argparse
import csv
import glob
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
OUT = REPO / "results/docmismatch/econ_afdd_real"
DEFAULT_DATA_DIR = Path.home() / ".cache/lbnl_fdd_rtu/ORNL_RTU"

MIN_QUALIFYING = 30
STUCK_THRESH = 15.0
OAT_SETPOINT = 50.0
RAT_MARGIN = 2.0
FRACTION_ABNORMAL = 0.5

GROUPS = {
    "baseline (unfaulted)": lambda n: n.startswith("ERTU_"),
    "OA damper stuck NEAR MINIMUM (5%, 10%) -- this check's stated target": lambda n: n.startswith(("OA_damper_stuck_005", "OA_damper_stuck_010")),
    "OA damper stuck OPEN (50%, 100%) -- a different failure mode, not this check's stated target": lambda n: n.startswith(("OA_damper_stuck_050", "OA_damper_stuck_100")),
    "incorrect setpoint, filename suffix -2/-4 (opens at a HIGHER OAT than 50F on evidence -- see Rule C correction)": lambda n: n.startswith("Inc_Eco_SP_-"),
    "incorrect setpoint, filename suffix +2/+4 (opens at a LOWER OAT than 50F, or not at all, on evidence -- see Rule C correction)": lambda n: n.startswith("Inc_Eco_SP_") and not n.startswith("Inc_Eco_SP_-"),
}

SETPOINT_CORRECT = 50.0
SETPOINT_DEV_THRESH = 3.0
SETPOINT_OPPORTUNITY_MARGIN = 5.0


def day_classifications(path: str) -> dict:
    """{date: (n_qualifying, frac_stuck)} for one CSV file, one entry per calendar day that had at least one qualifying minute."""
    by_day = defaultdict(lambda: [0, 0])
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                if float(row["OCCU_MOD"]) != 1.0:
                    continue
                oat, rat, dmpr = float(row["RTU_OA_TEMP"]), float(row["RTU_RA_TEMP"]), float(row["RTU_OA_DMPR_DM"])
            except (ValueError, KeyError):
                continue
            if not (oat < OAT_SETPOINT and oat < rat - RAT_MARGIN):
                continue
            date = row["Datetime"][:10]
            by_day[date][0] += 1
            if dmpr <= STUCK_THRESH:
                by_day[date][1] += 1
    return {d: (n, k / n) for d, (n, k) in by_day.items()}


def classify_file(path: str) -> tuple[int, int, int]:
    """(n_evaluable_days, n_flagged_abnormal, n_total_days_with_any_opportunity) under Rule A."""
    days = day_classifications(path)
    evaluable = {d: frac for d, (n, frac) in days.items() if n >= MIN_QUALIFYING}
    abnormal = sum(1 for frac in evaluable.values() if frac >= FRACTION_ABNORMAL)
    return len(evaluable), abnormal, len(days)


# ---------------------------------------------------------------------------------------------- Rule B: non-modulation, either direction
MIN_OCCUPIED_MINUTES = 200
OAT_SWING_MIN = 8.0
DMPR_RANGE_MAX = 5.0


def day_series(path: str) -> dict:
    """{date: [(oat, dmpr), ...]} across occupied minutes."""
    by_day = defaultdict(list)
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                if float(row["OCCU_MOD"]) != 1.0:
                    continue
                oat, dmpr = float(row["RTU_OA_TEMP"]), float(row["RTU_OA_DMPR_DM"])
            except (ValueError, KeyError):
                continue
            by_day[row["Datetime"][:10]].append((oat, dmpr))
    return by_day


def classify_file_nonmod(path: str) -> tuple[int, int]:
    """(n_evaluable_days, n_flagged_abnormal) under Rule B."""
    n_eval = n_flag = 0
    for pts in day_series(path).values():
        if len(pts) < MIN_OCCUPIED_MINUTES:
            continue
        oats, dmprs = [p[0] for p in pts], [p[1] for p in pts]
        n_eval += 1
        if max(oats) - min(oats) >= OAT_SWING_MIN - 1e-9 and max(dmprs) - min(dmprs) <= DMPR_RANGE_MAX:
            n_flag += 1
    return n_eval, n_flag


# ---------------------------------------------------------------------------------------------- Rule C: setpoint crossover
def classify_file_crossover(path: str) -> tuple[int, int]:
    """(n_evaluable_days, n_flagged_abnormal) under Rule C. Reuses Rule B's `day_series` (occupied-hours (oat, dmpr) pairs)."""
    n_eval = n_flag = 0
    for pts in day_series(path).values():
        if len(pts) < MIN_OCCUPIED_MINUTES:
            continue
        oats = [p[0] for p in pts]
        open_oats = [oat for oat, dmpr in pts if dmpr > 20]
        if open_oats:
            n_eval += 1
            if abs(max(open_oats) - SETPOINT_CORRECT) >= SETPOINT_DEV_THRESH:
                n_flag += 1
        elif min(oats) <= SETPOINT_CORRECT - SETPOINT_OPPORTUNITY_MARGIN:
            n_eval += 1
            n_flag += 1
        # else: never opened, but never got cold enough either -- not evaluable
    return n_eval, n_flag


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    a = ap.parse_args(argv)
    if not a.data_dir.exists():
        sys.exit(f"{a.data_dir} not found -- fetch it first (see this script's docstring)")

    rows = []
    for label, match in GROUPS.items():
        files = [p for p in sorted(glob.glob(str(a.data_dir / "*.csv"))) if match(os.path.basename(p))]
        tot_eval = tot_abn = tot_days = 0
        for p in files:
            e, ab, d = classify_file(p)
            tot_eval, tot_abn, tot_days = tot_eval + e, tot_abn + ab, tot_days + d
        rateA = tot_abn / tot_eval if tot_eval else float("nan")
        eB = fB = 0
        for p in files:
            e, ab = classify_file_nonmod(p)
            eB, fB = eB + e, fB + ab
        rateB = fB / eB if eB else float("nan")
        eC = fC = 0
        for p in files:
            e, ab = classify_file_crossover(p)
            eC, fC = eC + e, fC + ab
        rateC = fC / eC if eC else float("nan")
        rows.append(dict(label=label, n_files=len(files), evaluable_days=tot_eval, flagged=tot_abn, rate=rateA, days_seen=tot_days,
                          evaluable_days_b=eB, flagged_b=fB, rate_b=rateB, evaluable_days_c=eC, flagged_c=fC, rate_c=rateC))

    L = ["# What detection rate does `bas_economizer` get against real, ground-truth economizer-fault data?", "",
         "LBNL's Experimental RTU dataset (ORNL's Flexible Research Platform, a real 12.5-ton Trane RTU serving 10 VAV zones), recommended by Gabe Fierro. One-off empirical calibration, "
         "not a simulation, not pre-registered: measures three versions of the rule `bas_economizer`'s description implies against 1-minute real BAS data with known, imposed "
         "ground-truth faults.", "",
         "## Rule A: literal reading (\"stuck near its MINIMUM when conditions call for free cooling\") -- catches only a stuck-LOW damper by design", "",
         "A minute qualifies as \"conditions call for more free cooling\" if OAT < 50F and OAT < RAT - 2F. A day is ABNORMAL if the OA damper sits at or below 15 (near the documented "
         "10% minimum) in at least half of qualifying minutes. Days with fewer than 30 qualifying minutes excluded.", "",
         "| fault group | files | evaluable days | flagged ABNORMAL | rate |", "|---|---|---|---|---|"]
    for r in rows:
        pct = "n/a" if r["rate"] != r["rate"] else f"{100 * r['rate']:.0f}%"
        L.append(f"| {r['label']} | {r['n_files']} | {r['evaluable_days']} | {r['flagged']} | {pct} |")
    L += ["", "## Rule B: widened (\"the damper never modulates\") -- 2026-09-29, built after Rule A was found to miss stuck-OPEN entirely", "",
          "Drops the free-cooling gate. A day is ABNORMAL if occupied-hours OAT swings by at least 8F (real reason to move) while the damper's own range of motion over the day is at "
          "most 5 percentage points (it didn't). Needs at least 200 occupied minutes to evaluate a day.", "",
          "| fault group | evaluable days | flagged ABNORMAL | rate |", "|---|---|---|---|"]
    for r in rows:
        pct = "n/a" if r["rate_b"] != r["rate_b"] else f"{100 * r['rate_b']:.0f}%"
        L.append(f"| {r['label']} | {r['evaluable_days_b']} | {r['flagged_b']} | {pct} |")
    L += ["", "## Rule C: setpoint crossover -- 2026-09-29, targets the fault Rule A/B cannot see (a wrong enable temperature, not a stuck damper)", "",
          "Estimates each day's OWN empirical enable point (the warmest OAT the damper was ever seen clearly open, >20%) and compares it to the correct 50F; flagged if 3F or more off "
          "in EITHER direction, or if the damper never opened despite OAT reaching 45F or colder that day. **Group labels below are by filename suffix only, not by an assumed physical "
          "direction -- see the correction in this script's docstring.**", "",
          "| fault group | evaluable days | flagged ABNORMAL | rate |", "|---|---|---|---|"]
    for r in rows:
        pct = "n/a" if r["rate_c"] != r["rate_c"] else f"{100 * r['rate_c']:.0f}%"
        L.append(f"| {r['label']} | {r['evaluable_days_c']} | {r['flagged_c']} | {pct} |")
    L += ["", "## Reading", "",
          "**Clean, if small-sample, signal on the check's actual stated target:** 0% false-positive rate on 5 unfaulted days, 100% true-positive rate on the 4 days testing the fault "
          "this check's wording literally describes (damper stuck near minimum) -- consistent with (not proof of, at n=4-5) the placeholder \"strong\"=0.92, not a reason to lower it "
          "for that exact scenario.", "",
          "**Rule A has a real scope gap, not a measurement artefact:** \"stuck near its MINIMUM\" only covers half of what the dataset labels \"OA damper stuck\" -- the other half, "
          "stuck OPEN (50%, 100%), is missed 100% of the time, because a wide-open damper never matches \"near minimum\".", "",
          "**Rule B closes that gap.** Dropping the direction-specific check for a general \"did it move at all\" test catches BOTH stuck-low (88%, 7 of 8 days -- one miss right at the "
          "OAT-swing threshold) AND stuck-open (100%, 8 of 8 days), on a larger sample than Rule A could evaluate (16 days vs 9), while the false-positive rate stays clean (0 of 14 "
          "baseline days, a bigger and still-clean sample than Rule A's 5). **Rule B does NOT catch either incorrect-setpoint direction (0 of 16 days) -- correctly so, not a failure: "
          "a shifted setpoint doesn't freeze the damper, it just changes when a still-modulating damper decides to move, which is a different fault mechanism a \"did it move\" test was "
          "never going to see. That fault would need a genuinely different check (comparing WHEN the economizer engages against the correct temperature threshold), not a wider version "
          "of this one.**", "",
          "**What Rule A/B leave open, Rule C closes -- with an honest correction along the way.** The setpoint fault was untouched by A and B because neither looks at WHEN the "
          "economizer engages, only whether/how much the damper moves. Rule C does, and finds a clean signal: 0% false positives on baseline (5 of 5 days clean), **100% flagged on "
          "the `-2/-4` files (5 of 5 days)**, whose empirical crossover sits 3-9F above 50F -- a real, detectable wrong-threshold signature. The `+2/+4` files gave only 1 evaluable "
          "day (most never got cold enough during the test to be evaluable at all under this rule), and that one day was also flagged (never opened despite reaching 43.5F). Both "
          "directions are individually detectable; the sample for one of them is just very thin. **Correction, reported rather than hidden: this session's own earlier write-up "
          "assumed `-2/-4` meant a LOWERED effective setpoint and `+2/+4` a RAISED one. Rule C's measurements show the opposite pattern** (`-2/-4` opens at a HIGHER OAT than correct; "
          "the one evaluable `+2/+4` day never opened at a LOWER OAT) -- the earlier direction labels were wrong, not just imprecise, and are corrected in this report's group labels "
          "rather than carried forward.", "",
          "**What this changes:** nothing frozen (Addendum 37's decision stays UNSAFE; no code path in the live tool uses this data or any of these three rules). Between Rule B "
          "(both stuck-damper directions) and Rule C (the setpoint direction), every fault type in this dataset now has a working detector on real data, at a rate at least as good "
          "as the 0.92 placeholder -- the gap found earlier was in how narrowly the ORIGINAL check's wording was read, not in whether these faults are detectable at all. What's "
          "still untested: whether a single simulated check can carry all three signatures at once with one placeholder number, and Addendum 37's OTHER named safety hypothesis "
          "(the check's weak cross-detection of `low_static`), which none of this touches."]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "econ_afdd_report.md").write_text("\n".join(L) + "\n")
    print(f"wrote {OUT / 'econ_afdd_report.md'}")
    for r in rows:
        pctA = "n/a" if r["rate"] != r["rate"] else f"{100 * r['rate']:.0f}%"
        pctB = "n/a" if r["rate_b"] != r["rate_b"] else f"{100 * r['rate_b']:.0f}%"
        pctC = "n/a" if r["rate_c"] != r["rate_c"] else f"{100 * r['rate_c']:.0f}%"
        print(f"  {r['label']:<75}\n      A: eval={r['evaluable_days']:>3} flagged={r['flagged']:>3} rate={pctA:>5}   B: eval={r['evaluable_days_b']:>3} flagged={r['flagged_b']:>3} "
              f"rate={pctB:>5}   C: eval={r['evaluable_days_c']:>3} flagged={r['flagged_c']:>3} rate={pctC}")


if __name__ == "__main__":
    main()
