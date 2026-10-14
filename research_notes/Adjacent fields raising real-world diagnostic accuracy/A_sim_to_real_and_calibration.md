# Area A: Simulator-to-real and model calibration with little real data

Scope: how people close the gap between a simulator or physics model and reality when real data are scarce. Sources: Bayesian calibration with discrepancy (buildings and general), domain randomization and adaptation (robotics, driving), online calibration of digital twins, simulation-based inference and simulator-as-prior methods, dynamic-borrowing priors, and sim-to-real numbers in fault diagnosis.

Conventions. Read status: `FULL_TEXT` = the passage with the number or claim was in what I retrieved; `ABSTRACT_ONLY`; `SNIPPET` = search-result summary only. `[INFERENCE]` marks my own reading for our hot-water engine. Where a fetch returned only part of a long page, I say so. Numbers are given with their context; I did not report numbers I did not see.

Honest headline before the items: I found **no source that gives a general rule for how many field measurements Kennedy-O'Hagan-type calibration needs** (the building papers I could open use anywhere from 12 monthly values to thousands of minute-level points, and the answer depends on identifiability, not count). I also found **no building-FDD paper that reports the same classifier's accuracy on simulation, on real data before adaptation, and after adaptation**. The cleanest such triple I found is from a robot fault-diagnosis paper (item 13).

---

## 1. Calibration with an explicit model-discrepancy term (Kennedy-O'Hagan), and why the discrepancy needs informative priors

**Technique:** Fit simulator parameters to field data while adding a Gaussian-process "discrepancy" term for the simulator's structural error, instead of forcing the parameters to absorb it.

**Field and source:**
- Brynjarsdottir and O'Hagan (2014), "Learning about physical parameters: the importance of model discrepancy", *Inverse Problems* 30(11):114007. https://tonyohagan.co.uk/academic/abs/simmach.html
- Menberg, Heo, Choudhary (2019), "Influence of error terms in Bayesian calibration of energy system models", *J. Building Performance Simulation* 12(1):82-96 (heat-pump model, building-energy community). https://www.repository.cam.ac.uk/handle/1810/279398

**What it does:** The standard framework writes field data as simulator output (at the calibrated parameters) plus a discrepancy function plus noise. The two papers examine what happens to the *parameter* estimates (not just the predictions) once the discrepancy term is included.

**Evidence of effect:** No quantitative evidence in what I could open (abstracts only). Qualitative findings: ignoring discrepancy gives biased and overconfident parameter estimates; adding a GP discrepancy makes predictions inside the data range correct, but the true parameters are recovered only when the discrepancy has a realistic prior. In the heat-pump test, many posteriors matched expectations but some parameters, especially discrepancy hyperparameters, were not inferable from data, and posteriors depended on the priors chosen.

**What it needs:** A simulator that can be run across the parameter range (usually through a GP emulator), field data at the output of interest, an explicit prior on discrepancy (magnitude, smoothness), and an identifiability check by varying the priors.

**Failure modes / caveats:** Calibration parameters and discrepancy trade off against each other, so more data does not by itself fix it. The discrepancy prior is where expert knowledge has to enter.

**Read status:** ABSTRACT_ONLY for both (author page and Cambridge repository record).

**Relevance to us [INFERENCE]:** Our "tenant answers are wrong with some probability" soft-evidence parameter is a discrepancy term. These papers say its prior should come from elicitation (interviews, work-order review) and be varied as a sensitivity check, not be learned from a few dozen visits.

---

## 2. Use the calibration discrepancy to decide which structural upgrade the model needs

**Technique:** Calibrate a simple model, inspect where observations and predictions disagree, upgrade the model structure accordingly, and compare variants by Bayes factors rather than RMSE.

**Field and source:** Monari (Univ. of Strathclyde), "An approach for identifying sources of inadequacy and upgrades in models with high-dimensional outputs and boundary conditions", arXiv:1710.06671 (v1, 2017). Real data from the IEA EBC Annex 58 test box. https://ar5iv.labs.arxiv.org/html/1710.06671

**What it does:** Starts with the simplest building thermal model, calibrates it with Bayesian calibration, uses the residual structure to pick the next upgrade, and accepts an upgrade only if the Bayes factor supports it. Aimed at avoiding a model that fits a bit better but extrapolates worse.

**Evidence of effect:** Real data: a 4-day test with 1-minute measurements (5,760 observations) and an 8-day free-float test (11,520 observations). Internal-temperature RMSE fell from 1.81 C (simplest model) to 0.67 C (retained model, sixth variant) on the first test, and from 1.46 C to 0.70 C on the second. The retained model's heat-loss coefficient was 3.72 W/K versus 3.64 W/K from an independent estimate. Several upgrades had decisive Bayes factors.

**What it needs:** Dense time series from a controlled test facility, an emulator, and the modeller's willingness to enumerate candidate upgrades.

