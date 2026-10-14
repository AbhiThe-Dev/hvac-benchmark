# Area B: Fault diagnosis and prognostics in industry, aerospace, automotive and buildings: how lab/simulation-built diagnostics get closer to field accuracy

Compiled 2026-10-10. Tools used: WebSearch and WebFetch only. Read-status key: `FULL_TEXT` = the passage with the number or claim was in what the fetch returned; `ABSTRACT_ONLY` = abstract or catalog page only; `SNIPPET` = search-result summary only.

Honest summary of the evidence base: most papers in this area report lab, benchmark, or simulation results. Real field accuracy numbers are scarce, and where they exist they are tiny samples (90 test sequences, one rooftop unit, one engine test with no ground truth). Several of the best-known sources are PDFs the fetch tool could not read as text (listed at the end). Where I found no number I say so.

Disclosure: when I fetched PDF URLs, the fetch tool automatically wrote the raw binary to the session's tool-results folder (it returned "unreadable"). I did not open, parse, or use those saved files. I avoided PDF URLs where an HTML/abstract alternative existed.

---

## Item 1. Evaluate by holding out whole physical units (leakage-free split), not random segments

**Technique:** Split train/test by physical machine (bearing) so no unit appears on both sides; report how performance depends on the number of distinct training units.

**Field and source:** Machine fault diagnosis (bearings). "Towards a more realistic evaluation of machine learning models for bearing fault diagnosis," arXiv:2509.22267, 2025. https://arxiv.org/abs/2509.22267 (HTML version read: https://arxiv.org/html/2509.22267)

**What it does:** Re-evaluates a standard 1D-CNN (WDCNN) on four public bearing datasets (CWRU, Paderborn PU, UORED-VAFCLS, HUST) under three protocols: segment-level leakage, bearing/condition-level leakage, and a leakage-free split by physical bearing. It also varies how many distinct bearings are in training.

**Evidence of effect:** Macro AUROC, time-domain input, leakage-free vs leaky: CWRU 63.2% vs 100% (condition-wise); PU 54.3% (SD 17.8) vs 86.9% (condition-wise) and 98.6% (repetition-wise); UORED 87.3% vs 90.2% (bearing-level) and 99.9% (segment-level). Frequency/envelope inputs show the same pattern (PU 61.3% and 77.0% leakage-free). The paper reports that the number of distinct training bearings, not the number of samples, drives generalization, and PU performance stays relatively low even as bearing count rises. It also states it could not reproduce the original PU paper's 98.3% multiclass accuracy. It cites prior work (not its own experiments) in which accuracy falls from near 100% to about 40-60% when moving to bearing-wise splits. It cites a prior finding of a significant domain shift between artificially damaged and naturally degraded bearings (no number given in what I read).

**What it needs:** Multiple physical units per fault class; discipline in how splits are built. No new data.

**Failure modes / caveats:** One architecture (WDCNN) and AUROC rather than accuracy; the HUST leakage experiment was not in the portion I read; these datasets contain few physical bearings (Paderborn has 32 per a search summary), so variance is large (SD up to about 18 points on PU).

**Read status:** FULL_TEXT for the results table (via fetch summarizer, second half of a ~200k-character page); abstract page also read.

**Relevance to us [INFERENCE]:** Our 0.76 (matched world) vs 0.51 (broad plant family) gap looks like the same effect: the right test unit is a whole plant held out of the generating assumptions, and the number of distinct plant types in the training/likelihood design may matter more than the number of simulated visits.

---

## Item 2. Digital-twin training plus domain-adversarial adaptation using unlabeled real data

**Technique:** Train on simulated (digital-twin) fault data, then adapt with a domain-adversarial network (DANN) that uses unlabeled real measurements.

**Field and source:** Industrial robot fault diagnosis. Chen, Fu, Zeng (as listed in a search result), "A domain adaptation neural network for digital twin-supported fault diagnosis," arXiv:2505.21046, 2025. https://arxiv.org/html/2505.21046v1

**What it does:** Builds a digital twin of a six-motor robot, generates 3,600 labeled simulated sequences (9 classes, 400 each), and tests on 90 sequences from the physical robot with injected failures. A DANN uses the real data's features (not its labels) to learn domain-invariant representations.

**Evidence of effect:** CNN trained on simulation scores 96.78% on simulated validation but 70.00% (SD 1.99) on real data. DANN raises real-data accuracy to 80.22% (SD 1.78), about +10 points. Other backbones trained on simulation only: LSTM 56.00%, Transformer 48.44%, TCN 44.22%. Training on the 90 real sequences alone gives only 13.97-18.10% across models. Healthy-class F1 on real data: 0.67 (DANN) vs 0.07 (CNN). The text notes an earlier LSTM result of about 96% simulated vs 69% real.

