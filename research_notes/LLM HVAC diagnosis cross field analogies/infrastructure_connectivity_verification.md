# Cross-sector "records vs reality" connectivity/topology verification, and where LLMs/VLMs appear

*Evidence tags: (FT) = I read the full text (PDF extracted locally); (ABS) = abstract/landing page only; (SNIP) = search-result snippet only, NOT verified, treat as a lead. Vendor material is labelled. Dates: LLM/VLM items are 2023-2026 with year noted; statistical foundations any age. Today is 2026-09-23. WebSearch budget for the session ran out (200/200) mid-task, so several planned searches did not run; see Gaps in each section and the last section.*

---

## 1. Electric utilities: customer-to-transformer, meter-to-feeder, phase identification, GIS/connectivity-model errors

### Takeaway
The accepted method is purely statistical: correlate/cluster AMI (smart-meter) voltage time series to find meters whose voltage does not co-move with the transformer/phase the record says they belong to, then send a crew only to the flagged subset. Real-field accuracy is much lower than headline numbers (meter-to-transformer 65-89% in a utility demo; ~53% precision of flagged pairs in a 13-feeder field verification), field verification itself is only ~95% accurate, and no LLM does any of the core work (LLMs appear only in outage-ticket classification, NL-to-SQL, and synthetic feeder generation).

### Cited Findings