**Failure modes / caveats:** One test facility only. Emulator hyperparameters were optimised and fixed (quasi-Bayesian). Discrepancy and calibration terms can interfere, conclusions depend on priors (vague priors can make inadequate models look competitive), and the final model still had unexplained residuals. The text and Table 4 disagree on one Bayes factor (619.94 vs 616.94).

**Read status:** FULL_TEXT (ar5iv rendering; results table and limitations retrieved).

**Relevance to us [INFERENCE]:** Suggests a way to use confirmed-cause visits: where the engine is confidently wrong, the pattern of misses shows which part of the plant model (for example, recirculation-loop behaviour) is missing, which is cheaper than refitting everything.

---

## 3. Test calibration methods against surrogate data with known truth (a good fit is not a good prediction)

**Technique:** Before trusting a calibration or diagnosis method, run it on simulator-generated "surrogate" cases where the true inputs and the true outcome are known, and score three things separately: goodness of fit, recovery of the true inputs, and accuracy of the downstream prediction.

**Field and source:**
- Judkoff, Polly, Neymark (2016), "A Method to Test Model Calibration Techniques", ACEEE Summer Study, NREL/CP-5500-67096. https://www.osti.gov/biblio/1324536 (preprint record: https://www.osti.gov/biblio/1324534)
- Garrett and New (2016), "Suitability of ASHRAE Guideline 14 Metrics for Calibration", *ASHRAE Transactions* 122:469-477. https://impact.ornl.gov/en/publications/suitability-of-ashrae-guideline-14-metrics-for-calibration/

**What it does:** Questions the assumption in ASHRAE Guideline 14 and BPI-2400 that meeting a goodness-of-fit threshold (NMBE, CV(RMSE)) means the calibration is acceptable. Both papers build a testing method that compares output-side error with input-side error (how well true parameters were recovered) and uses it to evaluate calibration systems.

**Evidence of effect:** No numbers in the abstract pages; the full results were not available to me. Garrett and New describe their correlation study as supporting the CV(RMSE) and NMBE metrics while suggesting alternatives, so the evidence is mixed rather than a clear failure of the metrics. A search summary (SNIPPET only, I could not open the source, Calama-Gonzalez et al. test-cell study at UCL) said an uncalibrated test-cell model passed the Guideline 14 tolerances yet over-predicted hourly temperature by about 3.2 C on average, reduced to about 0.68 C after Bayesian calibration; treat as unverified.

**What it needs:** A simulator that can generate truth-known cases, and a decision on which downstream quantity matters (here, savings; for us, correct cause).

**Failure modes / caveats:** The surrogate world shares the simulator's blind spots, so this tests the calibration procedure, not the simulator's realism. The authors themselves weigh surrogate against real-building data.

**Read status:** ABSTRACT_ONLY (both). The Guideline 14 thresholds (monthly: NMBE within 5 percent, CV(RMSE) 15 percent; hourly: 10 and 30 percent) are SNIPPET only and the search summary noted a 2023 edition supersedes 2014.

**Relevance to us [INFERENCE]:** Our 0.76 versus 0.51 matched-versus-broad-family test is already this kind of test. The addition worth borrowing is scoring three things separately (top-1, correct-cause posterior calibration, recovery of the true plant parameters) so that a good score on one is not read as success on the others.

---

## 4. History matching: rule out implausible parameter regions instead of fitting one posterior

**Technique:** Use a Bayesian emulator plus history matching to iteratively discard parameter settings that cannot reproduce the observations, accounting for emulator, discrepancy, and measurement uncertainty.

**Field and source:** Domingo et al. (2024), "Calibration under Uncertainty Using Bayesian Emulation and History Matching: Methods and Illustration on a Building Energy Model", *Energies* 17(16):4014. https://ideas.repec.org/a/gam/jeners/v17y2024i16p4014-d1455478.html

**What it does:** Applies the method to an EnergyPlus model of a domestic property with one year of observed gas consumption and temperature. Each wave of emulation removes regions of input space whose outputs are implausibly far from the observations.

**Evidence of effect:** From the abstract: only 0.3 percent of parameter configurations matched when gas consumption alone was matched, and 0.01 percent when gas and temperature were matched together. This shows how sharply additional output channels constrain the parameter space. No predictive-accuracy numbers.

**What it needs:** Emulator training runs, observed series for several outputs, and a statement of plausible discrepancy and measurement error.

**Failure modes / caveats:** Output is a non-implausible region, not a calibrated posterior, so it can still leave many equally good settings. A search summary (SNIPPET) mentioned 8 tuned parameters and monthly gas plus hourly temperature data; I could not confirm it.

**Read status:** ABSTRACT_ONLY (the MDPI full text returned HTTP 403).

**Relevance to us [INFERENCE]:** A natural fit for the "broad family of plausible plants": real visits can be used to *rule out* parts of the plant family (for example, plants whose recirculation temperatures could never produce what was observed) before any per-cause likelihood is refit.

---

## 5. Continuous (online) calibration of a digital twin: sequential Kennedy-O'Hagan versus particle filter

**Technique:** Update simulator parameters as data stream in, using a particle filter with an emulator, or windowed Kennedy-O'Hagan calibration, so that parameters that change over time are tracked.

