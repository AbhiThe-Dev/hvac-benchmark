# Closing the active-vs-random gap on real data: diagnosis, fix, validation

Status: **the premise is only partly right, the fix is small and mostly neutral, and I could not make active clearly better than the best
alternative at 24 readings on this building.** Full tables: `results/docmismatch/active/selection/selection_results.md` (all arms, CIs,
ablations, by-season) and `.../selection/diagnostics.md`. New pickles: `results/docmismatch/active/{real,sim}_sel.pkl` (paired, same episodes and
seeds as `real_oat.pkl` / `sim_oat.pkl`, which are untouched). Code: `src/docmismatch/active/{model,engine,calibrate,selection}.py`,
`scripts/{12,14}` (default behaviour bit-identical: rerun reproduces the old pickles to <1e-6), `scripts/13_selection_report.py`,
`scripts/13_selection_diagnostics.py`, `tests/test_selection.py` (44 tests pass in the suite; 11 new). `scripts/exploration_selection/` holds the
throwaway probes quoted below (they point at scratch pickle paths; not polished).

Conventions as in `active_findings.md`: class-balanced, 95% cluster-bootstrap CIs, tau=0.95, OAT-only context model, stopping derived post hoc from
never-stopped 24-reading trajectories, real = day-level-observable swaps + all correct edges (493 episodes: 73 wrong / 420 right, so few wrong episodes
and heavy clustering), sim = hard-observable + matched correct edges (748). "acc n=k" = forced verdict accuracy after k readings, no stopping.

## 1. Testing the premise (BEFORE numbers, paired active minus random, `real_oat.pkl`)

| setting | acc n=1 | n=2 | n=4 | n=8 | n=24 | readings (cap 24) | resolved |
|---|---|---|---|---|---|---|---|
| lodo | +0.17 [0.07, 0.27] | +0.17 [0.06, 0.28] | +0.14 [0.05, 0.22] | +0.12 [0.02, 0.21] | +0.02 [-0.05, 0.09] | -3.9 [-5.7, -2.4] | +0.23 [0.13, 0.35] |
| loso | +0.06 [-0.04, 0.16] | +0.10 [0.02, 0.22] | +0.11 [0.02, 0.19] | +0.09 [0.00, 0.17] | +0.01 [-0.07, 0.09] | -6.3 [-8.0, -4.7] | +0.32 [0.24, 0.40] |
| hist_loso | +0.08 [-0.02, 0.17] | +0.10 [0.04, 0.17] | +0.00 [-0.06, 0.07] | -0.03 [-0.10, 0.06] | -0.07 [-0.19, 0.02] | -9.7 [-11.8, -6.6] | +0.55 [0.41, 0.67] |

* "Active is no better than random at n=24": true, but that is a **ceiling, not a failure of ranking**. Active leads at n<=8 (+0.10 to +0.17, CIs exclude 0 in
  lodo and loso), resolves 23-55 points more episodes and needs 4-10 fewer readings. At n=24 every policy lands at 0.72-0.79 in lodo/loso,
  including a static owner sweep (rule_based 0.79). The evidence available in 24 readings simply caps forced accuracy near 0.75-0.8 (Section 3, D5).
* "In hist_loso active is worse than random at n=24 (0.65 vs 0.72)": the point estimate is -0.07 but the paired CI [-0.19, 0.02] includes 0. **Not established.**
  What is established is the calibration deficit: accuracy among resolved is 0.57 [0.50, 0.64] against a nominal 0.95, with 65% of episodes "resolved".
* The deficit is concentrated in one season. hist_loso by season of the test day, forced accuracy after 24 readings (point estimates; only 5 wrong episodes in spring):
  fall (58% of episodes, 46 of 73 wrong): active 0.56, random 0.67; winter: active 0.78, random 0.76; spring (5 wrong episodes): active 0.72, random 0.83; summer (no wrong episodes): active 0.87, random 0.77. At n=4..12 active is at 0.51-0.52 in
  fall, i.e. it calls nearly everything "wrong" (balanced accuracy 0.5).

## 2. Diagnosis (what causes it; evidence in `diagnostics.md`, mostly D1-D5)

