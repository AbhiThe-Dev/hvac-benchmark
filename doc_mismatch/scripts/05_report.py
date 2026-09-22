"""Stage 5: render results/docmismatch/results.md from saved JSON (no numbers are typed by hand)."""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "results" / "docmismatch"
FAMS = ["wrong_ahu_mapping", "vav_zone_swap", "plant_loop_mapping", "sensor_mapping", "same_medium_branch", "parallel_peer_swap"]
FAM_LABEL = {"wrong_ahu_mapping": "Wrong AHU", "vav_zone_swap": "VAV-zone swap", "plant_loop_mapping": "Plant loop", "sensor_mapping": "Sensor mapping",
             "same_medium_branch": "Same-medium branch", "parallel_peer_swap": "Parallel peer swap"}
VLABEL = {
    "evidence_only": "Evidence only (no encoder)",
    "struct_only": "Documentation structure only (no encoder, no evidence)",
    "zero_shot_pretrained_masked": "Pretrained decoder, zero-shot (masked edge)",
    "zero_shot_pretrained_present": "Pretrained decoder, zero-shot (edge present)",
    "struct+random_frozen": "Structure + random-init encoder, frozen",
    "struct+pretrained_frozen": "Structure + pretrained encoder, frozen",
    "struct+scratch_finetuned": "Structure + scratch encoder, fine-tuned",
    "struct+pretrained_finetuned": "Structure + pretrained encoder, fine-tuned",
    "ev+random_frozen": "Evidence + random-init encoder, frozen  [no pretrain]",
    "ev+pretrained_frozen": "Evidence + pretrained encoder, frozen  [pretrained]",
    "ev+scratch_finetuned": "Evidence + scratch encoder, fine-tuned  [no pretrain]",
    "ev+pretrained_finetuned": "Evidence + pretrained encoder, fine-tuned  [pretrained]",
}
CORE = ["evidence_only", "ev+random_frozen", "ev+pretrained_frozen", "ev+scratch_finetuned", "ev+pretrained_finetuned"]
CONTROLS = ["struct_only", "zero_shot_pretrained_masked", "struct+random_frozen", "struct+pretrained_frozen", "struct+scratch_finetuned", "struct+pretrained_finetuned"]


def load(d):
    p = OUT / d / "metrics.json"
    return json.loads(p.read_text()) if p.exists() else None


def cell(x, k, sd=True):
    if x is None:
        return "–"
    s = f"{x[k]:.2f}"
    return s + (f" ±{x[k + '_sd']:.2f}" if sd and (k + "_sd") in x and x[k + "_sd"] >= 0.005 else "")


def main_table(m, view, slc, variants):
    rows = ["| Model | F1 (bal.) | AUROC | AUPRC (bal.) | Recall | Clean FP rate |", "|---|---|---|---|---|---|"]
    for v in variants:
        x = m[v][view].get(slc)
        rows.append(f"| {VLABEL[v]} | {cell(x, 'f1_bal')} | {cell(x, 'auroc')} | {cell(x, 'auprc_bal')} | {cell(x, 'recall')} | {cell(x, 'fpr_clean')} |")
    return "\n".join(rows)


def n_of(m, view, slc):
    x = m["evidence_only"][view].get(slc)
    return f"{x['n_pos']} corrupted vs {x['n_neg']} clean" if x else "n/a"


def _m(d):
    p = OUT / d / "metrics.json"
    return json.loads(p.read_text()) if p.exists() else None