**Field and source:** "Continuous calibration of a digital twin: comparison of particle filter and Bayesian calibration approaches", arXiv:2011.09810 (2020). Authors are not shown in the text I retrieved (I believe Ward, Choudhary and co-authors, Growing Underground case; unverified). https://ar5iv.labs.arxiv.org/html/2011.09810

**What it does:** Calibrates a 1D physics model of an unheated underground hydroponic farm (ventilation rate and internal air speed) against relative humidity. Compares static KOH, windowed (sequential) KOH, and a particle filter with a GP emulator.

**Evidence of effect:** Toy problem (40 synthetic points, ventilation halved midway): posterior-prediction RMSE 1.1 percent for the particle filter and 0.9 percent for sequential KOH; static KOH on all 40 points put the ventilation estimate midway between the two true values. With 10 percent noise the particle filter could not detect the change. Real monitored data (118 points, August-October 2018): static KOH gave a ventilation rate drifting from 6.5 to 5.6 ACH, while sequential values were closer to 3 ACH in one period, i.e., the answer depended on the method. Run time for the toy problem: static KOH 22,572 s for 40 points versus 786 s for the particle filter with 1,000 particles.

**What it needs:** A fast or emulated simulator, a stream of measurements, tuning of window size (4 points was judged best) and particle count.

**Failure modes / caveats:** Particle-filter variance grows over time; the particle filter cannot quantify model bias by itself, so the authors recommend pairing it with periodic KOH; neither sequential method clearly tracked the known setpoint changes on real data; measurements fell outside the simulated range at times.

**Read status:** FULL_TEXT for the first 100,000 of 103,332 characters.

**Relevance to us [INFERENCE]:** Plants drift (valve settings, scaling, pump wear), so a single fitted parameter set per building may be stale; but the result also warns that streaming updates on noisy data can chase noise.

---

## 6. Domain randomization, from fixed textures to automatic domain randomization (and how it fails)

**Technique:** Randomize the simulator's nuisance parameters widely enough that the real world looks like one more sample, then train only on simulation.

**Field and source:**
- Tobin et al. (2017), "Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World", IROS 2017, arXiv:1703.06907. https://ar5iv.labs.arxiv.org/html/1703.06907
- OpenAI et al. (2019), "Solving Rubik's Cube with a Robot Hand", arXiv:1910.07113 (automatic domain randomization, ADR). https://ar5iv.labs.arxiv.org/html/1910.07113
- Muratore et al. (2022), "Robot learning from randomized simulations: a review", arXiv:2111.00956. https://ar5iv.labs.arxiv.org/html/2111.00956

**What it does:** Tobin trains an object detector on non-realistic random-texture renderings and tests on real images. ADR starts narrow and widens each parameter's range automatically whenever the policy performs well, so difficulty grows with competence.

**Evidence of effect:**
- Tobin (sim-only training, real test): about 1.5 cm average localization error; 1.3 cm object only, 1.8 cm with distractors, 2.4 cm with occlusions. Removing distractors from training raised errors to 7.2 and 7.4 cm on distractor and occlusion tests. Fewer than 1,000 distinct textures degraded performance noticeably; about 5,000 images were already workable with pretrained weights and gains continued to roughly 50,000. Authors note the detectors still overfit simulated data.
- ADR (real robot, block reorientation, mean consecutive successes): manual (hand-set) randomization 2.7 versus 13.3 for ADR (large) and 32.0 for ADR (extra-extra-large), while manual randomization scored 42.5 in simulation. A narrow ADR run scored 21.0 in simulation but 1.4 on the robot. Rubik's cube, 10 real trials each: mean successes 1.8 (manual) versus 26.8 (best ADR with face-angle sensing); vision pose errors on the real robot were about 7.8 degrees with randomization versus about 129 degrees without it.
- Review: too-wide randomization can produce infeasible or conservative policies and numerical instability; static ranges are hand-tuned and give lower final performance than adaptive schemes.

**What it needs:** A simulator that exposes the relevant nuisance parameters, large compute, and (for ADR) a way to measure success to drive range expansion. No real data for the basic method.

**Failure modes / caveats:** Success in simulation does not predict success on hardware (42.5 versus 2.7). ADR's "too wide" failure is a hypothesis in that paper, not a measured result. Broad randomization trades peak accuracy for robustness.

**Read status:** FULL_TEXT for Tobin; FULL_TEXT for the first 100,000 of about 193,000 characters of ADR (Table 3 and Table 6 retrieved); FULL_TEXT for the first 100,000 of about 140,000 characters of the review.

**Relevance to us [INFERENCE]:** The same split appears in our numbers (0.76 in a matched world, 0.51 across a broad family). The robotics lesson is that the randomized family must contain the real world and that its breadth should be earned and checked against real outcomes, not set by hand.

---

## 7. Structured randomization and synthetic-pretraining-plus-real-fine-tuning (autonomous driving)