| candidate | verdict | evidence |
|---|---|---|
| (a) empty/flat readings mis-ranked | **REAL, but a small effect on accuracy** | 57% of real 4-h blocks are empty for vav_sat/vav_pwr; emptiness is all-or-nothing per (slice, member) (92% of groups), identical across channels, and depends on time of day (informative share by occupancy fraction 0.00 / 0.24 / 0.78 / 0.50; non-monotone). The OAT-only model's informativeness regression sees only outdoor temperature (held-out-season log-loss 0.696 vs 0.695 for a constant), so the original active read informative streams 44% of the time vs 49% for random (loso). An all-context logistic with squares cuts that log-loss to 0.48. |
| (b) mis-specified likelihood / overconfidence | **REAL, and it is the main cause in hist_loso, but not fixable from training data here** | Under the model fitted without a season, the TRUE owner pairs of fall look non-owner-like (mean LLR M:X per reading +0.64 / -0.30 / -0.74 on channels 0-2 for vav_pwr; 5 of 9 rooms negative); other seasons are strongly positive (winter +2.9 / +3.7). Fall is 8 of the 14 days; the model trained without it sees 6 days. Removing a common season shift (estimated from all readings, even from the X class oracle-style) changes hist_loso accuracy by <= +0.03 (probe `an15.py`): the failure is M-class specific, not a level shift. Inflating pair effects (x2, x3, tau >= 0.5 / 0.8, tau_M >= 0.6 / 1.2) did not help either (hist_loso n=24: 0.53-0.67 vs 0.67 with the informativeness fix alone). |
| (c) greedy EIG over-samples one pair; correlation handled wrongly | **REAL (two mechanisms)** | (i) In hist_loso the original active spends 96% of its readings on the documented pair and reads 1.7 distinct owners (random: 10% and 9.3). (ii) The model gave every channel of a pair its own independent random effect, but the three channels are computed from the same two streams: cross-channel correlation of pair-level offsets is 0.5-0.9 (vav_pwr X pairs 0.89 / 0.58 / 0.60; estimated rho 0.78 for vav_sat / vav_pwr, 0.29 for vav_zone), so reading a second channel of the same pair was counted as a fresh independent look. Note this only bites where EIG concentrates on one pair. |
| (d) OAT extrapolation outside training range | **NOT the cause** | only 8% of offered slices lie outside the training OAT range; clamping the context to the training range changes nothing (Section 5, `clip`). The context-vs-pooled gap in hist_loso is the same M-class transfer failure, not extrapolation. |
| (e) baselines misleading | **PARTLY** | traversal and rule_based read an empty night block first (occupancy 0 => 0 informative readings), so they sit at exactly 0.50 for 8-12 readings: their real-data numbers are handicapped, as `active_findings.md` said. But a fair informed baseline does NOT beat plain random: random over readings predicted informative (`random_info`) is 0.68 / 0.67 / 0.71 at n=24 (lodo / loso / hist_loso) vs random 0.74 / 0.72 / 0.73, and an oracle random over readings that ARE informative is no better (0.69-0.72). Reading only informative streams does not raise accuracy at 24 readings; what raises it is choosing WHICH pair to read. |
| Evidence ceiling (D5, hist_loso) | **the reason nothing wins at n=24** | with all informative readings the model reaches 0.87 (fall 0.81); with 24 random informative readings 0.66; 24 doc-pair-only 0.71; 24 non-doc-only 0.60; 24 round-robin over owners 0.75 (one draw per episode, +-0.03). The doc pair alone is decisive for wrong documentation (0.81-0.88) but calls right documentation wrong in fall (0.51-0.59); alternatives alone are the mirror image. A mixed, owner-diverse set of readings is best, but even it is at 0.75 and its advantage over active/random is within the noise of this experiment. |

Root cause, one sentence: on this building 24 readings carry limited evidence (ceiling about 0.75-0.8 forced accuracy, 1/3 of episodes are vav_zone where the classes barely differ), so
active's real advantage is speed at small n; and in hist_loso the class-M likelihood learned from three 2-day seasons does not recognise the true owners in the fall, which makes
any policy that trusts it (active concentrates on the documented pair) confidently wrong on fall.

## 3. What I changed (all new options, default OFF; the `sel` variant turns on the first two)

1. **Informativeness model + online slice learning** (`model.py`, `engine.py`; `info`): p_info from a ridge-logistic on all context columns plus squares of outdoor temp and load
   (instead of a linear regression on the mean-shift features), and a beta-binomial online update: readings taken earlier in the same slice (empty or not, whatever the pair/channel)
   shift the predicted informativeness of the rest of the slice with prior strength kappa = (1-ICC)/ICC estimated from the training pools (real: kappa 0.2-0.5, i.e.
   one empty reading nearly kills the slice; sim: 0.2 to 50 depending on the channel).
2. **Shared pair effect across channels** (`sp`): a pair's random effect has a factor common to its channels with correlation rho estimated from training cells (clip 0..0.9); the
   shared factor is integrated out exactly in the belief (`ll_pair`), and used in the EIG predictive. rho = 0 reduces exactly to the old model (tested).
3. New baselines/hooks: `random_info` (random among readings predicted informative), `random_oracle` (analysis only), `custom` (fixed order), `calibrate_beta*(policy=, fitkw=, runkw=)`.
4. Probed and **not adopted** (no gain on the real test days, code kept off): inflating pair effects (`tau_scale`, `tau_min`, `tauM_min`); per-owner reading cap (`pair_cap` 1-6; hist_loso n=24 0.64-0.68,
   resolved fraction collapses at small caps); EIG on slice-averaged class separation (`sel_pooled`, to avoid chasing extreme-OAT slices; no change, still 89% of reads on the doc pair);
   calibrating beta under the deployed active policy instead of random order (loso accuracy among resolved fell to 0.63, noisy with 2-day nested seasons); clamping context (`clip`);
   removing a common season shift; per-season/oracle recalibration of X. Nothing tuned on the test episodes made it into `sel`.

## 4. BEFORE / AFTER (`oat` = original, `sel` = new; same episodes; CIs are cluster bootstrap)

Headline tables (active BEFORE = original; AFTER = `sel`; the other AFTER arms use the same new belief model). Full tables with every arm: `selection_results.md`.

