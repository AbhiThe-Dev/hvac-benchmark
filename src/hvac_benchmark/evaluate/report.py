"""Generate `results/results.md` and the accompanying plots.

The plan requires the topology counts to appear before any percentage,
chart, or savings claim, evidence to be labeled as a small case-study
sample, and pooled cross-topology confidence bands to never be presented as
generalizing across buildings. This module enforces that structure in code
rather than leaving it to prose discipline.
"""

from __future__ import annotations

from pathlib import Path

from ..config import BenchmarkConfig
from ..experiment.runner import TrialResult
from ..graph.inventory import TopologyInventory
from ..pipeline import Bundle, RelationAvailability
from .aggregate import GroupSummary, paired_savings, summarize_group
from .plots import plot_paired_savings, plot_recovery_curves, plot_threshold_cost_distribution
from .troubleshooting_report import build_troubleshooting_section

FEEDS_POLICIES_ORDER = ("active", "frozen_initial", "rule_based", "traversal", "random")


def _fmt_summary(s) -> str:
    if s.n == 0:
        return "n/a (0/N seeds attained)"
    return f"{s.median:.0f} [{s.lo:.0f}-{s.hi:.0f}] tests (n={s.n})"


def _fmt_final(s) -> str:
    if s.n == 0:
        return "n/a"
    return f"{s.median:.2f} [{s.lo:.2f}-{s.hi:.2f}]"