**Technique:** Sample simulated scenes from distributions that follow real-world structure (road geometry, plausible placements) rather than uniformly, and use synthetic data to pretrain before a small amount of real labelled data.

**Field and source:**
- Prakash et al. (2019), "Structured Domain Randomization: Bridging the Reality Gap by Context-Aware Synthetic Data", ICRA 2019, arXiv:1810.10093. https://ar5iv.labs.arxiv.org/html/1810.10093
- Johnson-Roberson et al. (2017), "Driving in the Matrix: Can Virtual Worlds Replace Human-Generated Annotations for Real World Tasks?", ICRA 2017, arXiv:1610.01983. https://ar5iv.arxiv.org/html/1610.01983

**What it does:** Both train car detectors (Faster R-CNN) on synthetic images and test on the KITTI benchmark. Structured randomization places objects by context-aware distributions; Johnson-Roberson uses a game-engine simulator.

**Evidence of effect:** Prakash, KITTI average precision (easy / moderate / hard), 25,000 synthetic images: uniform randomization 56.7 / 38.8 / 24.0; structured randomization 77.3 / 65.6 / 52.2. On a 1,500-image subset, structured randomization scored 69.6 / 65.8 / 52.5, versus 59.7 / 54.3 / 45.6 for 70,000 real images from a different domain (BDD100K), and 85.1 / 88.3 / 88.8 for 6,000 in-domain real KITTI images. Fine-tuning the structured-randomization model on real KITTI beat real data alone, with the gain largest when few labelled real images were available (values only in a figure I could not read). Johnson-Roberson (mean AP easy / moderate / hard): 10k synthetic 0.554 / 0.383 / 0.290; 50k synthetic 0.686 / 0.501 / 0.393; 200k synthetic 0.680 / 0.526 / 0.421; versus 2,975 real Cityscapes images 0.625 / 0.427 / 0.357.

**What it needs:** Domain knowledge to write the scene-structure distributions; tens of thousands of synthetic samples; a few real labelled samples for fine-tuning.

**Failure modes / caveats:** Pure synthetic training still trails in-domain real training by a wide margin. One class (cars), one detector, one benchmark in both papers. Johnson-Roberson calls its results preliminary and notes a single synthetic image carries less training value than a real one; its Cityscapes comparison may reflect a similar-geography overlap.

**Read status:** FULL_TEXT for both (tables retrieved).

**Relevance to us [INFERENCE]:** Replace uniform ranges over plant parameters with a structured generator of plants (building type, riser count, loop layout, equipment mix) drawn from what plants look like; the data show a 20 to 30 point swing from structure alone. The "pretrain on sim, then add real" gain is largest at small real-sample sizes, which matches our expected tens-to-hundreds of visits.

---

## 8. Adapt the simulator's parameter distribution using a handful of real rollouts

**Technique:** Instead of freezing the randomization ranges, update the distribution over simulator parameters so that simulated behaviour matches (SimOpt) or serves the task on (AdaptSim) a few real trials, then retrain in the updated simulator.

**Field and source:**
- Chebotar et al. (2019), "Closing the Sim-to-Real Loop: Adapting Simulation Randomization with Real World Experience", ICRA 2019, arXiv:1810.05687. https://ar5iv.labs.arxiv.org/html/1810.05687
- "AdaptSim: Task-Driven Simulation Adaptation for Sim-to-Real Transfer", arXiv:2302.04903 (2023); authors and venue not shown in the retrieved text (I believe Ren et al., CoRL 2023; unverified). https://arxiv.org/html/2302.04903v1

**What it does:** SimOpt interleaves a few real rollouts with updates of a Gaussian distribution over simulation parameters. AdaptSim meta-learns, in simulation, a policy that proposes parameter changes from real trajectories, optimizing task reward rather than dynamics match.

**Evidence of effect:**
- SimOpt, real robots: each iteration used 3 real rollouts. Swing-peg-in-hole inserted the peg in 90 percent of 20 trials after two iterations (one iteration got close but did not insert). Drawer opening succeeded in all 20 trials after the update. In simulation, standard randomization only converged at a 2 cm cabinet-position standard deviation; at 10 cm policies became conservative and did not open the drawer. No real-robot baseline success rate was reported.
- AdaptSim (pushing, real-data efficiency): reached normalized reward 0.83 with 16 real trials; training in the target alone reached 0.84 at 40; uniform randomization plus target training reached 0.82 at 40 (and dropped from 0.63 to 0.56 at 4 trials). About 2 to 2.5 times fewer real trials. In its simulated comparison table it was below the best system-identification baseline in 3 of 15 columns (pushing well-defined case 0.95 vs 0.98, pushing OOD-4 0.77 vs 0.79, scooping OOD-1 0.64 vs 0.66).

**What it needs:** A parameterised simulator that can be rerun many times, a way to compare real and simulated trajectories, and the ability to run the real system a few times (here 3 rollouts per iteration or about 16 trials). AdaptSim also needs about 36 hours of simulated meta-training.

