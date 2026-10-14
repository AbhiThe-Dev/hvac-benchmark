# Adversarial whitespace check: technician-guided, symptom-scoped, test-sequencing diagnostics for building PLUMBING and ELECTRICAL (as of 6 Oct 2026)

Target capability, as defined by the requester:
- (a) technician-reported symptom as input
- (b) a ranked set of candidate root causes
- (c) recommends the NEXT check, ordered by information gain per cost/time/risk
- (d) updates after each result
- (e) stops when confident
- (f) may use building data (BAS/meter/sensor) or equipment relationships

Method: 49 distinct web searches plus about 30 page fetches (full query list in Section 4). The search tool is a general web index, US-only. Vendor claims are marked VENDOR CLAIM (unverified). Where a fetch tool summarized a page and I could not see the raw text, I say so.

## 1. Does anyone already meet the full target capability (a)-(f) for plumbing or electrical in buildings?

### Takeaway
I did NOT find a product, paper, patent or repo that meets all of (a)-(f) for building plumbing or electrical. The narrow claim survives. A broad claim ("nobody does AI-guided troubleshooting for plumbers/electricians") is false: many LLM apps do (a)+(b) loosely, and the method itself is old prior art (Heckerman 1995; Dezide's patented engine). The closest hits are (1) the June 2026 arXiv paper "LLM-as-an-Investigator" (a, b, d, e plus partial c; electrical/hydraulic/mechanical forum threads; no building data), (2) Dezide Advisor (a, b, c, d for generic machinery; no plumbing/electrical customers listed), and (3) HVAC-only measureQuick AI Assist, which reads live probe data and "points you at the next thing to check".

### Cited Findings
- Closest academic match: "LLM-as-an-Investigator: Evidence-First Reasoning for Robust Interactive Problem Diagnosis" (Marozzo and Liò, arXiv 2606.13220, submitted 11-12 June 2026). The abstract-page summary says the agent generates competing hypotheses, asks targeted clarifying questions, and keeps gathering evidence until one hypothesis substantially outweighs the others. Domains: mechanical, electrical, hydraulic. — [arXiv abs](https://arxiv.org/abs/2606.13220)
- Its HTML version (as summarized by the fetch tool): 303 solved forum threads (electrical 96, hydraulic 105, mechanical 102). It maintains a normalized probability distribution over candidate solutions, stops at confidence threshold tau=0.90 or a 5-10 question budget, and uses simulated users. The summary says the paper "doesn't explicitly frame this as expected information gain optimization". No real technician or building data. Reported accuracy about 64-66 vs 33-35 for direct answering. — [arXiv HTML](https://arxiv.org/html/2606.13220)
- CONFLICT inside my own fetches: a first fetch of the PDF listed the domains as "plumbing, HVAC, electrical, IT". The abstract page and the HTML version both say mechanical/electrical/hydraulic. I trust the latter two. "Hydraulic" there likely means fluid-power or hydraulic-equipment forums, not building plumbing, but I could not confirm this from the full text. The PDF could not be text-extracted locally. Treat the domain labels as UNVERIFIED in detail. Link: [arXiv PDF](https://arxiv.org/pdf/2606.13220)
- Decision-theoretic troubleshooting is established prior art: Heckerman, Breese and Rommelse (1995) generate repair/observation sequences with minimum expected cost. Microsoft used Breese/Heckerman Bayesian networks for Windows printer troubleshooting. — [Heckerman/Breese framework, arXiv 1302.3563](https://arxiv.org/pdf/1302.3563); [printer troubleshooting history via search](https://www.researchgate.net/publication/221047784_Printer_Troubleshooting_Using_Bayesian_Networks)
- Commercial implementation of the same method exists: Dezide Advisor. Per Dezide, the engine "finds an optimal sequence of steps balancing belief of the step being helpful with its cost", handles uncertain or missing replies, and is "protected by 8 patents". — [Dezide decision technologies](https://www.dezide.com/technology/decision-technologies/); [Dezide technology page, 8 patents claim from search snippet](https://www.dezide.com/technology/)
- Dezide's named customers: Atlas Copco, Siemens-Gamesa, Quickline, IBA, Lyse, FARO, Liebherr, Vestas, ENERCON. Industries include "Construction" but no plumbing, electrical, pumps or building services are named. — [Dezide customers](https://www.dezide.com/customers/)
- Dezide size, from an aggregator of unknown reliability: about $2.4M revenue, 22 people in 2025. — [Latka](https://getlatka.com/companies/dezide.com) (low-reliability aggregator)
- Closest building-adjacent academic work I found, but passive or municipal, not technician-driven: a Bayesian active fault isolation method for leak localization in water distribution networks (IEEE, 2022). It computes posterior probabilities per hypothesis, designs control inputs to separate hypotheses, and iterates with posteriors as the next priors. — [TU Delft PDF/IEEE entry via search](https://www.dcsc.tudelft.nl/~mohajerin/Publications/journal/2022/AFD.pdf); [IEEE](https://ieeexplore.ieee.org/document/9880532/). Meets b, c-like (active input design, not cost-ordered technician checks), d, f (hydraulic model). Does NOT meet a (no technician symptom) or building scale.
- Building-electrical academic work found is passive ML classification, not sequential test selection. Example: VMD + QGA-SVM building electrical fault classification, 91.67% accuracy. — [PMC10027836](https://pmc.ncbi.nlm.nih.gov/articles/PMC10027836/)
- Building Bayesian-network FDD papers are almost all HVAC. — [ScienceDirect HVAC BN](https://www.sciencedirect.com/science/article/abs/pii/S0306261922013071); [whole-building BN fault diagnosis](https://www.researchgate.net/publication/349607442_Bayesian_Networks_for_Whole_Building_Level_Fault_Diagnosis_and_Isolation)
- Generic interactive-troubleshooting test selection research exists: Chen, Renders, Chehreghani, Krause (2017), a sampling-based online learning framework for sequentially selecting low-cost tests (about 1100 root causes and 950 tests per search snippet; domain not building). — [arXiv 1703.05452](https://arxiv.org/abs/1703.05452)
- Telecom craftsperson prior art (1994): Harris Corp patent US5533093, "Automated trouble-shooting mechanism resident in craftsperson's portable test and communications device", later associated with Fluke. Successive instruction screens direct the technician to derive more information "until the application engine has refined a field of potential causes to a single probable source". Domain is telephone line testing. — [US5533093](https://patents.google.com/patent/US5533093)
- No Google Patents hit specific to plumbing or electrical building troubleshooting with test selection surfaced (see Gaps). Patent searches returned vehicle, medical, DSL, printer and Dezide-authoring patents. — [search results incl. US6192302, US8086423](https://patents.google.com/patent/US8086423); [Dezide authoring tool patent](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7385716)

### Inferences
- The defensible gap is not "AI troubleshooting" and not "Bayesian test sequencing" as methods. It is the combination of cost/info-gain-ordered checks, with posterior updates and stopping, scoped to one symptom, and coupled to building data and equipment-relationship maps, in plumbing and electrical. I found no one doing that combination as of Oct 2026.
- The requester should not claim method novelty. Heckerman 1995 and Dezide's patents cover core sequencing. The novelty claim should be about the domain application plus the symptom-scoped map and BAS/meter data coupling.
- The nearest threat from research is LLM-as-an-Investigator style agents (posterior over hypotheses, stop threshold). It is a few months old, evaluated on forum threads, and has no cost model or building data. A follow-up that adds building data is easy to imagine.
- Dezide could in principle author plumbing/electrical guides. Nothing found shows it has, and its listed customers are OEM machinery, wind and telecom. This is absence of evidence from a customer page, not proof.

### Gaps
- Could not read full text of arXiv 2606.13220. The "hydraulic" domain meaning and whether test selection uses an information-gain proxy remain unconfirmed.
- Could not run Google Patents or Espacenet CPC-class searches directly. Only web-index hits were reviewed. A patent targeting building plumbing/electrical test selection could exist unseen.
- Dezide case studies (individual PDFs) were not read.

## 2. Candidate table: every candidate found, with (a)-(f)

Legend: Y = evidence of it; P = partial or implied; N = no evidence found; ? = could not determine. "VC" = vendor claim, unverified. Confidence = my confidence in the row's classification.

| # | Name | URL | Date | Trade | a | b | c | d | e | f | Evidence / reason | Conf. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | LLM-as-an-Investigator (Marozzo, Liò) | https://arxiv.org/abs/2606.13220 | Jun 2026 | electrical/hydraulic/mechanical forum threads | Y | Y | P | Y | Y | N | Hypothesis distribution, clarifying questions chosen to discriminate, stop at tau=0.90; paper does not frame it as EIG; no cost; forum data, no building data | Med-high (abstract + HTML; full text not read) |
| 2 | Dezide Advisor | https://www.dezide.com/technology/decision-technologies/ | Active 2026; patents ~2000s-2010s | general machinery (wind, telecom, medical, etc.); NOT plumbing/electrical | Y (guided from a problem) | Y | Y | Y | ? | N | "optimal sequence of steps balancing belief ... with its cost"; handles uncertain replies | Med-high on method; high that no plumbing/electrical customer is listed |
| 3 | Heckerman/Breese/Rommelse decision-theoretic troubleshooting | https://arxiv.org/pdf/1302.3563 | 1995-96 | printers/electro-mechanical | Y | Y | Y | Y | Y | P | Foundational method; model-based | High |
| 4 | Puig/Mohajerin-lineage Bayesian active fault isolation for water networks | https://ieeexplore.ieee.org/document/9880532/ | 2022 | municipal water distribution (not building plumbing) | N | Y | P | Y | P | Y | Posteriors become next-step priors; active input design | Med-high |
| 5 | ServiceTitan Atlas Troubleshooting (Field Pro) | https://help.servicetitan.com/docs/use-atlas-for-troubleshooting-with-field-pro-in-mobile | Atlas mobile replaced Field Assistant (July 2025); Fall 2025 release | HVAC, residential/commercial, plumbing | Y | P (VC: "identify likely causes") | N | P (follow-up questions on same equipment) | N | P (equipment record/model) | Answers "with cited sources"; user asked to "include temps, operating conditions, or error codes"; looks like manual/RAG Q&A, not sequenced test selection (my inference) | Med |
| 6 | TradePals VoltPal (electrician) and PipePal (plumber) | https://tradepals.net/ ; https://tradepals.net/voltpal | 2026 (copyright) | electrical, plumbing | Y | P (VC: "ranked probable causes") | ? (VoltPal page: "troubleshooting wizard", 27 equipment types; flow not detailed) | N (no iterative flow described) | N | N | Photo/fault-code input; NEC refs; HVAC not offered | Med (VC) |
| 7 | ElectriciansMate | https://www.electriciansmate.app/ | copyright 2025 | electrical | Y | ? | ? | ? | ? | N | VC: "AI Guided Diagnostics ... troubleshooting steps tailored to your selected system and fault type" | Low-med |
| 8 | Jenova "Electrician's Assistant" / "AI Plumber's Assistant" pages | https://www.jenova.ai/en/resources/ai-electricians-assistant | 27 Aug 2026 (page date) | electrical, plumbing | Y | Y (VC: ranks by likelihood) | P (asks specific meter readings first) | P (conditional "if you measure X then inspect Y") | P (stop-and-escalate boundaries) | N | Closest to the target behavior in a product-style page, but it reads as a generic LLM chat wrapper with a measurement-first persona; page text is marketing | Low-med (VC) |
| 9 | Rheem Fix It Tool | https://www.rheem.com/fixittool/ | current | water heaters (Rheem only) | P (error codes/product questions) | ? | P (question sequence mimics Technical Service Analysts) | Y (question flow) | P | N | "asks product specific questions to identify the error code ... diagnose the problem, provide step by step suggestions"; no ranking/test-selection detail | Med |
| 10 | A.O. Smith Virtual Remote Assistant | https://www.hotwater.com/support.html (via search result) | current | water heaters | P | N | N | N | N | N | Live video help, not algorithmic (search-snippet description) | Low-med |
| 11 | PlumbWise AI, PlumbAI, PlumbIQ, Plumber AI Pro (apps) | https://play.google.com/store/apps/details?id=com.plumbwise.app.ai ; https://www.plumb-ai.com/ | 2025-26 (undated) | plumbing | Y | N/? | N | N | N | N | Photo diagnosis and repair steps; PlumbAI is aimed at homeowners ("before you book a plumber") | Med |
| 12 | measureQuick AI Assist / Smart Diagnostics | https://measurequick.com/ai-assist/ | v3.5.x, 2025-26 | HVAC only | P | Y (implicit "likely causes") | P ("points you at the next thing to check") | Y (re-reads live probe data) | N | Y (live probe data via 80+ Bluetooth tools) | Reads measurements directly from connected probes; no plumbing/electrical mention | Med-high. Nearest functional analogue to the requester's HVAC tool; HVAC-only |
| 13 | Prentis, Bluon AI MasterMechanic, ACLogics, OxMaint | https://www.prentis.co/ ; https://www.bluon.ai/about | 2025-26 | HVAC only | Y | P | ? | ? | N | N | Prentis "AI Copilot for HVAC Technicians"; Bluon: RAG+RLHF, ~50,000 support scenarios, no plumbing/electrical plans stated | Med. Expansion risk to other trades |
| 14 | Trane Technologies Tech Assistant | https://www.trane.com/residential/en/resources/blog/press-releases/trane-technologies-launches-ai-powered-technician-assistant/ | 15 Sep 2025 | HVAC | Y | N | N | P (follow-up questions) | N | N | Searches Trane product documentation, asks follow-ups when unclear | Med-high |
| 15 | Johnstone Supply app virtual assistant | https://www.johnstonesupply.com/mobile-app | 2026 | HVACR | Y | N | N | N | N | N | Identifies equipment, finds parts, answers questions | Low-med |
| 16 | Microsoft Dynamics 365 Field Service Copilot | https://www.microsoft.com/en-us/dynamics-365/blog/business-leader/2024/05/02/enabling-fast-flexible-cost-effective-service-with-microsoft-copilot-in-dynamics-365-field-service/ | 2024-26 | any | Y | N | N | N | N | P (asset history) | Pulls manuals, KB, work-order history into step-by-step guides | Med |
| 17 | ECI GlobalEdge "AI Assist" | https://portalerp.com/noticia/eci-adds-ai-troubleshooting-to-its-globaledge-field-service-app | 2025-26 | field service | P | P | N | N | N | P (work-order + equipment data) | Troubleshooting recommendations from existing work-order and equipment data (search snippet only) | Low |
| 18 | XOi (Vision, Mentors) | https://xoi.io/ | current | HVAC/plumbing/electrical | N | N | N | N | N | P (equipment data) | Photo-based equipment ID, service history, live-video expert mentoring | Med |
| 19 | Streem, Help Lightning | https://www.softwareadvice.com/remote-support/streem-profile/ | current | any | N | N | N | N | N | N | AR/video remote expert | Med |
| 20 | Milwaukee ONE-KEY | https://www.protoolreviews.com/milwaukee-one-key-technology/ | current | tools | N | N | N | N | N | N | Tool tracking, press/crimp verification reports; no diagnostic reasoning found | Med |
| 21 | Fluke (MDA-550 guided setups; eMaint AI, Mar 2026) | https://pressroom.fluke.com/fluke-transforms-emaint-into-purpose-built-ai-platform-to-accelerate-smarter-faster-maintenance-work/ | 16 Mar 2026 | industrial/electrical maintenance | P | N | N | N | N | P | Guided measurement setups; CMMS AI for work orders and manuals; no hypothesis ranking found | Med |
| 22 | Wint, Phyn, Flo by Moen | https://wint.ai/product/technology/ ; https://phyn.com/products/phyn | current | water monitoring | N | N | N | N | N | Y | Continuous leak/anomaly detection on water lines; not technician-symptom-driven | Med-high |
| 23 | Johnson Controls OpenBlue Intelligence (OBI) | https://openblue.johnsoncontrols.com/artificial-intelligence | 2024-26 | HVAC/energy/faults | P | P | N | N | N | Y | Conversational access to building energy, equipment and fault data; not plumbing/electrical | Med |
| 24 | Schneider EcoStruxure PME, Eaton EPMS | https://www.se.com/us/en/product-range/65404-ecostruxure-power-monitoring-expert/ ; https://www.eaton.com/us/en-us/digital/brightlayer/brightlayer-data-centers-suite/eaton-epms/epms-standard.html | current | electrical power monitoring | N | P (root-cause of disturbances) | N | N | N | Y | Passive waveform/root-cause analytics | Med |
| 25 | GitHub: Smart-Diagnostics-Wiring-Viewer | https://github.com/esp046-cyber/Smart-Diagnostics-Wiring-Viewer | 2025 | electrical/P&ID | Y | ? | N | N | N | P (stored diagrams) | Symptom input + retrieval of steps from maintenance history; 0 stars, 4 commits | Med |
| 26 | GitHub: ElectricFaultDiagnosis | https://github.com/fparrale/ElectricFaultDiagnosis | ECICE 2025 | electrical distribution | N | P | N | N | N | Y | Passive BN fault detection on a dataset; 0 stars | Med |
| 27 | Harris/Fluke US5533093 | https://patents.google.com/patent/US5533093 | filed 14 Nov 1994 | telephone lines | Y (trouble tickets) | P | P | Y | Y | P | Iterative refinement to "single probable source" | Med-high |
| 28 | Probook (a16z-led $34M Series A, $6M Sequoia seed) | https://news.crunchbase.com/venture/interesting-startup-deals-ai-defense-tech-healthcare/ | 2026 | home services OS | N | N | N | N | N | N | Dispatch/back-office; no diagnostic claim seen | Low-med |
| 29 | Hugin / Dezide-lineage BN authoring patents | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7385716 | ~2008 | generic | Y | Y | Y | Y | ? | N | Generic Bayesian troubleshooter authoring | Med |

### Takeaway
No row has Y in c, d, e and f for plumbing or electrical. Rows 1, 2 and 3 have the method but not the domain/data coupling. Rows 6, 8 and 11 serve plumbing/electrical but without evidence of sequenced test selection. Row 12 comes closest in function but only for HVAC.

### Cited Findings
- (Table sources above.) Source quality varies. Rows 5, 9, 12, 14, 21 and 22 come from vendor pages (VENDOR CLAIM). Rows 1, 3, 4 and 27 are primary research or patent sources. Rows 6, 7, 8, 11 are app-store or marketing pages.
- Atlas troubleshooting supports "Commercial HVAC, Residential HVAC, and Plumbing", requires Field Pro Standard, and returns "cited sources". — [ServiceTitan help](https://help.servicetitan.com/docs/use-atlas-for-troubleshooting-with-field-pro-in-mobile)
- TradePals lists a plumber companion (PipePal), electrician companion (VoltPal), and others; it says HVAC is not currently offered. — [TradePals](https://tradepals.net/)
- ServiceTitan acquired Conduit Tech and launched the Atlas AI platform at Pantheon 2025. — [ServiceTitan press](https://www.servicetitan.com/press/servicetitan-major-product-expansions-pantheon-2025) (HVAC-oriented; relevance to plumbing/electrical not verified)

### Inferences
- The most plausible way the gap closes is not a startup copying the method but an incumbent (ServiceTitan Atlas, TradePals, measureQuick) extending an existing LLM+documentation product into sequenced questioning. They already have plumbing (Atlas, PipePal) or the sensor-reading pattern (measureQuick). Nothing found shows they have.
- The Jenova/Electrician's Assistant style "measurement-first" behavior suggests a general LLM with a good prompt can imitate (a)-(e) informally. This is a substitute risk, not a rigorous competitor. It has no explicit probabilities, no cost model, no building data.

### Gaps
- Could not verify internals of any commercial app (no hands-on testing, no source access). "Does not meet c" means "no evidence found", not "proven absent".
- Rows 7, 8, 11, 17 rely on thin marketing pages or search snippets.
- TradePals PipePal page itself was not fetched (only the trade list and VoltPal page).

## 3. Adjacent substitutes the requester should worry about

### Takeaway
The biggest practical substitute is the general-purpose chatbot that tradespeople already use, plus manufacturer apps (Rheem, Trane) and remote-expert video. None provides sequenced, building-data-aware test selection, but they set the price of "good enough" at near zero.

### Cited Findings
- General LLM use by tradespeople is widespread. CNN (10 Oct 2025) ran "Your plumber has a new favorite tool: ChatGPT". Fetch was blocked (HTTP 451), so only the headline is verified. — [CNN](https://www.cnn.com/2025/10/10/tech/ai-chatgpt-blue-collar-jobs)
- Housecall Pro survey of 400+ tradespeople in North America: more than 70% tried AI tools, about 40% actively use them (from search summary; I did not open the primary source). — [Contractor magazine via search](https://www.contractormag.com/technology/news/55408579/ai-adoption-accelerates-as-contractors-look-for-productivity-gains)
- ServiceTitan "2026 State of AI in the Trades": 1,032 contractors across seven trades; 12% have embedded AI in operations, 34% are experimenting; barriers: lack of training (44%), integration complexity (44%). The landing page does NOT give trade-level or troubleshooting-specific figures. — [ServiceTitan](https://www.servicetitan.com/guides/2026-ai-in-the-trades)
- A search summary cites a 1,017-contractor survey with active AI engagement rising from 46% (Dec 2025) to 52% (Sep 2026) and electricians reporting the highest satisfaction. The source of that figure was not identified; treat as UNVERIFIED. — [search result summary](https://www.servicetitan.com/guides/2026-ai-in-the-trades)
- Rheem Fix It Tool imitates its Technical Service Analysts' diagnostic process for water heaters. — [Rheem](https://www.rheem.com/fixittool/)
- A.O. Smith offers a Virtual Remote Assistant that lets technicians see through the customer's camera. — [A.O. Smith support](https://www.hotwater.com/support.html)
- Remote-expert and AR tools (Streem, XOi Mentors, Help Lightning) connect a field tech with a senior expert over live video. — [Software Advice Streem](https://www.softwareadvice.com/remote-support/streem-profile/); [XOi](https://xoi.io/)
- XOi says it cuts callbacks and second truck rolls by 40% (VENDOR CLAIM, unverified). — [XOi summary via search](https://www.capterra.com/p/174225/Vision/)
- Trane's Tech Assistant (15 Sep 2025) shows that HVAC OEMs are shipping doc-search assistants into technician apps. — [Trane](https://www.trane.com/residential/en/resources/blog/press-releases/trane-technologies-launches-ai-powered-technician-assistant/)
- Fluke Reliability is adding AI to its eMaint CMMS (beta March 2026). — [Fluke press](https://pressroom.fluke.com/fluke-transforms-emaint-into-purpose-built-ai-platform-to-accelerate-smarter-faster-maintenance-work/)
- Microsoft Dynamics 365 Field Service Copilot supplies step-by-step guidance from manuals, KB and asset history. — [Microsoft](https://www.microsoft.com/en-us/dynamics-365/blog/business-leader/2024/05/02/enabling-fast-flexible-cost-effective-service-with-microsoft-copilot-in-dynamics-365-field-service/)
- Trade-neutral field service software (Housecall Pro, Jobber, FieldEdge) is reported to lack specialized AI diagnostic assistants; the source is a low-quality listicle, so treat as weak. — [Simpro blog via search](https://www.simprogroup.com/blog/hvac-apps)
- Y Combinator and Techstars scans: trade-AI startups surfaced (Bidflow W2026 for electrical bidding, Fresco for takeoffs, Opsonic back office, Bravi fenestration) are estimating/back-office, not diagnostics. A Techstars Spring 2026 company, Plexus, is an "AI observability platform for physical systems" (telemetry anomaly diagnosis). — [YC construction list via search](https://www.ycombinator.com/companies/industry/construction); [Techstars Spring 2026](https://www.techstars.com/newsroom/meet-the-startups-joining-techstars-spring-2026-accelerator-programs)

### Inferences
- The substitute to beat is "a tradesperson pastes the symptom into ChatGPT/Claude/Gemini". Value must come from what a chatbot lacks: the site's actual equipment relationships, live meter/BAS data, calibrated probabilities and cost-ordered checks.
- ServiceTitan is the most dangerous distribution channel because it already embeds LLM troubleshooting for plumbing in the technician app. Its design (cited-source Q&A) differs from the requester's, but a feature addition is plausible.
- Remote-expert video tools substitute for the same pain (junior tech lacks diagnostic order) with a human, and are already purchased.

### Gaps
- No survey data found specific to electricians/plumbers using chatbots for troubleshooting (as opposed to quoting, scheduling, code lookup).
- The primary Housecall Pro survey was not opened; the CNN article body could not be read.
- Did not check forums/YouTube/Reddit usage directly, so the "knowledge on forums and YouTube" substitute is asserted, not measured. Note, however, that arXiv 2606.13220 built its whole benchmark from solved technical forum threads, which evidences that forum knowledge is abundant. — [arXiv HTML](https://arxiv.org/html/2606.13220)

## 4. Search coverage, what could not be searched, and residual risk

### Takeaway
49 distinct queries across product, startup, academic, patent, GitHub and survey sources found no full match. Absence is meaningful for public, indexed products. It is weak for stealth startups, internal tools at large vendors, paywalled databases and non-English markets.

### Cited Findings
Queries run (WebSearch, US-only index), in order:
1. AI troubleshooting assistant for plumbers
2. electrician troubleshooting AI copilot
3. Bayesian diagnosis building plumbing fault
4. decision-theoretic troubleshooting next best test electrical
5. guided troubleshooting water heater app technician
6. Trade Copilot AI trades technicians (returned crypto-trading noise)
7. ServiceTitan Atlas AI technician troubleshooting launch
8. Milwaukee Tool ONE-KEY AI troubleshooting electrician
9. Fluke AI diagnostic guided troubleshooting electrical maintenance
10. electrical panel breaker fault diagnosis decision support system building
11. LLM copilot field technicians building systems troubleshooting startup 2026
12. Y Combinator AI for trades electricians plumbers startup diagnostics
13. "fault tree" OR "Bayesian" troubleshooting plumbing water distribution building hot water recirculation diagnosis paper
14. patent troubleshooting test selection information gain probable cause plumbing OR electrical building
15. "Use Atlas for troubleshooting with Field Pro in mobile"
16. Streem OR XOi OR "Help Lightning" remote expert plumbing electrical AI diagnosis 2026
17. survey tradespeople using ChatGPT electricians plumbers percent AI usage 2026
18. Techstars field service building diagnostics AI startup technicians
19. arXiv LLM agent troubleshooting sequential diagnosis test selection expected information gain
20. GitHub electrical troubleshooting assistant open source diagnosis tree Bayesian
21. "Sherlock" HVAC AI diagnostic assistant technicians plumbing electrical expansion
22. Hey Tradesman OR Fixlify OR "Wrench AI" OR "Tradesmen AI" troubleshooting diagnosis tech
23. AI diagnostic copilot HVAC technicians startup raises seed troubleshooting equipment
24. Schneider Electric OR Eaton OR ABB AI assistant electrical troubleshooting facility technician root cause power monitoring
25. Dezide Advisor troubleshooting Bayesian network decision-theoretic Grundfos
26. Hugin troubleshooting Bayesian network sequential test selection commercial service technicians
27. Microsoft Dynamics 365 Field Service Copilot troubleshooting guide technician agent
28. building water system leak diagnosis technician AI Phyn OR Flo OR "Moen Smart Water" commercial plumbing diagnostics
29. hot water recirculation legionella building water digital twin diagnostic root cause startup
30. Heckerman Breese troubleshooting Bayesian networks Microsoft Answer Wizard printer legacy commercial
31. Dezide customers industries troubleshooting guided Bayesian 2025 OR 2026
32. expert system plumbing fault diagnosis knowledge-based troubleshooting domestic water
33. XOi Technologies AI troubleshooting plumbing electrical 2026 technician assistant
34. Johnson Controls OR Honeywell OR Siemens building technician AI assistant guided troubleshooting electrical plumbing 2026
35. "AI foreman" OR "AI journeyman" electrician troubleshooting app
36. Bayesian active fault isolation leakage localization water distribution networks Puig sensor test selection
37. PlumbPal OR "PlumbWise" OR "Plumber's Assistant" AI plumbing diagnosis app readings pressure troubleshooting steps
38. Google Patents guided diagnosis technician recommends next diagnostic test probability ranked causes water heater OR plumbing OR electrical panel
39. Ridgid Emerson OR Klein Tools OR Fluke Connect AI assistant troubleshooting app launched 2026 plumbers electricians
40. Johnstone Supply OR "Parts Town" OR Lennox OR Trane OR Carrier technician app AI troubleshooting 2026
41. LLM agents building fault diagnosis BAS data technician question benchmark arXiv 2026
42. Housecall Pro OR FieldEdge OR Jobber AI technician diagnostic troubleshooting feature
43. Product Hunt AI electrician troubleshooting diagnostic app launch
44. MeasureQuick AI diagnostics smart tools sensor readings technician guided
45. Wint OR Wateroam OR "Samsara" commercial building water systems AI root cause investigation plumbing technician
46. water heater OR boiler Bayesian network fault diagnosis troubleshooting probabilistic test sequence
47. electrical wiring fault localization building technician sequential measurement selection probabilistic reasoning
48. Trane Technologies AI-powered technician assistant launch HVAC field service
49. Crunchbase stealth startup "troubleshooting" AI electricians OR plumbers seed funding 2026

Pages fetched and read (WebFetch, summarized by a fast model, so wording is second-hand): jenova.ai electrician assistant; ServiceTitan Atlas home and troubleshooting help pages; Rheem Fix It; Prentis; Bluon; tradesman-ai.com (redirect to CrewMAKR, no content); tradesmanai.co.uk (UK gas/boiler engineers, flowchart diagnostics); Smart-Diagnostics-Wiring-Viewer; ElectricFaultDiagnosis; ElectriciansMate; TradePals and VoltPal; PlumbAI; measureQuick AI Assist; Dezide decision-technology and customers pages; arXiv 2606.13220 (abs, HTML, PDF); arXiv 1703.05452 abs; US5533093; ServiceTitan 2026 AI report. Not obtained: PlumbWise Play-store page (fetch returned no content); CNN article (HTTP 451); IEEE 9880532 page (empty fetch; relied on TU Delft PDF snippet); arXiv 1703.05452 PDF (binary).

### Inferences
Residual risk, ranked:
1. HIGH: stealth or very early startups. YC/Techstars were checked only through search snippets and two cohort pages, not by reading full directories. A seed-stage "diagnostic copilot for electricians/plumbers" with Bayesian test selection could exist unindexed. LinkedIn, Crunchbase and PitchBook were not searched directly (Crunchbase surfaced only via news pages).
2. HIGH: incumbents' internal roadmaps (ServiceTitan, Trane, Johnson Controls, Siemens, Schneider, Fluke, Milwaukee). Public docs show LLM/RAG, but roadmap or beta features are invisible.
3. MED-HIGH: Dezide or similar BN-troubleshooting vendors (Hugin-based integrators) may have private building-services deployments. Customer pages are marketing-selected.
4. MED: patents. Search engines index patents poorly; applications from 2025-26 are largely unpublished (18-month delay).
5. MED: academic work behind paywalls or in non-English venues (Chinese building electrical/water literature in particular). Only open-access snippets were viewed.
6. MED: very recent arXiv work. The June 2026 Marozzo and Liò paper surfaced only by luck on the "information gain" query; similar preprints on LLM sequential diagnosis may be missed.
7. LOW-MED: app stores. Many small AI plumber/electrician apps exist (PlumbWise, PlumbIQ, PlumberAI, SparkyPal, Elec-Mate, Master Electrician). I sampled a few, did not install any, and cannot rule out one that implements adaptive question sequencing.

Suggested honest wording for the gap, which this evidence supports: "We found no existing product, paper or patent (as of Oct 2026, public sources) that combines cost- and information-gain-ordered next-check recommendation with posterior updating and stopping, scoped to a single technician-reported symptom and driven by building data and equipment-relationship maps, for building plumbing or electrical systems. The method family is established (decision-theoretic troubleshooting; Dezide) and chat-based plumbing/electrical assistants exist; our claim is about the domain, the symptom-scoped map use and the data coupling."

### Gaps
- Not searched or not reachable: LinkedIn company search, Crunchbase/PitchBook databases, Espacenet/Google Patents structured CPC queries, Google Scholar, IEEE/Elsevier full text, non-English sources, app-store review mining, Reddit/forum survey data on AI use, and any hands-on testing of competitor apps.
- The web search tool returned noisy or marketing-heavy results for several queries (for example the "Trade Copilot" query returned only crypto tools). Several summaries came from SEO listicles; those were used only for pointers, not as evidence.
- Evidence strength differs: Dezide, the arXiv paper and the patents are primary or semi-primary. Everything about TradePals, ElectriciansMate, Jenova and the plumbing apps is marketing text.