**What it needs:** A twin that generates all fault classes; a set of unlabeled real sequences from the target machine (here 90); deep-learning expertise and compute.

**Failure modes / caveats:** Tiny real test set (90) from a single dataset; the page does not say whether the robot was in a lab or in service; the claim that it works with few target labels is not directly tested; the remaining ~20-point gap to a clean score is attributed to unmodelled physics.

**Read status:** FULL_TEXT.

**Relevance to us [INFERENCE]:** The sim-to-real drop of about 26 points on a small physical system is the same order as our matched-to-broad drop. Unlabeled field data (visit readings without confirmed causes) could plausibly support adaptation or at least recalibration of the observation model, which is cheaper to get than confirmed causes.

---

## Item 3. Simulation-pretrained HVAC models adapted with a few days of target-building data

**Technique:** Pretrain a model of normal operation (and a fault classifier) on a simulated data-rich building; adapt to the real building using only a few days of normal-operation data.

**Field and source:** Building HVAC (VAV). (a) Dowling and Zhang, "Transfer Learning for HVAC System Fault Detection," arXiv:2002.01060, 2020. https://ar5iv.labs.arxiv.org/html/2002.01060 (b) Rooftop-unit classifier trained on a simulated multi-unit library: IIF-IIR record 149438, "Generalizability of a machine learning fault classifier utilizing a ..." (title truncated on the page; authors and year not shown on the page I read) https://iifiir.org/en/fridoc/generalizability-of-a-machine-learning-fault-classifier-utilizing-a-149438 and the associated UNL dissertation record https://digitalcommons.unl.edu/dissertations/AAI30813543 (author not shown on the page).

**What it does:** (a) Learns a state-transition model from a simulated EnergyPlus medium office, then transfers by weighted least squares (target data weighted 10.0, source 0.01) to the real PNNL Systems Engineering Building. (b) Trains a classifier on simulated data for fixed-orifice RTUs, reduced to 9 input features (8 quantitative, 1 qualitative), then checks it on lab data and one real unit.

**Evidence of effect:** (a) On the real building's hourly data: validation MSE (0-1 normalized) 0.041 with transfer vs 0.267 from scratch vs 0.019 best possible. About 3 days of hourly target data gave the main gain; a neural-network variant approached baseline with 2 days; the summer transfer used two weeks of normal data. The fault classifier itself was tested only in simulation (one simulated filter-fouling fault): precision/recall about 55-59%, and the test periods differ, so the transfer benefit for classification is not isolated. (b) In the field, one RTU unlike the training units at a manufacturing facility in Omaha: it correctly predicted all refrigerant-undercharge cases from that unit (one fault type, one unit). Lab performance was reported "significantly better" than existing protocols, no numbers on the page; performance improved with fault severity; rebalancing the training set and choosing informative features were needed.

**What it needs:** (a) A reasonable simulator of the same equipment class; days to weeks of normal-operation data from the target; comparable components. (b) A simulated library covering several units; feature reduction to what field units actually measure.

**Failure modes / caveats:** (a) Modest classification scores; one source-target pair, one fault, one VAV box; assumptions about noise (unit variance) did not hold; transfer assumes similar components. (b) Single unit, single fault; no false-alarm or miss rates on the abstract page.

**Read status:** (a) FULL_TEXT; (b) ABSTRACT_ONLY.

**Relevance to us [INFERENCE]:** The transferable asset here is normal-condition data from the target site, which is cheap to collect; for hot water that would mean a short logging period or a few "healthy" visits to recalibrate expected readings. Notably, even here the fault classification was never validated on real faults.

---

## Item 4. Simulation-only training with signal conditioning to shrink the sim-real gap (and the validation hole when no ground truth exists)

**Technique:** Train only on physics-simulated vibration from many bearing geometries; apply a conditioning chain (cepstrum pre-whitening, high-pass filter, moving quartile averaging, amplitude normalization) to simulated and real signals alike.

**Field and source:** Aerospace/industrial bearings. "A Generalized Convolutional Neural Network Model Trained on Simulated Data for Fault Diagnosis in a Wide Range of Bearing Designs," Sensors 25(8):2378, 2025 (Univ. of Southampton with Safran data). https://pmc.ncbi.nlm.nih.gov/articles/PMC12030810/

**What it does:** Simulates 137 bearing designs and trains a CNN on 1,200 one-second simulated samples (outer race, inner race, ball faults). Real data (CWRU lab bearings; ground-test data from a Safran jet engine) is used only for testing, never in training.

**Evidence of effect:** On CWRU drive-end bearing, 88.42% average on the full set (outer race 94.28%, inner race 89.06%, ball 75%); 95.73% average over diagnosable drive-end and fan-end samples; ball faults weakest; fan-end bearing worse (outer race 55.55% on the full set). On the real engine test (180 one-second segments): 86.03% labelled outer-race, which the authors say matches the supplier's label, and 13.97% labelled ball/cage, which the authors present as detection but did not verify against ground truth. No formal accuracy figure for the engine; no ablation of the conditioning chain on engine data.