**Failure modes / caveats:** Only unimodal Gaussian distributions learned; sensitive to initial variance and the discrepancy measure; two tasks, 20 trials each; AdaptSim fails when the real object behaves in ways absent from simulation (Brussels sprouts), and depends on the chosen simulation parameter space.

**Read status:** FULL_TEXT for SimOpt; FULL_TEXT for the first 100,000 of 100,451 characters of AdaptSim.

**Relevance to us [INFERENCE]:** The closest analogue to "use confirmed visits to update our prior over plant types and parameters" rather than only to update cause frequencies. It also shows the effort scale: single-digit to a few tens of real events can move a simulator-trained policy a lot when the update targets the right parameters.

---

## 9. Replace the worst simulator component with a model learned from a few minutes of real data

**Technique:** Identify the one component the simulator models worst, learn it from real data (a small supervised model), and put it back inside an otherwise physics-based simulator.

**Field and source:** Hwangbo et al. (2019), "Learning agile and dynamic motor skills for legged robots", *Science Robotics* 4(26), arXiv:1901.08652. https://ar5iv.labs.arxiv.org/html/1901.08652

**What it does:** The ANYmal quadruped's series-elastic actuators have dynamics that are hard to model analytically (the paper cites nearly a hundred parameters). The authors train a neural "actuator network" on real data, embed it in a rigid-body simulator, train the locomotion policy in simulation, and deploy it.

**Evidence of effect:** Torque error on validation data was 0.740 Nm for the learned model versus 3.55 Nm for an ideal-actuator model (0.966 versus 5.74 Nm on test data). Policies trained with the ideal or the analytical actuator model could not take a single step on the real robot; the analytical model had received more than a week of tuning without much success. The real data came from under 4 minutes of excitation (over 1 million samples at 400 Hz). The resulting controller followed commanded speeds with 2.2 percent error, reached 1.5 m/s on hardware against a prior record of 1.2 m/s, and recovered from falls in 9 of 9 initial configurations.

**What it needs:** Real-robot excitation data for the poorly modeled component, a way to measure the component's inputs and outputs in isolation, and a simulator that accepts a learned module.

**Failure modes / caveats:** Assumes actuators are independent; test error was higher than validation error; one robot platform; inertial parameters still off by up to about 20 percent and handled by randomization; real data volume (over a million samples) is large in sample count even if short in time.

**Read status:** FULL_TEXT.

**Relevance to us [INFERENCE]:** Suggests spending scarce real measurements on isolating the single most mis-specified piece (candidates: tenant-answer reliability, check reliability, check durations) rather than refitting the whole likelihood table. Seeded-fault experiments are the equivalent of the excitation run.

---

## 10. Simulator as a functional prior, with a learned gap process that data override as they accumulate

**Technique:** Build a Bayesian neural network whose prior is the (randomized) simulator plus a zero-mean Gaussian-process "sim-to-real gap", so predictions follow the simulator when data are scarce and follow the data when data are plentiful.

**Field and source:** Rothfuss, Sukhija, Treven et al. (ETH Zurich) (2024), "Bridging the Sim-to-Real Gap with Bayesian Inference" (Sim-FSVGD), arXiv:2403.16644. https://arxiv.org/html/2403.16644v2

**What it does:** The functional prior is the sum of a domain-model process (simulator run at parameters sampled from a prior) and a gap process (GP). Inference is functional SVGD. Applied to dynamics learning for a pendulum and a real RC car (a drifting maneuver).

**Evidence of effect:** Per the paper's text: model-based reinforcement learning on the RC car used less than half the data of the state of the art, with about 2 times fewer episodes in simulation and on hardware (20 episodes of 100 steps). Supervised NLL was "orders of magnitude" lower in the low-data regime and similar to baselines as data grew; no numeric NLL given in text. The real-world amount of data in minutes was not reported.

**What it needs:** Query access to a fully observable simulator, a prior over simulator parameters, and GP hyperparameters expressing belief about how big the gap is.

**Failure modes / caveats:** The gap-GP hyperparameters encode the user's belief and must be set sensibly; no stress test with a badly mis-specified simulator; Gaussian score approximation; low-dimensional systems.

**Read status:** FULL_TEXT.

**Relevance to us [INFERENCE]:** The structure we want for the likelihood tables: simulator-derived values as the prior, an explicit gap term, and automatic handover to field data as visit counts grow. The caveat is that the gap's prior scale is itself an assumption we would have to elicit.

---

## 11. Simulation-based inference breaks silently under misspecification; a small ground-truth calibration set repairs calibration

**Technique:** When learning posteriors from simulator output with neural networks (simulation-based inference), detect misspecification and correct it using a small set of real observations with known true parameters.

**Field and source:**
- Cannon, Ward, Schmon (2022), "Investigating the Impact of Model Misspecification in Neural Simulation-based Inference", arXiv:2209.01845. https://ar5iv.labs.arxiv.org/html/2209.01845
- Ward et al. (2022), "Robust Neural Posterior Estimation and Statistical Model Criticism", NeurIPS 2022. https://papers.nips.cc/paper_files/paper/2022/hash/db0eac6747e3631eb91095cd76065611-Abstract-Conference.html
- Wehenkel et al. (2024), "Addressing Misspecification in Simulation-based Inference through Data-driven Calibration" (RoPE), arXiv:2405.08719. https://arxiv.org/html/2405.08719

