"""results.md section for the troubleshooting-against-a-blueprint
evaluation mode. Kept in its own module and called additively from
`evaluate/report.py` so the existing discovery-mode report logic is never
touched by this addition.
"""

from __future__ import annotations

from ..config import BenchmarkConfig
from ..experiment.blueprint import Blueprint
from ..experiment.troubleshooting_runner import TroubleshootingTrialResult
from .troubleshooting_aggregate import summarize_troubleshooting_group

BLIND_POLICIES_ORDER = ("active", "full_sweep", "blueprint_literal")
SYMPTOM_POLICIES_ORDER = ("active", "symptom_naive", "full_sweep", "blueprint_literal")


def _fmt(s) -> str:
    if s.n == 0:
        return "n/a (0 attained)"
    return f"{s.median:.0f} [{s.lo:.0f}-{s.hi:.0f}] (n={s.n})"


def _fmt_rate(s) -> str:
    if s.n == 0:
        return "n/a"
    return f"{s.median:.1%} [{s.lo:.1%}-{s.hi:.1%}]"


def build_troubleshooting_section(
    troubleshooting_results: list[TroubleshootingTrialResult],
    blueprints_by_building: dict[str, list[Blueprint]],
    config: BenchmarkConfig,
) -> list[str]:
    lines: list[str] = []
    if not troubleshooting_results:
        return lines

    topologies = sorted({r.building_id for r in troubleshooting_results})

    lines.append("## Troubleshooting-against-a-blueprint (separate evaluation mode)\n")
    lines.append(
        "**This section is a separate evaluation mode from the full-topology-discovery results "
        "above and is never blended with them.** Discovery mode assumes near-zero prior knowledge "
        "and measures tests to reconstruct an entire graph from scratch. This mode assumes the "
        "opposite starting condition: a trusted blueprint (the true graph, deliberately corrupted "
        "at a few points) is already given, and the task is to find the corrupted edge(s) in as "
        "few tests as possible -- the day-to-day troubleshooting scenario, not a periodic full "
        "audit.\n"
    )
    lines.append(
        f"- **{len(topologies)} real topologies** evaluated in this mode: {', '.join(topologies)} "
        "(the same `feeds`-eligible topologies used by the primary discovery benchmark above).\n"
        f"- Corruption severities tested: {list(config.troubleshooting_severities)} corrupted "
        f"edge(s) (an edge = one corruption event; misattribution counts as one event even though "
        f"it touches two candidate pairs), with {config.troubleshooting_n_variants} "
        "independently-seeded corrupted-blueprint variants per (topology, severity), each replayed "
        f"across {config.troubleshooting_n_seeds_per_variant} tie-break/noise seeds -- a "
        "deliberately bounded sample (mirroring the ablation-subset bounding elsewhere in this "
        "report), not a statistically powered sweep.\n"
    )
    lines.append(
        "> **Evidence level: small case study, same caveat as the rest of this document.** Numbers "
        "below are within-topology variability across corrupted-blueprint variants and seeds, not "
        "additional independent buildings or corruption instances beyond what is listed above. No "
        "pooled cross-topology number is computed or implied anywhere in this section.\n"
    )
    lines.append(
        "**Belief model reuse:** this mode reuses the exact same Bernoulli update and "
        "expected-information-gain machinery as discovery mode (`bayes.update` / "
        "`expected_information_gain`), completely unmodified -- only the prior changes "
        "(near-certain on blueprint-claimed edges, sparse-floor elsewhere), confirming the two "
        "modes did not need a parallel inference system.\n"
    )
    lines.append(
        "**Candidate universe:** identical physically-plausible candidate set as discovery mode's "
        "`feeds` benchmark, not just blueprint-claimed edges -- required so an undocumented real "
        "connection (a *removal* corruption) can be tested at all. One consequence: **the "
        "`full_sweep` baseline only re-tests blueprint-claimed edges, so by construction it can "
        "never find a removal-type corruption** -- a structural limitation of that reference "
        "baseline, not a bug, visible below wherever removal corruptions appear in a topology's "
        "mix.\n"
    )
    lines.append(
        "**Metric:** tests needed until every corrupted candidate is simultaneously flagged "
        "(current belief disagrees with the blueprint's own claim), first-reached and "
        "sustained-to-end-of-trial, median [range] across variants x seeds, with attainment rate. "
        "Also reported: false-positive rate (fraction of genuinely-correct blueprint edges ever "
        "incorrectly flagged along the way) and needless-retest count (tests spent on edges that "
        "were both blueprint-claimed-true and genuinely correct) -- a technician chasing a phantom "
        "problem, or an algorithm ignoring the strong prior it was given, are both counted as real "
        "costs here, never as neutral.\n"
    )

    for bid in topologies:
        blueprints = blueprints_by_building.get(bid, [])
        types_seen = sorted({e.corruption_type for bp in blueprints for e in bp.events})
        lines.append(f"### {bid}\n")
        lines.append(
            f"Corruption types actually generated for this topology across all variants: "
            f"{', '.join(types_seen) if types_seen else 'none (too small/constrained to corrupt)'}.\n"
        )
        if not blueprints:
            lines.append(
                "_No corrupted-blueprint variants could be constructed for this topology (too few "
                "candidate parents to safely remove, fabricate, or misattribute an edge without "
                "ambiguity); skipped._\n"
            )
            continue

        for symptom_mode, policies_order, title in (
            (False, BLIND_POLICIES_ORDER, "Blind verification"),
            (True, SYMPTOM_POLICIES_ORDER, "Symptom-triggered"),
        ):
            subset = [r for r in troubleshooting_results if r.building_id == bid and r.symptom_mode == symptom_mode]
            if not subset:
                continue
            lines.append(f"**{title}**\n")
            for severity in config.troubleshooting_severities:
                sev_subset = [r for r in subset if r.requested_severity == severity]
                if not sev_subset:
                    continue
                lines.append(f"severity = {severity} corrupted edge(s):\n")
                lines.append(
                    "| policy | noise | first-flag (all corrupted) | rate | sustained | rate | "
                    "false-positive rate | needless retests |"
                )
                lines.append("|---|---|---|---|---|---|---|---|")
                for policy in policies_order:
                    for noise in config.noise_levels:
                        group = [r for r in sev_subset if r.policy == policy and r.noise_level == noise]
                        if not group:
                            continue
                        summary = summarize_troubleshooting_group(group)
                        lines.append(
                            f"| {policy} | {noise:.0%} | {_fmt(summary.tests_to_full_flag_first)} | "
                            f"{summary.first_attainment_rate:.0%} | "
                            f"{_fmt(summary.tests_to_full_flag_sustained)} | "
                            f"{summary.sustained_attainment_rate:.0%} | "
                            f"{_fmt_rate(summary.final_false_positive_rate)} | "
                            f"{_fmt(summary.final_needless_retests)} |"
                        )
                lines.append("")

        active_all = [r for r in troubleshooting_results if r.building_id == bid and r.policy == "active"]
        full_sweep_all = [r for r in troubleshooting_results if r.building_id == bid and r.policy == "full_sweep"]
        if active_all and full_sweep_all:
            active_attain = sum(1 for r in active_all if r.n_tests_to_full_flag_first is not None) / len(active_all)
            sweep_attain = sum(1 for r in full_sweep_all if r.n_tests_to_full_flag_first is not None) / len(
                full_sweep_all
            )
            if active_attain <= sweep_attain:
                lines.append(
                    f"> **Honest note for {bid}:** across all severities/noise levels tested here, active does "
                    f"not clearly beat full_sweep on attainment rate ({active_attain:.0%} vs {sweep_attain:.0%}) "
                    "-- reported plainly rather than smoothed over.\n"
                )

        if bid == "ddahu":
            lines.append(
                "> **Observation (not investigated here):** `ddahu`'s discovery-mode structured experiment "
                "already shows a high-noise reliability gap (see the primary benchmark section above). If "
                "this topology's troubleshooting attainment above is also weaker at noise=15%, that may be the "
                "same underlying difficulty showing up in a second evaluation mode -- noted as a possible "
                "connection only; the ddahu investigation itself remains separate, ongoing work and is not in "
                "scope for this section.\n"
            )

    return lines