**What it needs:** A validated physics simulator spanning the equipment family; real signals for testing; the conditioning pipeline.

**Failure modes / caveats:** Single-fault model applied to a case that may have multiple faults; no healthy class; CWRU data had looseness distorting signatures; the claim of beating transfer-learning benchmarks compares different subsets and conditions; for the real engine, there is no verified ground truth so the field result cannot be scored.

**Read status:** FULL_TEXT.

**Relevance to us [INFERENCE]:** Two lessons: (1) simulation-only training can work on clean lab data (88-96%) yet the one real-service test could not be scored, which is the honest state of most sim-to-field claims; (2) preprocessing that maps real readings to the simulator's representation (the analogue for us: reading normalisation such as recirculation-return temperature drop relative to design) is a cheap lever.

---

## Item 5. Public seeded-fault datasets and what building the ground truth actually took

**Technique:** Create labeled fault/no-fault datasets from simulation plus experimental test facilities, with fault severity, so algorithms can be tested.

**Field and source:** Building HVAC. Granderson, Lin, Harding, Im, Chen, "Building fault detection data to aid diagnostic algorithm creation and performance testing," Scientific Data 7:65, 2020. https://pmc.ncbi.nlm.nih.gov/articles/PMC7039876/

**What it does:** Releases data from EnergyPlus-Modelica and HVACSim+ simulations and from experimental facilities (LBNL FLEXLAB, Oak Ridge Flexible Research Platform), with AHU faults (stuck dampers, valve leakage or sticking, outdoor-air sensor bias of 1, 2 and 4 degrees C) and RTU faults (condenser fouling, setback errors, infiltration, thermostat bias).

**Evidence of effect:** No accuracy numbers (it is a data paper). What it reveals about real vs simulated signatures: only one direct comparison, a leaking heating coil whose simulated temperature offset matched the measured offset. It states EnergyPlus idealizes control and may miss short-term behaviour, so the HVAC was rebuilt in Modelica. It judged the HVACSim+ model adequate when hourly differences were under 20% of typical values, while its own table shows mixed-air differences up to about 2.3 degrees C that are not discussed. It does not systematically compare simulated and experimental fault signatures.

**What it needs:** A test facility able to impose faults (control overrides, bypass valves, mesh over a condenser, open windows); functional tests; careful ground-truth checking. Ground truth here was established by functional tests that confirmed sequences ran as designed, plus visual inspection of each faulted and fault-free dataset against expected trends and control logic.

**Failure modes / caveats:** Limited days per scenario; only some equipment types (chillers, boilers, dual-duct AHUs, VAV boxes and fan-coils are future work); missing-data handling not discussed; faults are imposed, not naturally occurring.

**Read status:** FULL_TEXT.

**Relevance to us [INFERENCE]:** Confirms that ground truth for seeded faults is built from checks plus expert inspection, not from the tool under test; a cooperating-building seeded-fault campaign for hot water could follow the same functional-test-then-inspect recipe, and the paper offers no evidence that simulated signatures can be trusted without that comparison (matching your 0.92 vs 0.69 experience).

---

## Item 6. Standardized diagnosis competitions on a real hardware testbed (NASA ADAPT, DXC)

**Technique:** Run many diagnostic algorithms on common fault-injection scenarios from a physical power-system testbed (and synthetic circuits), score on shared metrics.

**Field and source:** Aerospace electrical power systems. DXC'09/'10/'11 competitions (NASA Ames, PARC, TU Delft). Pages read: NTRS record 20100021404 (ProADAPT) https://ntrs.nasa.gov/citations/20100021404 ; NTRS 20100024257 https://ntrs.nasa.gov/citations/20100024257 ; Feldman et al., "Empirical Evaluation of Diagnostic Algorithm Performance Using a Generic Framework," IJPHM 2010 https://papers.phmsociety.org/index.php/ijphm/article/view/1344 ; DXC'11 catalog page https://catalog.data.gov/dataset/third-international-diagnostic-competition

**What it does:** DXC'09 compared 12 algorithms in 3 tracks (industrial hardware and synthetic); DXC'11 compared 11 across three tracks including a software track; a 2010 journal paper compares 13 algorithms under identical conditions on the ADAPT hardware and synthetic circuits. The winning industrial-track entry (ProADAPT) used Bayesian networks compiled to arithmetic circuits, composed from subsystem models (24 power-system models; the largest BN has over 1,000 variables); it ranked first in both industrial tiers (first of 9, first of 6).