**What it does:** Cannon et al. test standard neural SBI under increasing artificial misspecification. Ward et al. model the discrepancy between simulated and observed data explicitly. RoPE fine-tunes on a small real calibration set with known ground truth and uses an optimal-transport step between learned representations.

**Evidence of effect:** Cannon: posteriors tended to be overconfident (coverage below nominal), approximate posteriors became unusable at the larger toy misspecification levels, ensembles only partly helped, and no tested mitigation prevented failure in all cases (no summary numbers given). Wehenkel: RoPE was the only method that consistently returned well-calibrated, or slightly under-confident, estimates across tasks; on the real light-tunnel task it remained best even with over 1,000 calibration examples; fine-tuning-only and plain MLP baselines improved with more calibration data but stayed overconfident. A tuning weight gamma (authors recommend 0.1 to 1, default 0.5) controls how conservative the posterior is; at large values it collapses toward the prior and the calibration set size barely matters. The calibration set sizes for the real tasks are shown only in figures.

**What it needs:** A simulator, a calibration set of real observations with confirmed true parameters (the same kind of record as a visit with a confirmed cause), and a held-out test set (2,000 pairs in RoPE experiments).

**Failure modes / caveats:** Low-dimensional parameter spaces only; calibration data must overlap the test distribution (with disjoint support fine-tuning may fail and the posterior reverts toward the prior); label noise not handled; RoPE assumes the real observation depends on the parameter only through the simulated one; on one benchmark plain simulator-trained inference won, so the benchmark was not a real test.

**Read status:** FULL_TEXT for Cannon; ABSTRACT_ONLY for Ward et al.; FULL_TEXT for the first 100,000 of 154,068 characters of RoPE.

**Relevance to us [INFERENCE]:** The overconfidence finding matches our worry about confident wrong answers. The calibration-set idea maps onto visits with confirmed cause: even when too few to refit likelihoods, they can be used to check and correct stated confidence.

---

## 12. Treat the simulator's numbers as historical data that are discounted, with a robust mixture that gives way to conflict (dynamic borrowing)

**Technique:** Combine a prior from related data (here, simulator-derived) with new data through a power prior, a hierarchical model, or a robust meta-analytic-predictive prior (an informative component mixed with a vague one), so borrowing shrinks when the new data disagree.

**Field and source:**
- Viele et al. (2014), "Use of historical control data for assessing treatment effects in clinical trials", *Pharmaceutical Statistics* 13(1):41-54. https://pmc.ncbi.nlm.nih.gov/articles/PMC3951812/
- Schmidli et al. (2014), "Robust meta-analytic-predictive priors in clinical trials with historical control information", *Biometrics* 70(4):1023-1032 (via search summary), plus a software vignette that runs the method: https://cran.rstudio.com/web/packages/shrinkr/vignettes/map_prior_with_beastt.html

**What it does:** Clinical-trial statistics where "historical controls" play the role of our simulator prior. Viele compares separate analysis, pooling, test-then-pool, power priors and hierarchical models. Schmidli's robust prior adds a weakly informative mixture component.

**Evidence of effect:** Viele's worked example (historical control 65 of 100 responders; current trial 200 per arm): pooling beat a separate analysis on error only for true control rates of roughly 0.58 to 0.73, with its best region about 0.61 to 0.67, and type I error approached 20 percent at a true rate of 0.80. Test-then-pool capped the inflation but borrowed little (about 40 subjects at a true rate of 0.75). A 40 percent power prior borrowed a fixed 40 effective observations and its error inflation was unbounded. Hierarchical models borrowed dynamically and extended the useful region below 0.65, with prior choice affecting inflation. A separate analysis kept type I error under 0.025 with about 70 percent power at the baseline scenario. Vignette example (not a trial result): informative prior effective sample size about 48.7; with a 0.5 vague-mixture weight the posterior effective size rose from 70 (no borrowing) to 93.2, and posterior SD from 0.24 to 0.21 while the mean moved from 9.66 to 9.77.

**What it needs:** A defensible prior with a stated effective size, a choice of how much conflict triggers discounting, and enough new data for the conflict to show.

**Failure modes / caveats:** If the new data differ from the historical data, borrowing inflates error and costs power; the vague-component weight and the hierarchical variance prior are judgment calls; the vignette reports no conflict scenario.

**Read status:** FULL_TEXT for Viele (first 100,000 of 103,195 characters); SNIPPET (search summary) for Schmidli; FULL_TEXT for the vignette.

**Relevance to us [INFERENCE]:** Expresses our plan in standard terms: simulator-derived likelihood tables as a prior with a stated pseudo-count, a vague component for when real visits disagree, and a rule for how fast to hand over. The clinical results suggest the conflict region is where harm occurs, which is exactly where we have no data today.