**Problem scale / motivation**
- Utility distribution models contain more errors than transmission models, especially low voltage; meter-to-service-transformer mapping errors arise from maintenance and record-keeping (FT) — [Blakely & Reno, Sandia, "Identifying Errors in Service Transformer Connections", SAND2019-13628C, 2019](https://www.osti.gov/servlets/purl/1643233)
- "Phasing errors are common with GIS data" (EPRI's T. Short; regression on AMI voltage + kWh, two circuits; accepted draft dated 2012-07-11, IEEE Trans. Smart Grid ~2013, year of final publication unverified) (FT) — [Short, EPRI](http://distributionhandbook.com/papers/ieee_smart_grid_tshort_AMI_for_phase_identification_accepted_draft_2012-07-11.pdf)
- Historically the only way to correct phasing/meter-to-transformer records was to send crews; SDG&E calls this expensive, slow, and a safety risk (live-wire contact, cumulative miles driven) (FT) — [SDG&E EPIC-3 Project 3 Module 2 final report, 31 Dec 2021](https://www.sdge.com/sites/default/files/EPIC-3%20Project%203-AMI-Module%202%20Final%20Project%20Report.pdf)
- JEA (Jacksonville) stated it will use AMI data plus engineering analysis to correct topology errors "rather than performing an expensive manual audit" of its 80,000+ distribution transformers (FT) — [DOE Voices of Experience: Leveraging AMI Networks and Data, Mar 2019](https://www.energy.gov/sites/default/files/2024-02/01-03-2019_doe-voe-leveraging-ami-networks-and-data-report_508_0.pdf)
- The same DOE report says AMI lets utilities "identify and correct errors without a truck roll" for GIS/connectivity models, but gives no accuracy numbers (FT) — same DOE VOE report.

**Method card 1: SDG&E EPIC-3 AMI phase-ID + meter-to-transformer (M2T) demo (utility R&D report, Dec 2021) (FT)**
- (1) Mapping: hypothesis = which of 6 phase groups (A,B,C,AB,BC,AC) / which transformer a meter belongs to; evidence = 2 years of AMI voltage (0.15 V precision, Oct 2018-Oct 2020); "probe" = field crew or Google Street View; no sequential stopping rule; cost = truck rolls + safety.
- (3) Evaluation: two real feeders, Feeder A 325 transformers / 5,173 meters, Feeder B 649 transformers / 2,393 meters; constraint of only 2 meters per transformer to limit AMI backhaul data.
- Results, external vendors (field verification = "truth"): Methodology A phase-ID 98% / 97%, M2T 82% / 79% (feeders A/B); Methodology B phase-ID 83% / 92%, M2T 65% / 89%; internal simple time-series clustering phase-ID 72.5% / 95.5% (phase "groups" only, single-phase L-N meters only). Meter-to-transformer was "less precise" than phase-ID; report does not recommend commercialization under the 2-meters-per-transformer constraint.
- Data attrition: for M2T, 1,658 raw meters -> 960 with results (42% dropped by invalid geo, single-meter transformers, wrong frequency, frozen periods, outliers) (Table 12).
- (4) Failure modes: field verification was NOT 100% accurate, "approximately 95%" per one vendor's analysis; there is "no industry standard" minimum accuracy, >95% "in general" considered acceptable; algorithm-based phase-ID "may never be acceptable when employee safety is involved"; many utilities will not update OMS/GIS from algorithm output alone because the process is "new and unproven"; ground truth was blind (field results withheld until after initial runs).
- Worked example of targeted field audits (their Table 1-2): 1,000 meters, utility records 50% wrong, field crews 95% accurate, model 90% accurate, assume when both wrong they agree with prob 1/3. Visit only meters where model and record DISAGREE (450+50+2/3*50 = ~533 meters instead of 1,000) -> records accuracy ~96%, above the 95% crew accuracy, with about half the visits. If model accuracy is 99% you still visit ~503 (because records are 50% wrong), and the report concludes that when model accuracy is "significantly greater" than field-verification accuracy, "the need for truck rolls is removed entirely" and model output should replace records. This is a simplified illustration, not a field result.
- "Virtual field verification": for 72 meters where the model disagreed with the field-verified label, Google Street View (GMSV) gave conclusive answers for 35 (Feeder A, overhead lines); in all 35 the model was right and the field-verified label was wrong (Methodology A; Part II).
- (2) LLM role: none.
- (5) Transfer: the "visit only disagreements between record-implied and evidence-implied hypothesis" rule, plus modelling crew/test error rate explicitly (a test with ~95% reliability can be worse than a well-calibrated model), plus a cheap remote verification tier (Street View) before rolling a truck.

**Method card 2: Voltage-correlation flagging of mislabeled transformers (Sandia, 2019) (FT)**
- (1) Mapping: hypothesis per transformer = "all customers on the record are truly under it"; evidence = pairwise Pearson correlation of normalized voltage differences (4-day sliding windows, median across windows); flag a transformer if any pairwise correlation is below a threshold; transformers with a single customer cannot be tested; output is a list of transformers for crews; correction is a separate, harder step.
- (3) Evaluation: synthetic, 1,379 residential customers / 581 transformers, 1 year at 1-min then 15-min, OpenDSS on EPRI Test Circuit 5, Pecan Street load shapes; 1% customers mislabeled (13 customers) up to larger fractions, injected noise; achieved 100% flag accuracy (0 FN, 0 FP) for thresholds ~0.5-0.78 under 1% mislabel and noise. Real: ~15 months of 15-min data from a NE-US feeder, NO ground-truth labels, proof of concept validated with Google Street View; correlations between customers on the same real transformer can be as low as 0.77.
- Literature accuracy quoted: K-means with correlation distance 80-90% ([7] in paper); linear-regression pairing validated on only 36 transformers; Luan et al. correlation method field-validated on a 700-customer feeder in Vancouver, Canada (Luan, Peng, Maras, Lo, IEEE Trans. Smart Grid 2015, vol. 6; [IEEE Xplore](https://ieeexplore.ieee.org/document/7098424/), abstract not retrieved).
- (4) Failure modes: threshold trades FN vs FP; the correction stage of correlation methods was found to inject NEW errors (assigning a mislabeled customer to a wrong transformer) and to be "not robust to increasing levels of mislabeled customers", which is why they only flag; regression pairing not robust to noise.
- (2) LLM role: none.
- (5) Transfer: separate DETECTION (flag suspect record) from CORRECTION (re-assign); a detector that "cannot add error to the record" is preferable for trust; per-record pairwise consistency statistic with a cost-tuned threshold.

**Method card 3: Power-band data segmentation (PBDS), 13 real feeders (NC State, 2022-2023 arXiv) (FT)**
- (1) Mapping: same correlation idea but only use voltage segments recorded in a low-power band ([0,2] kW, >=1 h), because voltage drop in service lines under high load destroys correlation between meters on the same transformer; two-stage transformer-meter pairing: flag by average PCC / top-2 PCC, remove false positives with PBDS, then GIS check, then crew.
- (3) Evaluation: 1 year of 15-min data, 3,961 customers on 13 real North Carolina feeders; utility engineers did field verification on ALL 13 feeders in two rounds (correct labels, rerun, check remaining flags).
- Results: stage-1 flags 3.4% (136/3,961) and 1.6% (64/3,961) of meters; PBDS cut false positives 117->14 (88.0%) and 58->17 (70.7%); overall the 2-stage pairing achieved "52.6% accuracy and a false positive rate of 47.4%" (i.e. about half of flagged pairs were real errors after field verification); Feeder 9 (multiple reconfigurations) had the most false positives; residual FPs were meters at far ends of secondaries. Threshold "can be selected a little higher or lower depending on the cost of field verification"; in second-round phase checks the FP rate rose sharply.
- (2) LLM role: none. Authors say manual verification is "costly", so utilities want periodic automated verification.
- (5) Transfer: condition the evidence on operating regimes where the coupling is actually observable (in HVAC: only use trend windows when the zone/valve/damper coupling is excited), and choose the flag threshold from crew cost vs error cost. Also expect roughly a 1-in-2 hit rate on a flagged list in the field.

**Method card 4: Spectral clustering phase-ID (Sandia, SAND2018-13196C, 2018) (FT)**
- (1) Spectral clustering on AMI voltage with sliding-window ensemble; deliberately does NOT use substation voltage or transformer-connection labels, since using topology labels "requires that all other information in the distribution models is correct".
- (3) One real primary feeder, ~1,000 customers, 15 months; ~91% of predicted phase labels match utility labels, ~9% differ; claims "validate or correct over 99%" of labels and ">94% reduction in error" among the ~9% predicted wrong. NO field ground truth: validated by transformer-consistency (all customers on a transformer should get the same phase) then Google Street View on a subset; authors admit that without field labels it cannot be "absolutely certain".
- (4) Limits: Street View unusable where trees/underground cables; no field truth.
- (5) Transfer: use structural self-consistency of the record graph (siblings under one parent must agree) as a label-free validation and as a way to avoid conditioning on possibly-wrong records.

**Other statistical work (abstract level)**
- Maximum marginal likelihood phase-connection estimation, linearized 3-phase power flow, binary least squares, robust to incomplete measurements and inaccurate feeder models; tested on radial and meshed circuits (Wang & Yu, 2019) (ABS) — [arXiv 1902.09686](https://arxiv.org/abs/1902.09686)
- Comparison of published LV phase-ID methods on public data: voltage beats power for same-accuracy-class meters, combining both improves, ensemble learning across campaigns (Hoogsteyn et al., 2022) (ABS) — [arXiv 2204.06372](https://arxiv.org/abs/2204.06372)
- Topology (Laplacian) + line-impedance identification from smart-meter data, motivated by grid models being "unavailable, incomplete or outdated"; numerical tests only on IEEE 13/37/69-bus feeders (Guo, Yuan, Wang, IEEE Trans. Power Systems, year unverified) (FT-partial) — [OSTI 1961212](https://www.osti.gov/pages/servlets/purl/1961212)
- Information-theoretic topology recovery: Chow-Liu maximum spanning tree on mutual information of voltages; recovery succeeds with 8-bit quantization or millivolt-level precision, degrades when sampling intervals exceed ~20 minutes or windows are short (Speckhard, Sci. Reports 16:20547, 2026) (ABS) — [arXiv 2505.11517](https://arxiv.org/abs/2505.11517)
- Transmission-side analogue: topology/breaker-status errors treated as hypotheses in state estimation: normalized Lagrange multipliers to find suspect switching devices, then hypothesis testing (some Bayesian, giving conditional probabilities of suspect-device status) (SNIP, unverified beyond search summary) — [IEEE 667350](https://ieeexplore.ieee.org/document/667350/); a Gaussian-process mean-zero hypothesis test for topology errors that does not rely on WLS convergence, simulation only (Wu, Cheng, Gou, ~2012) (ABS-level read) — [paper PDF](http://math.iit.edu/~mcheng8/pdf/sample5.pdf)
- Active/actuate-and-observe field tools exist for phase ID: handheld low-frequency (about 4-8 Hz) signal injectors plus clamp receivers that trace a phase through the network (vendor/industry pages) (SNIP, unverified) — [Industrial Monitor Direct overview](https://industrialmonitordirect.com/blogs/knowledgebase/distribution-system-phase-id-methods-and-equipment), [Megger DCI3](https://www.megger.com/en-us/knowledge-hub/one-tool-for-cable-phase-identification)

**LLM/VLM use in electric distribution (found so far)**
- ComEd Grid Analytics (Sept 2024 article): LLM outage-message classification (calls, voicemails, trouble reports, log files, tickets -> outage type/location/timeline), NL-to-query "data democratization", customer chatbots, document summarization; no numbers ("first results look very promising... some work still needs to be done"); explicitly human-reviewed; NOT GIS/asset/connectivity data quality (ABS-level fetch) — [Utility Analytics Institute, 11 Sep 2024](https://utilityanalytics.com/large-language-models-grid-analytics/)
- A 2025 power-systems LLM survey lists no distribution topology/GIS/asset-record verification application; it rates fault diagnosis/anomaly detection "Medium" maturity and cites hallucination and reliability as barriers to deployment in core operations (ABS-level fetch) — [arXiv 2512.13004](https://arxiv.org/html/2512.13004v1)
- Fine-tuned LLM + physics-guided framework GENERATES synthetic distribution feeder models from natural language (IEEE 13/33-bus references; Jul 2026); it generates, it does not verify records (ABS) — [arXiv 2607.07237](https://arxiv.org/abs/2607.07237)
- Other snippet-only leads, unverified: "Power Grid Model Generation Based on Tool-augmented LLM" (IEEE TPWRS), "LLM4DistReconfig" (arXiv 2501.14960) — generation/optimization, not verification (SNIP).

### Inferences
- The community treats "records vs reality" as an unsupervised/semi-supervised anomaly-detection problem on a sensor-derived similarity structure. It is the same shape as the HVAC problem (hypothesis = which parent owns a child; evidence = co-movement statistics; crew = probe).
- Utilities do NOT run sequential/active, information-gain-driven audits in the literature I found; the "which records get a crew" logic is (a) flag list from a thresholded statistic, (b) model-vs-record disagreement, (c) cost-based threshold choice. The user's EIG + stopping-threshold design is more principled than anything found in this sector, but the sector supplies realistic error-rate numbers and pitfalls to benchmark against.
- Honest performance expectations: mid-60s to high-80s % meter-to-transformer accuracy on real feeders, ~50% precision on flagged transformer-meter pairs, ~30-40% of meters unusable for data reasons; benchmarks with 100% accuracy are synthetic.
- Design lessons that transfer: separate detect from correct; model the probe's own error (95%-reliable crews); label-free structural consistency as validation; regime-conditioned evidence; cost-tuned thresholds; cheap remote verification tier before the expensive one; sibling-consistency constraints.
- The signal-injection tools are the electric analogue of the user's "actuate-and-observe" physical test.

### Gaps
- Real cost per truck roll: no citable number found (search budget exhausted).
- Luan et al. 2015 (the canonical GIS-connectivity paper) abstract/accuracy not retrieved (IEEE Xplore returned nothing; Semantic Scholar 429). Only Sandia's one-line description (700-customer Vancouver feeder field validation) is available.
- No utility-published sequential/adaptive audit design (EPRI/NREL/INL reports, PG&E/Duke/Ausgrid) found; EPRI GenAI/GIS search did not run.
- No evidence found of LLMs used for GIS attribute cleaning, work-order mining for connectivity corrections, or connectivity-model QA. Absence not proven, only not found in this pass.
- Vendor "grid connectivity" products (Landis+Gyr, Itron, Sensus/Xylem, Aclara etc.) not covered.

---

## 2. Water, gas, district energy: asset-record errors, hydraulic-model connectivity, valve status, leak localization, sensor placement

### Takeaway
Water research has the most direct formal analogue to the user's design (Bayesian model-class selection over candidate connectivity events; identifiability analysis before deploying measurements; sequential sensor relocation) and the strongest evidence for cost-aware active verification (Flint lead-line ActiveRemediation: importance-weighted active learning choosing WHICH homes to dig, with a cheap $250 probe tier vs $2,500-5,000 full excavation). Gas has a regulatory sampling regime (PHMSA 49 CFR 192.607) that hard-codes a verify-records-by-sampling stopping rule with 95% confidence. LLM roles in water are natural-language wrappers around EPANET; none verifies records.

### Cited Findings

**Method card 5: Flint ActiveRemediation (KDD 2018) (FT)**
- (1) Mapping: unknown label per home (lead/galvanized vs safe); records "incomplete or lost"; probe tiers = full excavation ($2,500-5,000) vs hydrovac inspection (as low as ~$250, but fails 20-25% of the time through pavement); evidence = predictive model on city records + water samples + observed materials; sequential protocol with a fixed budget; decision rules: greedy (highest predicted hazard), uniform random, epsilon-greedy, and Importance Weighted Active Learning (IWAL), which oversamples uncertain homes. Baseline data problem: only 36 verified points in summer 2016 (~250 by end of Phase One), heavily cherry-picked from three neighborhoods.
- (3) Evaluation: back-test on the 6,505 homes actually identified by FAST Start (through Sep 2017) + a larger simulated Flint, 25 simulated runs. Results: unnecessary replacement visits 18.8% (actual) -> 2.0% (proposed); mean hit rate 98.0% vs 81.2% actual; savings 10.7% per successful replacement ($621.7; ~$11M over 18,000 planned replacements, ~2,000-2,100 more homes). Greedy has the highest hydrovac hit rate (91%) and uniform the lowest (63%), yet IWAL, which targets homes with risk probability "near 70%", wins overall: "Higher HVI hit rate is not better; instead, it is the choice of which homes to explore".
- (4) Limits: cost model ignores crew travel time; finite-population end effect; results are simulation/back-test not a controlled deployment.
- (2) LLM role: none (2018). 
- Source: [Abernethy et al., ActiveRemediation, KDD'18](https://arxiv.org/abs/1806.10692)
- Real-world aftermath (news summary, ABS-level): with the model-guided approach hit rate ran ~70% overall in 2017 (>80% late 2017; 8,833 homes explored, 6,228 replaced); after the contractor stopped using the model in 2018 the hit rate fell to ~15% (10,531 explored, 1,567 lead); reasons included a heat-map PDF instead of the model, unanswered emails, and political pressure for citywide coverage; also records "neither wholly digitized nor wholly accurate" — [Route Fifty, Jan 2019](https://www.route-fifty.com/management/2019/01/artificial-intelligence-lead-flint/153911/)
- Follow-on audit (single-author independent-researcher preprint, Aug 2026, NOT peer reviewed): across 153 New York localities using predictive models to classify lead service lines, 75 (49%) record a single uniform material; 7 are contradicted by their own physical verification (6 beyond sampling explanation), including NYC boroughs; screening idea "zero variance flags; contradiction confirms" (ABS + FT skim) — [arXiv 2608.19922](https://arxiv.org/abs/2608.19922)

**Method card 6: Locating unknown partially/fully closed valves (Do, Simpson, Deuerlein, Piller, JWRPM 144(8), 2018)**
- (1) Mapping: hypothesis = unknown valve statuses/minor-loss settings that explain discrepancy between hydraulic model and real system; evidence = flows/heads at measurement points; three-stage inversion: local sensitivity analysis to find valves that CANNOT be localized by the available measurements, genetic algorithm + extended-period simulation for preliminary localization, Levenberg-Marquardt refinement. Abstract text from search snippet (SNIP); numbers of network/valves not retrieved — [ASCE](https://ascelibrary.org/doi/abs/10.1061/(ASCE)WR.1943-5452.0000958), [HAL](https://hal.inrae.fr/view/index/identifiant/hal-02607513)
- (5) Transfer: pre-test identifiability screen (which record errors could be distinguished with the sensors at hand vs need a physical test).

**Bayesian connectivity detection in water networks (SNIP, unverified, ScienceDirect blocked)**
- Hydraulic model classes defined as candidate connectivity events; connectivity detection framed as Bayesian model updating; most probable events maximize evidence/posterior; uses pipe flow-rate data; Transitional MCMC for model-class selection — [ScienceDirect PII S026689202030014X (2020, "stochastic framework... connectivity detection problems")](https://www.sciencedirect.com/science/article/abs/pii/S026689202030014X), [PII S0951832018310913 ("Bayesian model updating approach for detection-related problems in water distribution networks")](https://www.sciencedirect.com/science/article/abs/pii/S0951832018310913). Authors, journal, network sizes and accuracy not retrieved.

**Sequential/adaptive sensing for leak localization**
- Iterative scheme: EPANET sensitivity matrix (simulated vs measured pressure differences), n-1 fixed pressure sensors plus ONE relocatable sensor; first pass ranks candidate leak nodes, the mobile sensor is moved to the most probable location, second pass refines; no formal stopping rule (two passes evaluated). Evaluation on L-Town (782 nodes, 33 candidate sensor sites): 7,820 simulated runs (leak of 6.38 m3/h at every node x 10 random sensor placements) plus one real BattLeDIM leak (pipe p257), 30 random placements. Result: first relocation cut distance to the leak by 45-61%; with 3 sensors (2 fixed + 1 mobile) mean error ~180 m (BattLeDIM cut-off 300 m) and the true leak in the top ~12 ranked nodes; a second iteration helps only when 1-2 sensors are available; on the real leak with 3 sensors: average rank 13 and 260 m after the first iteration; localization is worse in parts of the network with sparse sensor sites or large pipes (FT) — [Cholewa et al., 2024](https://arxiv.org/abs/2406.19900)
- Context claims in that paper: only 10-20% of leaks are visible on the ground; acoustic localization reaches ~100-200 m on steel/cast iron, 20-100 m on plastic, so covering 100 km needs >1,000 listening points (FT, same paper).
- Sequential forward sensor selection using information theory / mutual information for leak localization exists (Sensors 2022) (SNIP) — [MDPI Sensors 22(2):443](https://www.mdpi.com/1424-8220/22/2/443).

**Gas: PHMSA records-vs-reality regime (49 CFR 192.607) (regulation, read via Cornell LII)**
- Where an operator lacks traceable, verifiable, complete (TVC) records, it must verify material properties in situ during excavations. Sample size rule: one excavation per mile rounded up (with a cap of 150 excavations for populations >150 miles per the fetched summary; paragraph (e)(2)(i)), populations defined by wall thickness, grade, manufacturing process, and manufacture/construction dates. If a test finds properties "not consistent with available information or existing expectations", the operator must run an "expanded sampling program" designed for at least 95% confidence that recorded properties are valid; NDT methods must be validated against destructive tests and "conservatively account for measurement inaccuracy". — [49 CFR 192.607](https://www.law.cornell.edu/cfr/text/49/192.607)
- Practice: verification piggybacks on "opportunistic digs" using in-situ NDT by qualified technicians; ILI tool algorithms may reduce dig needs; alternative sampling plans allowed if 95% confidence is shown (industry article, MISTRAS, Nov/Dec 2024; vendor-adjacent) — [Inspectioneering](https://inspectioneering.com/journal/2024-12-26/11366/in-situ-verification-of-pipeline-material-properties-maop-determination-and-en)
- A typical transmission pipeline has 4,000-4,500 discrete data points per mile to document (engineering firm article, Feb 2024, vendor-written) — [Plant Engineering/Dewberry](https://www.plantengineering.com/six-ways-to-understand-pipeline-tvc-right-from-the-start/); one TVC record-review project covered 3,200 miles of transmission pipe and was done by manual "feature assessment" of scanned documents, no AI mentioned (vendor, TRC, 2019) — [TRC](https://www.trccompanies.com/projects/gas-mega-rule-tvc/)
- (2) LLM role: none found for gas records. A 2026 "Pipeline-agent" LLM decision-support paper exists (SNIP; ScienceDirect 403, not read) — [S2667143326000429](https://www.sciencedirect.com/science/article/pii/S2667143326000429)

**LLM/VLM in water (2025-2026)**
- LLM-EPANET: RAG + multi-agent code generation over EPANET/WNTR; 56-81% overall accuracy, >90% on simpler queries, 69 curated test queries; benchmark on Net2/Anytown-type networks (Goldshtein, Perelman, Schuster, Ostfeld; arXiv Mar 2025, revised Feb 2026) (ABS) — [arXiv 2503.16191](https://arxiv.org/abs/2503.16191)
- WaterAdmin: bi-level agent, LLM does "community context abstraction" (demand context) above optimization-based pump/valve control; EPANET simulation only (Apr 2026) (ABS) — [arXiv 2604.10343](https://arxiv.org/abs/2604.10343)
- EPANET-Agentic (Water Research 2026): natural-language control of WNTR/EPANET simulations, human-in-the-loop (SNIP) — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0043135426001156)
- None of these verify network records or choose what to verify.

**District energy**: not covered (no source retrieved).

### Inferences
- Bayesian model-class selection for connectivity (water) is the closest published cousin of the user's categorical posterior over owners; the transferable extras are (i) identifiability analysis to say a priori which alternatives a given sensor set cannot separate, and (ii) sequential relocation of a scarce probe based on the first-pass posterior.
- Flint is the cleanest evidence that the right selection criterion is informativeness, not likelihood of mismatch: pick items with posterior near the decision boundary (p~0.7 there), keep an exploration fraction to avoid selection-biased training data, and use a cheap tiered probe (hydrovac vs excavation) with an explicit effective-cost-per-success metric (TotalCosts / successful finds).
- PHMSA supplies a regulatory template for a stopping rule and for "expand the sample when a test contradicts the record": stratify records into populations by provenance/era, sample a minimum per population, target a confidence level, and enlarge sampling on inconsistency. HVAC analogue: stratify documented connections by drawing set/renovation phase, expand verification when a test contradicts the drawing.
- Piggybacking verification on visits that happen anyway ("opportunistic digs") is a cost lever the HVAC planner could model (zero marginal travel cost when a technician is already in that room/AHU).
- LLMs in water are interface/context layers around a physical simulator, consistent with a "LLM proposes/explains, statistics decides" division of labor.
- The relocatable-sensor result quantifies the value of a second, targeted measurement: the first adaptive move captured most of the gain (45-61% error reduction), and extra iterations only mattered when sensing was very sparse, supporting a small-number-of-adaptive-probes design with a diminishing-returns stopping rule.

### Gaps
- Bayesian water connectivity paper's authors, N, and accuracy not retrieved (403). Do et al. case-study details not retrieved (HAL Anubis block).
- No source for water-utility GIS asset-record error rates (other than Flint/NY lead lines), hydrant-test or valve-exercise verification programs, DMA-boundary verification, or sewer records.
- District heating/cooling records verification: nothing found.
- Gas: no risk-based selection literature or numeric mismatch rates found (article did not give NDT accuracy or failure rates).

---

## 3. Process plants / P&ID: as-built vs as-designed, digitization, consistency checking

### Takeaway
The P&ID literature (2024-2026) is almost entirely about converting drawings into graphs (digitization) and querying them, not verifying them against the plant. Deep-learning graph extraction reaches roughly 75-84% AP/mAP on a public benchmark (real + synthetic diagrams); on two diagrams, a prompt-only multimodal LLM reaches only ~56-59% edge accuracy end-to-end (38-50% if decomposed without domain rules) and 74-81% edge accuracy once process design rules are supplied. No system found decides what to walk down next; no plant-walkdown/MOC-discrepancy paper was retrieved.

### Cited Findings
**Method card 7: Relationformer P&ID-to-graph + PID2Graph benchmark (DLR, arXiv Nov 2024, rev. Dec 2025, IEEE DSAA 2025) (FT)**
- (1) Mapping: image -> nodes (symbols) + edges (connections) jointly; no probe or stopping.
- (3) Evaluation: first public P&ID benchmark with graph-level ground truth (real + synthetic diagrams; Zenodo 14803338); node AP 83.63%, edge mAP 75.46%; >25% improvement in edge detection accuracy over a modular symbol-detection + line-detection baseline. (2) LLM role: none (authors note Llama 3.2 used only for English polishing). (4) Limits: transformer needs lots of data; real P&IDs are more complex than synthetic. — [arXiv 2411.13929](https://arxiv.org/abs/2411.13929)

**Method card 8: MLLM two-stage P&ID -> process graph (Imperial College, ESCAPE-36, Jun 2026; arXiv Jul 2026) (FT)**
- (1)+(2): Gemini-3.0-Pro, prompt-only, no fine-tuning; end-to-end vs decomposed "extract tags, then reconstruct topology" with a text file of chemical-engineering design rules and process overview. (3) Two ANSI-standard case studies, ten runs each. Nitrogen PSA plant: E2E total accuracy 68.56% (node 86.32%, edge 55.58%); decomposed + rules 88.78% (node 100%, edge 80.58%). Slime/off-gas plant: E2E 67.31% (edge 58.87%) -> decomposed + rules 85.21% (node 99.73%, edge 74.12%). Decomposition WITHOUT rules did not beat E2E (edge accuracy fell to 50.19% and 37.84%).
- (4) Limits: two diagrams; proprietary model confidentiality; motivating text says P&ID topology "could support automated consistency checking" (future, not done). — [arXiv 2607.19568](https://arxiv.org/abs/2607.19568)

**ChatP&ID (Alimin & Schweidtmann, Mar 2026; AIChE J. 2026) (FT)**
- LLM agent queries a knowledge graph built from DEXPI smart P&IDs (GraphRAG/PathRAG "locate-and-trace"); abstract claims +18% accuracy over raw images, -85% token cost vs ingesting smart P&ID files, GPT-5-mini + ContextRAG 91% accuracy at $0.004/task; evaluation set is only 19 QA pairs; one simple P&ID page needed >150,000 tokens when fed raw. It answers questions about the drawing; it does not compare drawing to plant. — [arXiv 2603.22528](https://arxiv.org/abs/2603.22528)

**VLM-as-judge for P&ID object detection (Siemens, Oct 2025; ICASSP 2026 submission) (FT)**
- Gemini 2.5 Flash / Gemma3 look for objects the detector missed; best prompt (grounding + text tags + bbox) F1 0.876 (P 0.833, R 0.924) for Gemini vs 0.815 for Gemma3; ~6M input tokens per pass through the dataset; used to guide a PaliGemma re-detection. This is quality control of digitization, not plant verification. — [arXiv 2510.03376](https://arxiv.org/abs/2510.03376)

**Other**
- P&ID Pilot: hybrid genetic algorithm + LLM to synthesize PFD topologies then an LLM agent converting PFDs to "validated" P&IDs with rule compliance and 100% execution success (Jul 2026; generation, not verification) (ABS) — [arXiv 2608.11220](https://arxiv.org/abs/2608.11220)
- Vendor P&ID recognition (Operon): "object detection and topology exploration", agentic workflow/chat features, no accuracy numbers, no consistency check vs as-built or 3D model (vendor) — [Operon](https://www.operonsolutions.com/en/docs/pid-recognition)

### Inferences
- The "LLM/VLM in process plants" story is document-to-structure extraction and Q&A. The reported best edge scores (Relationformer edge mAP 75.5%; prompt-only MLLM 74-81% edge accuracy even with domain rules, ~56-59% without) show even reading the DOCUMENT connectivity is unreliable, so any LLM-extracted "documented owner" in the HVAC pipeline should carry its own uncertainty rather than be treated as certain.
- Two transferable ideas: (i) decompose extraction from topology reasoning and inject domain rules (node accuracy ~100%, edge accuracy still the weak link), (ii) a second model as judge for "missed items" (F1 ~0.88) could be a cheap QA layer on the documented graph before verification starts.
- Nothing here addresses probing the physical plant or stopping rules.

### Gaps
- No source retrieved on plant walk-down practice, management-of-change discrepancy rates, as-built vs as-designed discrepancy percentages, laser-scan-to-P&ID/3D consistency, or AVEVA/Hexagon/Bentley products (search budget ran out before these).
- PID2Graph real-diagram dataset size not extracted (PDF table not readable).
- Digital-twin consistency literature not covered.

---

## 4. Construction / BIM: BIM-vs-as-built deviation detection and LLM/VLM roles

### Takeaway
As-built deviation detection is geometric (registered point cloud vs model, tolerance heat maps), not LLM-based; it can only see what is exposed, which matters for concealed HVAC. LLM/VLM work in this sector is about checking BIM/drawings against codes and regulations (2025-2026), with moderate reported accuracy and mostly semantic reasoning wrapped around a rule/geometry engine.

### Cited Findings
- Scan-vs-BIM workflow (vendor, CHECKTOBUILD): upload registered point cloud + BIM, align, evaluate each element for position/size/tolerance, output pass/fail per element type; stated accuracy "inherits" the scanner's absolute accuracy; includes MEP route verification "in built condition" (vendor claims, no benchmark numbers) — [CHECKTOBUILD](https://checktobuild.com/scan-vs-bim/)
- MEP reconstruction from LiDAR (2025): reported 89.74% of pipes and 80.31% of ducts within a 10 mm distance tolerance; another line reports precision 98.9%, recall 90.9%, F1 0.95 for unseen MEP component types (SNIP, unverified; ScienceDirect 403) — [S2352710225018984](https://www.sciencedirect.com/science/article/abs/pii/S2352710225018984)
- LLM-driven BIM code compliance: GPT/Claude/Gemini/Llama integrated with Revit to interpret codes, generate Python scripts, and run semi-automated checks; two case studies (single-family house, office); no accuracy numbers in abstract; a search snippet (unverified) adds that it works best on well-structured models with accurate room tags (Madireddy et al., Jun 2025) (ABS + SNIP) — [arXiv 2506.20551](https://arxiv.org/abs/2506.20551)
- SGR-BIM (Jun 2026): cross-modal knowledge graph aligning user intent, regulatory semantics and BIM geometry; 679 expert-validated fire-safety code queries, 84.3% accuracy (+8.6% over baseline); LLM handles semantics, a geometric reasoning layer handles geometry (ABS) — [arXiv 2606.12065](https://arxiv.org/abs/2606.12065)
- Door detection + LLM chain-of-thought to enumerate facilities against statutory counts on floor plans (Sep 2025) (ABS) — [arXiv 2509.17283](https://arxiv.org/abs/2509.17283)
- Active view selection: a 2026 Bayesian next-best-view paper chooses camera views to reduce uncertainty only where it matters for a downstream task (computer graphics, NOT construction verification) (ABS) — [arXiv 2605.05095](https://arxiv.org/abs/2605.05095)

### Inferences
- The as-built sector's core verification is passive/exhaustive scanning with tolerance checks; "what to verify next" appears only as next-best-view planning in robotics/graphics, which is conceptually the same objective as expected information gain but not connected to building records in anything I found.
- Concealed mechanical systems (above ceilings, in walls, in shafts) defeat scan-vs-BIM, so for HVAC the equivalent of a scan is indirect sensor evidence, which is the user's approach.
- LLM value here is reading codes/specs, i.e. the "documentation side"; deviation vs reality remains geometric.

### Gaps
- Not retrieved (search budget): foundational scan-vs-BIM literature (Bosché-style, progress monitoring), photo/VLM as-built comparison, RFI/submittal LLM work, drawing-vs-spec conflict detection, BIM handover accuracy studies for facility management. I have background familiarity with these but have not verified them here, so they are not asserted.
- The two ScienceDirect items are snippet-only.

---

## 5. Telecom outside plant, subsurface utilities (SUE), rail/airport (brief)

### Takeaway
Other sectors show the same pattern: inventory records are commonly 20-30% out of sync (vendor claim), reconciliation is tiered by cost, and the formal standard for tiered verification of buried-asset records is ASCE 38 subsurface utility engineering (records -> surface survey -> geophysics -> exposure). No LLM work retrieved for these.

### Cited Findings
- Telecom inventory reconciliation (vendor Prodapt, 2020): physical vs logical inventory "often 20-30% out of sync"; 30-40% of record issues are auto-fixable, the rest go to subject-matter-expert review via tickets; up to 80% of record issues attributed to manual field-service updates (vendor claims) — [Telecom Ramblings](https://www.telecomramblings.com/2020/03/accelerating-network-inventory-reconciliation-process-time-by-up-to-60-using-rpa/)
- Fiber "triage" vendor blog (May 2026) claims a 50% truck-roll reduction with no supporting data and no discrepancy rates or triage criteria (vendor marketing, unsupported) — [Sequential Tech](https://www.sequentialtech.com/blog/telecom-circuit-inventory-reconciliation/)
- Passive optical networks: search snippets say ONU-to-splitter/branch-fiber correspondence "often changes" and manual topology records are inaccurate, and there are patents on inferring ODN logical topology (SNIP, unverified; patents US 11405103, 11722217).
- ASCE 38 quality levels D (existing records) -> C (survey visible features and correlate with records) -> B (geophysical designating) -> A (exposure/"locating" by test holes; type, size, material, position). The FHWA-commissioned 1999 Purdue study of 71 projects estimated SUE saved 1.9% of construction cost, i.e. $4.62 per $1 spent; DelDOT moved from ad hoc test holes to designating first, then deciding whether to dig (FT) — [FHWA HIF-22-002 flyer](https://www.fhwa.dot.gov/utilities/pdf/hif22002.pdf)
- Rail/airport asset-register reconciliation: nothing retrieved.

### Inferences
- ASCE 38 is a ready-made vocabulary for the HVAC "test ladder": record (QL-D) -> trend/BMS correlation (QL-C/B analogue) -> actuate-and-observe -> physical duct trace (QL-A), with each rung having cost and reliability.
- Telecom's auto-fix vs manual-review split suggests a two-outcome triage: high-confidence posteriors update records without a visit; ambiguous ones queue for a technician.

### Gaps
- No independent (non-vendor) telecom outside-plant discrepancy rates; no LLM/VLM telecom-records work; rail/airport not covered.

---

## 6. Cross-cutting synthesis: (a) accepted non-LLM method, (b) next-action selection and stopping, (c) unreliable record/model, (d) LLM/VLM contribution

### Takeaway
(a) Correlation/clustering/regression/Bayesian model-selection on sensor data; (b) real sequential or cost-aware selection exists only in Flint's IWAL, water sensor relocation, and network-tomography experimental design, while utilities use thresholded flag lists and model-vs-record disagreement; the only formal stopping rule found is PHMSA's 95%-confidence sampling; (c) sectors handle unreliable records by not conditioning on them, validating by structural self-consistency, modelling the test error, and separating detection from correction; (d) LLM/VLM contribution to the core verification problem is essentially nil in the retrieved evidence; it is document parsing, code/spec reading, Q&A and simulator wrappers.

### Cited Findings
**(a) Accepted non-LLM methods and reported accuracies**
- Electric: voltage-correlation flagging; spectral/ensemble clustering; regression on voltage and kWh; MML phase estimation; Chow-Liu on mutual information; accuracies above (real field: 65-89% M2T, 72.5-98% phase-ID in SDG&E; ~53% precision of flagged pairs on 13 NC feeders; ~91% agreement with records on one ~1,000-customer feeder) — sources in Section 1.
- Water: Bayesian model updating for connectivity (SNIP); sensitivity + GA + LM for valves; EPANET-simulation leak localization with relocatable sensors — Section 2.
- Gas: statistical sampling with NDT and 95% confidence — [49 CFR 192.607](https://www.law.cornell.edu/cfr/text/49/192.607)
- Process plants: CNN/transformer graph extraction, 75-84% mAP — [arXiv 2411.13929](https://arxiv.org/abs/2411.13929)
- Construction: registered point-cloud vs model tolerance checks — vendor description above.

**(b) Next-action selection and stopping**
- Active/adaptive: ActiveRemediation IWAL (pool-based active learning with budget B, chooses homes near p~0.7, epsilon exploration variants) — [KDD'18](https://arxiv.org/abs/1806.10692); iterative sensor relocation — [arXiv 2406.19900](https://arxiv.org/abs/2406.19900); online experimental design for network tomography: "Opal" sequential probe allocation from optimal experimental design + MLE with regret guarantees, 13.64% better estimation accuracy than baseline on the Roofnet topology (Apr 2025; classical and quantum lossy networks) — [arXiv 2504.21549](https://arxiv.org/abs/2504.21549)
- Cost-aware thresholds: flag threshold chosen "depending on the cost of field verification" — [PBDS arXiv 2210.00155](https://arxiv.org/abs/2210.00155); effective cost per success = TotalCosts / successes in Flint — KDD'18; SDG&E's target-the-disagreements arithmetic — [SDG&E report](https://www.sdge.com/sites/default/files/EPIC-3%20Project%203-AMI-Module%202%20Final%20Project%20Report.pdf)
- Stopping: PHMSA 95%-confidence sampling with expansion on inconsistent findings; SDG&E states there is "no industry standard" accuracy cutoff and ~95% is "generally considered acceptable"; leak-relocation paper shows two iterations without a formal stopping criterion.
- Tiered probes: ASCE 38 QL-D to QL-A — [FHWA](https://www.fhwa.dot.gov/utilities/pdf/hif22002.pdf); hydrovac vs excavation; Street View vs crew.

**(c) Handling an unreliable record/model**
- Do not condition on record labels: spectral-clustering phase-ID uses no transformer labels because that "requires that all other information in the distribution models is correct" — [Sandia SAND2018-13196C](https://www.osti.gov/servlets/purl/1575156)
- Flag only, never auto-correct, so the method cannot inject errors — [Sandia SAND2019-13628C](https://www.osti.gov/servlets/purl/1643233)
- Treat field truth as noisy (~95%) and audit the audit with independent evidence (Street View overturned crew labels 35/35 conclusive cases) — SDG&E report.
- Population-level records sanity checks: uniform recorded values ("zero variance") as a flag, contradiction with own verification as confirmation (single-author preprint, 2026) — [arXiv 2608.19922](https://arxiv.org/abs/2608.19922)
- Records unavailable/outdated -> reconstruct topology from data alone (Laplacian reconstruction, Chow-Liu) — [OSTI 1961212](https://www.osti.gov/pages/servlets/purl/1961212), [arXiv 2505.11517](https://arxiv.org/abs/2505.11517)
- Transmission state estimation treats breaker/topology status as unknown constrained variables to be tested (SNIP) — [IEEE 667350](https://ieeexplore.ieee.org/document/667350/)

**(d) LLM/VLM contribution (all 2023-2026 items found)**
- Electric: outage-message classification/NL-to-query at ComEd (2024, no metrics) — [UAI](https://utilityanalytics.com/large-language-models-grid-analytics/); synthetic feeder generation (2026) — [arXiv 2607.07237](https://arxiv.org/abs/2607.07237); survey finds no distribution-topology use (2025) — [arXiv 2512.13004](https://arxiv.org/html/2512.13004v1)
- Water: LLM-EPANET 56-81% on 69 queries (2025) — [arXiv 2503.16191](https://arxiv.org/abs/2503.16191); WaterAdmin context abstraction (2026) — [arXiv 2604.10343](https://arxiv.org/abs/2604.10343)
- Process: MLLM P&ID digitization 68% -> 89% total accuracy with decomposition + rules on 2 diagrams (2026) — [arXiv 2607.19568](https://arxiv.org/abs/2607.19568); ChatP&ID 19 QA pairs (2026) — [arXiv 2603.22528](https://arxiv.org/abs/2603.22528); VLM judge F1 0.876 (2025) — [arXiv 2510.03376](https://arxiv.org/abs/2510.03376)
- Construction: LLM code compliance in Revit (2025) — [arXiv 2506.20551](https://arxiv.org/abs/2506.20551); SGR-BIM 84.3% on 679 queries (2026) — [arXiv 2606.12065](https://arxiv.org/abs/2606.12065)
- Utility survey caveat: hallucination/reliability "significant barriers" to LLMs in core operational roles — [arXiv 2512.13004](https://arxiv.org/html/2512.13004v1)

### Inferences
- What transfers to the HVAC documentation-mismatch system, technique by technique:
  1. Posterior over owner hypotheses + probe likelihood models: the water Bayesian model-class approach and the SDG&E confusion-matrix framing both support giving each test a calibrated error model (crew/test reliability ~95% is a realistic prior; do not treat outcomes as ground truth).
  2. Select by informativeness, not by highest mismatch probability (Flint IWAL; EIG is the principled form) and keep an exploration share so evaluation data are not selection-biased.
  3. Cost tiers and effective-cost-per-confirmed-finding as the comparison metric (Flint), with tiers analogous to ASCE 38 and Street View before truck roll.
  4. Stopping: a posterior-confidence threshold is the Bayesian analogue of PHMSA's 95%-confidence sampling; add "expand sampling within the provenance population on contradiction" as a policy.
  5. Population structure: stratify documented connections by provenance (drawing set, renovation phase, contractor) since record errors cluster; flag suspiciously uniform documentation.
  6. Detect vs correct separation and sibling-consistency constraints (transformer siblings must share a phase; VAVs under one AHU must share supply-air behavior).
  7. Regime-conditioned evidence and resolution checks (power-band segmentation; 20-minute sampling degradation; 8-bit voltage precision) map to trend interval and sensor resolution requirements per test.
  8. Identifiability screening before dispatch (valve-status paper): tell the planner which hypotheses the current sensors cannot separate, so a physical test is truly needed.
  9. Expect coverage loss: 30-40% of meters unusable for data reasons; single-child parents cannot be tested by sibling correlation.
  10. Report metrics that count flagged-list precision (about 1 in 2 true errors in the NC field study) because "accuracy" on synthetic data is misleading.
- LLM roles that are defensible in this pipeline, based on analogues: parsing/normalizing documentation into candidate-owner graphs (with uncertainty; P&ID edge accuracy ~55-81%), judge/QA for missed items (VLM-judge F1 ~0.88), natural-language interface over the simulator/posterior (LLM-EPANET, ChatP&ID). No analogue supports an LLM choosing the next test or judging mismatch.

### Gaps
- The instruction to find how utilities decide which records get a crew found only algorithm-side rules; no operational policy documents (crew scheduling, audit sampling plans) were found.
- No quantified truck-roll costs in any sector except Flint probe costs ($250 hydrovac; $2,500-5,000 excavation; $5,000 replacement) and the vague safety/cost statements in SDG&E's report.
- Coverage limits caused by the 200-search cap: P&ID walkdown/MOC, scan-vs-BIM literature, VLM as-built comparison, RFI/LLM construction, telecom independent studies, rail/airport, district energy, EPRI/NREL utility reports, vendor connectivity analytics, gas LLM, and Luan 2015 numbers remain unresearched or unverified. A parent agent can re-run these if the budget (CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION) is raised.
- Reliability note: WebFetch returned model-generated summaries for HTML/abstract pages (possible small errors); numbers marked (FT) were re-read from locally extracted PDF text, numbers marked (ABS)/(SNIP) should be spot-checked before publication. The Route Fifty and NY-audit figures in particular should be double-checked.
- Unresolved discrepancy: Flint hit-rate figures differ by source (KDD back-test mean 81.2% "actual"; Route Fifty ~70% overall in 2017 and >80% late 2017; a BlueConduit-related snippet says 15% -> 81%).