**Evidence of effect:** From pages I could read: no per-algorithm accuracy or false-alarm numbers. A search-result summary (SNIPPET, unverified, source PDF unreadable to me) reported very large spreads in Tier-2 false-positive rates on the hardware data, from about 0% to above 80% across algorithms, and noted that the official-winner decision was disputed; I do not rely on those numbers. The testbed's stated design purpose (from a search snippet) is to expose real-world issues that small-scale experiments and simulations miss.

**What it needs:** A physical testbed with fault injection and common data/scoring formats; participants' algorithms; considerable organizer effort.

**Failure modes / caveats:** Competition winners can reflect scoring design; I could not retrieve the results tables or lessons-learned text (PDFs unreadable); parameters' provenance for the winning BN was not in the abstracts I read.

**Read status:** ABSTRACT_ONLY (plus SNIPPET for the false-positive spread).

**Relevance to us [INFERENCE]:** The structure that did best on real hardware was a hand-composed probabilistic model, which resembles ours; but I could not confirm how its parameters were set, so I cannot say it transfers. The valuable idea is a shared scenario set and metrics that include nominal (no-fault) runs, so that false positives are scored.

---

## Item 7. Pre-deployment protocol testing with grey-box simulation and outcome-category scoring

**Technique:** Score FDD protocols with thousands of generated fault scenarios (from grey-box models fitted to lab data), classify each response (correct, false alarm, misdiagnosis, missed detection, no diagnosis), and combine into a cost-weighted figure of merit.