---

## 13. Sim-to-real accuracy drop in diagnosis, and what unlabeled real data bought (robot digital twin)

**Technique:** Train a fault classifier on digital-twin simulations and adapt it to real data with domain-adversarial training that uses unlabeled real samples.

**Field and source:** Chen, Fu, Zeng (2025), "A domain adaptation neural network for digital twin-supported fault diagnosis", arXiv:2505.21046 (reported accepted at ICCAD 2025). https://arxiv.org/html/2505.21046

**What it does:** Diagnoses 9 states (normal plus 8 motor failure modes) of a six-motor robot. Simulated source set 3,600 sequences (400 per class); real target set 90 sequences, all used as test data in the main experiments.

**Evidence of effect:** Trained on simulation only and tested on real data: CNN 70.00 percent, LSTM 56.00, Transformer 48.44, TCN 44.22. Domain-adversarial training with the CNN backbone: 80.22 percent (about +10 points), using unlabeled real features only. The text also says an earlier version of the LSTM reportedly fell from 96 percent on simulated validation data to 69 percent on real data (a secondhand figure in that paper). Training on the real data alone (about 63 sequences) gave 14 to 18 percent, close to chance for 9 classes.

**What it needs:** A digital twin that can generate labelled fault data, and unlabeled real data from the target system (here 90 sequences).

**Failure modes / caveats:** Even after adaptation about 20 percent of real cases are wrong; best simulation-only model was only 70 percent; the paper's own description of whether labelled target data are used is internally inconsistent; the real sample is tiny; more compute and deep-learning expertise are required.

**Read status:** FULL_TEXT (arXiv HTML; abstract page also read).

**Relevance to us [INFERENCE]:** The one sim-versus-real pair reported (96 to 69 percent, secondhand) is a drop of about 27 points, the same order as our 0.76 to 0.51 and 0.92 to 0.69. The gain from unlabeled real data (+10 points) is modest compared with the gap, which supports spending effort on labelled confirmed-cause visits instead.

---

## 14. Building-HVAC fault diagnosis from simulation or lab data: what small real data bought

**Technique:** Pretrain or calibrate on simulated or lab fault data, then use a little real data to adapt (normal-operation data only, injected field samples, or few labelled faults).

**Field and source:**
- Dowling and Zhang (2020), "Transfer Learning for HVAC System Fault Detection", arXiv:2002.01060. https://ar5iv.labs.arxiv.org/html/2002.01060
- Sanchez-Zabala and Gomez-Acebo (2026), "Evaluating learning strategies for fault diagnosis in HVAC systems under labeled data scarcity", *Energy and Buildings* 357:117134. https://scienceportal.tecnalia.com/en/publications/evaluating-learning-strategies-for-fault-diagnosis-in-hvac-system/
- Abdul Ghani (2025), "Data-Driven Detection of Leaking Valves in Air Handling Units", NeurIPS 2025 listing. https://neurips.cc/virtual/2025/133735
- Chu, Cho, Park (2023), "Development of FDD Model for a Real-life Case using Transfer Learning with Synthetic Data", Energy Proceedings vol. 38. https://www.energy-proceedings.org/development-of-fdd-model-for-a-real-life-case-using-transfer-learning-with-synthetic-data/

**What it does:** Dowling and Zhang learn a state-transition model on a source building (EnergyPlus) and transfer it to a real building with weighted least squares. Sanchez-Zabala benchmarks labelled-data scarcity strategies on three public datasets. Abdul Ghani trains on 80 lab AHU runs and adds 1,000 high-confidence field samples. Chu et al. transfer from a HVACsim+ source model using only normal operation data of the target AHU.

**Evidence of effect:**
- Dowling and Zhang: on a real PNNL building, a transferred linear model reached validation MSE 0.041 versus 0.267 from scratch (0.019 best possible), with roughly 3 days of data. But their fault classification, in simulation only, reached only about 55 to 59 percent precision and recall, and no real-building fault data were used.
- Sanchez-Zabala: balanced accuracy becomes acceptable for most algorithms once there are more than 100 labelled fault instances per class (air-handling datasets); data augmentation, semi-supervised learning and a hybrid raised balanced accuracy by up to 15.24, 13.08 and 19.98 percent depending on starting label count; a simulation-based metamodel transfer added only 0.35 percent over those in a preliminary test.
- Abdul Ghani: 97.41 percent accuracy on unseen lab runs; about 99 percent after injecting 1,000 field samples, but field accuracy before adaptation and field ground-truth labels were not available.
- Chu et al.: "satisfactory", no numbers in the abstract.

**What it needs:** From a few days of normal data (Dowling) to more than 100 labelled faults per class (Sanchez-Zabala) to a thousand field samples (Abdul Ghani).

**Failure modes / caveats:** Dowling's derivation assumes Gaussian noise with unit variance and comparable components in both buildings; no real-fault validation anywhere except through unverifiable pseudo-labels; simulation-based transfer gains were tiny next to simply getting labelled faults. A related real-AHU dataset paper (Wang et al., 2024, *Data in Brief*) states that models built on simulated data often reflect real conditions poorly, but gives no accuracy comparison.