def corrections_section():
    import pickle
    L = ["\n## v2 corrections: what changed and why (numbers above are the corrected ones)\n"]
    stages = [("v1 as originally reported", "eval_v1"), ("S0 refactored code, every fix OFF (reproduces v1)", "eval_s0"), ("S1 + variance floor 0.1 and clipping of standardized inputs", "eval_s1"),
              ("S2 + slot-level support mask (insufficient: see text)", "eval_s2"), ("S3 + regime-level support mask", "eval_s3"), ("S4 = final: + uninformative channels missing + calibrated threshold", "eval")]
    V = ["evidence_only", "ev+random_frozen", "ev+pretrained_frozen", "ev+scratch_finetuned", "ev+pretrained_finetuned"]
    for view, sl, title in (("spec_C", "hard", "specified split, test C, all hard"), ("loto_pooled", "hard", "LOTO pooled, all hard"), ("loto_A", "hard", "held-out A, all hard"), ("loto_B", "hard", "held-out B, all hard")):
        L.append(f"**AUROC, {title}** (stages are cumulative; S0-S3 share the v2 observability labels only where a slice depends on them, 'hard' does not)\n")
        L.append("| Stage | " + " | ".join(v.replace("ev+", "").replace("_", " ") for v in V) + " |\n|---|" + "---|" * len(V))
        for name, d in stages:
            m = _m(d)
            if m is None:
                continue
            L.append(f"| {name} | " + " | ".join((f"{m[v][view][sl]['auroc']:.2f}" if sl in m[v][view] else "–") for v in V) + " |")
        L.append("")
    old, new = _m("eval_v1"), _m("eval")
    L.append("**Clean false-positive rate at the operating threshold, v1 vs v2** (v1: zero false positives on 6 validation documents; v2: 90th percentile of 24 held-out clean calibration documents per training topology)\n")
    L.append("| Model | v1 spec C | v2 spec C | v1 LOTO pooled | v2 LOTO pooled | v1 held-out B | v2 held-out B |\n|---|---|---|---|---|---|---|")
    for v in V:
        L.append(f"| {VLABEL[v]} | " + " | ".join(f"{m[v][vw]['hard']['fpr_clean']:.2f}" for vw in ("spec_C", "loto_pooled", "loto_B") for m in (old, new)) + " |")
    raw = OUT / "eval" / "raw.pkl"
    if raw.exists():
        r = pickle.load(open(raw, "rb"))["res"]
        cases = {c["case_id"]: c for c in (json.loads(l) for l in open(OUT / "cases.jsonl"))}
        L.append("\n**Corrupted cases excluded from scoring because a corrupted edge sits in a feature regime the head had no training support for**\n")
        L.append("| Fold | excluded | of which hard | remaining hard-observable |\n|---|---|---|---|")
        for f, ids in r["unsup_cases"].items():
            test = r["splits"][f]["test"]
            hard = sum(cases[i]["difficulty"] == "hard" for i in ids)
            rem = sum(1 for i in test if cases[i]["difficulty"] == "hard" and cases[i]["observable"] == "true" and i not in set(ids))
            L.append(f"| {f} | {len(ids)} | {hard} | {rem} |")
    return "\n".join(L) + "\n"


def real_section():
    p = OUT / "real_frp" / "real_results.json"
    if not p.exists():
        return ""
    d = json.loads(p.read_text())
    L = ["\n## Real-data test: ORNL FRP RTU-VAV field data (LBNL FDD Data Sets RTU, `ORNL_RTU/ERTU_*.csv`)\n"]
    L.append(f"{d['n_events']} documentation-error events (all 45 room-pair swaps x 4 connection types) x {d['n_days']} real days; each (event, day) is scored against the clean documentation of the same day. "
             "Evidence detector = untrained margin rule on coupling checks (no per-box airflow exists in this data); structure-only = pretrained decoder zero-shot on the documented graph. "
             "CIs: two-way cluster bootstrap over events and days (2000 draws).\n")
    L.append("| Slice | events | days | Evidence rule AUROC [95% CI] | Structure-only AUROC | Δ [95% CI] |\n|---|---|---|---|---|---|")
    for k, v in d["real"].items():
        L.append(f"| {k} | {v['n_events']} | {v['n_days']} | {v['rule']:.3f} [{v['rule_ci'][0]:.2f}, {v['rule_ci'][1]:.2f}] | {v['struct']:.3f} | {v['delta']:+.3f} [{v['delta_ci'][0]:+.2f}, {v['delta_ci'][1]:+.2f}] |")
    L.append("\n**Same untrained rule on the simulated benchmark** (hard vs clean, pooled within topology, group bootstrap)\n")
    L.append("| Slice | n | AUROC [95% CI] |\n|---|---|---|")
    for k, v in d["sim_rule"].items():
        L.append(f"| {k} | {v['n']} | {v['rule']:.3f} [{v['ci'][0]:.2f}, {v['ci'][1]:.2f}] |")
    L.append("\nDay-level observability (real): " + "; ".join(f"{f}: {o['observable']} observable / {o['ambiguous']} ambiguous / {o['unobservable']} unobservable" for f, o in d["day_obs"].items()) + ".\n")
    return "\n".join(L) + "\n"