def generate_report(
    bundles: list[Bundle],
    inventories: list[TopologyInventory],
    availabilities: dict[tuple[str, str], RelationAvailability],
    main_results: list[TrialResult],
    ablation_results: list[TrialResult],
    provenance_report: dict,
    config: BenchmarkConfig,
    results_path: Path,
    troubleshooting_results: list | None = None,
    blueprints_by_building: dict | None = None,
) -> None:
    plots_dir = results_path / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    real_bundles = [b for b in bundles if b.category == "real"]
    synthetic_bundles = [b for b in bundles if b.category == "synthetic"]
    inv_by_id = {inv.building_id: inv for inv in inventories}

    feeds_usable_real = [
        b for b in real_bundles if availabilities[(b.tg.building_id, "feeds")].available
    ]
    feeds_unavailable_real = [
        b for b in real_bundles if not availabilities[(b.tg.building_id, "feeds")].available
    ]
    duplicate_real = [b for b in real_bundles if inv_by_id[b.tg.building_id].is_duplicate_of is not None]

    lines: list[str] = []
    lines.append("# HVAC Topology Discovery Benchmark -- Results\n")

    # --- Required lead: topology counts before any percentage/chart/savings claim ---
    lines.append("## Topology counts (read this first)\n")
    lines.append(
        f"- **{len(feeds_usable_real)} distinct real topologies** are used in the primary `feeds` "
        f"benchmark below, after merging, exclusions, and duplicate de-duplication "
        f"({len(duplicate_real)} duplicate(s) found and excluded from this count)."
    )
    lines.append(
        f"- **{len(feeds_unavailable_real)} additional real topologies** were extracted from the same "
        f"corpus but are **not** part of the primary `feeds` benchmark (each reason given below); they are "
        f"still evaluated on `hasPoint`/`hasPart` where those relations are available."
    )
    lines.append(
        f"- **{len(synthetic_bundles)} supplementary synthetic AHU-VAV-zone graphs** are reported "
        f"**separately** and are never included in the real-topology counts above."
    )
    lines.append("")
    lines.append("Real topologies and their primary-benchmark status:\n")
    lines.append("| building_id | config_type | feeds available? | reason |")
    lines.append("|---|---|---|---|")
    for b in real_bundles:
        avail = availabilities[(b.tg.building_id, "feeds")]
        dup = inv_by_id[b.tg.building_id].is_duplicate_of
        reason = f"duplicate of {dup}" if dup else avail.reason
        lines.append(f"| {b.tg.building_id} | {b.tg.config_type} | {avail.available and not dup} | {reason} |")
    lines.append("")
    if duplicate_real:
        lines.append(
            "> Note on duplicates: a structural duplicate is flagged when two topologies have the "
            "identical multiset of (Brick type, relation-typed edge) after erasing real entity names -- "
            "not when they merely share a facility. In this corpus, parallel- and series-fan-powered-unit "
            "testbeds (`pfpu`/`sfpu`) are typed generically as `Terminal_Unit` in the source Brick models, "
            "so the physical distinction between them (parallel vs. series fan arrangement) is not captured "
            "by any type or relation this benchmark can see, making their graphs indistinguishable under "
            "this abstraction even though they are different physical equipment.\n"
        )

    lines.append(
        "> **Evidence level: this is a small case-study sample, not a statistically powered benchmark.** "
        "30 seeds per topology/noise condition measure within-topology variability (noise realization + "
        "tie-breaking), not additional independent buildings. Results are reported per topology; no pooled "
        "cross-topology confidence interval is computed or implied anywhere in this document.\n"
    )

    # --- Provenance ---
    lines.append("## Data provenance\n")
    if provenance_report["fallback_used"]:
        lines.append(
            f"**Brick-example fallback was used.** Reason: {provenance_report['fallback_reason']}. "
            f"Results below are still from the primary corpus where available; see `provenance.json`."
        )
    else:
        lines.append(
            "All Brick models were extracted from the primary Figshare source via ranged HTTP reads "
            "(see `provenance.json` for per-file checksums, source URLs, and license/citation metadata)."
        )
    lines.append("\nFile-to-building mapping (see `file_to_building.json` for full evidence text):\n")
    lines.append("| building_id | config_type | member files |")
    lines.append("|---|---|---|")
    for bid, info in provenance_report["file_to_building"].items():
        lines.append(f"| {bid} | {info['config_type']} | {', '.join(info['member_files'])} |")
    if provenance_report["excluded_groups"]:
        lines.append("\nExcluded/ambiguous groupings:\n")
        for g in provenance_report["excluded_groups"]:
            lines.append(f"- {g['building_id']} ({g['status']}): {g['members']}")
    lines.append("")

    # --- Inventory ---
    lines.append("## Graph inventory\n")
    lines.append("| building_id | category | nodes | feeds | hasPoint | hasPart | unknown classes | aliases applied |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for b in bundles:
        inv = inv_by_id[b.tg.building_id]
        lines.append(
            f"| {inv.building_id} | {b.category} | {inv.n_nodes} | "
            f"{inv.relation_counts.get('feeds', 0)} | {inv.relation_counts.get('hasPoint', 0)} | "
            f"{inv.relation_counts.get('hasPart', 0)} | {len(inv.unknown_classes)} | {len(inv.class_aliases_applied)} |"
        )
    lines.append("")

    # --- Main results, feeds ---
    def group_key(r: TrialResult):
        return (r.building_id, r.relation, r.experiment, r.policy, r.noise_level)

    grouped: dict[tuple, list[TrialResult]] = {}
    for r in main_results:
        grouped.setdefault(group_key(r), []).append(r)

    lines.append("## Primary benchmark: `feeds`\n")
    lines.append(
        "For each topology, tests needed to *first* and to *sustainedly* reach the primary "
        f"P>={config.primary_precision:.0%}/R>={config.primary_recall:.0%} threshold (secondary "
        f"P>={config.secondary_precision:.0%}/R>={config.secondary_recall:.0%} in parentheses where attained), "
        "median [range] across seeds, with attainment rate. Never-attained cells say so plainly.\n"
    )

    all_summaries: list[GroupSummary] = []
    for b in feeds_usable_real + synthetic_bundles:
        bid = b.tg.building_id
        for experiment in ("independent", "structured"):
            key0 = (bid, "feeds", experiment, "active", 0.0)
            if key0 not in grouped:
                continue
            lines.append(f"### {bid} ({b.category}) -- {experiment} experiment\n")
            for noise in config.noise_levels:
                lines.append(f"**noise = {noise:.0%}**\n")
                lines.append("| policy | first-attain (90/90) | rate | sustained | rate | final P | final R |")
                lines.append("|---|---|---|---|---|---|---|")
                for policy in FEEDS_POLICIES_ORDER:
                    key = (bid, "feeds", experiment, policy, noise)
                    if key not in grouped:
                        continue
                    summary = summarize_group(grouped[key], config)
                    all_summaries.append(summary)
                    lines.append(
                        f"| {policy} | {_fmt_summary(summary.primary_first)} | "
                        f"{summary.primary_first_attainment_rate:.0%} | "
                        f"{_fmt_summary(summary.primary_sustained)} | "
                        f"{summary.primary_sustained_attainment_rate:.0%} | "
                        f"{_fmt_final(summary.final_precision)} | {_fmt_final(summary.final_recall)} |"
                    )
                lines.append("")

            # plots at noise=0.05 (representative) across all policies
            results_by_policy = {
                policy: grouped.get((bid, "feeds", experiment, policy, 0.05), [])
                for policy in FEEDS_POLICIES_ORDER
            }
            if any(results_by_policy.values()):
                recovery_path = plots_dir / f"{bid}_{experiment}_recovery.png"
                plot_recovery_curves(results_by_policy, f"{bid} ({experiment}, noise=5%)", recovery_path)
                cost_path = plots_dir / f"{bid}_{experiment}_threshold_cost.png"
                plot_threshold_cost_distribution(
                    results_by_policy, config.primary_precision, config.primary_recall,
                    f"{bid} ({experiment}, noise=5%) tests-to-90/90", cost_path,
                )
                lines.append(f"![recovery]({recovery_path.relative_to(results_path)})")
                lines.append(f"![threshold cost]({cost_path.relative_to(results_path)})\n")

            active_key = (bid, "feeds", experiment, "active", 0.0)
            random_key = (bid, "feeds", experiment, "random", 0.0)
            if active_key in grouped and random_key in grouped:
                savings = paired_savings(grouped[active_key], grouped[random_key], config)
                savings_path = plots_dir / f"{bid}_{experiment}_paired_savings.png"
                plot_paired_savings(savings, f"{bid} ({experiment}) active vs random, noiseless", savings_path)
                lines.append(f"![paired savings]({savings_path.relative_to(results_path)})\n")

    if feeds_unavailable_real:
        lines.append("### Topologies excluded from the `feeds` benchmark\n")
        for b in feeds_unavailable_real:
            avail = availabilities[(b.tg.building_id, "feeds")]
            lines.append(f"- **{b.tg.building_id}**: {avail.reason} "
                         f"({avail.n_true_edges} true edge(s), {avail.n_candidates} candidate(s) generated).")
        lines.append("")

    # --- Secondary relations ---
    lines.append("## Secondary benchmarks: `hasPoint`, `hasPart`\n")
    lines.append(
        "Evaluated independently from `feeds`; only the independent-edge experiment is run here "
        "(structured beliefs are defined only for `feeds` terminal-unit/zone targets). Reported as final "
        "precision/recall/F1 (median [range] across seeds) at noise=5%, active policy, since the point of "
        "this section is coverage/availability rather than a full policy comparison.\n"
    )
    for relation in ("hasPoint", "hasPart"):
        lines.append(f"### `{relation}`\n")
        lines.append("| building_id | available? | reason | final P | final R | final F1 |")
        lines.append("|---|---|---|---|---|---|")
        for b in real_bundles:
            avail = availabilities[(b.tg.building_id, relation)]
            key = (b.tg.building_id, relation, "independent", "active", 0.05)
            if avail.available and key in grouped:
                summary = summarize_group(grouped[key], config)
                lines.append(
                    f"| {b.tg.building_id} | yes | -- | {_fmt_final(summary.final_precision)} | "
                    f"{_fmt_final(summary.final_recall)} | {_fmt_final(summary.final_f1)} |"
                )
            else:
                lines.append(f"| {b.tg.building_id} | no | {avail.reason} | -- | -- | -- |")
        lines.append("")

    # --- Ablations ---
    if ablation_results:
        lines.append("## Ablations (representative subset only)\n")
        lines.append(
            f"Run on {', '.join(sorted(set(r.building_id for r in ablation_results)))} only, to bound total "
            "compute; not a full per-topology ablation grid.\n"
        )

        lines.append("### Uniform-prior ablation (independent experiment, active policy)\n")
        abl_grouped: dict[tuple, list[TrialResult]] = {}
        for r in ablation_results:
            abl_grouped.setdefault((r.building_id, r.relation, r.experiment, r.policy, r.noise_level, r.prior_kind), []).append(r)
        lines.append("| building_id | noise | prior | first-attain (90/90) | rate |")
        lines.append("|---|---|---|---|---|")
        for bid in sorted(set(r.building_id for r in ablation_results)):
            for noise in config.noise_levels:
                for prior_kind in ("sparse", "uniform"):
                    if prior_kind == "sparse":
                        key = (bid, "feeds", "independent", "active", noise)
                        src = grouped
                    else:
                        key = (bid, "feeds", "independent", "active", noise, "uniform")
                        src = abl_grouped
                    if key not in src:
                        continue
                    summary = summarize_group(src[key], config)
                    lines.append(
                        f"| {bid} | {noise:.0%} | {prior_kind} | {_fmt_summary(summary.primary_first)} | "
                        f"{summary.primary_first_attainment_rate:.0%} |"
                    )
        lines.append("")

        lines.append("### Structured cardinality sensitivity (lambda)\n")
        lines.append("| building_id | noise | lambda | first-attain (90/90) | rate | parent-count violations |")
        lines.append("|---|---|---|---|---|---|")
        by_lam: dict[tuple, list[TrialResult]] = {}
        for r in ablation_results:
            if r.experiment == "structured":
                by_lam.setdefault((r.building_id, r.relation, r.experiment, r.policy, r.noise_level, r.lam), []).append(r)
        for bid in sorted(set(r.building_id for r in ablation_results)):
            for noise in config.noise_levels:
                for lam in config.lambda_sensitivity:
                    if lam == config.default_lambda:
                        # the default lambda is already covered by the main grid
                        key = (bid, "feeds", "structured", "active", noise)
                        src = grouped
                    else:
                        key = (bid, "feeds", "structured", "active", noise, lam)
                        src = by_lam
                    if key not in src:
                        continue
                    summary = summarize_group(src[key], config)
                    lines.append(
                        f"| {bid} | {noise:.0%} | {lam} | {_fmt_summary(summary.primary_first)} | "
                        f"{summary.primary_first_attainment_rate:.0%} | {summary.total_parent_count_violations} |"
                    )
        lines.append("")

    # --- Where do gains come from ---
    lines.append("## Where gains come from\n")
    lines.append(
        "Comparing **frozen_initial** vs **active** isolates *adaptive selection* benefit (both start from the "
        "same information-gain-ranked priors; only active updates that ranking after each observation). "
        "Comparing **active (independent)** vs **active (structured)** isolates *structured-inference* benefit "
        "at a fixed selection strategy. Comparing the *uniform-prior* ablation vs the default *sparse* prior "
        "isolates how much of any gain is already present in the prior itself, before any adaptive selection. "
        "See the per-topology tables above; where active and frozen_initial are statistically indistinguishable "
        "at noise=0% in the independent experiment, this confirms the expected invariant (noiseless independent "
        "edges carry no information about each other, so nothing is left for adaptation to exploit) rather than "
        "indicating a bug.\n"
    )

    # --- Traversal heuristic disclaimer ---
    lines.append("## On the \"traversal heuristic\" baseline\n")
    lines.append(
        "**The traversal heuristic in this benchmark is a modeled assumption about unaided search order "
        "(fixed equipment-class precedence, location-ordered where metadata permits), not an empirically "
        "validated account of technician behavior.** No technician search sequences were observed or encoded "
        "anywhere in this codebase. Any favorable comparison to this baseline should be read as \"outperforms "
        "this modeled traversal heuristic,\" never as \"outperforms actual technician search.\"\n"
    )

    # --- Limitations ---
    lines.append("## Limitations and scope\n")
    lines.append(
        "- This experiment evaluates discovery of **asserted metadata** through **simulated** direct-relationship "
        "tests. It does not validate physical interventions, hardware, actual technician behavior, workflow, or "
        "deployment economics.\n"
        "- Closed-world approximation: an unasserted relationship is treated as absent for scoring. Even a "
        "correctly merged Brick model can omit real, physically-present connections that were simply never "
        "modeled by whoever authored it.\n"
        "- No UI, database, time-series fault inference, or building physics simulator is included.\n"
        "- Seed/noise ranges shown above are within-topology variability; between-topology variation is shown "
        "only through the separate per-topology results above, never as a pooled interval.\n"
    )

    # --- Troubleshooting-against-a-blueprint (separate evaluation mode) ---
    lines.extend(
        build_troubleshooting_section(troubleshooting_results or [], blueprints_by_building or {}, config)
    )

    (results_path / "results.md").write_text("\n".join(lines))