### real / `lodo`
| arm | resolved | readings (cap 24) | readings among resolved | acc among resolved (nominal 0.95) | acc n=1 | acc n=2 | acc n=4 | acc n=8 | acc n=12 | acc n=24 |
|---|---|---|---|---|---|---|---|---|---|---|
| active BEFORE | 0.27 [0.16, 0.42] | 19.7 [17.7, 21.4] | 8.1 [7.1, 9.3] (104/493) | 0.89 [0.81, 0.96] | 0.70 [0.58, 0.79] | 0.72 [0.60, 0.82] | 0.75 [0.68, 0.80] | 0.73 [0.66, 0.79] | 0.72 [0.66, 0.80] | 0.77 [0.70, 0.82] |
| **active AFTER** | 0.19 [0.09, 0.29] | 21.0 [19.2, 22.4] | 7.9 [6.4, 8.8] (82/493) | 0.92 [0.80, 0.99] | 0.68 [0.62, 0.73] | 0.72 [0.67, 0.78] | 0.76 [0.70, 0.81] | 0.73 [0.66, 0.78] | 0.73 [0.67, 0.79] | 0.78 [0.72, 0.83] |
| random AFTER | 0.04 [0.01, 0.08] | 23.7 [23.5, 23.9] | 17.3 [11.1, 18.3] (23/493) | 0.95 [0.78, 1.00] | 0.52 [0.48, 0.59] | 0.55 [0.50, 0.61] | 0.61 [0.54, 0.68] | 0.61 [0.55, 0.67] | 0.69 [0.61, 0.78] | 0.74 [0.68, 0.79] |
| random_info AFTER (random over readings predicted informative) | 0.03 [0.01, 0.04] | 23.8 [23.6, 23.9] | 16.4 [13.1, 17.9] (19/493) | 0.92 [0.70, 1.00] | 0.53 [0.47, 0.60] | 0.56 [0.50, 0.61] | 0.58 [0.52, 0.64] | 0.62 [0.55, 0.69] | 0.64 [0.57, 0.72] | 0.68 [0.62, 0.74] |
| frozen AFTER | 0.18 [0.09, 0.28] | 21.1 [19.4, 22.3] | 7.6 [5.7, 8.6] (81/493) | 0.90 [0.76, 0.98] | 0.68 [0.62, 0.74] | 0.73 [0.68, 0.79] | 0.76 [0.70, 0.82] | 0.75 [0.67, 0.82] | 0.72 [0.65, 0.78] | 0.76 [0.69, 0.83] |
| traversal AFTER | 0.00 [0.00, 0.00] | 24.0 [24.0, 24.0] | n/a (0/493) | n/a | 0.50 [0.50, 0.50] | 0.52 [0.48, 0.58] | 0.52 [0.48, 0.58] | 0.50 [0.46, 0.55] | 0.49 [0.45, 0.56] | 0.50 [0.45, 0.56] |
| rule_based AFTER | 0.03 [0.00, 0.06] | 23.9 [23.7, 24.0] | 20.0 [16.0, 21.0] (19/493) | 0.50 [0.50, 1.00] | 0.50 [0.50, 0.50] | 0.50 [0.50, 0.50] | 0.50 [0.50, 0.50] | 0.50 [0.50, 0.50] | 0.71 [0.64, 0.79] | 0.79 [0.73, 0.84] |

### real / `loso`
| arm | resolved | readings (cap 24) | readings among resolved | acc among resolved (nominal 0.95) | acc n=1 | acc n=2 | acc n=4 | acc n=8 | acc n=12 | acc n=24 |
|---|---|---|---|---|---|---|---|---|---|---|
| active BEFORE | 0.43 [0.32, 0.54] | 16.3 [14.2, 18.1] | 6.0 [5.1, 7.0] (156/493) | 0.79 [0.69, 0.88] | 0.58 [0.48, 0.70] | 0.65 [0.55, 0.74] | 0.71 [0.65, 0.76] | 0.68 [0.63, 0.74] | 0.71 [0.64, 0.76] | 0.73 [0.68, 0.78] |
| **active AFTER** | 0.39 [0.28, 0.47] | 17.0 [15.1, 18.8] | 5.9 [4.7, 7.0] (128/493) | 0.85 [0.75, 0.94] | 0.66 [0.61, 0.72] | 0.67 [0.62, 0.73] | 0.70 [0.65, 0.76] | 0.70 [0.65, 0.75] | 0.72 [0.68, 0.77] | 0.75 [0.69, 0.79] |
| random AFTER | 0.10 [0.04, 0.16] | 22.7 [21.9, 23.5] | 10.4 [8.7, 12.9] (38/493) | 0.77 [0.66, 0.92] | 0.52 [0.48, 0.58] | 0.55 [0.49, 0.60] | 0.60 [0.53, 0.67] | 0.59 [0.53, 0.66] | 0.70 [0.64, 0.76] | 0.72 [0.66, 0.77] |
| random_info AFTER (random over readings predicted informative) | 0.06 [0.02, 0.12] | 23.4 [22.7, 23.9] | 13.9 [11.3, 18.1] (26/493) | 0.69 [0.20, 0.94] | 0.54 [0.47, 0.59] | 0.58 [0.52, 0.65] | 0.61 [0.55, 0.66] | 0.58 [0.52, 0.63] | 0.60 [0.56, 0.65] | 0.67 [0.62, 0.73] |
| frozen AFTER | 0.37 [0.27, 0.46] | 17.4 [15.6, 19.2] | 5.9 [5.1, 7.3] (125/493) | 0.84 [0.75, 0.92] | 0.66 [0.61, 0.72] | 0.68 [0.61, 0.74] | 0.71 [0.66, 0.76] | 0.71 [0.66, 0.75] | 0.71 [0.65, 0.76] | 0.74 [0.69, 0.79] |
| traversal AFTER | 0.00 [0.00, 0.00] | 24.0 [24.0, 24.0] | n/a (0/493) | n/a | 0.50 [0.50, 0.50] | 0.51 [0.48, 0.58] | 0.51 [0.48, 0.58] | 0.50 [0.46, 0.57] | 0.49 [0.45, 0.56] | 0.49 [0.45, 0.55] |
| rule_based AFTER | 0.10 [0.04, 0.17] | 23.6 [23.3, 23.9] | 20.5 [19.3, 22.0] (52/493) | 0.93 [0.50, 1.00] | 0.50 [0.50, 0.50] | 0.50 [0.50, 0.50] | 0.50 [0.50, 0.50] | 0.50 [0.50, 0.50] | 0.72 [0.64, 0.81] | 0.79 [0.73, 0.85] |

