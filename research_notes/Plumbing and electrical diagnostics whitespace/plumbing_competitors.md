# Competitive landscape: commercial building plumbing / water-system operations, diagnostics, maintenance (as of Oct 2026)

Method note (read first). This was a breadth-first pass of roughly 40 searches/fetches. "Verified" below means a fetched page or search-result text said it; I flag the weaker cases. Many fetches were run through a summarizing model, so quoted phrases are as returned by the fetch tool and should be re-checked against the live page before being used in a published report. Several named companies were NOT researched (listed under Gaps). I did not find any product that does ranked "which test next" for a plumbing symptom, but absence of evidence from ~40 queries is not proof of absence; what I checked for each is stated.

---

## Q1. Leak / flow monitoring: who exists, what do they actually do, and do they diagnose or only detect/alert?

### Takeaway
Leak/flow monitoring is the most crowded plumbing category and almost entirely detect -> alert -> (auto-shutoff) -> report. Nothing I found helps a technician decide which physical check to do next to find the cause of a symptom. Phyn changed hands for ~$25M in 2025, while WINT raised $36M (Series D) and sells an insurer-backed warranty, so capital is flowing to "prevent water damage" (insurance-driven), not to technician troubleshooting.

### Cited Findings
- **WINT (Water Intelligence)**: AI water platform for commercial real estate, multifamily, enterprises, facility management, data centers, hospitality, construction, industrial. Home page language: "real-time anomaly detection and remote automatic shut off"; claims "20-25% Less water consumption" and "90% Less damage"; monitors nine system types including domestic cold/hot water, HVAC, cooling towers, sprinklers, irrigation. Customers listed: Empire State Realty Trust, Mace, The Hartford; HSB partnership with water-damage warranty. The fetch of the home page found no explicit root-cause or leak-pinpointing language and no technician-guidance language (I read the home page only, not docs or case studies) — [wint.ai](https://wint.ai/)
- **WINT funding**: $35M Series C Aug 2023 (Inven Capital, Insight Partners) — [TechCrunch](https://techcrunch.com/2023/08/10/water-intelligence-startup-wint-nabs-35m-to-help-companies-find-and-stop-leaks/), [Facilities Dive](https://www.facilitiesdive.com/news/wint-water-management-leak-detection-fundraise/690646/). $36M Series D led by LIP Ventures and Inven Capital; the fetched Yahoo Finance article was dated September 2026 and reports 2025 results of 1.15B gallons saved, ~$100M damage prevented, 1,300+ incidents addressed, "the industry's only global insurer warranty", and expansion to "water temperature analysis and boiler health monitoring tools"; customers HP, Suffolk Construction, Empire State Building — [Yahoo Finance](https://finance.yahoo.com/technology/ai/articles/wint-lands-36m-series-d-114900782.html) (secondary republisher; the Series D date is from the fetch summary and should be confirmed; a second hit reports the same raise at [Ventureburn](https://ventureburn.com/wint-raises-36m-ai-water-intelligence/)).
- **Flo by Moen (Fortune Brands)**: "Property Water Security System" for rental/multifamily property managers: web dashboard, devices track pressure, flow rate, temperature; alerts by dashboard/text/call/email; automatic shutoff; consumption analytics. Fortune Brands quote: it "allows users to communicate within the system so it's easy to track when maintenance crews have resolved potential issues." The article describes no technician-specific diagnostic features — [Multifamily Executive](https://www.multifamilyexecutive.com/property-management/flo-by-moen-introduces-water-security-system-for-multifamily-properties_o)
- **Moen Flo Smart Water Network (CES 2024)**: 240 pressure/flow measurements per second on the main line; AI learns the household "fingerprint", detects leaks as small as one drop per minute, and groups discovered fixtures into categories for reporting. Residential-first; shipping to production builders — [CEPRO](https://www.cepro.com/news/moen-flo-smart-water-network-monitor-emergency-shutoff-ai-ces-2024/132485/) and [Moen KBIS release](https://kbis.com/exhibitor_news/beyond-smart-moen-leverages-artificial-intelligence/).
- **Phyn**: ultrasonic flow sensing + "HD pressure analysis" + AI; products Phyn Smart Water Assistant, Smart Water Sensor, Phyn Plus (pro-installed shutoff), Phyn Dashboard. Sold via insurers, utilities, property managers, builders, plumbers; plans to expand "Preferred Installer Network" in builder and multifamily. Acquired May 23, 2025 from Belkin by an investor group led by Jonathan Scott — [Phyn press release](https://phyn.com/blogs/press-releases/phyn-acquired-by-investment-group-led-by-property-brothers-jonathan-scott-to-accelerate-growth-in-smart-water-solutions). Price reported ~$24.9-25M (Los Angeles Business Journal / Korea Daily headlines; I did not open them) — [LABJ](https://labusinessjournal.com/engineering/investment-group-buys-phyn-for-nearly-25-million/), [Korea Daily](https://en.koreadaily.com/phyn-startup-acquisition-25m/). Earlier funding: $12M from Belkin/Uponor in 2019, $37M total at that time — [Gearbrain](https://www.gearbrain.com/smart-water-monitoring-system-phyn-2636631940.html).
- **Bluebot**: clamp-on ultrasonic meter for 3/4" to 4" pipes, leak alerts and multi-property monitoring, submetering — [bluebot.com/business](https://www.bluebot.com/business/). March 2, 2026: American Leak Detection (Water Intelligence plc) became preferred partner: resells/white-labels Bluebot devices, ALD is Bluebot's "exclusive installation and repair services partner for online sales", to integrate with ALD's leak-detection network; complements ALD's existing StreamLabs partnership — [TipRanks](https://www.tipranks.com/news/company-announcements/water-intelligence-expands-smart-leak-prevention-push-with-bluebot-deal). I found no Bluebot funding round.
- **StreamLabs**: ultrasonic monitor + shutoff valve (StreamLabs Control), app alerts — [Nest Alpha roundup](https://www.nestalpha.com/post/best-smart-water-leak-detectors) (weak secondary source). Already tied to ALD as above.
- **Buoy Labs**: described as using machine learning to work out what is causing water usage (fixture disaggregation in residential app) — [Gearbrain](https://www.gearbrain.com/smart-leak-and-flood-detectors-2563785823.html) (snippet only).
- **Municipal/utility metering analytics (not building-level)**: Badger Meter BlueEdge (software analytics on water quality, usage, asset performance; acquired SmartCover Systems for $185M, Jan 2025) — [Badger Meter](https://www.badgermeter.com/newsroom/badger-meter-introduces-blueedge/), [10-K](https://www.sec.gov/Archives/edgar/data/9092/000095017025020889/bmi-20241231.htm). Mueller and Xylem/Sensus named as competitors in same 10-K; Xylem sold international Sensus to AURELIUS May 2026 and kept North American Sensus. Buyer is the utility, not the building technician.
- **Adjacent patent evidence**: Pillar Technologies reportedly holds patents fusing pipe-coupled flow data with humidity/temp/liquid sensors to confirm whether an anomaly is localized to the monitored area (localization of leak extent, not a repair-step recommender) — [Patsnap summary](https://www.patsnap.com/resources/blog/articles/home-water-leak-detection-technology-2026-patents/) (secondary).

### Inferences
- The leak-monitoring buyer is the owner/insurer/property manager, and the value proposition is avoided claims. The technician who is dispatched after an alert gets "there is an anomaly / water is off" and must still find the cause by trial and error; ALD's white-label-plus-service tie-up is the closest thing to "monitoring leads to a human responder," but ALD's value is physical leak location services, not software guidance (inferred from the deal description).
- Insurer-backed warranties (WINT-HSB) show the commercial model that exists; a diagnosis-guidance product would need a different buyer (service contractor / facility maintenance) and different proof.

### Gaps
- Did not verify Fluid, Hydrosmart (the name collided with unrelated water-treatment firms; I found no Legionella/flow "Hydrosmart" product), Honeywell/Mueller analytics at building scale, "flow-based AI for commercial/multifamily" beyond WINT/Moen/Phyn/Bluebot.
- WINT docs, case studies and G2 reviews were not read, so I cannot say WINT has no leak-location or "recommended action" feature; I only checked the home page and press coverage.
- No G2/Capterra review complaints gathered for any monitoring vendor.

---

## Q2. Water quality / Legionella / water-management-program (WMP) software and temperature monitoring

### Takeaway
This category is dominated by compliance documentation (ASHRAE 188 plans, logs, audit trails) plus wireless temperature sensing and automated flushing. It tells the building when a number is out of range; I found no product claiming to tell a technician why a hot-water loop is failing or which check to run next.

### Cited Findings
- **HC Info LAMPS**: cloud platform for water quality management plans, data benchmarking, training; claims alignment with ASHRAE 188/514, CMS QSO-17-30, Joint Commission EC.02.05.02, VHA 1061 — [hcinfo.com](https://hcinfo.com/).
- **Oxmaint Legionella compliance**: schedules prevention tasks, captures results digitally, generates audit-ready records — [Oxmaint](https://oxmaint.com/industries/facility-management/legionella-risk-management-for-facility-maintenance-teams). iFactory and EnVigilance also market ASHRAE 188 compliance content with temperature monitoring ([iFactory](https://ifactoryapp.com/industries/hvac/legionella-prevention-water-management-program), [EnVigilance](https://envigilance.com/compliance/legionella-compliance/)). These look like vendor marketing pages of uncertain traction.
- **SmarterWater (Smarter Technologies, UK-based; phone number is UK)**: pipe and tank temperature sensors, automatic flushing units, "temperature trends data and system profiling", alerts including freeze and scald risk, SmarterView cloud platform. The page did not explicitly describe root-cause diagnostics for temperature failures — [smarterwater.tech/legionella](https://smarterwater.tech/legionella/).
- **Hydrosense (Legionella test kits)**: 25-minute on-site Legionella pneumophila test with mobile reader and online result storage — [hydrosense-legionella.com](https://hydrosense-legionella.com/products/).
- **Watts IntelliStation (digital mixing valve)**: monitors "pressure, temperature, and flow/BTU data", +/-2 F control, BACnet IP/MSTP and Modbus to the BAS, Watts OnSite app notifications, sanitization mode; page reviewed did not list fault codes or troubleshooting procedures (those would be in the IOM manual, which I did not read) — [Watts IntelliStation](https://www.watts.com/products/plumbing-flow-control-solutions/mixing-valves/digital-mixing-valves/intellistation) and search summary at [Watts digital mixing valves](https://www.watts.com/products/plumbing-flow-control-solutions/mixing-valves/digital-mixing-valves).
- **CDC toolkit** states potable-water control framework that these products map to — [CDC](https://www.cdc.gov/control-legionella/php/toolkit/potable-water-systems-module.html).
- **M&A signal**: Watts acquired Josam (drainage/plumbing, Jan 2024, ~$99M net), I-CON Systems (Jan 2025, ~$70.3M net), Haws (Nov 2025) — [Watts 10-K FY2024](https://www.sec.gov/Archives/edgar/data/795403/000155837025001102/wts-20241231x10k.htm), [10-Q Q1 2025](https://www.sec.gov/Archives/edgar/data/795403/000155837025006887/wts-20250330x10q.htm), [Watts 10-K FY2025](https://www.sec.gov/Archives/edgar/data/795403/000110465926018541/wts-20251231x10k.htm) (Haws date from search summary). I did not verify what I-CON Systems does.
- Xylem closed the $7.5B Evoqua acquisition May 2023; Xylem Vue is a utility-oriented data platform — [Xylem Vue](https://www.xylem.com/en-us/brand/xylem-vue/platform/), [WWD](https://www.wwdmag.com/wastewater-treatment/press-release/33005632/xylem-completes-acquisition-of-evoqua-in-75b-transaction).

### Inferences
- Compliance software is documentation-heavy; sensors give alarms on out-of-range temperature. The gap between "loop is below 140 F at distal point" and "recirc pump, balancing valve, mixing valve, or heater is the cause" appears unserved in what I read, but I did not review Nexus, Opti, Vanguard, Sensorex or Nuvolo (see Gaps).

### Gaps
- Not researched: Nexus, Opti, Vanguard, Sensorex, Nuvolo's water-management module, Xylem's/Watts's connected Legionella products by name, any US-specific temperature-monitoring startups.
- No pricing, funding, or traction for the compliance platforms.
- No G2/Capterra reviews gathered.

---

## Q3. Hot-water / recirc / boiler / water-heater and pump/booster monitoring (OEM connected products)

### Takeaway
OEMs offer remote monitoring and alarms for their own equipment; what I could verify is limited to marketing-level statements. Grundfos is the clearest "predictive" claim, but its public language is condition monitoring and fault prediction, not step-by-step diagnosis.

### Cited Findings
- **Grundfos iSOLUTIONS**: "real-time monitoring, remote control, fault prediction and system optimisation"; MONITOR uses a combined sensor (vibration, liquid temperature, ultrasonic); Hydro MPC-E booster integrates with iSOLUTIONS and BMS for remote monitoring and predictive-maintenance alerts. The page fetched had no detail on alarm diagnostics or recommended troubleshooting actions — [Grundfos iSOLUTIONS](https://www.grundfos.com/solutions/learn/grundfos-isolutions), [Grundfos eCademy](https://www.grundfos.com/us/learn/ecademy/all-courses/condition-monitoring-for-pumps-and-systems/an-introduction-to-grundfos-isolutions-monitor), [Construction Week](https://www.constructionweekonline.com/features/grundfos-aftermarket-solutions).
- **Lochinvar**: SMART SYSTEM controls with CON-X-US remote monitoring; **Rheem**: EcoNet; **Bradford White**: "Smart Control Technology ... real-time diagnostics" — all from one aggregator search page, so treat as unverified marketing summaries — [theplumbingdirectory brand comparison](https://theplumbingdirectory.com/water-heaters/brands/). I did not open OEM pages.
- **WINT** added "boiler health monitoring" tools (see Q1 source) — a monitoring vendor moving into heating-plant plumbing.

### Inferences
- OEM remote monitoring is equipment-specific and mostly serves the OEM/rep/distributor service model; cross-vendor, system-level (heater + recirc + mixing valve + pump) diagnosis is a plausible gap but not confirmed.

### Gaps
- Not researched: A.O. Smith, Taco, Armstrong, Bell & Gossett connected offerings, Sulzer, KSB, Flowserve, Xylem pump analytics. No evidence either way about their alarm-diagnostic content.
- Did not read any IOM/manual for fault trees.

---

## Q4. Field service management (FSM) for plumbers and their AI: does any offer diagnostic guidance?

### Takeaway
Only ServiceTitan (Atlas / Field Pro, with Bluon) states AI-guided diagnosis and troubleshooting, and the strongest evidence is HVAC-oriented. Its language is generic knowledge retrieval, not likelihood- or cost-ranked next-test guidance for a plumbing symptom.

### Cited Findings
- **ServiceTitan Atlas**: "Access equipment knowledge, troubleshooting guides, calculators, diagnostics, and replacement parts from the field"; "Look up job details and customer history in natural language"; caveat "Atlas may generate inaccurate, incomplete, or outdated responses." Capability depends on Field Pro subscription and loaded equipment docs — [ServiceTitan help: Atlas](https://help.servicetitan.com/commercial/docs/atlas-home).
- **Pantheon 2025 press release**: "From pre-job briefs and real-time diagnostics, to daily activity summaries and follow-up handoffs into Marketing Pro, ServiceTitan now equips technicians and managers with AI-driven coaching, actionable insights, and AI-guided diagnosis & troubleshooting for both commercial and residential equipment." The page referenced plumbing only in navigation; no plumbing-specific diagnostic announcement was found there — [ServiceTitan press](https://www.servicetitan.com/press/servicetitan-major-product-expansions-pantheon-2025).
- **ServiceTitan plumbing AI blog**: Atlas gives "instant access to equipment documents, service history, replacement parts, manuals, and troubleshooting guidance—all without calling the office or flipping through old PDFs"; techs can "pull up calculations, diagnostic tests, and job details with a quick voice or text query." Other AI features are business-side (call analysis, dispatch, ads, job-value prediction) — [ServiceTitan blog](https://www.servicetitan.com/blog/plumbing-ai-tools-for-business).
- **Bluon MasterMechanic**: "step-by-step answers to questions HVAC operators may have during upgrades, replacements, repairs and troubleshooting activities"; trained on "50,000 real-world problem-solution scenarios" (later marketing cites 135,000 calls — a conflict I could not reconcile, likely just updated figures); HVAC-only, no plumbing mention — [Facilities Dive](https://www.facilitiesdive.com/news/bluons-new-generative-ai-tool-hvac-operators/692276/); the 135,000-call figure is from a search summary of [RazorSync](https://www.razorsync.com/resources/5-hvac-troubleshooting-apps-every-service-tech-needs/). BusinessWire release returned HTTP 403; URL: [BusinessWire](https://www.businesswire.com/news/home/20230829582808/en/Bluon-Introduces-MasterMechanic-an-Innovative-AI-Based-on-50000-Tech-Support-Calls-to-Help-HVAC-Technicians-Diagnose-Problems-in-the-Field). Housecall Pro also lists a Bluon integration (title seen only) — [Housecall Pro help](https://help.housecallpro.com/en/articles/11557855-bluon-integration).
- **Reviews**: ServiceTitan rated about 4.5/5 on G2 (345+ reviews) and 4.4 on Capterra; common complaints are long setup, learning curve, expensive add-ons, slow support, billing/cancellation issues (BBB). None of the cited complaint summaries concern diagnostic guidance — [G2](https://www.g2.com/products/servicetitan/reviews), [Capterra](https://www.capterra.com/p/150053/ServiceTitan/reviews/), [OneCrew summary](https://www.getonecrew.com/post/servicetitan-reviews). Percentages come from aggregator blogs.
- **General AI use by plumbers**: CNN reports plumbers using ChatGPT and Housecall Pro-type tools — [CNN](https://www.cnn.com/2025/10/10/tech/ai-chatgpt-blue-collar-jobs). A "PlumberGPT" and "PlumbVision" are mentioned only in a low-quality listicle snippet — [empathyfirstmedia](https://empathyfirstmedia.com/best-plumbing-contractor-ai-tools/); I could not verify they exist as products.

### Inferences
- ServiceTitan's diagnostic AI is a manuals/knowledge retrieval layer on its own installed base; I found no claim of cost/likelihood ranking or use of live building sensor data. ServiceTitan is the largest likely entrant if the niche proves valuable.

### Gaps
- Jobber, Housecall Pro, FieldEdge, Workiz, FieldPulse AI features were not individually checked (only listed in comparison search results). I therefore cannot say they lack diagnostic guidance.
- The Atlas fetch summarizer said Atlas is "trade-agnostic"; that was the summarizer's inference, not a ServiceTitan quote.

---

## Q5. Facility / CMMS platforms with plumbing modules

### Takeaway
CMMS vendors are adding AI for work-order drafting, PM generation and asset recognition, not symptom-to-test diagnosis. Evidence here is thin and mostly from comparison blogs.

### Cited Findings
- **UpKeep**: mobile CMMS (founded 2014) with "Nova" AI assistant that chats, speaks, drafts work orders, and in Agent mode can change CMMS records; sells UpKeep Edge wireless IoT sensors separately — [Facilio comparison](https://facilio.com/blog/upkeep-vs-limble-cmms/), [aitoolgiant](https://www.aitoolgiant.com/reviews/best-ai-cmms-maintenance-tools-2026.html) (third-party blogs).
- **Limble**: AI PM builder ingests unstructured manuals and asset data into PM checklists; 2026 Winter Release added Asset Snap (identify/log assets from a photo), Resource Planning, MCP integration layer — same sources.
- **Johnson Controls OpenBlue** integration library lists leak-detection integrations (Wellstat and Water Intelligence) — [JCI OpenBlue integrations](https://www.johnsoncontrols.com/openblue/openblue-data-platform/integrations).
- **Facilio** publishes a "plumbing dispatch software for multi-site operators" guide (positions itself in this space) — [Facilio](https://facilio.com/blog/plumbing-dispatch-software/).

### Inferences
- CMMS AI centers on documentation and records. No cited feature recommends the next diagnostic step.

### Gaps
- Nuvolo, Fiix, ServiceChannel, Accruent, IBM Maximo: no direct evidence gathered (Nuvolo returned nothing relevant). Cannot claim they lack diagnostics.

---

## Q6. Plumbing-specific AI copilots, digital twins, as-built documentation, and sewer/camera inspection AI

### Takeaway
Sewer inspection AI is real and funded, but it serves municipalities/contractors and classifies pipe defects (a different problem: infrastructure condition, not building-symptom diagnosis). I found no credible plumbing-specific diagnostic copilot.

### Cited Findings
- **RedZone Robotics**: robotic inspection + services, NASSCO-certified defect coding, IntegrityPRO software powered by VODA.ai, AI routines in Solo robots. Milestone Partners led acquisition (announced "June 4"; year not captured in the snippet) — [RedZone](https://redzone.com/services/), [IntegrityPRO](https://redzone.com/integritypro/), [Trenchless Technology](https://trenchlesstechnology.com/milestone-partners-acquires-redzone-robotics/).
- **Envirosight**: introduced machine learning in ROVVER X Aug 2025 for automated detection/classification of cracks and joints; early adopters report 40% less post-inspection reporting time (search summary; the crawler product page itself did not describe AI defect detection, only 3D modeling via WinCan, and listed buyers: municipalities, contractors, DOTs, utility locators, engineering firms, CIPP installers) — [Envirosight crawlers](https://envirosight.com/products/crawlers/).
- **VODA.ai**: risk modeling and inspection analytics for collection mains — [voda.ai](https://voda.ai/collection-inspections/).
- **ULC Technologies**: robotic cased-pipeline inspection services — [ULC](https://ulctechnologies.com/services/robotic-cased-pipeline-inspection/).
- Generic LLM copilots (ChatGPT, Microsoft Copilot) are what plumbers actually use per CNN (link in Q4). Microsoft Dynamics 365 Field Service Copilot gives next-step guidance from error codes (e.g., "green warning light, error code 45") — [9altitudes](https://9altitudes.com/insights-events/articles/ai-in-the-field-how-copilot-elevates-service-operations); general field-service, not plumbing-specific.
- Patent search (Google Patents via search) surfaced pipeline fault detection, leak location, and water-network monitoring patents, none describing recommending next technician tests — [US20210293654A1](https://patents.google.com/patent/US20210293654A1/en), [WO2012153147A1](https://patents.google.com/patent/WO2012153147A1/en), [US6310555B1](https://patents.google.com/patent/US6310555B1/en). One search only, not a systematic patent landscape.

### Inferences
- The space between "alarm fires" and "technician has a ranked checklist" looks empty in plumbing among what I found; the closest analogs are Bluon (HVAC) and Dynamics 365 (generic).

### Gaps
- Not researched: Pipe-Vision (no hit), digital twin/riser-documentation startups, YC/Techstars directories, LinkedIn job posts, Crunchbase/PitchBook pages for most firms. RedZone acquisition year not confirmed.

---

## Q7. Building-wide FDD/analytics platforms that claim water/plumbing

### Takeaway
Platforms that mention water cover it with one or a few "spike in consumption / leak" rules; their diagnosis machinery is HVAC. Water/plumbing is not a primary use case for any I reviewed.

### Cited Findings
- **Clockworks Analytics** (MIT Building Science origin, 2008): says it detects deviations "across HVAC, electrical, plumbing, and other critical building systems", identifies relationships between issues, diagnoses root cause and provides recommended actions; water skill named "Spike in Water Consumption – Potential Water Leak" — [Clockworks software](https://clockworksanalytics.com/software/), [FDD white paper](https://go.clockworksanalytics.com/hubfs/FDD-White-Paper.pdf). Note: the identical skill description appeared in the Willow fetch below; which vendor's page owns the text is ambiguous (possibly a shared skills catalog or a re-post); verify before attributing.
- **Willow**: the fetched skills page named only one water skill, the same "Spike in Water Consumption – Potential Water Leak" ("continuously analyzes water consumption data to flag unexpected spikes that often precede the discovery of leaks"); no legionella, hot water or pump skills named — [Willow skills and insights](https://willowinc.com/willow-skills-and-insights/3002/).
- **Mapped**: AI data-integration layer (not an FDD product); $42.8M raised over 5 rounds, Series B on Jun 26, 2025, investors include Allegion and MetaProp (Tracxn) — [Tracxn](https://tracxn.com/d/companies/mapped/__RK_eOAv3lvMqXaDpp_YoNzyjCX1Mpg2S4aS7OG15Th8), [PitchBook](https://pitchbook.com/profiles/company/434211-22).
- **JCI OpenBlue**: marketed for remote diagnostics, predictive maintenance, compliance monitoring; leak detection reached through third-party integrations (Wellstat, Water Intelligence) — [JCI 10-K FY2025](https://www.sec.gov/Archives/edgar/data/833444/000083344425000097/jci-20250930.htm), [OpenBlue integrations](https://www.johnsoncontrols.com/openblue/openblue-data-platform/integrations).
- Market context: H1 2026 smart-building consolidation described as a $5.6B wave — [ai-smart-buildings.com](https://www.ai-smart-buildings.com/when-your-ai-vendor-gets-acquired-the-building-os-continuity-clause-h1-2026s-5-6b-consolidation-wave-just-made-mandatory/) (low-reliability blog, headline only), [Memoori](https://memoori.com/ai-powered-smart-building-startups-2026/).

### Inferences
- Water coverage inside BAS-centric FDD stops at consumption anomalies; cause-level diagnosis for plumbing symptoms is not shown.

### Gaps
- Brainbox, KGS, Siemens, Honeywell Forge, Schneider: not researched beyond appearing in results. Could not verify any water/plumbing rule libraries for them.

---

## Q8. Does any competitor guide a technician through WHICH TEST OR CHECK TO DO NEXT for a plumbing symptom, ranked by likelihood/cost?

### Takeaway
I found no product that does this for plumbing. The nearest are ServiceTitan Atlas ("AI-guided diagnosis & troubleshooting", generic and manual-driven) and Bluon MasterMechanic (HVAC, step-by-step LLM answers). Neither claims likelihood- or cost-ranked next-check selection, and neither is shown using live sensor data.

### Cited Findings
- Closest quote, ServiceTitan: "AI-guided diagnosis & troubleshooting for both commercial and residential equipment" — [ServiceTitan press](https://www.servicetitan.com/press/servicetitan-major-product-expansions-pantheon-2025). What I checked: that press page, the Atlas help page, and the plumbing AI blog. No ranking, probability or cost language was found in any.
- Bluon: "step-by-step answers ... during upgrades, replacements, repairs and troubleshooting activities", HVAC only — [Facilities Dive](https://www.facilitiesdive.com/news/bluons-new-generative-ai-tool-hvac-operators/692276/).
- Dynamics 365 Field Service Copilot returns next-step guidance from a described symptom (generic field service) — [9altitudes](https://9altitudes.com/insights-events/articles/ai-in-the-field-how-copilot-elevates-service-operations).
- Monitoring products checked (WINT home page, Moen multifamily article, SmarterWater, Watts IntelliStation page, Grundfos iSOLUTIONS page, Clockworks/Willow water skills) did not show next-test guidance on the pages I read.

### Inferences
- A reasonable working hypothesis: no vendor is shipping probabilistic next-test selection for plumbing symptoms as of the pages read. The strongest caveat is that I read marketing pages, not product docs, demos or training material, and several large vendors (Siemens, Honeywell, Schneider, Xylem, Nuvolo, Maximo) were not examined.
- Plausible near-term entrants: ServiceTitan (installed base, Atlas, Bluon partnership), Bluon (could extend beyond HVAC), WINT (moving into boiler and temperature analysis).

### Gaps
- No access to ServiceTitan Field Pro product demos, Bluon's app, or any in-app content. LinkedIn job posts, patents beyond one search, and YC/Techstars directories were not mined.

---

## Q9. Visible gaps (reviews complaining, missing features)

### Takeaway
I found little direct review evidence about plumbing diagnostics. The gap case rests mainly on what the products do not claim, which is weaker than user complaints.

### Cited Findings
- ServiceTitan complaint themes are setup/learning curve/add-on cost/support/billing, not diagnostics — [OneCrew](https://www.getonecrew.com/post/servicetitan-reviews), [BBB](https://www.bbb.org/us/ca/glendale/profile/digital-marketing/servicetitan-inc-1216-1290182/complaints).
- Atlas's own help page warns it "may generate inaccurate, incomplete, or outdated responses" and depends on what equipment documentation the admin loads — [ServiceTitan help](https://help.servicetitan.com/commercial/docs/atlas-home).
- Fortune Brands quote about tracking when "maintenance crews have resolved potential issues" shows the multifamily product tracks resolution, not diagnosis — [Multifamily Executive](https://www.multifamilyexecutive.com/property-management/flo-by-moen-introduces-water-security-system-for-multifamily-properties_o).

### Inferences
- Review sites for monitoring vendors were not mined, so claims of user-reported gaps cannot be made.

### Gaps
- No G2/Capterra review text on WINT, Phyn, Moen Flo commercial, Bluebot, LAMPS, UpKeep, Limble. Would need a dedicated pass.

---

## Q10. Recent M&A and funding (2023-2026) signalling market direction

### Takeaway
Capital and M&A are concentrated in (a) insurer/owner-driven leak prevention (WINT), (b) distribution/service tie-ups around monitoring devices (ALD-Bluebot, ALD-StreamLabs), (c) strategic buys of plumbing hardware and controls by Watts, and (d) utility metering software (Badger-SmartCover). The consumer-leak pioneer Phyn sold for roughly $25M, a modest outcome.

### Cited Findings
- WINT: $35M Series C (Aug 2023); $36M Series D (reported Sept 2026) — sources in Q1.
- Phyn: acquired by Jonathan Scott-led group May 2025, reported ~$24.9-25M — sources in Q1.
- Water Intelligence/ALD-Bluebot preferred partnership Mar 2, 2026 — [TipRanks](https://www.tipranks.com/news/company-announcements/water-intelligence-expands-smart-leak-prevention-push-with-bluebot-deal).
- Badger Meter acquired SmartCover Systems, $185M, Jan 2025 — [10-K FY2024](https://www.sec.gov/Archives/edgar/data/9092/000095017025020889/bmi-20241231.htm) (via search summary).
- Watts: Josam (Jan 2024), I-CON Systems (Jan 2025), Haws (Nov 2025) — sources in Q2.
- Xylem-Evoqua $7.5B (closed May 2023); international Sensus sold to AURELIUS (May 2026) — sources in Q1/Q2.
- Mapped Series B Jun 2025 — Tracxn link in Q7.
- RedZone Robotics acquired by Milestone Partners — [Trenchless Technology](https://trenchlesstechnology.com/milestone-partners-acquires-redzone-robotics/) (year not confirmed).
- ServiceTitan added Atlas/Field Pro/Bluon AI diagnostics in 2025 — [ServiceTitan press](https://www.servicetitan.com/press/servicetitan-major-product-expansions-pantheon-2025).

### Inferences
- Incumbent hardware makers are buying products and controls, which suggests that a diagnostics software layer would more likely be acquired than compete head on.
- ServiceTitan's AI-diagnosis push is at the contractor-software layer; an independent tool aimed at building maintenance technicians is not directly addressed by it from what I read.

### Gaps
- Deal terms for several items rest on search summaries, not primary filings. Crunchbase/PitchBook funding for Bluebot, Fluid, SmarterWater, Hydrosense not retrieved.

---

## Not researched (explicit coverage list for the report writer)
Fluid, Buoy (beyond one snippet), Hydrosmart (no relevant product found), Nexus, Opti, Vanguard, Sensorex, Nuvolo, Fiix, ServiceChannel, Accruent, IBM Maximo, A.O. Smith, Taco, Armstrong, Bell & Gossett, Sulzer, KSB, Flowserve, Jobber, FieldEdge, Workiz, FieldPulse, Brainbox, KGS, Siemens, Honeywell Forge, Schneider, Pipe-Vision, digital-twin/riser-documentation startups, LinkedIn job posts, YC/Techstars directories, any systematic patent landscape.