**Field and source:** HVAC (unitary air conditioners). Yuill and Braun, HVAC&R Research 19(7), 2013 (abstract page https://iifiir.org/en/fridoc/evaluating-the-performance-of-fault-detection-and-diagnostics-137114 ); Yuill, Cheung, Braun, Purdue IRACC 2014 (https://docs.lib.purdue.edu/iracc/1543 ); Yuill dissertation, Purdue (https://docs.lib.purdue.edu/open_access_dissertations/398 ).

**What it does:** Feeds measurements or simulated scenarios into a candidate protocol and records its response; groups outcomes by each fault's effect on capacity and efficiency; converts them into an expected monetary value across deployment conditions weighted by probability. The 2014 variant uses neural-network-based generation of semi-random test conditions because a fixed finite test set can be learned and gamed.

**Evidence of effect:** Of six widely used protocols in the case studies, most performed poorly (qualitative; no numbers on the pages). In the figure-of-merit comparison of nine protocols, one was far more valuable than the others. Lab data were not evenly spread across the operating space, which is why simulation was added.

**What it needs:** Lab datasets from several sources, grey-box model fitting, a scenario generator, and an explicit cost model.

**Failure modes / caveats:** No numeric rates on the abstract pages; evaluation depends on the fidelity of grey-box models; a fixed test set can be learned.

**Read status:** ABSTRACT_ONLY.

**Relevance to us [INFERENCE]:** Directly usable: score our tool on freshly generated random scenarios (including no-fault visits) in the same six outcome categories and attach minutes-and-callback costs. This avoids tuning to the benchmark and fits our safety-versus-speed decision rule.

---

## Item 8. Field verification of deployed FDD output, and what operators then do with it

**Technique:** Physically inspect a sample of buildings or units to measure false positives, misses, and out-of-scope faults of deployed FDD; interview operators about acting on the results.

**Field and source:** Building HVAC. (a) "Field measurement based validation of fault diagnostics for commercial [HVAC systems]," IIF-IIR record 146447 (authors per search result: Ebrahimifakhar, Chen, Yuill, Crowe) https://iifiir.org/en/fridoc/field-measurement-based-validation-of-fault-diagnostics-for-commercial-146447 ; (b) UNL dissertation on prevalence and field validation across six FDD providers https://digitalcommons.unl.edu/dissunl/252 ; (c) PNNL, "Analysis of automated fault detection and diagnosis records as an indicator of HVAC fault prevalence" https://www.pnnl.gov/publications/analysis-automated-fault-detection-and-diagnosis-records-indicator-hvac-fault ; (d) Markus, Hobson, Gunay, Bucking, Energy and Buildings 268, 2022 https://experts.mcmaster.ca/scholarly-works/2273507

**What it does:** (a) Compared one tool's flags on 49 rooftop units in two retail buildings with site inspection. (b) Did the same across six FDD providers. (c) Aggregates AFDD records from thousands of buildings, acknowledging false positives and negatives and planning manual inspections to estimate bias. (d) Showed 11 operations professionals their own portfolio's analytics.

**Evidence of effect:** (a) Three error types seen: faults reported that were absent, faults present but unreported, and present faults outside the tool's scope. In one case all 27 CO2 sensors were classified as faulted although inspection found no CO2 sensors installed in one building. Counts of false positives and misses are not on the page; authors say 49 RTUs from one tool cannot support generalization but suggest some FDD results are more reliable than others. (b) False positives and negatives exist but field results and FDD fault conditions are in "good agreement" (no rates on the page). (c) No rates in the abstract. (d) Only 2 of 11 interviewees said they would make controls changes in response.

**What it needs:** Site visits to verify a sample; vendor data sharing; for operator studies, access to practitioners.

**Failure modes / caveats:** Small samples; inspection is itself imperfect; none of the pages I read give precision or false-alarm rates.

**Read status:** ABSTRACT_ONLY for all four.

**Relevance to us [INFERENCE]:** Two takeaways: keep an explicit "other / not modelled" outcome and score it, and add input-integrity checks (flagging faults on instruments that do not exist is a data/documentation failure, not an equipment fault). The operator result suggests acceptance risk sits alongside accuracy.

---

## Item 9. Add an explicit false-alarm mitigation layer after seeing field false alarms

**Technique:** After initial field data produced false alarms, add a mitigation algorithm that suppresses them while preserving detection.

**Field and source:** Residential HVAC. Choi, Yoon, Im, Jung, Kolar, Dyer, Choi, "Field-based AFDD for refrigerant undercharge in residential HVAC systems: enhancing reliability through false alarm mitigation," Energy and Buildings 363:117582, 2026. https://impact.ornl.gov/en/publications/field-based-afdd-for-refrigerant-undercharge-in-residential-hvac-/ and https://www.osti.gov/pages/biblio/3364708-field-based-afdd-refrigerant-undercharge-residential-hvac-systems-enhancing-reliability-through-false-alarm-mitigation . Related lab-and-field RTU study: Wang, Gorbounov et al., Purdue conference 2016 https://docs.lib.purdue.edu/iracc/1590 and https://iifiir.org/en/fridoc/lab-and-field-evaluation-of-fault-detection-and-diagnostics-for-32217

**What it does:** Compares a rule-based detector with two ML detectors (decision tree, k-nearest neighbours) on actual building data using a minimal feature set. Both families first produced false alarms; a mitigation step was added.

**Evidence of effect:** Both approaches detected undercharge of 30% or more. After mitigation the false-alarm rate was 0% for ML and 0% (ORNL page) or 0.6% (OSTI page) for rule-based; the two pages I read disagree slightly, so treat as under 1%. The rule-based method started worse than ML but became comparable after mitigation. Pre-mitigation false-alarm rates, dataset size, and the mitigation mechanism are not on either page. In the Purdue/UTRC RTU work, the lab showed high-confidence detection with a low false-alarm rate, and four RTUs at two Florida sites were monitored with manually injected faults detected above a preset threshold (example 10% COP degradation); no numbers on the page.

**What it needs:** Real field data from the target equipment class, including fault-free periods to expose false alarms.

**Failure modes / caveats:** Small field dataset, one fault type; mitigation may cost sensitivity for small faults (the study reports detection for 30% or larger undercharge).

**Read status:** ABSTRACT_ONLY.

**Relevance to us [INFERENCE]:** Evidence that a post-hoc suppression layer can bring false alarms near zero in field data, but only with fault-free field data to find them; for us, early pilot visits where the tool's confident answer was wrong are the equivalent training signal.

---

## Item 10. Fuse expert-built structure with sparse service-log data (fusion learning)

**Technique:** Extract a causal structure and cause frequencies from free-text maintenance logs with a human-in-the-loop tagging method, merge it with a sensor-learned network, and estimate parameters from both.

**Field and source:** Industrial equipment (UPS units in an IT department). "Fusion-Learning of Bayesian Network Models for Fault Diagnostics," PMC8622961 (venue and year not shown in what I retrieved). https://pmc.ncbi.nlm.nih.gov/articles/PMC8622961/

**What it does:** Experts tag a subset of incident rows; tags are extended to the rest over three iterations; tags map to symptom, cause, and link categories producing a text-derived graph. A sensor-based graph is learned with the text edges as constraints; the final graph is the union and parameters come from both.

**Evidence of effect:** 733 raw incident rows over about three years; experts fully tagged 421; 429 rows remained after discarding non-diagnostic entries; tagging took about 20 minutes per row. Sensor-only graph had 2 edges (6 variables); text graph 41 edges (38 variables); fused 43 edges. For the symptom "unable to set thresholds," the sensor-only model attributed 63.6% to a disconnected sensor, whereas the fused model added a faulty management card (9.1%) and software issues (27.3%); the authors estimate relying on sensors alone would misdiagnose 36.4% of the time. Unifying inconsistent tags changed the estimated probability of a high-temperature alarm from 4/62 (0.065) to 40/62 (0.645).

**What it needs:** A few hundred logged incidents with causes recorded, domain experts for tagging (about 20 minutes per row), and sensor data aligned by timestamp.

**Failure modes / caveats:** Single case; no predictive accuracy or cross-validation on the fused model; assumes logs are accurate; only causes recorded in logs can be modelled; only six sensor faults quantified; class imbalance from rare failures.

**Read status:** FULL_TEXT (last ~6,000 characters of the page not read).

**Relevance to us [INFERENCE]:** About 400 tagged service records were enough to build structure and rough cause frequencies, which is within our "tens to a few hundred visits" horizon; but the 10-fold swing caused by tag coding shows cause-frequency estimates can be dominated by how causes are named, so a fixed cause taxonomy should be agreed before collecting.

---

## Item 11. Decision-theoretic troubleshooters built from elicited probabilities and updated with resolved cases

**Technique:** Bayesian-network troubleshooting that recommends the next question or repair by expected cost, with priors elicited from experts and counts updated as cases are resolved.

**Field and source:** Printer support (Microsoft, HP/Dezide) and heavy trucks (Scania with Linköping). Heckerman, Breese, Rommelse, "Decision-Theoretic Troubleshooting," CACM 1995 https://www.microsoft.com/en-us/research/publication/decision-theoretic-troubleshooting/ ; Skaanning, Jensen, Kjærulff, "Printer Troubleshooting Using Bayesian Networks," 2000 https://vbn.aau.dk/en/publications/printer-troubleshooting-using-bayesian-networks (metadata only) and Skaanning, ERCIM News 56, 2004 https://www.ercim.eu/publication/Ercim_News/enw56/skaaning.html ; Pernestål thesis 2009 and Warnquist thesis 2015 (Linköping; via search summaries); Prytz et al., Engineering Applications of AI 41:139-150, 2015 https://mw.hh.se/caisr/index.php?oldid=2101

**What it does:** Heckerman et al. use a special-structure BN of issues, causes, and symptoms, with Dirichlet distributions assessed at knowledge-acquisition time; resolved cases update probabilities and add variables, so the system adapts to its user population, and a pilot deployment is reported. The Dezide/HP line has field experts author the knowledge base and aims at minimum expected steps and cost. Linköping/Scania work (via search summaries) built BN troubleshooters for truck subsystems, noting that faults are rare and data scarce, and developed ways to combine training data with expert knowledge. Prytz et al. mined workshop records and logged vehicle data.

**Evidence of effect:** No quantitative field accuracy or cost-savings numbers on any page I could read. The ERCIM article makes no quantitative claims and says tuning from field data is future research. Prytz et al. report that the data sources had problems because they were not designed for data mining, that machine-selected features beat expert-chosen features, and that the approach could generate profit (no numbers). My searches found no study that varies expert-elicited probabilities and measures how diagnostic accuracy changes against field-updated parameters.

**What it needs:** Expert elicitation sessions, a case database with confirmed repair outcomes, and an update procedure (Dirichlet counts).

**Failure modes / caveats:** The 1995 style assumes causes and actions map one-to-one and uses one-step lookahead (per a search-result critique, not verified); repairs change system state, so static BNs need special handling (per a Linköping paper summary); workshop records are noisy.

**Read status:** Heckerman: ABSTRACT_ONLY; Skaanning 2000: metadata only; ERCIM: FULL_TEXT; Prytz: ABSTRACT_ONLY; Pernestål and Warnquist: SNIPPET.

**Relevance to us [INFERENCE]:** This is the closest published design to our engine, and the absence of published field-accuracy numbers (elicited versus updated) is itself the finding: there is no outside benchmark for how much updating helps, so our pilot would generate it. The Dirichlet-count design is a ready mechanism for the cause-frequency update that you found most valuable.

---

## Item 12. Technician-collected data has its own error rate; fix with input checks and training

**Technique:** Audit a year of field-technician data from a diagnostic app, detect misuse, add real-time user-error filters, and adjust training.

**Field and source:** Residential HVAC service. DOE/NREL/Southface project "Optimizing residential HVAC systems: evaluating how usage of smart diagnostic tools ..." https://www.energy.gov/eere/buildings/optimizing-residential-hvac-systems-evaluating-how-usage-smart-diagnostic-tools (report PDF at nrel.gov/docs/fy24osti/88387.pdf not read)

**What it does:** Analyzed 12 months of measureQuick app data from business-as-usual installations and tune-ups. Found errors in how technicians used the app and Bluetooth probes; built user-error detection filters that the app owner added to later versions; the filters warn technicians of likely mistakes such as incorrect probe placement before a performance snapshot is taken. Technician training also changed.

**Evidence of effect:** The page gives no numbers (no error fraction, no before/after). Qualitatively confirms that technician-entered or technician-measured readings have a real error rate and that a vendor responded with built-in checks.

**What it needs:** App data logs, someone to audit them, and the ability to ship software changes.

**Failure modes / caveats:** No quantification on the page; one product and one fault domain; vendor claims such as large callback reductions in case studies (SNIPPET, unverified) were not used.

**Read status:** ABSTRACT_ONLY (short project page).

**Relevance to us [INFERENCE]:** Supports modelling check-reading error explicitly (soft evidence) rather than treating a technician's reading as truth, and suggests the cheapest early mitigation is an in-tool plausibility prompt before a reading is accepted.

---

## Item 13. Occupant feedback as symptom evidence in a diagnostic Bayesian network

**Technique:** Treat comfort votes and window/radiator actions as additional symptoms and as possible "control faults" in a diagnostic BN, comparing diagnosis with three information levels.

**Field and source:** Building HVAC. Human-informed whole-building FDD, REHVA Journal article https://www.rehva.eu/rehva-journal/chapter/human-informed-building-automation-enhanced-whole-building-system-fdd ; a related 2025 BuildSys poster (Mosteiro-Romero, Upasani, Itard) known only from a search summary.

**What it does:** Delft seven-floor office, 15 participants reporting comfort via a smartphone app in September-October 2024 plus office sensors every 5 minutes. Case 1: building management data only; Case 2: plus office sensors; Case 3: plus self-reported comfort and window/radiator behaviour. The model reasons about malfunction versus occupant action.

**Evidence of effect:** Case 1 attributed CO2 symptoms to the CO2 sensors and humidity symptoms to AHU operation; Case 2 confirmed incorrect CO2 readings and suggested occupant controls could explain humidity; Case 3 found window operation the most likely explanation for unmet thermal preference. No accuracy metrics, no validation of feedback against ground truth, and the reliability of occupant reports is not quantified. Authors say continuous self-reporting is unrealistic because of survey fatigue and that baselines relying on expert knowledge and documentation may be outdated.

**What it needs:** Occupant reporting channel, extra sensors, expert-defined baselines.

**Failure modes / caveats:** 15 participants, one building, two months; hedged interpretation; the paper does not say how conditional probabilities were obtained.

**Read status:** FULL_TEXT (journal-style article).

**Relevance to us [INFERENCE]:** The one building-diagnostic example that uses occupants as evidence gives no reliability number, so our simulated finding (soft evidence helps when tenants are unreliable) has no empirical counterpart here; the tenant-answer reliability measurement would be new data.

---

## Item 14. Hybrid physics-plus-data diagnosis (physics residuals as features)

**Technique:** Compute residuals against a simple nominal-behaviour model and feed them, with raw sensors and lagged features, into a classifier; or tune component physics models from commissioning-style tests.

**Field and source:** (a) University of Victoria doctoral oral-exam abstract (candidate named in the URL as Maryam Ahang) https://www.uvic.ca/graduatestudies/oral-exams/exam-candidates/data/maryam-ahang.php ; (b) Xu and Haves, "Field Testing of Component-Level Model-Based Fault Detection Methods for Mixing Boxes and VAV Fan Systems," LBNL-50678, ACEEE 2002 https://eta-publications.lbl.gov/bibcite/reference/24942 ; (c) leads from search summaries only: Fu et al. 2025 (Electronics, Southampton), Reddy chiller model work (ASHRAE RP-1139).

**What it does:** (a) Feature-level and ensemble fusion of sensors, lagged features, and physics residuals from lightweight nominal surrogate models, with conformal prediction for calibrated uncertainty. (b) SPARK equation-based component models, configured from design and manufacturer data and tuned with functional-test data, field-tested on a mixing-box and VAV fan system in an experimental facility and a commercial office.

**Evidence of effect:** (a) On a CSTR benchmark both fusion strategies gained about 3 points over data-only baselines (98.94% and 99.00%); on the Tennessee Eastman process the best hybrid reached 93.55% (single classifier) and 93.78% (stacking). The author notes accuracy and uncertainty calibration are separate properties. These are simulated benchmarks; the thesis's real heat-exchanger test (93.33% on unseen severe faults) belongs to a different method (a variational-autoencoder health index). (b) Models represented correct operation and detected several types of incorrect operation; no numbers on the page. (c) SNIPPET only, unverified: a hybrid physics-plus-neural-network prognostic reported 15% better accuracy and 20% less uncertainty than "traditional methods" on N-CMAPSS and a fuel rig; a chiller study estimated about 320 and 400 data points for model parameters to stabilize and noted lab-only demonstration for lack of field fault-free-and-faulty chiller data.

**What it needs:** A nominal-behaviour model per equipment class, test data to tune it, and a classifier layer.

**Failure modes / caveats:** The only effect size I could verify is about +3 points on simulated benchmarks; no field comparison of hybrid versus data-only against real faults was found.

**Read status:** (a) ABSTRACT_ONLY; (b) ABSTRACT_ONLY; (c) SNIPPET.

**Relevance to us [INFERENCE]:** Our engine already is physics-first; the evidence offered here suggests that residual-style features add little over a good model and that the larger practical value of physics is in building test scenarios (Item 7). I found no field-validated residual-learning result to cite, so I would not plan on one.

---

## Patterns across items

- **The honest drop is large.** Where sim-to-real or unit-held-out numbers exist they are 20-45 points: robot 96.8% sim vs 70% real (Item 2); bearing AUROC 100% leaky vs 63% leakage-free on CWRU, 99% vs 54% on Paderborn (Item 1). Our 0.76 vs 0.51 sits inside this range.
- **Adaptation recovers part, not all.** Unlabeled real data plus adaptation gave about +10 points (Item 2); a few days of normal target-building data cut prediction error from 0.267 to 0.041 against a 0.019 floor (Item 3). Both still left a gap, and neither was demonstrated on real faults.
- **Cheap target-site data beats labeled faults.** The things that helped most needed no confirmed faults: normal-operation data, unlabeled readings, fault-free periods to expose false alarms (Items 2, 3, 9).
- **Field verification finds categories of error that benchmarks hide:** flags on instruments that do not exist, faults the tool was never built to see, and operator inaction (Item 8: 2 of 11 would act). A tool needs an "other/out of scope" path and input-integrity checks.
- **Human and record quality are first-class error sources.** Technician app errors triggered input filters and retraining (Item 12); service logs were not designed for mining and a re-coding of tags moved one cause frequency from 0.065 to 0.645 (Items 10, 11).
- **The key comparison for us is unpublished.** I found no study measuring field accuracy of elicited versus data-updated probabilities in troubleshooting BNs (Item 11), and no reliability measurement for occupant reports (Item 13); published designs update counts from resolved cases but give no effect size.
- **Physics helps most in evaluation, least proven in diagnosis.** The best-supported use of physics-based models was generating randomized test scenarios and scoring protocols (Item 7); verified hybrid gains were about 3 points on simulated benchmarks (Item 14).
- **Seeded-fault data is labor-intensive and its signature fidelity is rarely checked.** The LBNL dataset's ground truth came from functional tests plus expert visual inspection, with essentially one simulated-versus-real comparison (Item 5).

---

## Sources I could not read (or only saw via search summaries)

Unreadable (PDF, binary returned; auto-saved by the tool and not opened):
- DXC'09 report (c3.ndc.nasa.gov DXC09_Competition_Final.pdf; ntrs 20100024257 PDF), DXC'11 report (DXC11.pdf), Kurtoglu et al. ADAPT benchmarking (PHM 2009).
- Warnquist, "Troubleshooting Trucks - Automated Planning and Diagnosis" (Linköping 2015 PDF), and Pernestål's 2009 thesis page (redirect then 404).
- DOE BTO 2021 peer-review slides on AFDD fault prevalence and test datasets/prioritization (PDF).
- Lessmeier et al., PHM Europe 2016 (Paderborn benchmark; the original artificial vs real damage accuracy numbers); arXiv 1612.06025 (building operator needs; abstract read only); arXiv 2007.01965 (transfer learning in PHM; read via ar5iv, qualitative only).
- NISTIR 6994 and 7365 (APAR/VPACC field tests), PNNL-14157 (WBD at FAA Denver), PNNL-24000 and PNNL-SA-166037 (SMDS RTU field tests), IEA Annex 34 final report (VTT S217) and technical synthesis.
- SCE/ETCC lab assessments of retrofit RTU FDD tools (behind a download form).

Blocked (403 or access denied): Processes 11(8):2323 (hybrid Bayesian network residual features for chillers, claimed +24.5% accuracy over single-type nodes in a search summary only); Fraunhofer nine-AHU residual-model study; Energies 15(15):5534 review; Southampton Electronics 2025 hybrid prognostics page; FlightGlobal NFF article; TAMU copy of Katipamula et al. field test results; Pritoni et al. (LBNL FDD market barriers, escholarship; seen only as a search summary: recommendations require technician action, causing delays).

Seen only as search summaries (SNIPPET, unverified, not relied on): avionics no-fault-found rates (reported around 20-50% of removals in older and secondary sources, e.g. 38% at one airline workshop in 1995); Henrion et al. (UAI 1996) finding that diagnosis with belief networks is insensitive to noise in probabilities (outside my area; a later study reportedly finds sensitivity when small probabilities are rounded to zero); vendor claims about technician callback reductions and false-positive ramp-down curves; DXC'09 Tier-2 false-positive table; Katipamula 2014 slides (9% of 503 RTUs at 181 sites maintained properly); Wang/Gorbounov DOE target (false alarm rate under 1%) which is a project goal, not a result.
