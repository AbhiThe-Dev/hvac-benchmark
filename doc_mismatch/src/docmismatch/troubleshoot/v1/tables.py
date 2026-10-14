"""Markdown tables generated from the data (so the documentation cannot drift from the code): `python -m docmismatch.troubleshoot.v1 --tables`."""

from __future__ import annotations

from . import catalogue as K
from . import causes as C
from . import data as D


def _mins(c: K.CheckV1) -> str:
    parts = [f"{c.access_min:g}", f"{c.do_min:g}", f"{c.wait_min:g}"]
    return " + ".join(parts) + f" = {c.access_min + c.do_min + c.wait_min:g}"


FEATURE_TEXT = {"reheat": "box has reheat", "pressure_independent": "box is pressure-independent"}


def _needs(c: K.CheckV1) -> str:
    out = [f"{n.item}" + (f" (else +{n.fallback_min:g})" if n.fallback_min is not None else " (required)") for n in c.needs]
    if c.feature:
        out.append(f"{FEATURE_TEXT[c.feature]} (required)")
    return "; ".join(out) or "nothing"


def _sees(c: K.CheckV1) -> str:
    if c.is_reading:
        items = sorted(c.detects.items(), key=lambda kv: -kv[1])
        return ", ".join(f"{k} {v:.2f}" for k, v in items) + f"; every other cause {c.bg:.2f}"
    base = f"hit {c.v0.tpr:.2f} / false alarm {c.v0.fpr:.2f} (v0's rates)"
    if c.overrides:
        base += "; refined causes: " + ", ".join(f"{k} {v:.2f}" for k, v in sorted(c.overrides.items(), key=lambda kv: -kv[1]))
    return base


def cause_table() -> str:
    rows = ["| Branch | Cause | What it covers | Share of its lump (placeholder) | v0 lump | Where in the guides |", "|---|---|---|---|---|---|",
            "| documentation | Documented box is wrong (which one), or fed by something not on the list | the drawings' claim about which box serves the room | prior P(wrong) 0.15, of which 10% unlisted (v0's placeholders) | (v0's own causes) | v0 |"]
    for c in C.CAUSES:
        rows.append(f"| {c.group} | `{c.id}`: {c.label} | {c.detail} | {c.share:.2f} | {c.lump} | {', '.join(c.refs)} |")
    return "\n".join(rows)


def catalogue_table() -> str:
    rows = ["| Check | Family | Minutes (access + do + wait) | Needs (fallback when missing) | Causes it sees: P(positive), placeholder | Procedure in |", "|---|---|---|---|---|---|"]
    for c in K.CATALOGUE:
        rows.append(f"| `{c.name}` | {c.family} | {_mins(c)} | {_needs(c)} | {_sees(c)} | {', '.join(c.refs)} |")
    return "\n".join(rows)


def reading_table() -> str:
    rows = ["| Check | Quantity | Normal when | Source of the expected value |", "|---|---|---|---|"]
    for c in K.CATALOGUE:
        if c.reading is not None:
            r = c.reading
            rule = (f"within {r.tol:g} {r.unit} of {r.expected:g}" if r.tol is not None and r.expected is not None else
                    f"within {r.rel_tol:.0%} of the expected value" + (f" (documented `{r.expected_attr}`, else the technician's)" if r.expected_attr else " (the technician's)") if r.rel_tol is not None else
                    "at or above the minimum for the inlet size" if r.low_fn is not None else f"at least {r.low:g} {r.unit}")
            rows.append(f"| `{c.name}` | {r.quantity} ({r.unit or 'no unit'}) | {rule} | {r.source} |")
    return "\n".join(rows)


def tier_table() -> str:
    rows = ["| Tier | Data items | What it means |", "|---|---|---|"]
    for t, items in D.TIERS.items():
        rows.append(f"| {t} | {', '.join(sorted(items)) or 'none'} | {D.TIER_TEXT[t]} |")
    return "\n".join(rows)


def all_tables() -> dict[str, str]:
    return dict(causes=cause_table(), catalogue=catalogue_table(), readings=reading_table(), tiers=tier_table())
