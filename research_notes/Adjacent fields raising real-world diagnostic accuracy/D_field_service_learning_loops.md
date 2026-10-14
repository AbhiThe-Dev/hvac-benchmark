# Area D: Field-service and technical-support troubleshooting systems and their learning loops

Compiled 2026-10-10. Tools used: WebSearch and WebFetch only. Read status per item is one of FULL_TEXT, ABSTRACT_ONLY, SNIPPET (definitions in the brief). Everything marked `[INFERENCE]` is my own reading for our hot-water tool, not a claim of the source.

## Headline finding before the items

I found **no published learning curve** (diagnostic accuracy as a function of the number of field cases) for a deployed field-service troubleshooter, and **no quantitative before/after number for any "learns from resolved cases" loop** in what I could open. Where the loops are described (Microsoft, HP/Aalborg, Cummins, Bosch, BAE, Honeywell), they are described as designs, patents or forecasts. The numbers that do exist concern (a) how unreliable the raw labels are, (b) how much cleaning the logs need, (c) vendor claims with no baseline, and (d) one retrieval system with a measured score. Sobering, but it is itself a finding.

---

## 1. Dirichlet-prior troubleshooting networks that update from resolved cases (Microsoft)

**Technique:** Expert-assessed Dirichlet priors on a bipartite issue/cause/symptom Bayesian network, expected-repair-cost action selection, and probability updating as cases are resolved.

