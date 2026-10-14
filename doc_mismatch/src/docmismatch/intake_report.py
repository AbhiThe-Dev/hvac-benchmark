"""Readiness report for a field building: which connection checks can this building's recorded points support, and which missing points would unlock more.

`slot_readiness(fb)` is the structured result; `report(fb)` renders it (with data-quality, documentation and date-alignment checks) as markdown.
The 0.5 / 0.8 thresholds below are REPORTING thresholds (what to call "usable"), not statistical decision rules; nothing here is fitted or scored.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import timedelta

import numpy as np

from .data import SLOTS
from .evidence import VARIATION_K, _noise_sd
from .intake import FieldBuilding, parse_date

# COMPLETE list of the recorded signals each evidence channel reads (evidence._pair_errors). `o` = the slot's owner equipment, `m` = the member.
# "a|b" = either signal is enough (a cooling coil uses its sensible rate when it exists, else its total rate). A test perturbs every signal to keep this exact.
CHANNEL_SIGNALS: dict[str, dict[int, list[tuple[str, str]]]] = {
    "ahu_vav": {0: [("m", "t_in"), ("o", "sat")], 1: [("m", "flow"), ("o", "flow")], 2: [("m", "flow"), ("o", "flow")]},
    "vav_zone": {0: [("o", "flow"), ("m", "temp")], 1: [("o", "t_dis"), ("m", "temp")], 2: [("o", "flow"), ("o", "t_dis"), ("m", "temp")]},
    "loop_branch": {0: [("m", "t_in"), ("o", "t_sup")], 1: [("m", "flow"), ("o", "flow")], 2: [("m", "flow"), ("o", "flow")]},
    "branch_coil": {0: [("o", "flow"), ("o", "t_in"), ("o", "t_out"), ("m", "rate")], 1: [("o", "flow"), ("m", "rate")], 2: [("o", "flow"), ("m", "rate")]},
    "loop_pump": {0: [("m", "flow"), ("o", "flow")], 1: [("m", "flow"), ("o", "flow")], 2: [("m", "kw"), ("o", "flow")]},
    "loop_source": {0: [("m", "t_out"), ("o", "t_sup")], 1: [("m", "rate"), ("o", "flow"), ("o", "t_sup"), ("o", "t_ret")], 2: [("m", "rate"), ("o", "flow"), ("o", "t_sup"), ("o", "t_ret")]},
    "coil_ahu": {k: [("o", "flow"), ("o", "sat"), ("o", "mat"), ("m", "rate_s|rate")] for k in range(3)},
    "coil_vav": {k: [("o", "flow"), ("o", "t_dis"), ("o", "t_in"), ("m", "rate")] for k in range(3)},
    "ahu_sat": {k: [("o", "flow"), ("o", "mat"), ("o", "htg"), ("o", "clg"), ("m", "value")] for k in range(3)},
    "vav_dat": {k: [("o", "t_in"), ("o", "flow"), ("m", "value")] for k in range(3)},
}
# Signals the engine READS when present but does not require. VAV `reheat` (reheat power) enters the predicted discharge temperature of `vav_dat`; without it the
# prediction ignores reheating, so that check is less reliable while a box is heating. (A test asserts these do change the output.)
OPTIONAL_SIGNALS: dict[str, list[tuple[str, str]]] = {"vav_dat": [("o", "reheat")]}
SLOT_MEANING = {
    "ahu_vav": "which air handler supplies each VAV box", "vav_zone": "which room each VAV box serves", "loop_branch": "which water loop feeds each coil branch",
    "branch_coil": "which branch feeds each coil", "loop_pump": "which loop each pump belongs to", "loop_source": "which loop each boiler / chiller belongs to",
    "coil_ahu": "which air handler each coil belongs to", "coil_vav": "which VAV box each reheat coil belongs to", "ahu_sat": "which air handler each supply-air-temperature sensor is on",
    "vav_dat": "which VAV box each discharge-air-temperature sensor is on",
}
def resolve(sig: str, kind: str, function: str) -> str:
    """A heating coil reads its `rate`; a cooling (or unknown-function) coil reads `rate_s` when it exists, else `rate` (evidence._pair_errors, coil_ahu)."""
    return "rate" if (sig == "rate_s|rate" and kind == "Coil" and function == "heating") else sig


MIN_COV = 0.5      # a series counts as usable when at least this fraction of its hours has a value
OK_FRAC = 0.8      # a channel counts as supported when this fraction of the documented pairs can compute it
WINDOW_H = 1008    # 6 weeks: the engine's "visit window"


def _series_status(fb: FieldBuilding, eq: str, sig: str) -> str:
    """'ok' | 'not recorded' | 'low coverage' | 'flat' for one equipment signal (alternatives 'a|b': best of them)."""
    best = "not recorded"
    rank = {"not recorded": 0, "low coverage": 1, "flat": 2, "ok": 3}
    for s in sig.split("|"):
        x = fb.ev.get(f"{eq}|{s}")
        if x is None:
            st = "not recorded"
        else:
            x = x[fb.active_hours]
            good = x[np.isfinite(x)]
            if len(good) < MIN_COV * len(x):
                st = "low coverage"
            elif good.std() <= VARIATION_K * _noise_sd(s, good):
                st = "flat"
            else:
                st = "ok"
        if rank[st] > rank[best]:
            best = st
    return best


def slot_readiness(fb: FieldBuilding) -> dict:
    """{slot: dict(n_pairs, channels: {k: fraction of documented pairs whose signals are all usable}, missing: {(equipment type, signal, reason): n equipment},
    supported: [channels >= OK_FRAC], status: FULL | PARTIAL | NOT TESTABLE)} over the DOCUMENTED (owner, member) pairs."""
    out = {}
    by_slot = defaultdict(list)
    for c in fb.claims:
        by_slot[c.slot].append(c)
    status_cache: dict = {}

    def st(eq, sig):
        if (eq, sig) not in status_cache:
            status_cache[(eq, sig)] = _series_status(fb, eq, sig)
        return status_cache[(eq, sig)]

    for slot, claims in by_slot.items():
        if slot not in CHANNEL_SIGNALS:
            out[slot] = dict(n_pairs=len(claims), channels={}, missing={}, supported=[], status="NOT CHECKED BY THE EVIDENCE ENGINE")
            continue
        n = len(claims)
        ok = {k: 0 for k in CHANNEL_SIGNALS[slot]}
        missing: dict = defaultdict(set)
        blocked_by: dict = {k: Counter() for k in CHANNEL_SIGNALS[slot]}
        for c in claims:
            eq_of = {"o": c.owner, "m": c.member}
            for k, needs in CHANNEL_SIGNALS[slot].items():
                res = [(who, resolve(sig, fb.equipment[eq_of[who]]["kind"], fb.equipment[eq_of[who]].get("function", ""))) for who, sig in needs]
                bad = [(who, sig, st(eq_of[who], sig)) for who, sig in res if st(eq_of[who], sig) != "ok"]
                if not bad:
                    ok[k] += 1
                for who, sig, why in bad:
                    kind = fb.equipment[eq_of[who]]["kind"]
                    missing[(kind, sig, why)].add(eq_of[who])
        chans = {k: ok[k] / n for k in ok}
        supported = [k for k, f in chans.items() if f >= OK_FRAC]
        status = "FULL" if len(supported) == len(chans) else ("PARTIAL" if supported else "NOT TESTABLE")
        out[slot] = dict(n_pairs=n, channels=chans, missing={k: len(v) for k, v in missing.items()}, supported=supported, status=status)
    return out


def _unlock(slot: str, kind: str, sig: str) -> list[int]:
    """channels of `slot` that read this (equipment kind, signal) -- for the 'what would unlock it' column"""
    spec = SLOTS[slot]
    ks = []
    for k, needs in CHANNEL_SIGNALS[slot].items():
        for who, s in needs:
            allowed = spec["owner"] if who == "o" else spec["member"]
            if kind in allowed and sig in s.split("|"):
                ks.append(k)
    return ks


def quality_flags(fb: FieldBuilding) -> list[str]:
    out = []
    for pid, q in fb.qa.items():
        why = []
        if q.coverage < 0.8:
            why.append(f"only {q.coverage:.0%} of hours have a value")
        if q.longest_gap_h > 48:
            why.append(f"longest gap {q.longest_gap_h} h")
        if q.n_raw and (q.n_out_of_range / q.n_raw > 0.01):
            why.append(f"{q.n_out_of_range} out-of-range values")
        if q.n_raw and ((q.n_nonnumeric + q.n_sentinel) / q.n_raw > 0.01):
            why.append(f"{q.n_nonnumeric} non-numeric and {q.n_sentinel} sentinel values")
        if q.n_duplicate_ts:
            why.append(f"{q.n_duplicate_ts} duplicate timestamps")
        if why:
            out.append(f"`{pid}`: " + "; ".join(why))
    return out


def alignment_flags(fb: FieldBuilding) -> list[str]:
    """Does the trend period match the time the documentation was verified? (a later renovation makes the truth stale)"""
    ctx = fb.context
    start, end = fb.t0_local.date(), (fb.t0_local + timedelta(hours=fb.n_hours)).date()
    built = parse_date(ctx.get("as_built_date"))
    out = []
    if built is None:
        out.append("as_built_date is missing: the date the connections were marked up / verified is unknown, so a later change to the building cannot be ruled out")
        return out
    if end < built:
        out.append(f"the trends end ({end}) before the as-built markup ({built}): they show a different state of the building")
    gap = (start - built).days
    mods = ctx.get("modifications") or []
    for m in mods:
        d = parse_date(m.get("date"))
        if d is None:
            continue
        if built < d <= end:
            out.append(f"modification on {d} ({m.get('note', 'no note')}) is after the markup ({built}) and {'inside' if d >= start else 'before the start of'} the trend window: the marked-up connections may no longer be true for this data")
    if gap > 365 and not mods:
        out.append(f"the trends start {gap // 30} months after the markup and no modifications are listed: confirm nothing was changed in between")
    return out


def report(fb: FieldBuilding) -> str:
    r = slot_readiness(fb)
    md = [f"# Intake readiness: {fb.building_id}", ""]
    end = fb.t0_local + timedelta(hours=fb.n_hours)
    oat = next((fb.ev[k] for k in fb.ev if k.endswith("|oat")), None)
    n_act = int(fb.active_hours.sum())
    md += ["## Data coverage", "", f"- Period: {fb.t0_local:%Y-%m-%d} to {end:%Y-%m-%d} ({fb.n_hours / 24:.0f} calendar days), local standard time. "
           f"Days with data: {n_act // 24} in {fb.n_chunks} separate chunk(s) ({n_act / WINDOW_H:.2f} six-week windows' worth). Coverage below is judged over those days only.",
           f"- Points: {len(fb.points)} usable in the point list, {len(fb.qa)} with trend data; {len(fb.claims)} documented connections."]
    if oat is not None and np.isfinite(oat).any():
        g = oat[np.isfinite(oat)]
        md.append(f"- Outdoor temperature: {g.min():.0f} to {g.max():.0f} C (5th-95th percentile {np.percentile(g, 5):.0f} to {np.percentile(g, 95):.0f} C). "
                  + ("The engine was built on simulated buildings over a full year of weather; a narrow range limits what it can say." if np.ptp(np.percentile(g, [5, 95])) < 15 else ""))
    else:
        md.append("- No outdoor-temperature point: the operating context cannot be computed (a Weather equipment with an `oat` point is required).")
    if n_act < WINDOW_H:
        md.append(f"- NOTE: {n_act // 24} days with data is less than one six-week window (42 days). That is enough to read the connections, but not to learn how a building behaves across weather.")
    md.append("")

    md += ["## What each connection check can use", "",
           "Channel = one kind of consistency test between two ends of a connection. Each channel cell = the fraction of the documented connections whose needed points are recorded, cover at least "
           f"{MIN_COV:.0%} of hours and vary beyond sensor noise. Status: FULL = all channels reach {OK_FRAC:.0%}; PARTIAL = some do; NOT TESTABLE = none do.", "",
           "| connection | documented | channel 0 | channel 1 | channel 2 | status | what would unlock more |", "|---|---|---|---|---|---|---|"]
    for slot, d in sorted(r.items()):
        if not d["channels"]:
            md.append(f"| {slot} | {d['n_pairs']} | - | - | - | {d['status']} | |")
            continue
        unlock = []
        for (kind, sig, why), n in sorted(d["missing"].items(), key=lambda kv: -kv[1]):
            ks = _unlock(slot, kind, sig)
            if ks and len(unlock) < 3:
                unlock.append(f"{kind} `{sig}` {why} on {n} unit(s) (needed by ch {','.join(map(str, ks))})")
        chans = [f"{d['channels'].get(k, float('nan')):.0%}" for k in range(3)]
        md.append(f"| {slot}: {SLOT_MEANING.get(slot, '')} | {d['n_pairs']} | {chans[0]} | {chans[1]} | {chans[2]} | {d['status']} | {'; '.join(unlock)} |")
    if "vav_zone" in r:
        md += ["", "Note on `vav_zone`: even with every point recorded, ordinary operation cannot tell which box serves which room (Addendum 11: no better than chance in simulation). "
                   "That check needs deliberate changes to the room setpoints (Addendum 13) or a box override; trends from commissioning tests that contain such changes are the useful data."]
    md.append("")

    if "vav_dat" in r:
        lacking = sorted({c.owner for c in fb.claims if c.slot == "vav_dat" and f"{c.owner}|reheat" not in fb.ev})
        if lacking:
            md += [f"Note on `vav_dat`: {len(lacking)} box(es) have no `reheat` (reheat power) point, e.g. {', '.join(lacking[:3])}. The predicted discharge temperature then ignores reheating, "
                   "so that check is less reliable while a box is heating. Boxes with no reheat coil are unaffected.", ""]

    md += ["## Documentation and truth", ""]
    per = defaultdict(Counter)
    for c in fb.claims:
        per[c.slot][c.verified] += 1
    if per:
        md += ["| connection | documented | verified right | verified wrong | unknown |", "|---|---|---|---|---|"]
        for slot in sorted(per):
            cn = per[slot]
            md.append(f"| {slot} | {sum(cn.values())} | {cn['yes']} | {cn['no']} | {cn['unknown']} |")
        md.append("")
        try:
            fb.base()
        except ValueError as e:
            md += [f"- PROBLEM: {e}", ""]
        multi = Counter((c.slot, c.member) for c in fb.claims)
        dup = [f"{m} ({s})" for (s, m), n in multi.items() if n > 1]
        if dup:
            md += [f"- PROBLEM: {len(dup)} member(s) documented under more than one owner in the same slot, e.g. {', '.join(dup[:5])}", ""]
        n_unver = sum(1 for c in fb.claims if c.verified == "unknown")
        if n_unver == len(fb.claims):
            md += ["- No connection is marked verified: the data can be checked by the tool but not scored (we need verified-right and verified-wrong connections to measure accuracy).", ""]
        elif not any(c.verified == "no" for c in fb.claims):
            md += ["- No verified-wrong connection: useful for false-alarm testing, not for testing whether errors are caught.", ""]
    else:
        md += ["- No connections.csv: nothing to check yet.", ""]

    md += ["## Does the data match the time the documentation was verified?", ""]
    al = alignment_flags(fb)
    md += ([f"- {a}" for a in al] if al else ["- No conflict found between the trend period and the listed dates."]) + [""]

    q = quality_flags(fb)
    md += ["## Data quality", ""] + ([f"- {x}" for x in q] if q else ["- No point failed the coverage, range, sentinel or duplicate checks."]) + [""]
    if fb.notes:
        md += ["## Notes from loading", ""] + [f"- {n}" for n in fb.notes] + [""]
    return "\n".join(md)