### real / `hist_loso`
| arm | resolved | readings (cap 24) | readings among resolved | acc among resolved (nominal 0.95) | acc n=1 | acc n=2 | acc n=4 | acc n=8 | acc n=12 | acc n=24 |
|---|---|---|---|---|---|---|---|---|---|---|
| active BEFORE | 0.65 [0.52, 0.75] | 13.0 [10.7, 15.5] | 7.3 [6.1, 8.8] (287/493) | 0.57 [0.50, 0.64] | 0.58 [0.49, 0.66] | 0.64 [0.57, 0.71] | 0.61 [0.56, 0.66] | 0.62 [0.57, 0.67] | 0.62 [0.56, 0.70] | 0.65 [0.59, 0.71] |
| **active AFTER** | 0.66 [0.55, 0.77] | 11.3 [9.2, 13.9] | 5.0 [4.2, 6.0] (296/493) | 0.61 [0.55, 0.67] | 0.61 [0.56, 0.68] | 0.62 [0.57, 0.68] | 0.65 [0.58, 0.71] | 0.64 [0.58, 0.70] | 0.62 [0.56, 0.67] | 0.67 [0.62, 0.73] |
| random AFTER | 0.10 [0.02, 0.20] | 22.7 [21.1, 23.8] | 11.0 [9.1, 13.3] (40/493) | 0.70 [0.61, 0.76] | 0.50 [0.45, 0.55] | 0.54 [0.49, 0.58] | 0.61 [0.55, 0.66] | 0.64 [0.58, 0.71] | 0.66 [0.58, 0.73] | 0.73 [0.66, 0.80] |
| random_info AFTER (random over readings predicted informative) | 0.13 [0.03, 0.23] | 22.2 [20.4, 23.8] | 10.1 [8.4, 16.5] (42/493) | 0.70 [0.63, 0.78] | 0.56 [0.50, 0.61] | 0.60 [0.52, 0.67] | 0.59 [0.49, 0.70] | 0.60 [0.52, 0.70] | 0.62 [0.53, 0.69] | 0.71 [0.63, 0.79] |
| frozen AFTER | 0.65 [0.52, 0.75] | 12.2 [9.9, 14.7] | 5.9 [5.4, 6.8] (295/493) | 0.58 [0.52, 0.64] | 0.61 [0.57, 0.68] | 0.58 [0.52, 0.65] | 0.65 [0.59, 0.72] | 0.63 [0.57, 0.69] | 0.60 [0.54, 0.67] | 0.66 [0.60, 0.72] |
| traversal AFTER | 0.00 [0.00, 0.00] | 24.0 [24.0, 24.0] | n/a (0/493) | n/a | 0.50 [0.50, 0.50] | 0.51 [0.48, 0.56] | 0.51 [0.49, 0.56] | 0.49 [0.45, 0.56] | 0.47 [0.42, 0.53] | 0.48 [0.43, 0.55] |
| rule_based AFTER | 0.07 [0.01, 0.13] | 23.7 [23.4, 24.0] | 20.0 [18.8, 21.9] (35/493) | 1.00 [1.00, 1.00] | 0.50 [0.50, 0.50] | 0.50 [0.50, 0.50] | 0.50 [0.50, 0.50] | 0.50 [0.50, 0.50] | 0.58 [0.50, 0.66] | 0.62 [0.50, 0.74] |

