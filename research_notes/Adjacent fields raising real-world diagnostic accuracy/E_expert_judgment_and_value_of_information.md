# Area E: structured expert judgment, value of information, and what to measure first

Brief followed: `brief.md` in this folder. Tools used: WebSearch and WebFetch only (plus one local Python calculation, item 14, clearly marked as mine).
Read-status key: `FULL_TEXT` = the passage with the number or claim was in what I retrieved; `ABSTRACT_ONLY` = abstract or record page; `SNIPPET` = search-result summary only.
Items marked `[INFERENCE]` are my own reading for our hot-water tool, not something a source says.

Housekeeping note: WebFetch automatically cached four PDF responses it could not parse (Cooke TU Delft database, a TU Delft repository file, two UAI/KER papers) into the harness tool-results folder under `.claude/projects/.../tool-results/`. I did not choose to save them, did not open them, and did not use them. All four are listed as unreadable below.

---

## 1. Cooke's Classical Model: seed-question weighting of experts

**Technique:** Score each expert on "seed" questions whose true answers are known to the analyst, then weight experts by calibration times informativeness when pooling their distributions on the target questions.

**Field and source:**
- Cooke RM, Goossens LLHJ (2008). "TU Delft expert judgment data base." *Reliability Engineering and System Safety* 93(5):657-674. https://pureportal.strath.ac.uk/en/publications/tu-delft-expert-judgment-data-base/
- Colson A, Cooke RM. "Cross validation for the classical model of structured expert judgment." *Reliability Engineering and System Safety* (year not shown on the page I read). https://pureportal.strath.ac.uk/en/publications/cross-validation-for-the-classical-model-of-structured-expert-jud/
- Colson A, Cooke RM (2018). "Expert Elicitation: Using the Classical Model to Validate Experts' Judgments." (page indicates *Review of Environmental Economics and Policy* 12(1); journal inferred by the page, verify). https://www.rff.org/publications/journal-articles/expert-elicitation-using-the-classical-model-to-validate-experts-judgments/

**What it does:** Experts answer calibration questions from their own field plus the real target questions. Each expert gets a statistical-accuracy score and an information score; their product sets the weight in a linear pool. Results are compared against a plain equal-weight pool.

**Evidence of effect:**
- 2008 database review: 45 expert panels under contract, nearly all with seed variables; the abstract says performance-based and equal-weight combinations were compared but gives no numbers.
- Update covering 33 professionally contracted studies (2006 to March 2015): fewer than one third of individual experts were statistically accurate. In-sample, performance weighting beat equal weighting in all but 1 of 33 studies.
- Out-of-sample (cross-validation, splitting the seed questions): performance weighting has lower statistical accuracy than equal weighting out-of-sample (a penalty that shrinks with more training questions; it reaches 75% of the equal-weight value when 80% of seeds train the weights), but about double the information once training uses at least 50% of the seeds. On the authors' Out-of-Sample Validity Index, performance weighting beat equal weighting in 26 of 33 studies (sign-test probability 0.001 as stated in the abstract).

**What it needs:** Seed questions with known answers that are plausibly representative of the target questions, a panel of several experts, and a facilitator. The abstract does not state how many seeds or experts are typical, so I do not report a figure.

**Failure modes / caveats:** Weights are estimated from a small number of noisy seed answers, so they are themselves uncertain; the out-of-sample accuracy penalty is real. The headline "performance beats equal" is strongest in-sample. Seeds from a different sub-domain may not transfer.

**Read status:** ABSTRACT_ONLY for all three (the Cooke and Goossens 2008 PDF came back unparseable).

**Relevance to us `[INFERENCE]`:** With only a handful of technicians to interview, performance weights would be very noisy; the out-of-sample penalty argues for equal weights plus discussion (item 2) as the default, and using seed-style questions mainly to show each technician how overconfident they are. The "fewer than one third calibrated" figure is a sober prior for how far to trust any single technician's cause-frequency numbers.

---

## 2. Structured group elicitation with discussion: IDEA protocol (and SHELF)

**Technique:** Experts give private estimates, see the group's, discuss reasons (not just numbers), re-estimate privately, then the analyst aggregates mathematically (IDEA = Investigate, Discuss, Estimate, Aggregate). SHELF is the related Sheffield framework that fits a group distribution to experts' elicited quantiles.

**Field and source:**
- Hemming V, et al. (2018). "Eliciting improved quantitative judgements using the IDEA protocol: A case study in natural resource management." *PLOS ONE* (DOI 10.1371/journal.pone.0198468; first author and title as I recall them, the page text I received had the data but no header). https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0198468
- Hemming V, Armstrong N, Burgman M, Hanea A (2020). "Improving expert forecasts in reliability: Application and evidence for structured elicitation protocols." *Quality and Reliability Engineering International* 36(2):623-641. https://spiral.imperial.ac.uk/handle/10044/1/75222
- Williams CJ, Wilson KJ, Wilson N (2020, rev. 2021). "A Comparison of Prior Elicitation Aggregation using the Classical Method and SHELF." arXiv:2001.11365 (related DOI 10.1111/rssa.12691). https://arxiv.org/abs/2001.11365
- SHELF home page, University of Sheffield. https://shelf.sites.sheffield.ac.uk/
- Soares M, Colson A, Bojke L, et al. (2024). "Recommendations on the Use of Structured Expert Elicitation Protocols for Healthcare Decision Making." *Value in Health* 27(11):1469-1478. https://www.ispor.org/heor-resources/good-practices/article/recommendations-on-the-use-of-structured-expert-elicitation-protocols-for-healthcare-decision-making