def main():
    cases = [json.loads(l) for l in open(OUT / "cases.jsonl")]
    audit = json.loads((OUT / "diversity_audit.json").read_text())
    m = load("eval")
    sf = load("eval_scalefree")
    comps = json.loads((OUT / "eval" / "comparisons.json").read_text())
    L = []
    P = L.append
    findings = (ROOT / "findings.md")
    if findings.exists():
        P(findings.read_text())
    P("\n---\n# Generated tables (from results/docmismatch/eval/*.json)\n")
    P("## Benchmark composition\n")
    c = Counter((x["topology_letter"], x["difficulty"]) for x in cases)
    P("| Topology | Hard | Easy | Clean | Total |\n|---|---|---|---|---|")
    names = {"A": "A `sys07_vav_reheat` (1 AHU, 10 VAV, 1 HW + 1 CHW loop; vendored)", "B": "B `sys03_psz_ac` (10 single-zone AHUs, no plant; vendored)",
             "C": "C `vav_2ahu_2loops` (2 AHUs, 2 HW + 2 CHW loops; built)", "D": "D `vav_3ahu_2loops` (3 AHUs, 2 HW + 2 CHW loops, Golden CO climate; built)"}
    for t in "ABCD":
        h, e, cl = c[(t, "hard")], c[(t, "easy")], c[(t, "clean")]
        P(f"| {names[t]} | {h} | {e} | {cl} | {h + e + cl} |")
    P(f"| **Total** | {sum(v for (t, d), v in c.items() if d == 'hard')} | {sum(v for (t, d), v in c.items() if d == 'easy')} | {sum(v for (t, d), v in c.items() if d == 'clean')} | {len(cases)} |\n")
    P("## Diversity audit (Phase 12)\n")
    P("Every row is a distinct physical event (one row per event; no paraphrases, no re-windowed duplicates). "
      "'Substitutions' counts distinct (topology, true owner -> documented owner) pairs; 'Components' counts distinct equipment nodes touched.\n")
    P("| Family | Rows | Base topologies | Distinct targets | Distinct components | Distinct replacement endpoints | Distinct substitutions | Leakage groups | Degree-preserving rows | Subtypes |\n|---|---|---|---|---|---|---|---|---|---|")
    for f in FAMS:
        a = audit[f]
        P(f"| {FAM_LABEL[f]} | {a['rows']} | {a['base_topologies']} | {a['distinct_target_connections']} | {a['distinct_components']} | {a['distinct_replacement_endpoints']} | "
          f"{a['distinct_actual_to_documented_substitutions']} | {a['distinct_leakage_groups']} | {a['degree_preserving_rows']} | {', '.join(f'{k}:{v}' for k, v in a['subtypes'].items())} |")
    P("\nCandidate funnel (proposed -> passing every hard filter): " + "; ".join(f"{FAM_LABEL[f]} {audit[f]['candidates_proposed']} -> {audit[f]['candidates_passing_hard_filter']}" for f in FAMS) + ".\n")
    P("## Observability (Phase 8)\n")
    P("| Family | observable | ambiguous | unobservable |\n|---|---|---|---|")
    for f in FAMS:
        o = audit[f]["observable"]
        P(f"| {FAM_LABEL[f]} | {o.get('true', 0)} | {o.get('ambiguous', 0)} | {o.get('false', 0)} |")
    P("")
    for view, title in (("spec_C", "Specified split: train on A+B, test on held-out topology C"), ("spec_D", "Specified split: same model, second held-out topology D"),
                        ("loto_pooled", "Leave-one-topology-out, pooled over the four held-out topologies (each case scored by a model that never saw its topology)")):
        P(f"## Headline: {title}\n")
        P("Mean ± sd over 5 training seeds. Threshold fixed on validation only (smallest threshold with 0 false positives on validation clean cases). "
          "'bal.' = negatives re-weighted to 50% prevalence (chance AUPRC = 0.5).\n")
        for slc, nm in (("hard_observable", "Hard mismatches with sufficient physical evidence (primary)"), ("hard", "All hard mismatches"), ("easy", "Easy mismatches (sanity check; plausibility-confounded)")):
            P(f"**{nm}** — {n_of(m, view, slc)}\n")
            P(main_table(m, view, slc, CORE + CONTROLS if slc == "hard_observable" else CORE + ["struct_only", "zero_shot_pretrained_masked"]))
            P("")
    P("## By corruption family (AUROC, leave-one-topology-out pooled)\n")
    P("| Model | " + " | ".join(FAM_LABEL[f] for f in FAMS) + " |\n|---|" + "---|" * len(FAMS))
    for v in CORE + ["struct_only", "zero_shot_pretrained_masked"]:
        P(f"| {VLABEL[v]} | " + " | ".join(cell(m[v]["loto_pooled"].get(f), "auroc", sd=False) for f in FAMS) + " |")
    P("\nRows per family slice: " + ", ".join(f"{FAM_LABEL[f]} {m['evidence_only']['loto_pooled'][f]['n_pos']}" for f in FAMS) + f"; clean negatives are the held-out topology's own (family slices share them).\n")
    P("## By held-out topology (hard AUROC / clean FP rate), leave-one-topology-out\n")
    P("| Model | A | B | C | D |\n|---|---|---|---|---|")
    for v in CORE:
        P(f"| {VLABEL[v]} | " + " | ".join(f"{m[v][f'loto_{t}']['hard']['auroc']:.2f} / {m[v][f'loto_{t}']['hard']['fpr_clean']:.2f}" for t in "ABCD") + " |")
    P("\n## Observable vs not-observable vs degree-controlled slices (AUROC, leave-one-topology-out pooled)\n")
    slices = [("hard_observable", "Observable"), ("hard_not_observable", "Ambiguous + unobservable"), ("hard_degree_preserving", "Degree-preserving (structure-controlled)"),
              ("hard_observable_dp", "Observable AND degree-preserving"), ("hard_degree_shift", "Retargets (degree shift; structure-confounded)")]
    P("| Model | " + " | ".join(f"{n} (n={m['evidence_only']['loto_pooled'][s]['n_pos']})" for s, n in slices) + " |\n|---|" + "---|" * len(slices))
    for v in CORE + CONTROLS:
        P(f"| {VLABEL[v]} | " + " | ".join(cell(m[v]["loto_pooled"].get(s), "auroc", sd=False) for s, _ in slices) + " |")
    P("\n## Does pretraining help? Paired group-bootstrap of Δ AUROC (pretrained − no-pretrain)\n")
    P("Resampling leakage groups (2000 draws); case scores averaged over 5 seeds. Positive Δ = pretrained better. CI excluding 0 = distinguishable from no effect.\n")
    P("| Comparison | Slice | View | AUROC (first) | AUROC (second) | Δ | 95% CI |\n|---|---|---|---|---|---|---|")
    nice = {"finetuned_ev": "Evidence + pretrained FT − evidence + scratch FT", "frozen_ev": "Evidence + pretrained frozen − evidence + random frozen",
            "finetuned_struct": "Structure + pretrained FT − structure + scratch FT", "frozen_struct": "Structure + pretrained frozen − structure + random frozen",
            "pretrained_ft_vs_evidence_only": "Evidence + pretrained FT − evidence only", "pretrained_frozen_vs_evidence_only": "Evidence + pretrained frozen − evidence only",
            "evidence_vs_struct": "Evidence only − structure only (does physical evidence matter?)"}
    for k, v in comps.items():
        view, name, sl = k.split("/")
        if sl in ("hard_not_observable",):
            continue
        P(f"| {nice[name]} | {sl} | {'LOTO pooled' if view == 'loto' else 'train A+B → test C'} | {v['auroc_a']:.3f} | {v['auroc_b']:.3f} | {v['delta']:+.3f} | [{v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f}] |")
    if sf:
        P("\n## Sensitivity: scale-free features (absolute log-error columns removed)\n")
        P("Same pipeline, same seeds; only the evidence feature set changes. AUROC / clean FP rate on observable hard cases.\n")
        P("| Model | LOTO pooled | spec C | spec D |\n|---|---|---|---|")
        for v in CORE:
            P(f"| {VLABEL[v]} | " + " | ".join(f"{sf[v][w]['hard_observable']['auroc']:.2f} / {sf[v][w]['hard_observable']['fpr_clean']:.2f}" for w in ("loto_pooled", "spec_C", "spec_D")) + " |")
    P(corrections_section())
    P(real_section())
    (OUT / "results.md").write_text("\n".join(L) + "\n")
    print("wrote", OUT / "results.md")


main()