### sim / `hist`
| arm | resolved | readings (cap 24) | readings among resolved | acc among resolved (nominal 0.95) | acc n=1 | acc n=2 | acc n=4 | acc n=8 | acc n=12 | acc n=24 |
|---|---|---|---|---|---|---|---|---|---|---|
| active BEFORE | 0.75 [0.67, 0.82] | 9.4 [7.5, 11.2] | 4.7 [3.6, 5.9] (559/748) | 0.93 [0.87, 0.97] | 0.78 [0.69, 0.85] | 0.80 [0.72, 0.87] | 0.81 [0.74, 0.88] | 0.83 [0.73, 0.88] | 0.79 [0.71, 0.85] | 0.79 [0.71, 0.86] |
| **active AFTER** | 0.71 [0.61, 0.81] | 10.1 [7.9, 12.0] | 4.6 [3.4, 5.6] (518/748) | 0.88 [0.81, 0.95] | 0.81 [0.73, 0.87] | 0.82 [0.74, 0.88] | 0.80 [0.72, 0.88] | 0.81 [0.72, 0.88] | 0.81 [0.74, 0.87] | 0.78 [0.69, 0.85] |
| random AFTER | 0.36 [0.29, 0.44] | 19.7 [18.7, 20.6] | 12.3 [10.6, 13.6] (266/748) | 0.93 [0.86, 0.97] | 0.60 [0.56, 0.64] | 0.60 [0.56, 0.64] | 0.63 [0.59, 0.67] | 0.66 [0.62, 0.71] | 0.67 [0.62, 0.71] | 0.73 [0.67, 0.78] |
| random_info AFTER (random over readings predicted informative) | 0.41 [0.33, 0.49] | 18.9 [17.7, 20.0] | 11.8 [10.4, 13.0] (303/748) | 0.96 [0.93, 0.98] | 0.59 [0.55, 0.63] | 0.62 [0.57, 0.66] | 0.64 [0.60, 0.68] | 0.69 [0.63, 0.73] | 0.72 [0.67, 0.77] | 0.80 [0.74, 0.85] |
| frozen AFTER | 0.71 [0.62, 0.79] | 9.9 [8.0, 12.0] | 4.1 [3.2, 5.1] (522/748) | 0.94 [0.88, 0.98] | 0.81 [0.73, 0.87] | 0.84 [0.76, 0.89] | 0.83 [0.75, 0.90] | 0.79 [0.71, 0.86] | 0.79 [0.70, 0.86] | 0.77 [0.68, 0.84] |
| traversal AFTER | 0.50 [0.39, 0.62] | 15.5 [13.5, 17.9] | 7.6 [5.3, 9.4] (374/748) | 0.98 [0.94, 1.00] | 0.81 [0.74, 0.87] | 0.77 [0.68, 0.84] | 0.78 [0.70, 0.85] | 0.78 [0.70, 0.84] | 0.80 [0.73, 0.87] | 0.79 [0.70, 0.85] |
| rule_based AFTER | 0.51 [0.38, 0.62] | 15.0 [12.7, 17.4] | 6.3 [5.3, 8.0] (378/748) | 1.00 [0.99, 1.00] | 0.80 [0.74, 0.86] | 0.80 [0.72, 0.87] | 0.82 [0.75, 0.88] | 0.80 [0.72, 0.87] | 0.80 [0.72, 0.86] | 0.82 [0.75, 0.89] |

### sim / `visit`
| arm | resolved | readings (cap 24) | readings among resolved | acc among resolved (nominal 0.95) | acc n=1 | acc n=2 | acc n=4 | acc n=8 | acc n=12 | acc n=24 |
|---|---|---|---|---|---|---|---|---|---|---|
| active BEFORE | 0.70 [0.60, 0.78] | 10.5 [8.5, 12.4] | 4.8 [3.9, 5.7] (521/748) | 0.96 [0.93, 0.98] | 0.78 [0.70, 0.84] | 0.78 [0.69, 0.84] | 0.80 [0.73, 0.86] | 0.81 [0.74, 0.86] | 0.81 [0.73, 0.87] | 0.81 [0.73, 0.87] |
| **active AFTER** | 0.69 [0.61, 0.77] | 11.0 [9.1, 13.0] | 5.3 [4.2, 6.5] (517/748) | 0.96 [0.94, 0.98] | 0.80 [0.73, 0.86] | 0.80 [0.73, 0.86] | 0.83 [0.76, 0.88] | 0.81 [0.74, 0.87] | 0.82 [0.75, 0.87] | 0.84 [0.77, 0.89] |
| random AFTER | 0.36 [0.29, 0.43] | 19.7 [18.7, 20.6] | 12.1 [10.9, 13.1] (269/748) | 0.96 [0.91, 0.99] | 0.57 [0.53, 0.61] | 0.61 [0.57, 0.65] | 0.63 [0.58, 0.66] | 0.67 [0.62, 0.71] | 0.70 [0.65, 0.74] | 0.75 [0.69, 0.81] |
| random_info AFTER (random over readings predicted informative) | 0.40 [0.31, 0.48] | 19.0 [17.9, 20.1] | 11.6 [10.2, 12.7] (300/748) | 0.96 [0.93, 0.99] | 0.59 [0.55, 0.63] | 0.63 [0.59, 0.66] | 0.67 [0.63, 0.71] | 0.70 [0.65, 0.74] | 0.74 [0.68, 0.79] | 0.79 [0.73, 0.84] |
| frozen AFTER | 0.68 [0.58, 0.77] | 10.9 [9.2, 13.0] | 5.0 [3.9, 6.0] (509/748) | 0.95 [0.92, 0.98] | 0.80 [0.73, 0.86] | 0.82 [0.75, 0.88] | 0.83 [0.76, 0.89] | 0.82 [0.75, 0.88] | 0.82 [0.75, 0.88] | 0.81 [0.76, 0.87] |
| traversal AFTER | 0.45 [0.33, 0.55] | 16.2 [13.8, 18.4] | 6.7 [4.1, 8.8] (330/748) | 0.96 [0.91, 0.99] | 0.76 [0.67, 0.82] | 0.71 [0.62, 0.79] | 0.76 [0.68, 0.83] | 0.76 [0.68, 0.83] | 0.78 [0.71, 0.84] | 0.79 [0.71, 0.84] |
| rule_based AFTER | 0.51 [0.39, 0.63] | 15.2 [12.9, 17.5] | 6.5 [5.7, 7.7] (379/748) | 0.99 [0.96, 1.00] | 0.75 [0.67, 0.82] | 0.76 [0.69, 0.83] | 0.77 [0.69, 0.84] | 0.75 [0.67, 0.82] | 0.78 [0.69, 0.85] | 0.79 [0.71, 0.85] |