**Read status:** FULL_TEXT for Dowling and Zhang; ABSTRACT_ONLY for Sanchez-Zabala, Abdul Ghani, and Chu et al.

**Relevance to us [INFERENCE]:** The only quantitative label-volume benchmark I found (about 100 labelled faults per class for acceptable accuracy) is larger than "tens to a few hundred visits across 17 causes", so at our scale labelled data should be used to calibrate and discount the simulator prior rather than to train a data-driven classifier.

---

## Patterns across items

- **Real data is spent on a few well-chosen things, not on refitting everything.** The successful sim-to-real results used single-digit to tens of real events (3 rollouts per iteration, 16 trials, 4 minutes for one actuator) and targeted a specific piece: the simulation parameter distribution (items 8), the worst component (9), or the gap term (10).
- **Randomization breadth is not the lever; containing the real world and structure are.** Hand-set randomization gave 42.5 in simulation and 2.7 on hardware, while an adaptive widening reached 32.0 (item 6); structured sampling beat uniform by 20 to 30 AP points (item 7); in SimOpt, too-broad ranges made policies conservative.
- **Discrepancy must be modeled, but its prior cannot be learned from small data.** Kennedy-O'Hagan results and the building papers agree that parameters are recoverable only with realistic discrepancy priors, and discrepancy hyperparameters are often non-identifiable (items 1, 2, 5). This is where elicited knowledge belongs.
- **Naive simulator-trained inference is overconfident when the simulator is wrong.** Neural SBI under misspecification gave under-covering posteriors and no mitigation worked everywhere; a small calibration set with known truth restored calibration (item 11). Calibration of stated confidence is the cheapest thing to fix with a few labelled cases.
- **Borrowing from the simulator should be dynamic and bounded.** Pooling or fixed-weight power priors help only in a narrow band of similarity and inflate error outside it; hierarchical or robust-mixture priors extend that band but still lose when the conflict is large (item 12). The simulator-as-prior-with-gap structure (item 10) is the same idea in a different guise.
- **Good fit and good prediction are different things.** Guideline 14 style fit metrics, simulated validation accuracy (96 percent, then 69 percent real), and manual-randomization simulated success (42.5) all failed to predict real performance (items 3, 6, 13). Testing on truth-known surrogate cases scored three ways is the common safeguard.
- **Sim-to-real drops in diagnostics are large and only partly closed by adaptation.** About 27 points (96 to 69 percent, secondhand) for one robot diagnostic, with 70 percent real accuracy for the best simulation-only model and +10 points from unlabeled adaptation; building-FDD papers report weak or unverified real-data numbers (items 13, 14).
- **Evidence volume is thin where we need it.** I found no rule for the number of field measurements needed for calibration, no same-classifier building-FDD drop figure, and no domestic-hot-water-specific calibration result I could open.

## Sources I could not read (or could only partly read)

- Unreadable PDFs (binary returned, nothing extracted): arxiv.org/pdf/1703.06907, arxiv.org/pdf/2011.09810, arxiv.org/pdf/2002.01060 (replaced with ar5iv HTML renderings, which read fine); publications.ibpsa.org simbuild2024_2292.pdf; aivc.org p_1035.pdf; osti.gov servlets purl 2440970. Note: the fetch tool itself cached these binary responses in its own tool-results folder when it hit PDF URLs; I did not open or use them.
- Blocked or failed: web.eecs.utk.edu Garrett and New full PDF (certificate error); UCL manuscript baycal.pdf (over the size limit) and its landing page (HTTP 403); MDPI Domingo et al. full text (403); PMC page for the power-prior/commensurate-prior paper (bot check; Hobbs et al. not read); Europe PMC for Viele (403, read PMC instead); INIS record for the UCL test-cell paper (402); Schmidli's BORIS repository page (bot-protection page); NRC page and INL PDF for NUREG/CR-6823 (403 / not read, so no evidence on nuclear-PRA generic-prior updating).
- Not located or only metadata: Chong and Menberg (2018) "Guidelines for the Bayesian calibration of building energy models"; Chong et al. (2017) large-datasets calibration (only a thesis statement via search summary that Bayesian calibration was limited to monthly data); Kennedy and O'Hagan (2001) original; Bres (2020) "Calibration of Domestic Hot Water System Simulations With Stochastic Profiles" (BauSIM; metadata page only, no abstract); Kapteyn, Pretorius, Willcox (2021) predictive digital twin (search summary only, no numbers); Hobbs et al. (2011) commensurate priors.
- Do not cite: arXiv:2208.00124 ("Physical Parameter Calibration") is marked withdrawn.
- Partly read (first 100,000 characters only, remainder unread): ADR (about 193k chars), the domain randomization review (about 140k), RoPE (about 154k), digital-twin calibration (103k), Viele (103k), AdaptSim (100.5k).