**What it does:** Discussion is meant to surface evidence individuals lack; anonymity before and after limits anchoring on the loudest person. Equal-weight averaging of the second-round numbers is the default aggregate.

**Evidence of effect:**
- Natural-resource case (305 invited, 101 consented, 76 completed round 1, 58 round 2; 14 questions; groups of 5-9): median group error 0.032 versus 0.042 for individuals (lower is better; a log-ratio error scale). Calibration of 80% intervals was 0.69 for both individuals and groups (nominal 0.80), so groups were more accurate but not better calibrated. Round 2: 36 of 44 individuals who revised improved accuracy (median gain 0.008); group calibration rose from about 0.69 to 0.77; informativeness did not change. All 58 pooled into one "super group" did no better than the average 5-9 member group.
- Defence reliability case study (IDEA combined with the Classical Model): average expert's 90% intervals contained the truth 36% of the time. Equal-weight aggregation plus a discussion phase with revised estimates improved calibration, accuracy and score; performance-weighted aggregation added precision and information. The page gives no further numbers.
- SHELF: in one clinical-trial elicitation, equal weights, the Classical Method and SHELF all outperformed individual experts on proper scoring rules, with SHELF best of the three (no numbers on the arXiv page). The SHELF site itself cites no performance evidence. The 2024 ISPOR report lists five protocols (SHELF, modified Delphi, Cooke, IDEA, MRC) and, in the text I could read, makes no quantitative recommendation.

**What it needs:** A facilitated session (can be remote), 5-10 experts, a few hours; for IDEA a round of private numbers before and after. SHELF has free R software.

**Failure modes / caveats:** The natural-resource study has no control group that re-estimated without feedback, so the gain cannot be cleanly attributed to discussion (the authors say so). Groups stayed under-calibrated (0.77 vs 0.80 nominal is close, but individuals sat at 0.69). The reliability paper is a single case. I found no head-to-head of SHELF versus IDEA versus Delphi.

**Read status:** PLOS ONE paper FULL_TEXT (first 100,000 of about 156,000 characters); Hemming 2020 ABSTRACT_ONLY (publisher page returned 403, repository page read); Williams et al. ABSTRACT_ONLY; SHELF site and ISPOR report page-level only.

**Relevance to us `[INFERENCE]`:** The cheap, evidenced part is aggregation of several technicians and one discussion round, not the elaborate weighting. If we interview building engineers about cause frequencies, doing it as a short two-round exercise (private numbers, discussion of why numbers differ, private revision) is the best-supported way to get a usable cause-frequency prior; expect it to remain somewhat overconfident, so widen it.

---

## 3. Seniority, reputation and self-rating do not predict who is accurate

**Technique (negative result):** Test the common shortcut of weighting experts by experience, publications or peer reputation.

**Field and source:** Burgman MA, McBride M, Ashton R, Speirs-Bridge A, Flander L, Wintle B, Fidler F, Rumpff L, Twardy C (2011). "Expert status and performance." *PLOS ONE* (PMC3146531). Retrieved through Europe PMC's open-access full text: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3146531/fullTextXML

**What it does:** Six facilitated workshops (123 experts; biosecurity, ecology, public health, weeds) gave private interval estimates on 5-10 factual questions each, saw the group's results, discussed, and re-estimated; accuracy was then compared with peer-rated expertise, years of experience, publications and qualifications.

**Evidence of effect:**
- Peer-rated expertise tracked years of experience (r about 0.49 to 0.84 across workshops) and self-rating (r = 0.85), but correlations between peer-rated expertise and actual accuracy ranged from -0.39 to 0.22 in round 1 and -0.47 to 0.12 in round 2; none significant.
- Average accuracy improved after discussion in all six workshops. The highest-status person often performed worse than the post-discussion group average.
- The paper does not report a direct expert-versus-novice comparison.

**What it needs:** Nothing special; this is a warning about a weighting shortcut.

**Failure modes / caveats:** Questions were factual almanac-style items, not diagnostic frequencies; 13-25 people per workshop gives low power for each correlation.

**Read status:** FULL_TEXT.

**Relevance to us `[INFERENCE]`:** Do not weight a 30-year veteran above a junior VAV or plumbing engineer just for tenure when pooling frequency estimates; weight by performance on feedback questions or pool equally. This also cautions that a single prestigious interviewee is not a safe sole source for the cause-frequency vector.

---

## 4. Question format: separate lower bound, upper bound, best guess, then confidence

**Technique:** Ask for a realistic lowest value, a realistic highest value and a best guess, then ask how confident they are that the true value lies inside, instead of requesting a fixed-level interval such as "give an 80% interval."

**Field and source:** Speirs-Bridge A, Fidler F, McBride M, Flander L, Cumming G, Burgman M (2010). "Reducing Overconfidence in the Interval Judgments of Experts." *Risk Analysis* 30(3):512-523. https://ideas.repec.org/a/wly/riskan/v30y2010i3p512-523.html (authors as I recall them; the page I read gave the abstract and title)

**What it does:** The 4-step format lets experts report their own confidence rather than being told to hit a level, which exposes how wide their intervals really need to be.