### sim / `visit_loso`
| arm | resolved | readings (cap 24) | readings among resolved | acc among resolved (nominal 0.95) | acc n=1 | acc n=2 | acc n=4 | acc n=8 | acc n=12 | acc n=24 |
|---|---|---|---|---|---|---|---|---|---|---|
| active BEFORE | 0.70 [0.62, 0.80] | 9.8 [7.7, 12.0] | 3.8 [3.1, 4.5] (521/748) | 0.94 [0.91, 0.97] | 0.78 [0.72, 0.85] | 0.77 [0.69, 0.84] | 0.80 [0.73, 0.86] | 0.80 [0.73, 0.85] | 0.79 [0.72, 0.86] | 0.81 [0.74, 0.87] |
| **active AFTER** | 0.69 [0.60, 0.77] | 10.0 [8.0, 12.0] | 3.7 [3.0, 4.5] (513/748) | 0.95 [0.91, 0.97] | 0.78 [0.71, 0.84] | 0.79 [0.72, 0.85] | 0.81 [0.74, 0.87] | 0.81 [0.74, 0.86] | 0.81 [0.75, 0.87] | 0.82 [0.75, 0.88] |
| random AFTER | 0.39 [0.30, 0.46] | 19.3 [18.3, 20.2] | 11.8 [10.9, 12.7] (288/748) | 0.96 [0.91, 0.99] | 0.58 [0.54, 0.62] | 0.61 [0.57, 0.65] | 0.62 [0.57, 0.67] | 0.67 [0.62, 0.72] | 0.70 [0.65, 0.75] | 0.77 [0.71, 0.82] |
| random_info AFTER (random over readings predicted informative) | 0.40 [0.31, 0.48] | 18.7 [17.5, 19.9] | 10.7 [9.8, 11.5] (299/748) | 0.97 [0.94, 0.99] | 0.59 [0.55, 0.63] | 0.62 [0.58, 0.66] | 0.66 [0.62, 0.71] | 0.71 [0.66, 0.76] | 0.75 [0.69, 0.80] | 0.81 [0.75, 0.86] |
| frozen AFTER | 0.69 [0.60, 0.77] | 10.2 [8.2, 12.3] | 4.0 [3.3, 5.0] (512/748) | 0.94 [0.90, 0.97] | 0.78 [0.71, 0.84] | 0.80 [0.73, 0.86] | 0.82 [0.75, 0.88] | 0.81 [0.75, 0.87] | 0.81 [0.75, 0.87] | 0.80 [0.74, 0.87] |
| traversal AFTER | 0.46 [0.34, 0.58] | 15.2 [12.6, 17.8] | 5.1 [4.0, 6.7] (341/748) | 0.96 [0.92, 0.99] | 0.76 [0.68, 0.83] | 0.72 [0.63, 0.78] | 0.76 [0.69, 0.84] | 0.76 [0.69, 0.82] | 0.78 [0.71, 0.85] | 0.79 [0.72, 0.85] |
| rule_based AFTER | 0.50 [0.39, 0.62] | 14.8 [12.4, 17.6] | 5.7 [4.7, 7.2] (375/748) | 0.99 [0.98, 1.00] | 0.76 [0.68, 0.82] | 0.76 [0.68, 0.83] | 0.77 [0.69, 0.84] | 0.74 [0.67, 0.82] | 0.77 [0.68, 0.84] | 0.79 [0.71, 0.85] |

Paired differences (A minus B, same episodes) that matter, AFTER model (full set in `selection_results.md`):