**Field and source:** Consumer/product support (printing, Windows). Heckerman, Breese, Rommelse, "Decision-Theoretic Troubleshooting", Communications of the ACM 38(3), 1995 (https://www.microsoft.com/en-us/research/publication/decision-theoretic-troubleshooting/). Breese and Heckerman, "Decision-Theoretic Case-Based Reasoning" (AI&Stats workshop, 1995; https://proceedings.mlr.press/r0/breese95a.html). Breese and Heckerman, UAI 1996, "A Framework for Repair and Experiment" (https://arxiv.org/abs/1302.3563). J. Breese, post on Bayes-net diagnostics shipping in Windows 98 (https://web.engr.oregonstate.edu/~dambrobr/uai-archive-pre00/0025.html).

**What it does:** Each case is a small network; a relevant sub-network is pulled out of a large database during a session and used to recommend repairs and extra observations by expected cost. Dirichlet distributions are assessed at knowledge-acquisition time to express how strong each relationship is. As cases are resolved, the system records issues, causes, symptoms and repair outcomes, adds new variables, and updates the stored probabilities so inference adapts to the real user population. The 1996 paper adds repair actions and configuration changes as actions whose outcome can be observed.

**Evidence of effect:** No quantitative evidence found. The abstract says results from a pilot implementation and deployment are described, but I could not read them (the technical-report PDF came back as unreadable binary). The Breese post (FULL_TEXT) says 15 troubleshooters (printing, fonts, networking) shipped worldwide in Windows 98, that all models and content were created by the product-support group, and that the research group supplied only the inference and expected-cost code. No usage or call-reduction number is given.

**What it needs:** A support organisation willing to author the models (it did, at scale: product-support staff, not researchers), an assessment of prior strength per relationship, and a case-recording pipeline.

**Failure modes / caveats:** Update equations and the adaptation behaviour are not described in what I read, so I cannot say how fast priors yield to data. No evidence the updating was exercised long enough to measure.

**Read status:** ABSTRACT_ONLY for the CACM, AI&Stats and UAI papers; FULL_TEXT for the Breese post.

**Relevance to us `[INFERENCE]`:** The cleanest transplant is to write our 17-cause frequency vector and each check's reliability as Dirichlet/Beta priors with an explicit "equivalent sample size", so that tens of confirmed visits move them in a controlled way. Nothing here tells us what equivalent sample size to pick.

---

## 2. Expert probability elicitation protocol, and validation by simulated cases (printer troubleshooter patents; Dezide as a commercial product)

**Technique:** Bottom-up expert elicitation in percentages with a coarse ordinal scale for action reliability, then validating the finished model by generating cases from the model itself, having an expert accept or reject each, and replaying earlier accepted/failed cases as a regression suite.

**Field and source:** Printer support. Patent US 6,879,973 "Automated diagnosis of printer systems using Bayesian networks" (https://patents.google.com/patent/US6879973; same family as US 6,535,865; assignee and inventors not confirmed in the text I read, though search results associate the family with Skaanning, Jensen and Kjaerulff's printer work). Patent US 6,820,072 "Validation of probabilistic troubleshooters and diagnostic system" (https://patents.google.com/patent/US6820072B1/en). Dezide commercial page (https://www.dezide.com). The link between this printer work and Dezide (founder Claus Skaanning) rests on search summaries only (SNIPPET); I did not verify it in a document I opened.

**What it does:** Domain experts gave percentages instead of probabilities (10.0% rather than 0.1), estimated causes bottom-up starting with subcauses, one expert proposing and the group discussing until agreement. Action inaccuracy was put on a five-level scale (VL 0, L 2%, M 5%, H 10%, VH 20%). Costs combined time, risk, money and an "insult" factor that was rarely used and never fully defined. For validation, one engine draws a hidden true cause from the prior, a second engine recommends steps without knowing it, answers are simulated consistently with the cause, and an expert accepts or marks each sequence. A model is accepted if a preset number of sequences resolve acceptably, with binomial 95% and 99% bounds on failure probability; a history module replays recorded sequences against a revised model and flags each as similar, worse or better.

**Evidence of effect:** No calibration against real printer cases and no accuracy figures in what I read. Improvement from field data is described only as a future capability: logging "allows fine-tuning" of probabilities and costs, and measuring time from a step being suggested to being answered would give true time requirements. Dezide's page (FULL_TEXT) quotes Siemens Gamesa's diagnostics head saying technicians "can solve complex problems up to 70% faster" and claims IBA reached a 66% service-efficiency boost; no baseline, sample size or method is given, and the page does not describe self-learning or how repair outcomes are fed back. (An app-store listing says Dezide uses machine learning as repairs are tracked; I saw that only in a search summary, SNIPPET.)

**What it needs:** Several experts per model, time to agree, and a model that can generate cases from itself.

**Failure modes / caveats:** The validation loop checks the model against the expert's own intuition and against itself, not against reality; it detects inconsistencies and regressions, not miscalibration. The vendor figures are testimonials.

**Read status:** FULL_TEXT for both patents (first ~100k characters of each page; the remainder not read) and the Dezide page.

**Relevance to us `[INFERENCE]`:** We already have simulation, so the transferable parts are the regression-replay harness (every model revision is replayed on the fixed set of accepted/failed visits) and the binomial bound on failure rate for small test sets. It is also direct evidence that the industry norm is exactly our situation: expert-set numbers, no calibration, with real-case tuning deferred.

---

## 3. Maximum-likelihood update of an expert-built diagnostic network, gated by expert review of ranked supporting cases (BAE Systems)

**Technique:** Learn corrections to an expert-built Bayesian diagnostic model from failure case records, then show each proposed parameter change to a subject-matter expert together with the cases that drove it, and let the expert accept or reject.

**Field and source:** Aerospace/defence maintenance. US Patent 8,595,156 B2, Bovey and Senalp, BAE Systems, priority Oct 2008 (https://patents.google.com/patent/US8595156B2/en). Worked example is a pump tray; the text says it generalises to any multi-component system.

**What it does:** The initial network is built from a system model. A maximum-likelihood learning operation on case records adjusts failure-to-symptom conditional probabilities, failure priors and symptom-leak probabilities. Each case's contribution to each parameter change is measured by a likelihood gradient summed over epochs and used to rank the cases, which are shown as justification. A display threshold (example: a 40% parameter change) limits what the expert must look at.

**Evidence of effect:** None. The patent asserts the method can produce "highly accurate updated system models" but gives no accuracy or error figures. Cases record which symptoms were present or absent and which failures were confirmed present or absent; confirmation comes from a bench test after a suspect component is removed, and suspected failures later found absent are recorded as absent.

**What it needs:** A case store with symptom/failure presence-absence, bench-confirmed causes, and an expert with time to review changes.

**Failure modes / caveats:** The patent does not describe how technicians enter the confirmed cause, nor how many cases are needed. Confirmation by bench test is a luxury a hot-water call does not have.

**Read status:** FULL_TEXT (first ~100k of ~101k characters).

**Relevance to us `[INFERENCE]`:** A usable governance pattern for the first real data: do not let tens of visits silently overwrite simulation-derived priors; surface each proposed change with its supporting visits for the plumber or engineer to accept, and cap how far any single parameter can move.

---

## 4. Technician feedback capture designs and field-observable quality metrics (Bosch; Cummins)

**Technique:** Low-burden, delayed, one-tap outcome feedback; automatic capture of context; step-tracking with quality flags; dashboards on "solution found" rate and the position of the correct solution in the ranked list; change-control review before guidance is reordered.

**Field and source:** Automotive and engine service. US Patent 10,109,119 B2, Robert Bosch GmbH, "System and method for automotive diagnostic tool data collection and analysis" (https://patents.google.com/patent/US10109119B2/en). US Patent 9,384,453 B2, Cummins Inc., "Engine diagnostic system for high volume feedback processing" (https://patents.google.com/patent/US9384453B2/en).

**What it does:** Bosch: the tool asks the mechanic whether a suggested service record helped, only after a timeout set to the expected job duration (example: 8 hours); the question is yes/no or multiple choice, with an optional detailed form; VIN and codes are attached automatically; part SKUs can be scanned. Positive feedback raises a record's rank, negative lowers it, and a record with a preset number of negatives and few positives is dropped. Cummins: the system records written feedback and each session's steps as an audit trail; a quality filter flags sessions where steps were skipped, symptoms missing or verifications undocumented, and flagged trails are excluded from analysis; the dashboard reports solution-found rate and average position of the correct solution by location, technician and engine model; a solution-ordering module reorders fixes, and a change-control board approves, rejects or holds changes.

**Evidence of effect:** None. Neither patent reports response rates or accuracy improvement. Cummins gives only a hypothetical (a technician tries five solutions before the correct sixth).

**What it needs:** Integration into the diagnostic tool itself so context is captured automatically; an owner for the change-control step.

**Failure modes / caveats:** "Helped / did not help" is a weak, self-reported label, and a technician who skipped steps may give any answer. The Cummins quality filter is a design response to exactly that, but its effectiveness is not shown.

**Read status:** FULL_TEXT for both (first ~100k characters; Bosch page was ~175k characters, Cummins ~127k, remainder not read).

**Relevance to us `[INFERENCE]`:** Two cheap ideas: (i) ask the confirmed-cause question after the expected repair time, not at the door, and prefill everything the tool already knows; (ii) track "rank of the true cause in our list" and "checks to resolution" as field KPIs that can be measured even when the confirmed cause is only a weak label.

---

## 5. Case-based reasoning on legacy maintenance reports with expert cleaning (CASSIOPEE, CFM56-3 engines)

**Technique:** Build a case base from historical maintenance reports after experts remove cases with no or wrong diagnoses, and combine nearest-case retrieval with induced decision trees.

**Field and source:** Aircraft engine troubleshooting (Boeing 737 / Airbus A340 CFM56-3), built by AcknoSoft for a GE/SNECMA engineering firm. Secondary teaching page, Middlesex University (https://cwa.mdx.ac.uk/bis2040/lect8CBREx/cassiopee.html). Original (Heider, 1996) not opened.

**What it does:** Started from a legacy database of 23,000 engine maintenance reports built over 8 years; experienced engineers removed items with no diagnosis or a misdiagnosis, plus duplicates, leaving 16,000 cases of up to 100 features each. Retrieval of similar cases is used to shortcut the manual's diagnostic steps.

**Evidence of effect:** The page states diagnosis time was reduced by 50%. This is a secondhand figure with no baseline, comparison or source on the page. A search summary (SNIPPET) says the design goal was to halve diagnosis time; I could not tell whether 50% is a goal or a measurement. About 30% of the raw reports (7,000 of 23,000) were unusable as labelled cases.

**What it needs:** Years of structured reports, engineer time to clean them, and a regular channel for reports to reach the case base (the page says reports were collected by e-mail but does not say the case base was updated).

**Failure modes / caveats:** No accuracy, no case-growth evidence, and no evidence of maintenance of the case base after launch.

**Read status:** FULL_TEXT of the teaching page only; primary source not read.

**Relevance to us `[INFERENCE]`:** Plan for roughly a third of historical records being unusable as labels even when they come from a disciplined, regulated maintenance setting; a plumbing service company's work orders will probably be worse.

---

## 6. "Parts replaced" and closed-ticket codes as weak labels: how wrong they are

**Technique:** Treat replacement or repair events as failure labels (the default in fleet analytics), and recognise or correct their noise.

**Field and source:** (a) Aviation Today, "Special Report: Avoiding NFF", 2005, industry interviews (https://aviationtoday.com/2005/08/01/special-report-avoiding-nff). (b) SCANIA Component X dataset paper, arXiv 2401.15199 v2 (https://arxiv.org/html/2401.15199v2). (c) Viaduct blog on warranty data pitfalls (https://viaduct.ai/blog/the-top-3-pitfalls-to-avoid-when-analyzing-warranty-data), practitioner source.

**What it does / shows:** (a) A VP at Collins Aviation Services says about 35% of incoming repairs at his shops come back no-fault-found (NFF), and he estimates airline "mis-pulls" are up to two-thirds of NFFs. Some airlines say NFF plus "cannot duplicate" is 40 to 60% of reported component failures. An Air Wisconsin source says removing two units for one fix gives a 50-50 chance one returns NFF. A Delta analyst calls NFF a human-factors problem more than a technical one and describes a line "gotta change something" mentality, with parts replaced without following fault-isolation procedures. Mitigations named: a "hold" shelf (swap in a spare; if the fault recurs, the original was probably not the cause), tracking repeat-return serial numbers, and consolidating units. (b) The Scania dataset labels any component that was changed or marked repaired as failed, otherwise healthy: 2,272 of 23,550 training vehicles (about 9.6%) positive. The paper does not discuss replaced-versus-actually-faulty, and notes repairs are only visible if done in Scania's own network, so it restricts to vehicles with complete service history. (c) Warranty codes describe labour performed, not the vehicle's state; one root cause (broken belt, failed alternator, dead battery) can be coded as battery, alternator or belt replacement depending on how far a technician dug, and dealers vary more as the issue gets more complex.

**Evidence of effect:** No data on how much cleaner labels improve a model. The numbers are label-noise indicators: roughly 35% to 60% in avionics shops (interview-based, 2005, different domain).

**What it needs:** For better labels: a step that confirms the fix (fault gone after the repair, a swap-back test, or a "hold" period), and ideally one confirmed-cause field distinct from "part replaced".

**Failure modes / caveats:** Trade-press interviews, not measurements; avionics is not plumbing; the warranty source is a vendor blog with an interest in selling analysis.

**Read status:** FULL_TEXT for (a), (b) and (c).

**Relevance to us `[INFERENCE]`:** If a service partner's logs say "replaced recirculation pump" or "replaced mixing valve", expect a substantial share to be shotgun repairs or part-swaps that did not fix the complaint. Collect "did the complaint go away, and how long did it stay away" as part of the label.

---

## 7. Turning technician free text into labels: weak supervision, human-in-the-loop tagging, and what it costs in rows

**Technique:** Language-model embeddings with clustering and weak supervision to label sensor data from technicians' fault annotations; human-in-the-loop n-gram tagging to build a cause/symptom vocabulary and a Bayesian network from maintenance logs.

**Field and source:** Industrial condition monitoring and UPS fault diagnostics. Löwenmark et al., "Labelling of Annotated Condition Monitoring Data Through Technical Language Processing", PHM Society conference 2023 (https://papers.phmsociety.org/index.php/phmconf/article/view/3507) and "Technical Language Supervision for Intelligent Fault Diagnosis in Process Industry", arXiv 2112.07356 (https://arxiv.org/abs/2112.07356). Ademujimi and Prabhu, "Fusion-Learning of Bayesian Network Models for Fault Diagnostics", Sensors 2021 (https://pmc.ncbi.nlm.nih.gov/articles/PMC8622961/). Sexton, Hodkiewicz, Brundage, "Categorization Errors for Data Entry in Maintenance Work-Orders", PHM Society 2019 (https://papers.phmsociety.org/index.php/phmconf/article/view/790). Conte et al., HVAC work-order data quality, PHM Society Europe 2021 (https://papers.phmsociety.org/index.php/phme/article/view/2814).

**What it does:** Löwenmark labels unlabelled but annotated recordings from technician fault descriptions (SentenceBERT, k-means, weak supervision over aggregated features to cope with time-shift and class imbalance). Ademujimi and Prabhu tag a subset of incident-log text by hand with n-gram keywords, extend by automatic matching over three iterations, classify tags as symptom/cause/link, and merge a log-derived network with a sensor-derived one.

**Evidence of effect:** Löwenmark: F1 of 93 separating cable and sensor fault recordings from bearing-related ones (a coarse two-way split; the authors claim it is the first classification of field faults from unstructured annotations alone); no dataset size on the page. Ademujimi and Prabhu: 733 incident rows over about 3 years for about 300 UPS units; 421 fully manually tagged; 429 incidents remained after discarding "no fault found", "unknown resolution" and routine maintenance. Unifying synonymous tags changed the estimated share of "high temperature alarm" in a 62-event subset from 4/62 to 40/62. No classification accuracy for the fused model is reported (structural comparison against the authors' own reference graph only). Sexton et al. and Conte et al. (abstracts) say controlled vocabularies do not prevent entry errors when the schema does not fit how technicians talk, and that incomplete collection limits what HVAC work orders can support; no error rates on the pages.

**What it needs:** A few hundred log rows, a domain expert to build the tag vocabulary, and tolerance for losing about 40% of rows (733 to 429).

**Failure modes / caveats:** Cause frequencies estimated from raw logs can be off several-fold if vocabulary is fragmented; the Löwenmark split is coarse; no study I opened measured the accuracy of the resulting diagnostic model against an independent truth.

**Read status:** ABSTRACT_ONLY for Löwenmark (both), Sexton and Conte; FULL_TEXT for Ademujimi and Prabhu (first ~100k of ~106k characters).

**Relevance to us `[INFERENCE]`:** Cause-frequency priors are our most valuable unknown (+0.095 top-1 in simulation). This item shows that frequency estimates from partner work-order text depend heavily on synonym merging, so a short hand-built cause vocabulary with plumbers should precede any count of "how often is cause X".

---

## 8. Learning curves and misdiagnosis proxies from a real fab: module-level Bayesian networks (STMicroelectronics)

**Technique:** Learn Bayesian networks without supervision from contextual symptoms across production, process, equipment and maintenance databases, modelled at module rather than whole-equipment level.

**Field and source:** Semiconductor equipment maintenance. Abu-Samah, Shahzad, Zamai, Hubac, "Effective Maintenance by Reducing Failure-Cause Misdiagnosis in Semiconductor Industry (SI)", International Journal of Prognostics and Health Management 6(1), 2015 (https://papers.phmsociety.org/index.php/ijphm/article/view/2241).

**What it does:** From utilisation data of a major manufacturer the authors observe that both failure durations and the number of repair actions per failure had grown significantly, and read this as misdiagnosis. They propose two lines of defence (stop equipment only when it is suspected of causing drift; improve failure and cause identification after a stoppage) and test them as proofs of concept.

**Evidence of effect:** "Reliability and learning curves" indicate that modelling at module level gives 45% more accurate diagnosis than modelling the whole equipment. That is the only number on the abstract page; data sizes and the definition of accuracy are not given there.

**What it needs:** Joined-up databases across production, process, equipment and maintenance; per-module data.

**Failure modes / caveats:** Proof of concept, not a deployment; abstract only; "45% more accurate" is not interpretable without the baseline.

**Read status:** ABSTRACT_ONLY.

**Relevance to us `[INFERENCE]`:** "Repair actions per failure" and "failure duration" are available from any service partner's records without any confirmed cause, and can serve as before/after indicators of tool value; the module-level finding supports splitting our model by plant subsystem (storage, recirculation, mixing, distribution).

---

## 9. Active learning to choose which cases to label

**Technique:** Select the most informative unlabelled records for expert labelling and let semi-supervised learning cover the rest.

**Field and source:** Building HVAC fault diagnosis. Fan, Wu, Zhao, Mo, "Integrating active learning and semi-supervised learning for improved data-driven HVAC fault diagnosis performance", Applied Energy 356, 2024 (via https://ideas.repec.org/a/eee/appene/v356y2024ics0306261923017208.html). Also Andriani et al., IEOM 2021 (https://scholar.its.ac.id/en/publications/enabling-predictive-maintenance-using-machine-learning-in-industr/).

**What it does:** Five active-learning query strategies are compared for picking samples for expert labelling; self-training uses the unlabelled remainder.

**Evidence of effect:** Active learning reduces labelling cost by approximately 50% (Fan et al. abstract). Andriani et al. report about 99.85% for a final random forest but give no labelling-reduction number and no baseline on the page.

**What it needs:** A large unlabelled pool, a cheap model for scoring, and an expert who can label on demand.

**Failure modes / caveats:** I could not see which data the 50% was measured on, and neither source models the real cost of a label (an expert at a desk versus a technician returning to a site). A further 2026 RESS paper's claim that standard active learning is unsuitable in low-budget regimes appeared only in a search summary (SNIPPET); the page I tried to open for it did not load. I found no study that prices a technician's time per confirmed cause.

**Read status:** ABSTRACT_ONLY.

**Relevance to us `[INFERENCE]`:** Our scarce resource is visits with a trustworthy confirmed cause, not unlabelled records, so classical active learning applies only to choosing which visits or work orders to chase for confirmation (for example, visits where the tool was least certain or where it disagreed with the replaced part).

---

## 10. Peer-vetted tip sharing as the learning loop for service technicians (Xerox Eureka)

**Technique:** Let technicians author tips, have expert technician peers validate them, credit authors by name, and let the technician community, rather than a formal expert system, hold the knowledge.

**Field and source:** Photocopier field service. Whalen and Bobrow, "Communal knowledge sharing: the Eureka story", in Making Work Visible, Cambridge University Press, 2011 (https://www.cambridge.org/core/books/abs/making-work-visible/communal-knowledge-sharing/769CEB27F3DD35A6DDBAD4406A3FB136); SRI summary (https://sri.com/?p=85449). Background on Orr's ethnography, Talking About Machines, only via search summaries.

**What it does:** The project began as an expert system for field technicians; ethnography showed technicians invent fixes and share them informally, so the tool became a database of tips, each carrying the author's name and vetted by expert technicians who were the authors' peers.

**Evidence of effect:** Per the SRI page, Eureka debuted in 1994 and over about twelve years saved Xerox more than $100M in service costs. Reputation ("fame") was cited as the main motivator. No accuracy, repair-time or adoption-rate figure was on the pages I read.

**What it needs:** A technician community, peer validators with standing, visible credit, and light moderation.

**Failure modes / caveats:** The $100M has no stated baseline or method. Two further claims (that service-manual fault-isolation procedures were overly directive, and that attempts to formalise tacit knowledge into a database-driven expert system broke down) came only from search snippets, one from a mailing-list post, so I treat them as unverified (SNIPPET).

**Read status:** ABSTRACT_ONLY for the Cambridge chapter (no numbers); FULL_TEXT for the SRI page.

**Relevance to us `[INFERENCE]`:** For a tool whose users are plumbers and building engineers, adoption and label quality may depend more on peer credit and on the tool admitting that technicians sometimes know better than on tighter probabilities. A "technician's note" field that feeds model review is cheap.

---

## 11. Retrieval over past labelled incidents with temporal weighting (Microsoft RCACopilot)

**Technique:** Retrieve similar historical incidents, weighted by recency, together with their engineer-assigned root-cause categories, and predict a category for the new incident; collect diagnostic data automatically with handler scripts.

**Field and source:** Cloud/IT incident diagnosis. Chen et al., "Automatic Root Cause Analysis via Large Language Models for Cloud Incidents", arXiv 2305.15778 v4 (https://arxiv.org/abs/2305.15778; HTML at https://arxiv.org/html/2305.15778v4).

**What it does:** Experienced on-call engineers labelled each incident with a root-cause category, and these labels are ground truth. The system retrieves K=5 past incidents with a temporal decay factor of 0.3 and has an LLM predict the category and an explanation.

**Evidence of effect:** On 653 incidents from one Microsoft service over one year (75% train, 25% test), micro-F1 0.766 and macro-F1 0.533; baselines: FastText 0.076, XGBoost 0.022, fine-tuned GPT 0.103, GPT-4 embeddings 0.257. Summarising the collected diagnostic information raised scores from 0.689 / 0.510 to 0.766 / 0.533. 163 of 653 incidents (24.96%) belonged to root-cause categories not seen before; no accuracy is reported for them. The diagnostic-collection part has been in use at 30+ teams for over four years; the prediction part had been rolled out in one team for "several months", with only qualitative on-call feedback.

**What it needs:** A history of incidents with consistent engineer-assigned categories (hundreds), automated data collection, and an LLM.

**Failure modes / caveats:** Single service, single dataset; no learning curve with pool size; no per-novel-category result; macro-F1 far below micro-F1, indicating rare categories are mostly missed.

**Read status:** FULL_TEXT (HTML).

**Relevance to us `[INFERENCE]`:** A quarter of incidents being a never-seen category in one year of one cloud service is a useful order of magnitude for how big the "other" bucket may stay in a real plant population. The gap between micro and macro F1 is the pattern our rare causes would show.

---

## 12. Model-based troubleshooting seeded with "tribal knowledge" and a promise to learn (Honeywell AMOSS)

**Technique:** Model-derived diagnostics from the aircraft's own maintenance software, a cost-minimising troubleshooting algorithm, expert-supplied knowledge, and recording of outcomes so the system "learns".

**Field and source:** Airline line maintenance. Aviation Today, "Pulling aircraft diagnostics together digitally", April 2001 (https://www.aviationtoday.com/2001/04/01/pulling-aircraft-diagnostics-together-digitally/); and the 2005 "Avoiding NFF" report (item 6).

**What it does:** The diagnostics derive from Honeywell's Boeing 777 central-maintenance-computer software and use a cost-minimising troubleshooting algorithm; much of the knowledge came from senior maintenance-control staff ("tribal knowledge"); all interactions and outcomes are recorded so the system can learn from experience. It does not store repair history or legacy parts data, only pointers to other repositories.

**Evidence of effect:** None measured as of 2001. Ansett Australia forecast a 25% reduction in NFFs and a 10% reduction in maintenance-caused delays and cancellations; America West gave no figures; Honeywell spoke of performance guarantees. The 2005 article credits fault mapping on the 777 with a sharp NFF reduction (a Honeywell source, qualitative) and says AMOSS points technicians to the most probable fault. The article does not explain how field feedback updates the correlations, and a Honeywell speaker doubts a shared cross-operator database will happen because of sensitivity about maintenance records.

**What it needs:** Airline data access, trained maintenance-control staff, willingness to share records.

**Failure modes / caveats:** Forecasts, not results; vendor claims; no description of the learning mechanism; data silos block pooling.

**Read status:** FULL_TEXT for both articles.

**Relevance to us `[INFERENCE]`:** Closest published analogue to our design (model-derived probabilities, cost-minimising next check, expert-seeded) and it also had no field-measured accuracy at launch. Cross-company pooling of cases is likely to be a business problem before it is a technical one; a single partner's data is the realistic source.

---

## 13. Why diagnostic and fault-detection tools go unused in buildings, and what the interviews say

**Technique (negative result):** Documented barriers to adoption and acting on automated diagnostics in building HVAC.

**Field and source:** Andersen et al., "Barriers and drivers for implementation of automatic fault detection and diagnosis in buildings and HVAC systems: An outlook from industry experts", Energy and Buildings 303, 2024 (https://vbn.aau.dk/da/publications/barriers-and-drivers-for-implementation-of-automatic-fault-detect). Pritoni et al., "Market Barriers and Drivers for the Next Generation Fault Detection and Diagnostic Tools", ACEEE Summer Study 2022 (https://eta-publications.lbl.gov/publications/market-barriers-and-drivers-next). Trade article on the human element of FDD (https://facilitiesnet.com/buildingautomation/article.aspx?id=17350).

**What it does / shows:** Andersen et al. interviewed 29 experts from different HVAC company types and grouped barriers into five categories. Main findings: FDD does not sell well as a product, companies do not actively promote it, it is often seen as academic, the main bottlenecks are the fault-handling process and users' mindset, expert-rule systems remain the most common, and academic implementation studies are scarce because results are hard to validate under real operating conditions. Pritoni et al. note that technicians must act on FDD recommendations, causing delays and lost savings, and describe automatic correction deployed in four buildings; operators raised accountability and cybersecurity concerns. The trade article (anecdotal, no studies) says failing to involve operators early erodes trust and compares noisy FDD output to alarm fatigue.

**Evidence of effect:** No measured adoption rate or accuracy effect. The numbers are 29 interviews, 7 algorithms, 4 buildings.

**What it needs (what the sources suggest raises adoption):** Involving operators from design, repeated training, a defined process for who acts on a finding, and in some cases removing the human step.

**Failure modes / caveats:** Interview and abstract-level evidence; vendors' blogs on field-app adoption (workflow disruption, poor fit to connectivity and data-entry load, trust in own judgement) surfaced in search but are unsourced and I did not open them (SNIPPET only).

**Read status:** ABSTRACT_ONLY for the first two; FULL_TEXT for the trade article.

**Relevance to us `[INFERENCE]`:** Any plan to collect confirmed causes has to specify who records it, when, and what they get back; "tool recommended X, who acts?" is a recurring failure point, not the accuracy of X.

---

## 14. When the aid is wrong: operators following a failing fault-diagnosis aid (lab evidence)

**Technique (negative result):** Studies of fault-management support at three automation levels with periodic complete failure of the support.

**Field and source:** Lorenz, Di Nocera, Rottger, Parasuraman, "Automated fault-management in a simulated spaceflight micro-world", Aviation, Space, and Environmental Medicine 73(9), 2002 (https://ntrs.nasa.gov/citations/20040088120).

**What it does:** Operators used a fault-finding guide (low), an automated diagnosis and recovery advisory (medium) or automated diagnosis with approve/veto (high); 10% of trials had complete failure of the support.

**Evidence of effect:** Support improved diagnostic accuracy, shortened fault-identification time and reduced workload; no numbers on the page. When automation failed, identification times worsened more at the medium (advisory) level than at the high level, which the authors called unexpected. Related process-control studies (Bahner et al. 2008; Wickens et al. 2015) appeared only in search summaries and I did not open them (SNIPPET): they suggest operators keep following wrong recommendations and that conveying lower confidence helps.

**What it needs:** n/a (a caution).

**Failure modes / caveats:** Simulation with students or non-technicians; not building technicians; abstract only.

**Read status:** ABSTRACT_ONLY.

**Relevance to us `[INFERENCE]`:** Supports the shipped safety rule that the tool should state its confidence honestly and stay quiet or say "other" when unsure; a wrong-and-confident output costs more than slower help. It says nothing about the size of the effect for plumbers.

---

## Patterns across items

- **The honest state of the art is expert-seeded numbers plus a stated intention to learn.** Microsoft, HP/Aalborg, Honeywell AMOSS and Dezide all start from expert elicitation; the learning step is described as a design or a future capability, and I found no learning curve or before/after accuracy for any of them.
- **Label quality, not model class, is the visible bottleneck.** Parts-replaced labels are wrong a large share of the time in avionics (about 35% to 60% NFF/CND by interview), about 30% of CASSIOPEE's raw reports were removed, and about 40% of UPS log rows were unusable, while synonym fragmentation changed one cause's apparent share from 4/62 to 40/62. Frequency priors drawn from raw work orders are not safe `[INFERENCE]`.
- **Design for low-burden confirmation.** The patent designs converge on delayed (after the expected job time), one-tap, context-prefilled feedback, with a quality flag for sessions where the technician skipped steps. No response rates are reported anywhere I could read.
- **Field-observable proxies exist that do not need a confirmed cause:** rank of the correct solution, solution-found rate (Cummins), repair actions per failure and failure duration (STMicroelectronics), repeat returns. These can show whether a tool helps before a clean labelled set exists `[INFERENCE]`.
- **Model updates are governed, not automatic, in the designs that describe governance:** SME accept/reject with ranked supporting cases (BAE), a change-control board (Cummins), and a historical-case replay that marks revisions better/worse (HP-family validation patent).
- **Self-consistent validation is not field validation.** Simulated-case review confirms the model agrees with its authors; it cannot find miscalibration. This matches our own 0.92 to 0.69 experience `[INFERENCE]`.
- **Adoption is a social and process problem as much as an accuracy one:** peer-vetted, credited contributions (Eureka), a defined owner for acting on a finding (FDD interviews), and operator involvement. Vendor outcome claims (Dezide 70% faster; AMOSS forecasts) carry no baselines.
- **Novelty is persistent:** roughly a quarter of incidents in one cloud service-year had a never-seen root-cause category (RCACopilot), a reminder to keep "other" and "two-fault" alive in the posterior `[INFERENCE]`.

## Sources I could not read, or could read only in part

- Breese and Heckerman technical report with pilot results (Microsoft Research PDFs): returned as unreadable binary; the pilot numbers are therefore unknown.
- Skaanning, Jensen, Kjaerulff, "Printer Troubleshooting using Bayesian Networks" (IEA/AIE 2000) and the SACSO paper: not opened; only titles seen.
- arXiv 1301.3893 (knowledge acquisition tool for Bayesian-network troubleshooters): PDF came back unreadable.
- Linköping/Scania troubleshooting papers (Warnquist, Pernestål, Nyberg; Warnquist 2015 thesis; Pernestål 2009 thesis; Wettig et al., BMAW 2008 "A Bayesian approach to learning in fault isolation"): PDFs unreadable, abstract pages redirected or did not load. These are the most likely place for expert-prior-plus-field-data results on trucks; I could confirm only from search summaries that the theme exists (SNIPPET).
- Agosta et al. (Intel, Bayesian-network troubleshooting with refinement from cases): PDF unreadable; could not locate an abstract page.
- Compaq SMART/QUICKSOURCE (IAAI-92) and the AI Magazine CBR article: PDFs unreadable; the ">95% of calls" figure for SMART seen only in a search summary, not relied on.
- Shao et al., "Efficient Ticket Routing by Resolution Sequence Mining" (KDD 2008, IBM) and Sun et al. 2010: PDF unreadable; abstract pages carry no numbers.
- Heider 1996 CASSIOPEE and Cheetham and Watson 2006 review: not opened.
- Mercedes-Benz "Big Data Diagnosis" page (HTTP 403); DTIC "Bayesian Networks for Automated Equipment Diagnostic Support" (403); Cranfield NFF items (403); Whalen and Bobrow 2002 Eureka PDF and Orr's book (not opened); SAP blog on Eureka (403); HAL GPON-FTTH EM tutorial (bot-protection page); ScienceDirect page for Fan et al. (403); UNIST handle page (did not load).
- PubMed page for Wickens et al. 2015 (cookie wall); Bahner et al. 2008 not opened.
- Note on the fetch tool: for PDFs it returned as binary, the tool cached a copy automatically in its own results folder; I did not open, extract or use those cached files.