**Evidence of effect:** Three studies (n = 21, 24 and 34; epidemiologists, public health experts, marine ecologists). Meta-analysed overconfidence was 11.9% (95% CI 3.5 to 20.3), which corresponds to an 80% interval hit rate of 68.1%, described by the authors as a substantial reduction versus earlier work. In studies 2 and 3 the 4-step format cut overconfidence more than a 3-point format (Cohen's d = 0.61, 95% CI 0.04 to 1.18).

**What it needs:** Nothing beyond reordering the questions; works with a short written form or interview script.

**Failure modes / caveats:** Overconfidence was reduced, not removed: an 80% interval still captured the truth about 68% of the time. The effect varied across studies and the lower confidence-interval bound is near zero.

**Read status:** ABSTRACT_ONLY.

**Relevance to us `[INFERENCE]`:** For any number we ask a technician for (how often a cause occurs, how often a check misleads), elicit low, high, best, then confidence, and then widen the resulting interval, since even the best format leaves roughly a 12 point shortfall in coverage.

---

## 5. Natural-frequency wording: "out of 100 visits..."

**Technique:** Pose probability questions as counts in a concrete reference population ("of 100 visits where the cause was X, in how many would the tenant say Y?") rather than as percentages.

**Field and source:**
- Hoffrage U, Hafenbrädl S, Bouquet C (2015). "Natural frequencies facilitate diagnostic inferences of managers." *Frontiers in Psychology* 6:642. https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2015.00642/full
- Gigerenzer G, Hoffrage U (1995), as summarized in search results only (no page opened).

**What it does:** Natural frequencies tend to make Bayesian updating tasks easier because base rates are already embedded in the counts.

**Evidence of effect:** In 440 participants (259 undergraduates, 181 executives) doing two of four inference tasks, the proportion giving the Bayesian answer was 19.7% with percentages and 38.8% with natural frequencies. For undergraduates 14.6% to 40.5% (significant); for executives 26.6% to 36.2% (not significant, p = 0.095). No medical or technical practitioners in this sample. A search summary (SNIPPET) attributes roughly 16% to 46% to the 1995 original and about 10-20% to about 50% across 15 tasks to a secondary review; I did not verify these.

**What it needs:** A rewording of questions.

**Failure modes / caveats:** The evidence is about combining numbers someone hands you, not about whether frequency wording makes people produce more accurate numbers when asked to generate them. The effect was small and non-significant in the more experienced executive group.

**Read status:** Hoffrage 2015 FULL_TEXT; Gigerenzer and Hoffrage 1995 SNIPPET.

**Relevance to us `[INFERENCE]`:** Cheap to adopt in interviews and tenant-question wording, but I would not count on it to fix miscalibration. It is a courtesy to the respondent, not a calibration method.

---

## 6. Practitioner probability estimates: bad on base rates, mixed on evidence strength

**Technique (evidence about elicitation):** Ask clinicians for a pre-test probability, then how a test result would move it; compare with literature values.

**Field and source:** Morgan DJ, Pineles L, Owczarzak J, et al. (2021). "Accuracy of Practitioner Estimates of Probability of Diagnosis Before and After Testing." *JAMA Internal Medicine* 181(6):747-755 (PMC8022260). Full text via Europe PMC: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8022260/fullTextXML (author list as I recall; the retrieved text gave results, not authors). Abstract also at https://pure.psu.edu/en/publications/accuracy-of-practitioner-estimates-of-probability-of-diagnosis-be/

**What it does:** 723 outpatient practitioners in 8 US states were surveyed (585 responded, 553 completed: 290 residents, 202 attendings, 61 nurse practitioners or physician assistants) on four common scenarios; the "truth" was an expert panel's literature review.

**Evidence of effect:**
- Pre-test probabilities were overestimated in every scenario. Median pneumonia pre-test 80-85% versus an evidence range of 25-42%; breast cancer screening 2-10% versus 0.2-0.3%; cardiac ischemia 5-15% versus 1-4.4%; urinary tract infection (asymptomatic bacteriuria) 20-30% versus 0-1%.
- The implied strength of evidence (likelihood ratios) was often right for familiar, routine tests and badly wrong for others. Chest radiograph negative: median LR 0.21-0.35 versus 0.33 in the literature; urine culture negative 0.11-0.16 versus 0.11. But a positive exercise stress test was treated as roughly 19-51 times as likely under disease versus literature 2.0-2.7, and a negative mammogram as roughly 1.0 versus 0.05-0.24.
- Residents and attendings gave similar estimates; the differences between groups were small next to the gap from the evidence.

**What it needs:** A written vignette survey; hours of effort, not weeks.

**Failure modes / caveats:** Hypothetical vignettes, mostly trainees; pre-test was asked before seeing the case; the reference values came from an expert panel's literature review; survey reliability was not tested.

**Read status:** FULL_TEXT (first 100,000 of about 104,851 characters) plus abstract.

**Relevance to us `[INFERENCE]`:** This is the closest direct evidence for how elicited "cause frequencies" (pre-test) and "check reliabilities" (likelihood ratios) will behave. Expect frequency numbers to be skewed, probably toward whatever the technician's own caseload makes salient, and expect reliabilities of everyday checks (reading a return-line temperature) to be in the right ballpark while unfamiliar or "diagnostic-sounding" checks get inflated. Elicit reliabilities only for checks the person performs weekly.

---

## 7. How people misjudge frequencies: compression and memorability

**Technique (a bias to correct for):** Elicited frequencies of causes are systematically skewed; plan for it.

**Field and source:** Lichtenstein S, Slovic P, Fischhoff B, Layman M, Combs B (1978). "Judged frequency of lethal events." *Journal of Experimental Psychology: Human Learning and Memory* 4:551-578. https://scholarsbank.uoregon.edu/items/6e84075e-f186-4dfb-bbb1-380229907c3f/full

**What it does:** People estimated how often different causes of death occur; the study maps the pattern of error.

**Evidence of effect:** Judgments followed a consistent but biased scale: rare causes are overestimated and common ones underestimated, and specific causes are over- or under-weighted according to exposure, memorability and imaginability. Participants could not correct the bias even when told about it. The page gives no numeric effect sizes.

**What it needs:** Nothing; this is background for designing elicitation.

**Failure modes / caveats:** Mortality statistics from lay respondents are a long way from technicians estimating failure causes from their own caseload, who get feedback; the transfer is plausible but not shown here.

**Read status:** ABSTRACT_ONLY.

**Relevance to us `[INFERENCE]`:** Technicians' recalled frequencies will probably be flatter than reality (rare causes boosted, common ones shaved) and tilted toward dramatic or recently-fixed faults. A flattened prior is still better than none below roughly 30-100 confirmed cases in my calculation (item 14), but it should carry a small effective weight.

---

## 8. How precise do elicited probabilities need to be? Diagnostic networks are often insensitive, with conditions

**Technique (evidence on tolerance):** Perturb the probabilities of an expert-built diagnostic Bayesian network and measure how much diagnostic performance drops.

**Field and source:**
- Pradhan M, Henrion M, Provan G, Del Favero B, Huang K (1996). "The sensitivity of belief networks to imprecise probabilities: An experimental investigation." *Artificial Intelligence* 85(1-2):363-397. https://research.ucc.ie/en/publications/the-sensitivity-of-belief-networks-to-imprecise-probabilities-an/
- Henrion M, Pradhan M, Del Favero B, Huang K, Provan GM, O'Rorke P (1996). "Why Is Diagnosis Using Belief Networks Insensitive to Imprecision in Probabilities?" UAI 1996, 307-314. https://mlanthology.org/uai/1996/henrion1996uai-diagnosis
- Ng K-C, Abramson B (1990). "A Sensitivity Analysis of Pathfinder." UAI 1990. https://arxiv.org/abs/1304.1106 ; and the 1991 follow-up (UAI 1991, 242-248) https://arxiv.org/abs/1303.5734

**What it does:** Adds random noise to medical-network probabilities (a liver and bile disease network and subsets of CPCS) and to the Pathfinder lymph-node system, then measures how performance changes.

**Evidence of effect:**
- Pradhan et al.: even very different mappings from verbal frequency terms to numbers, and large amounts of noise, gave only modest drops in diagnostic performance; collapsing four-level variables to binary had no significant effect; diseases outside the network degraded performance modestly.
- Henrion et al. explain it two ways: performance was judged by the average probability given to the true disease, which is insensitive to symmetric noise; and the reference posteriors were often near 0 or 1, so noise barely moved them.
- Ng and Abramson 1990 reported substantial degradation from slight parameter changes in Pathfinder; the 1991 follow-up redid it leaving 0.0 and 1.0 unchanged and perturbing near-extreme values less, after which slight variations had little effect. The abstracts give no numbers.

**What it needs:** An existing network and a test set with confirmed diagnoses.

**Failure modes / caveats:** The conclusion depended on how perturbations were defined (symmetric noise versus log-odds, treatment of 0 and 1). Insensitivity to random noise does not cover systematic bias. Both conditions the Henrion paper gives for insensitivity (posteriors near 0 or 1, noise that averages out) are properties of those domains.

**Read status:** ABSTRACT_ONLY for all four.

**Relevance to us `[INFERENCE]`:** This is a cautionary counterpoint to our own finding that cause frequencies are worth +0.095 top-1. Our world has posteriors far from 0 or 1 (top-1 of 0.51 to 0.76) and our frequency errors would be systematic, not symmetric noise, which are exactly the two conditions under which these papers' reassurance fails. It also means a test of "does precision matter" must use systematic perturbations in the same direction a technician's bias would push (flatter, memorable-fault-heavy).

---

## 9. Sensitivity-guided elicitation: refine only the probabilities that matter

**Technique:** Elicit rough numbers for everything, run a sensitivity analysis on the model, then spend careful elicitation effort only on the parameters that move the output; stop when the model behaves acceptably, when more elicitation costs more than it gains, or when the knowledge simply is not there.

**Field and source:**
- Coupé VMH, van der Gaag LC, Habbema JDF (2000). "Sensitivity analysis: an aid for belief-network quantification." *Knowledge Engineering Review* 15(3):215-232. https://www.cambridge.org/core/journals/knowledge-engineering-review/article/abs/sensitivity-analysis-an-aid-for-beliefnetwork-quantification/7373C15BB1FA2DB64E82C82917A95D55
- van der Gaag LC, Renooij S, Witteman CLM, Aleman BMP, Taal BG (2002). "Probabilities for a probabilistic network: a case study in oesophageal cancer." *Artificial Intelligence in Medicine* 25(2):123-148 (PMID 12031603). Record via Europe PMC search: https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=TITLE%3A%22Probabilities%20for%20a%20probabilistic%20network%22&format=json&resultType=core ; earlier conference version "How to Elicit Many Probabilities" (UAI 1999), https://arxiv.org/abs/1301.6745

**What it does:** The oesophageal-cancer team found that existing elicitation methods were too slow for the number of probabilities needed, and built a procedure combining text-based statements with a scale carrying numerical and verbal anchors; the 2000 paper adds the iterate-and-prune sensitivity loop.

**Evidence of effect:** The scale-based method elicited many probabilities in a reasonable time, and a preliminary test on real patient data found the resulting network predicted the correct cancer stage for 85% of patients. The sensitivity-loop paper reports no numbers on its page.

**What it needs:** A model structure, two or more domain experts, and the ability to rerun the model with perturbed parameters; no field data.

**Failure modes / caveats:** The 85% figure is a preliminary test in one domain with two experts and says nothing about whether the sensitivity step itself improved it. I found no controlled comparison of sensitivity-guided versus uniform elicitation effort.

**Read status:** ABSTRACT_ONLY for all three.

**Relevance to us `[INFERENCE]`:** This is the formal version of what our simulation already showed. The direct application: spend interview time on the cause-frequency vector and on the few checks with the highest posterior impact, and accept rough numbers elsewhere. It does not by itself tell us which unknown is worth a field experiment; that needs item 10.

---

## 10. Value-of-information analysis: which unknown is worth measuring, and how much data

**Technique:** Compute the expected gain in decision quality from learning a parameter exactly (expected value of partial perfect information, EVPPI) and from a specific sample (expected value of sample information, EVSI, net of study cost); rank candidate studies by net benefit.

**Field and source:**
- Tuffaha HW, Gordon LG, Scuffham PA (2016). "Value of Information Analysis Informing Adoption and Research Decisions in a Portfolio of Health Care Interventions." *MDM Policy & Practice* (PMC6125050; DOI 10.1177/2381468316642238). Full text via Europe PMC: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6125050/fullTextXML
- Strong M, Oakley JE, Brennan A (2014). "Estimating Multiparameter Partial Expected Value of Perfect Information from a Probabilistic Sensitivity Analysis Sample: A Nonparametric Regression Approach." *Medical Decision Making* 34(3):311-326. https://eprints.whiterose.ac.uk/id/eprint/78428/ (page showed metadata only; method description is from a search summary)
- Johnson R, Woodcock J, de Nazelle A, et al. (2019). "A guide to Value of Information methods for prioritising research in health impact modelling." arXiv:1905.00008. https://arxiv.org/abs/1905.00008
- Fenwick E, et al. (2020). ISPOR VOI Task Force, Report 1. *Value in Health* 23(2):139-150. https://www.ispor.org/heor-resources/good-practices/article/value-of-information-analysis-for-research-decisions-an-introduction (abstract only)
- Straub D (2014). "Value of information analysis with structural reliability methods." *Structural Safety* 49 (reliability-engineering version; search summary only).

**What it does:** VOI ranks parameters (EVPPI) and study designs (EVSI minus cost) by the improvement they would buy in the decision, rather than by how much the model output wiggles. Strong et al. show EVPPI can be estimated from the single probabilistic-sensitivity-analysis sample by regression, avoiding nested Monte Carlo; Johnson et al. use it to allocate research time across model components.

**Evidence of effect:**
- Four Queensland skin-integrity interventions: for tissue adhesive, the VOI-optimal trial was 4 arms of 220 patients (return on investment 130%) versus a conventional 388 per arm (79%); for negative-pressure wound therapy the optimal design was 2 arms of 200 (ROI 133%) versus 400 per arm (66%). Nutritional support had large uncertainty (population EVPI AU$5.5 million) but low net benefit of research (AU$100,000, ROI 11%), so the decision was to approve with research.
- Ranking by net research benefit put wound therapy first (AU$1.2 million), then tissue adhesive (about AU$325,000), then nutritional support (AU$100,000); ranking by EVPI alone would have reversed that order, which the authors argue would misallocate limited research money.
- (SNIPPET, not opened) A review summarised in search results found that only 70 of 73,795 UK health-technology-assessment results reported EVPI, so uptake is low; another summary notes a parameter with low one-off EVPPI can matter in a sequential design.

**What it needs:** A model with probabilistic inputs, a decision metric, and a cost per study; EVPPI by regression needs only a few thousand model runs already generated by sensitivity analysis.

**Failure modes / caveats:** Authors note modelled interventions used different methods and that perfect implementation was assumed, which can overstate VOI. VOI is only as good as the input distributions; with elicited priors the answer inherits their overconfidence (items 2, 4, 6).

**Read status:** Tuffaha FULL_TEXT (first 100,000 of about 103,956 characters); Johnson et al. and ISPOR report ABSTRACT_ONLY; Strong et al. and Straub SNIPPET.

**Relevance to us `[INFERENCE]`:** Our simulation measured sensitivity (give the tool the true cause frequencies: +0.095 top-1). VOI would add two things: how uncertain we really are about each input (an input we already know well has little value even if the model is sensitive to it) and the cost of learning it (a few hundred confirmed cases versus seeded-fault experiments). The practical step is to treat cause frequencies, check reliabilities and tenant-answer reliability as random inputs in the simulator, compute EVPPI on expected minutes-to-fix and top-1, and then rank "what to collect first" per unit effort.

---

## 11. Check elicited frequencies against incoming records with a sequential test

**Technique:** Treat expert occurrence ratings as hypotheses, log real events in a structured system, and use Wald's sequential probability ratio test to see whether the data contradict a rating.

**Field and source:** Kornek D, Lotter M, Szkitsak J, et al. (2024). "Improving the safety of radiotherapy treatment processes via incident-driven FMEA feedback loops." *Journal of Applied Clinical Medical Physics* 25(9):e14455 (PMC11492396). Full text via Europe PMC: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11492396/fullTextXML

**What it does:** 23 pre-identified failure modes were presented through reporting terminals; staff filed reports; the test asked whether an expert occurrence rating was too low (alpha = beta = 0.10; null: rating equals what reports imply; alternative: one step higher; ratings only ever raised).

**Evidence of effect:** Over 15 months, 304 reports; 16 additional failure modes were found; one occurrence rating was raised (68 reports, confirmed after about 10 months) and 22 were not disproved. The other failure modes never reached a decision, mainly because there were too few reports. 12 of the 23 initial failure modes were never reported at all.

**What it needs:** A voluntary reporting channel with low friction, months of operation, staff buy-in.

**Failure modes / caveats:** Underreporting: the reporting rate was about 0.0006 per fraction against 1.3 per 1000 attendances at another centre, and the authors cannot tell low occurrence from non-reporting. The test could only detect ratings that were too low, not too high. Single centre; smaller centres expected to file fewer reports.

**Read status:** FULL_TEXT (first 100,000 characters).

**Relevance to us `[INFERENCE]`:** A realistic picture of what a pilot can achieve: with a few hundred logged cases, only the top few frequent causes will ever reach a decision against their elicited prior, and rare causes will remain at their elicited value. A pilot form that records the confirmed cause per visit is the minimum data product; it will mostly confirm the head of the distribution, not the tail.

---

## 12. Mining building maintenance work orders for failure-mode frequencies

**Technique:** Cluster and text-mine free-text computerised-maintenance-management-system (CMMS) work orders to separate failures from routine jobs and to count failure modes per equipment type.

**Field and source:**
- Gunay HB, Shen W, Yang C (2019). "Text-mining building maintenance work orders for component fault frequency." *Building Research & Information* 47(5):518-533. https://experts.mcmaster.ca/scholarly-works/2147103
- Yang C, Shen W, Chen Q, Gunay B (2018). "A practical solution for HVAC prognostics: Failure mode and effects analysis in building maintenance." *Journal of Building Engineering* 15:26-32. https://experts.mcmaster.ca/scholarly-works/2147114
- Conte A, Bolland C, Phan L, Brundage M, Sexton T (2021). "The Impact of Data Quality on Maintenance Work Order Analysis: A Case Study in Historical HVAC Maintenance Work Orders." PHM Society European Conference 6(1). https://papers.phmsociety.org/index.php/phme/article/view/2814
- "Using work order data to extract building performance metrics," ASHRAE Journal web article. https://www.ashrae.org/news/ashraejournal/using-work-order-data-to-extract-building-performance-metrics

**What it does:** Gunay et al. preprocess descriptions, cluster to isolate failure orders from routine maintenance, then use association-rule mining to find co-occurring terms; tested on a central plant with four boilers and five chillers and on 44 buildings, producing per-equipment and component-level failure-mode frequencies. The ASHRAE article reports four years of work orders from four large Ottawa commercial buildings, finding common failures such as failed valves, malfunctioning pumps and burnt ballasts.

**Evidence of effect:** No quantitative accuracy evidence found. None of the pages I read reports how the extracted frequencies compare with a hand-labelled ground truth. Conte et al. show qualitatively that missing values in key fields lower analysis accuracy and that facility staff must supply interpretation; the page gives no percentage of missing fields or unusable orders. The ASHRAE article does not discuss missing fields or misclassification and notes one climate and four buildings.

**What it needs:** Access to a CMMS export covering several years and many buildings, text-mining effort, and a domain expert to label clusters.

**Failure modes / caveats:** Free text is unstructured; work orders record what was done and reported, not necessarily the root cause (replace-and-hope is not visible). Vendor blog posts on HVAC callback and first-time-fix rates showed up in search; I did not use them because they are marketing material without methods.

**Read status:** Gunay, Yang and Conte ABSTRACT_ONLY; ASHRAE article FULL_TEXT of the web page.

**Relevance to us `[INFERENCE]`:** Work orders are plausible as a weak ranking of coarse fault categories (pump, valve, mixing valve) but weak as a source of our 17 specific causes, because the cause labels are not what the ticket records. A partner's tickets would need a small hand-labelled validation sample (technician reviews perhaps 50-100 tickets) before we use any frequency from them. I found no hot-water-specific building work-order study.

---

## 13. Generic reliability databases (OREDA, handbook prediction models): wide gaps to the field

**Technique (evidence about reliability of the source):** Use published generic failure rates as priors, and update with site data.

**Field and source:**
- Håbrekke S, Hauge S, Xie L, Lundteigen MA (2018). "Failure rates of safety critical equipment based on inventory attributes." ESREL 2018, 2419-2426. https://www.sintef.no/en/publications/publication/0198cc46f4f2-7b748f3d-aac8-487a-bacc-4f54e6f170c7/
- Jones J, Hayes J (1999). "A comparison of electronic-reliability prediction models." *IEEE Transactions on Reliability* 48(2):127-134. https://wrap.warwick.ac.uk/14281
- Weil L, Pecht M, Hakim E (1993). "Reliability Evaluation of Plastic Encapsulated Parts." *IEEE Transactions on Reliability* 42(4):608-616. https://web.calce.umd.edu/articles/abstracts/1993/reopep.htm
- exida (vendor) pages on OREDA versus its FMEDA predictions: https://exida.com/Blog/OREDA-Data-vs.-FMEDA-Data ; https://www.exida.com/Resources/Whitepapers/explaining-the-differences-in-mechanical-failure-rates-exida-fmeda

**What it does:** OREDA (offshore oil and gas) and similar handbooks publish generic failure rates by equipment class; handbook prediction models (for example MIL-HDBK-217) estimate rates from part factors.

**Evidence of effect:**
- Håbrekke et al.: generic data mostly cover equipment groups rather than attributes such as size, type, service and medium; the Norwegian study started from expert-suggested attributes but maintenance data were too sparse to support all of them, so it narrowed to four equipment types.
- Jones and Hayes compared five handbook models (including MIL-HDBK-217E and Bellcore) on field data from British and Danish manufacturers; predictions differed greatly from observed field behaviour and from each other; results sat in a table I could not see. Weil et al. conclude MIL-HDBK-217 results were misleading for plastic-encapsulated microcircuits (no numbers on the page).
- (SNIPPET only, not verified) A search summary of an SAE automotive-electronics comparison says predictions ranged from 39% low to 107% high of field values across eight modules.
- exida, a vendor that sells a competing method, states that aligned OREDA and FMEDA comparisons are "quite comparable" and attributes raw gaps to design specificity and site-specific failures; no ratios given.

**What it needs:** For Bayesian use, a generic prior plus plant-level counts; I did not open a source quantifying how many plant-level events are needed.

**Failure modes / caveats:** Different failure-mode definitions and scope make "generic" and "specific" rates non-comparable. The one neutral set of comparisons found is for electronics, not building systems. I found no building-systems equivalent of OREDA or NPRD with failure-mode frequencies for hot-water plants; the closest is item 12.

**Read status:** Håbrekke, Jones and Hayes, and Weil et al. ABSTRACT_ONLY; exida blog FULL_TEXT, whitepaper ABSTRACT_ONLY.

**Relevance to us `[INFERENCE]`:** Matches our own experience (a 0.92 assumed detection rate became 0.69 on real data). Treat any generic or simulated rate as a prior with a wide spread and a small effective weight, and plan to learn site-specific check reliability from our own cases rather than expecting a handbook to provide it.

---

## 14. Minimum case counts: what a few dozen to a few hundred confirmed visits can and cannot establish

**Technique:** Use multinomial/binomial interval arithmetic, the rule of three, and the "effective sample size" of an elicited prior to decide how many cases are enough and how much to trust a prior against data.

**Field and source:**
- Hanley JA, Lippman-Hand A (1983). "If nothing goes wrong, is everything all right? Interpreting zero numerators." *JAMA* 249(13):1743-1745; statement of the rule at https://en.wikipedia.org/wiki/Rule_of_three_(statistics) (the paper itself was not opened).
- Morita S, Thall PF, Müller P (2008). "Determining the effective sample size of a parametric prior." *Biometrics* 64(2):595-602. https://mdanderson.elsevierpure.com/en/publications/determining-the-effective-sample-size-of-a-parametric-prior
- Thompson SK (1987). "Sample size for estimating multinomial proportions." *American Statistician* 41(1):42: confirmed to exist via search; the formula and tables were not retrievable (publisher 403), so I do not quote them.
- My own calculation (local Python, not a source).

**What it does:** If an event is never seen in n cases, its 95% upper bound is about 3/n (exactly 1 minus 0.05^(1/n); the source says the approximation is good for n above 30; the general bound is minus the natural log of alpha divided by n). The ESS paper defines how many cases an informative prior is worth (for a Beta prior, a + b); for a vague-starting prior it is the sample size whose posterior is closest to the prior.

**Evidence of effect (sources):** Rule of three: 0 events in 30 cases still allows a rate up to about 10%. ESS: no numbers beyond the Beta(a, b) example on the page I read.

**Illustration from my own calculation `[INFERENCE]`, not a source.** Assumptions: 17 causes with Zipf-like true frequencies (largest 0.29, then 0.15, 0.10, 0.07, 0.06, smallest 0.017); an elicited prior that is a compressed version of the truth (frequencies raised to the 0.5 power then renormalised), which sits at a total-variation distance of 0.20 from the truth versus 0.37 for a uniform guess; Dirichlet blending of elicited prior with counts; 4,000 simulations per cell.

| Confirmed cases n | Counts only (error) | Prior ESS 10 | Prior ESS 30 | Prior ESS 100 |
|---|---|---|---|---|
| 10 | 0.45 | 0.22 | 0.18 | 0.19 |
| 30 | 0.26 | 0.20 | 0.16 | 0.16 |
| 100 | 0.14 | 0.13 | 0.12 | 0.12 |
| 300 | 0.08 | 0.08 | 0.08 | 0.08 |
| 1000 | 0.045 | 0.045 | 0.044 | 0.045 |

(Error = mean total-variation distance between estimated and true cause-frequency vector; the elicited prior alone scores 0.203.)
- Counts alone beat the compressed elicited prior only somewhere between 30 and 100 cases; a prior worth about 30 cases is the best blend up to about 100 cases and the benefit is gone by about 300.
- The correct single most-common cause is identified 89% of the time at n = 30 and 99% at n = 100; the correct set of the top three causes only 37%, 63% and 84% at n = 30, 100, 300.
- A cause whose true frequency is 1%, 2% or 5% is seen at least once in 30 cases with probability 26%, 45%, 79%; in 100 cases 63%, 87%, 99%; in 300 cases 95%, 100%, 100%.
- 95% credible interval for a cause with true frequency 5% (Beta, 0.5 prior): n = 30: 0.008 to 0.172; n = 100: 0.019 to 0.106; n = 300: 0.029 to 0.079. For 20%, n = 100: 0.13 to 0.29.
- Worst-case (p = 0.5) normal-approximation sample size for plus or minus 0.05 at 95% is 385 for one proportion, about 885 for all 17 causes simultaneously (Bonferroni) and about 983 for 29 categories; for plus or minus 0.10 it is 97, 222 and 246.
- Check reliability, which needs cases where the cause is actually present: estimating a detection rate near 0.9 to plus or minus 0.10 needs about 35 such cases, a rate near 0.69 needs about 82, worst-case about 96. Detecting that an assumed 0.90 is really 0.70 (one-sided, 5% error, 80% power) needs about 19 cases of that cause; 0.92 versus 0.69 needs about 13; 0.90 versus 0.80 needs about 69.
- Converting to visits: a cause that is 10% of visits needs roughly 350 to 960 visits to see 35 to 96 cases of it.

**What it needs:** A confirmed-cause label per visit; nothing else for the cause-frequency estimate.

**Failure modes / caveats:** All the table numbers depend on my assumed frequency shape and on the assumed bias of the elicited prior; they are an illustration of scale, not a forecast. Independence of visits and a stable case mix are assumed; real caseloads cluster by building and season, which makes the effective n smaller. Normal-approximation sample sizes are rough at small n.

**Read status:** Wikipedia rule-of-three page FULL_TEXT; Hanley and Lippman-Hand not opened (cited via that page and search results); Morita et al. ABSTRACT_ONLY; Thompson not read.

**Relevance to us `[INFERENCE]`:** Tens of cases are enough to detect that an assumed check reliability is grossly wrong (if enough of them contain that cause), a hundred is enough to rank the leading cause, and several hundred are needed to separate the top three or to pin down frequencies of mid-rank causes. Reliabilities of checks tied to rare causes cannot be learned from passive visit logs in any realistic time; those are the targets for seeded-fault experiments.

---

## Patterns across items

- Experts are overconfident even in the best protocols: 90% intervals held the truth 36% of the time in a defence reliability study; 80% intervals about 68% with the best question format. Plan to widen elicited intervals and treat elicited numbers as priors of modest weight (items 2, 4).
- The reliable gains are cheap ones: equal-weight pooling of several people plus one discussion round. Performance weighting from seed questions adds information but has an out-of-sample accuracy penalty, and with a small panel its weights are noisy (items 1, 2, 3).
- Seniority, self-rating and peer reputation do not predict accuracy; discussion and feedback do (item 3).
- Practitioners misjudge base rates by large factors but often get the evidential strength of routine, everyday checks about right; ask for reliabilities of things they do weekly, and calibrate cause frequencies against records (items 6, 7).
- Sensitivity is not value of information. VOI weighs how uncertain an input is, what the decision gains from learning it, and the study cost; in the one worked portfolio, ranking by EVPI alone reversed the ranking by net research benefit, and the VOI-optimal trials were smaller than conventional ones (items 9, 10).
- Diagnostic Bayesian networks have been found insensitive to noisy probabilities, but only in settings with symmetric noise and posteriors near 0 or 1, and even there the conclusion flipped depending on how noise was defined. Our regime (posteriors far from certain, systematic bias) is the one these results do not cover (item 8).
- Records are weak sources: underreported, sparse per category, free-text and rarely stating root cause; generic handbook rates disagree with field data and with each other, and I found no quantitative accuracy check of building work-order mining and no hot-water-specific data (items 11, 12, 13).
- On counts: roughly 100 confirmed cases rank the top cause and show whether an assumed reliability is badly wrong; several hundred are needed for the top three; rare causes and their check reliabilities will not be learned from passive logs and need seeded-fault experiments (items 11, 14).

---

## Sources I could not read

Unreadable (PDF returned as binary, or blocked), recorded and not used:
- Cooke and Goossens (2008), PDF at rogermcooke.net (binary).
- TU Delft repository file File_2e9a61ea... (binary; identity not determinable).
- arXiv PDF of "How to Elicit Many Probabilities" (UAI 1999) and the KER 2000 preview PDF at maxapress.com (binary); the abstract pages were used instead.
- Hemming et al. 2020 on Wiley (403); Forecasting 5(29) PDF on research.tudelft.nl (403).
- PubMed and PMC web pages (cookie or reCAPTCHA walls); Europe PMC's open-access full-text service worked and was used for items 3, 6, 10, 11.
- Taylor and Francis pages (403): Thompson 1987 and Håbrekke chapter; CCPS 2015 paper on equipment-data uncertainty (403), whose claim in a search summary that site data varied up to two orders of magnitude is unverified and not used; Cranfield DSpace NFF review page (403).

Claims that rest on search-result summaries only (flagged SNIPPET above): Gigerenzer and Hoffrage 1995 percentages; Strong et al. 2014 method description; Straub 2014; the 70 of 73,795 EVPI-reporting figure; the SAE automotive-electronics 39% low to 107% high figure; the "parameter with low one-off EVPPI can matter in a sequential design" statement.

Searched but nothing usable: a no-fault-found review (Khan et al. 2014, both parts: abstract pages have no removal percentages); NUREG/CR-6823 (confirmed to exist; chapters on empirical Bayes not retrieved); the Heckerman, Breese and Rommelse decision-theoretic troubleshooting results (abstract-level only; belongs to another area's search); a building-systems equivalent of OREDA/NPRD (none found).