| | setting | acc n=1 | n=4 | n=8 | n=24 | readings (cap 24) | resolved |
|---|---|---|---|---|---|---|---|
| active AFTER - active BEFORE | real lodo | -0.02 [-0.11, 0.10] | +0.02 [-0.02, 0.05] | -0.00 [-0.05, 0.04] | +0.02 [-0.00, 0.04] | +1.3 [0.5, 2.2] | -0.08 [-0.14, -0.02] |
| | real loso | +0.08 [-0.02, 0.18] | -0.00 [-0.04, 0.04] | +0.02 [-0.02, 0.05] | +0.02 [-0.02, 0.05] | +0.7 [-0.0, 1.5] | -0.04 [-0.08, -0.01] |
| | real hist_loso | +0.03 [-0.07, 0.14] | +0.04 [0.00, 0.08] | +0.02 [0.00, 0.05] | +0.03 [-0.01, 0.06] | -1.7 [-2.4, -1.0] | +0.01 [0.00, 0.02] |
| | sim hist | +0.03 [-0.04, 0.11] | -0.01 [-0.04, 0.03] | -0.02 [-0.07, 0.02] | -0.02 [-0.05, 0.01] | +0.8 [-0.6, 2.7] | -0.05 [-0.14, 0.02] |
| | sim visit | +0.02 [-0.01, 0.05] | +0.03 [0.01, 0.05] | -0.01 [-0.03, 0.02] | +0.03 [0.00, 0.08] | +0.5 [0.1, 0.8] | -0.01 [-0.02, 0.01] |
| | sim visit_loso | -0.00 [-0.03, 0.02] | +0.01 [-0.00, 0.04] | +0.01 [-0.02, 0.05] | +0.01 [-0.02, 0.05] | +0.2 [-0.1, 0.5] | -0.01 [-0.03, 0.00] |
| active AFTER - random AFTER | real lodo | +0.16 [0.09, 0.23] | +0.16 [0.08, 0.22] | +0.11 [0.03, 0.19] | +0.04 [-0.04, 0.11] | -2.7 [-4.3, -1.3] | +0.15 [0.07, 0.24] |
| | real loso | +0.14 [0.07, 0.20] | +0.11 [0.02, 0.19] | +0.11 [0.02, 0.18] | +0.03 [-0.04, 0.09] | -5.7 [-7.2, -4.0] | +0.29 [0.21, 0.36] |
| | real hist_loso | +0.11 [0.05, 0.17] | +0.04 [-0.03, 0.12] | -0.01 [-0.09, 0.09] | -0.06 [-0.15, 0.03] | -11.4 [-14.0, -8.6] | +0.57 [0.41, 0.69] |
| | sim hist / visit / visit_loso | +0.22 / +0.23 / +0.20 | +0.18 / +0.20 / +0.19 | +0.14 / +0.14 / +0.14 | +0.05 / +0.09 / +0.05 (CIs exclude 0 in visit, visit_loso) | -9.6 / -8.7 / -9.3 | +0.35 / +0.33 / +0.30 |
| active AFTER - random_info AFTER (fair informed baseline) | real lodo / loso / hist_loso, n=24 | +0.10 [0.02, 0.18] / +0.07 [0.02, 0.13] / -0.04 [-0.14, 0.06] | | | | | |
| active AFTER - traversal AFTER | sim hist n=24 | -0.01 [-0.07, 0.05] | | | | -5.4 [-7.2, -3.8] | +0.20 [0.06, 0.33] |

## 5. Ablation (active policy, real and sim; `selection_results.md` bottom; `oat` = BEFORE)

Real, forced accuracy at n=24 / accuracy among resolved / resolved fraction: lodo oat 0.77 / 0.89 / 0.27, info 0.78 / 0.90 / 0.27, sp 0.79 / 0.94 / 0.20, clip 0.77 / 0.89 / 0.27, sel 0.78 / 0.92 / 0.19;
loso oat 0.73 / 0.79 / 0.43, info 0.77 / 0.81 / 0.47, sp 0.76 / 0.80 / 0.37, clip 0.73 / 0.80 / 0.37, sel 0.75 / 0.85 / 0.39; hist_loso oat 0.65 / 0.57 / 0.65, info 0.67 / 0.59 / 0.68, sp 0.63 / 0.58 / 0.63,
clip 0.65 / 0.58 / 0.62, sel 0.67 / 0.61 / 0.66. Reading it: `info` is what moves n=1 in loso (0.58 -> 0.66) and n=24 (+0.04); `sp` is what makes confident answers more trustworthy
(accuracy among resolved 0.89 -> 0.94 in lodo, 0.79 -> 0.85 with both in loso) at the price of resolving fewer episodes; `clip` is null. Every one of these differences is inside its CI on its own.
Sim ablation (hist): oat 0.75 resolved / 0.93 acc among resolved; info 0.70 / 0.90; sp 0.75 / 0.93; sel 0.71 / 0.88.

## 6. Answering the request

**Did active earn its keep on real data?** Yes at small n, not at n=24. In lodo/loso (the two settings where the model is trained on the neighbouring days or the other seasons and is the
practical case) active AFTER beats random by +0.11 to +0.16 forced accuracy after 1-8 readings (CIs exclude 0), resolves 15-29 points more episodes and stops 3-6 readings earlier; by n=24 the gap is +0.03/+0.04 (CIs include 0).
It also beats the *fair* informed baseline `random_info` by +0.10 [0.02, 0.18] / +0.07 [0.02, 0.13] at n=24 in lodo/loso. It does **not** beat the static owner sweep (`rule_based`, 0.79 at n=24) at n=24, although it is 0.16-0.26 ahead
of it at n<=8 and the sweep is handicapped by its empty first block. In hist_loso active is still confidently wrong on fall (accuracy among resolved 0.61 [0.55, 0.68]; nominal 0.95); **I did not fix that and do not think selection can**
(D3/D5: the model does not recognise the true owners in fall; the best diversified oracle-informative probe reaches ~0.75). The right lever there is more training data from that regime, or abstention
(the parallel abstention workstream): with this likelihood, hist_loso "resolved" verdicts should not be trusted.

**What the changes bought.** Real: n=1 accuracy in loso 0.58 -> 0.66 (paired +0.08 [-0.02, 0.18], not significant), n=24 +0.02 in lodo/loso/+0.03 hist_loso (all CIs include 0); accuracy among resolved rose 0.79 -> 0.85 (loso),
0.89 -> 0.92 (lodo), 0.57 -> 0.61 (hist_loso) but the resolved fraction fell in lodo (0.27 -> 0.19, paired -0.08 [-0.14, -0.02]) and loso (-0.04 [-0.08, -0.01]); active still needs slightly more readings to resolve in lodo (+1.3 [0.5, 2.2]) and
fewer in hist_loso (-1.7 [-2.4, -1.0], reading count among resolved 7.3 -> 5.0, but those extra confident verdicts are still only 61% right). Empty readings among active's picks fell from 56% to 41% (loso) and from 49% to 25% (hist_loso) (probe `p1.py`, exploratory).
These are modest, mostly within noise.

## 7. Trade-offs and regressions (stated plainly)

* **Sim did not improve and mildly regressed on speed:** readings to resolve (cap 24) +0.8 [-0.6, 2.7] (hist), +0.5 [0.1, 0.8] (visit, statistically significant), +0.2 [-0.1, 0.5] (visit_loso); resolved fraction -0.05 [-0.14, 0.02] / -0.01 / -0.01.
  Accuracy among resolved in sim hist fell 0.93 [0.87, 0.97] -> 0.88 [0.81, 0.95] (unpaired CIs overlap; the `info`-only ablation gives 0.90, `sp`-only 0.93, so the drop is not clearly attributable to either);
  visit 0.96 -> 0.96, visit_loso 0.94 -> 0.95. Forced accuracy is unchanged within CI, with +0.03 [0.00, 0.08] at n=24 in visit.
* Real lodo/loso: fewer episodes resolved (calibration purchased with coverage), as above. Baselines (random, frozen, traversal, rule_based) are unchanged by the model change (`random AFTER - random BEFORE` <= 0.01).
* The pooled-context arm improves more than the context arm in sim hist at n=1 (+0.07 [0.02, 0.12]) and loses 5 readings in real hist_loso; not pursued.

## 8. Flagged judgment calls (after seeing results)

1. **All probing happened on the same real test episodes.** There is one building and one 14-day set; I ran ~15 exploratory variants (`scripts/exploration_selection/`) on those episodes and looked at the numbers. Adopted components (`info`, `sp`) were chosen because the diagnostics
   (D1, D4, which use only the evidence pool, not documentation labels) pointed at them, not because they scored best; but the decision to adopt them and to reject the others (tau inflation, per-owner cap, slice-averaged EIG, active-order beta calibration, context clamp, season-shift removal) was made after seeing test results. Treat the real AFTER numbers as exploratory, not held-out.
2. Hyperparameters that are estimated from training data only (so nested/held-out by construction): kappa from the training ICC, rho from training cells, the logistic informativeness coefficients. Hard-coded by me: feature set of the informativeness model (all context columns + squares of oat and load; chosen after seeing
   the non-monotone occupancy pattern in the full-pool emptiness rates), clipping of p_info to [0.03, 0.97] (0.02-0.98 after the online update), kappa clip [0.2, 50], rho clip [0, 0.9], minimum 12 cells and 2 readings per cell for rho, ridge lam 1 in the logistic. Not tuned by outcome.
3. `sel` = `info` + `sp` is the headline because both were motivated a priori by D1/D4; the individual ablations are reported. `clip` is off in `sel` because it did nothing, not because it hurt.
4. Beta calibration is unchanged (nested random-order, coarse grid) and is refitted with the new model; I did not change it because the active-order alternative was worse on real.
5. I inherited the earlier OAT-only-context choice (already flagged in `active_findings.md`); all comparisons here use it.
6. Real-data episodes with wrong documentation are only 73 (heavily clustered by day/slot), so paired CIs are wide; many "no difference" conclusions mean "cannot detect one".
7. The D5 ceiling numbers use one random draw per episode; +-0.03 noise.

## 9. What would actually help on this building

* Training data from the fall regime when scoring fall (`lodo` is fine: 0.78 forced accuracy, 0.92 among resolved) or a larger, multi-building real set; in hist_loso the limiting factor is the likelihood, not the reading order.
* Abstention keyed to regime coverage (e.g. refuse to resolve when the held-out slice's context/regime was never seen in training) instead of a nominal-tau stop; the parallel abstention agent owns this.
* If a per-pair sweep is acceptable operationally, "one informative reading per candidate owner, doc pair first" (round-robin) is a robust, model-free comparator: it is within noise of active at n=24 in hist_loso (0.75 vs 0.67, one draw) and cannot be misled by the model into over-sampling one pair.
