# Causes of hot-water complaints in commercial / multifamily central DHW with recirculation: cause taxonomy for a technician-guided diagnostic model

**How to read this file.** Evidence grades: STANDARD / MANUFACTURER / PEER-REVIEWED / TRADE-PRESS / FORUM-ANECDOTE / VENDOR-MARKETING. Each cited bullet carries its grade.
- Items tagged **(read)** mean I opened the document and read the passage (HTML, or text I extracted from the PDF myself).
- Items tagged **(snippet)** mean the claim comes from a search-result summary or a fetch summary of a page, and I did not see the full source. Treat those as leads, and confirm before hard-coding numbers.
- The "Inferences" subsections are my own engineering reasoning from the cited mechanisms. They are not sourced facts. This applies especially to the symptom-variant and reading-signature columns of the matrix.

**Headline caveats for the report writer.**
1. I found no published frequency distribution of causes of DHW complaints. The only quantitative anchors are the crossover prevalence (~50% of ~100 CA multifamily buildings), one practitioner's "95% of my cases are balancing" claim, and one UK hospital inquest.
2. I could not access the full text of ASHRAE Guideline 12 / Standard 188, the ASPE Plumbing Engineering Design Handbook, the CIBSE / HVCA guides, or most manufacturer service manuals (Armstrong, Taco, Grundfos, Lochinvar, A. O. Smith, PVI, Rheem, Cleaver-Brooks, Leonard, Symmons). The manufacturer evidence below is mostly one Powers (Watts) installation / troubleshooting document that I read directly, plus snippets.
3. The Taco mixing-valve PDF (102-489) came back font-encoded, so I could not read it. The Taco-attributed cause list below is from a search summary only.

---

## Q1. What do authoritative sources (standards, handbooks, manufacturers) list as causes? (Includes the cause taxonomy)

### Takeaway
Across the sources I could read, the cause list clusters into seven families:
- (A) plant / heat source and storage
- (B) mixing / tempering valves
- (C) recirculation hydraulics (pump, check valves, balancing, isolation valves, pipe sizing, velocity)
- (D) hot/cold crossover and cold-side or pressure effects
- (E) fixture-level
- (F) demand and capacity
- (G) controls, schedules, human changes and Legionella-driven setpoint changes

The better-evidenced families are crossover, balancing/hydraulics, and the pump/aquastat controls. Standards bodies (ASHRAE G12 / 188, CDC toolkit) frame temperature targets and monitoring rather than listing hot-water-complaint causes. Manufacturer troubleshooting tables exist mostly for mixing valves.

### Cited Findings

#### Standards / guidance framing (STANDARD-adjacent)
- CDC Legionella toolkit (implements the ASHRAE framework): store hot water above 140 F (60 C). Keep circulating hot water at or above 120 F (49 C). Recirculate continuously where possible. Install TMVs as close to fixtures as possible. Eliminate dead legs and flush low-flow runs and dead legs at least weekly. It names heat loss from uninsulated piping, dead legs / low-flow sections, tank temperature gradients without recirculation, and unmaintained heaters and mixing valves as temperature-degrading conditions. STANDARD-adjacent (federal guidance, **read**) — [CDC Potable Water module](https://www.cdc.gov/control-legionella/php/toolkit/potable-water-systems-module.html)
- ASHRAE Guideline 12-2020 addendum b references electric heat trace, alone or as a supplement to recirculation, to hold the recommended minimum temperature throughout the hot-water system. The older 12-2000 text is quoted (via a search summary) as 140 F storage with 124 F minimum recirculated return. These return figures conflict across editions (124 F vs the CDC's 120 F). STANDARD **(snippet; I did not read the Guideline text)** — [ASHRAE G12-2020 addendum b](https://www.ashrae.org/file%20library/technical%20resources/standards%20and%20guidelines/standards%20addenda/g12_2020_b_20210408.pdf)
- California 2025 compliance forms (via a search summary) call for a check valve or equivalent between the recirculation pump and the water-heating equipment, isolation valves on both sides of the pump, and a check valve on the cold line between the hot-water system and the nearest tee. These are CA-specific, not IPC/UPC. STANDARD (code form) **(snippet)** — [CEC form](https://www.energy.ca.gov/filebrowser/download/8379?fid=8379)

#### (A) Plant / heat source / storage
- Scale on plates adds thermal resistance in counterflow plate heat exchangers used for DHW. Fouling often goes asymptotic, so cleaning may restore only part of the lost output. PEER-REVIEWED **(snippet)** — [Online fouling detection of DHW heat exchangers (HAL)](https://hal-uphf.archives-ouvertes.fr/hal-03446026)
- Armstrong's IOM has a water-side heat-exchanger cleaning procedure. It warns that a completely plugged exchanger cannot be chemically cleaned because there is no flow, and that water-quality damage is not warranty-covered. MANUFACTURER **(snippet)** — [Armstrong IOM ABH79-599](https://armstronginternational.com/wp-content/uploads/IOM_ABH79-599_EN_20220601.pdf)
- A. O. Smith / Lochinvar-type tank and boiler heaters, residential-grade guidance. Causes listed: setpoint too low, burner not firing or dirty burner / gas supply, sediment insulating the element or heat transfer surface, a broken or missing dip tube (cold water short-circuits to the outlet), a failed element on electric units, and a lockout caused by a sensor rather than the board. TRADE-PRESS / FORUM-ANECDOTE, residential or consumer sources, not commercial service manuals **(snippet)** — [HomeTips](https://www.hometips.com/repair-fix/water-heater-not-heating-enough.html). I could not retrieve any commercial OEM troubleshooting table.
- Boiler-fed indirect tank undersized relative to simultaneous draws (80 kBtu/h boiler feeding a 40 gal indirect, tank temperature dropping during simultaneous showers). The suggested fix was a second tank in series. FORUM-ANECDOTE **(snippet)** — [Heating Help (Lochinvar search)](https://forum.heatinghelp.com/discussion/comment/1833217/)
- Closed-system thermal expansion: a check valve or backflow preventer on the supply makes the system closed, pressure rises with each firing, and the T&P valve discharges. The relief valve is not a thermal-expansion device. IPC, UPC and the standard plumbing code require thermal-expansion control. MANUFACTURER **(snippet)** — [A. O. Smith Technical Bulletin 45](https://www.hotwater.com/info-center/technical-bulletins/bulletin-45.html)
- Central heat-pump water heaters (CHPWH):
  - Return water that is too warm or too fast degrades COP and destroys stratification in single-pass systems. Swing tanks work well with CO2 heat pumps but poorly with lower-temperature refrigerants, which then rely on resistance heat.
  - A swing tank's setpoint and balancing-valve position determine whether return water goes to the swing tank or back to the mixing valve.
  - PEER-REVIEWED (ACEEE conference) **(snippet)** — [ACEEE SSB24 swing-tank paper](https://www.aceee.org/sites/default/files/proceedings/ssb24/pdfs/Eliminating%20the%20Swing%20Tank%20and%20Other%20Design%20Considerations%20in%20Large-Capacity%20CO2%20Heat%20Pump%20Water%20Heating.pdf)
- A monitored 10.5-ton central HPWH had commissioning problems: compressor not running while the circulating pump and fan gave the impression of operation, incorrect sensor placement, and non-optimal setpoints (140 F upper limit, 5 F deadband, and a 120 F tempering valve feeding the recirculation loop). PEER-REVIEWED / report **(snippet; URL attribution moderately uncertain)** — [OSTI 1358055 (Davis CHPWH)](https://www.osti.gov/biblio/1358055)
- Defrost / low-ambient lockout: I found no field source documenting hot-water complaints from HPWH defrost or ambient lockout. A swing-tank patent notes capacity declines at low ambient and resistance heat takes over. See Gaps.

#### (B) Thermostatic mixing / tempering valves
- Powers (Watts) Hi/Lo supply-fixture (430 + 420/427 + PRV) troubleshooting table. MANUFACTURER **(read; I extracted the PDF text)** — [Powers TI430-420](https://www.watts.com/dfsmedia/0533dbba17714b1ab581ab07a4cbb521/35401-source/6508945). The table maps symptoms to causes:
  - Outlet too hot at low flow: small-valve max temperature not set properly, or the thermal motor is not working.
  - Outlet too hot at high flow: large valve max not set, or the thermal motor is not working.
  - Outlet stable but **creeps high overnight**: recirculation lines not properly plumbed, PRV opening too soon, or the return pump runs constantly (fix is an aquastat on the return pump).
  - Outlet **too low at low and high flow**: hot supply too low (must be at least 25 F above the set temperature), hot-side checkstops not fully open or **stuck from liming**, or temperature not set properly.
  - **Outlet flow drops off**: PRV differential set too high so the large valve "starves" the system, checkstops stuck from liming, or system pressure varying by more than 50% of inlet supply pressure.
  - **Outlet cycles between hot and cold**: PRV differential too low, so the large valve starts controlling too early and hunts, or pressure varying by more than 50%.
  - Preventive maintenance: check checkstop poppet movement at least every 12 months and re-verify max-temperature settings every 3 months.
  - Piping rule: do not recirculate LTHW and HTHW with one pump, because return may exceed the mixer set point.
- Powers 1430-series (snippet): hot supply should be at least 15 F above set point; below the minimum flow the valve will not control to ASSE 1017; recirculation may be unbalanced or the valve oversized; heat rising through pipes can raise return temperatures unless a heat trap (about 2 ft drop) is used. MANUFACTURER **(snippet)** — [Powers 1430 manual](https://www.manualsdir.com/manuals/592987/powers-1430-series-hilo-master-mixing-valve.html)
- A Taco troubleshooting table (via a search summary) lists blocked strainers, fluctuating supply pressures (fix: PRVs on both supplies), hot/cold supplies reversed, and a fouled check valve as causes of unstable mix temperature. MANUFACTURER **(snippet; the Taco PDF itself was unreadable to me)** — [Taco 102-489](https://res.cloudinary.com/dzhpkjoqj/image/upload/Taco/102-489)
- Leonard states its valves are regulating mechanisms that need regular maintenance, with cleaning frequency depending on local water conditions. MANUFACTURER **(snippet)** — [Leonard / Watts catalog listing](https://www.watts.com/dfsmedia/0533dbba17714b1ab581ab07a4cbb521/35476-source/6512311)
- Fail-safe behavior (ASSE 1017 class): vendors describe thermal shut-off of the hot inlet if the cold supply fails, and the reverse. The Caleffi AngleMix description says shut-off is only guaranteed with an inlet-hot to mixed-outlet difference of at least 18 F. Braukmann TM50 requires at least 10 K. A valve that sees a failed or starved hot supply can therefore deliver cold or lukewarm water. MANUFACTURER **(snippet)** — [Caleffi NA 03617](https://www.caleffi.com/sites/default/files/media/external-file/03617_NA.pdf); [Resideo TM50](https://homecomfort-techlit.resideo.com/emeadocuments/pim%20-%20renamed/tm50-pd-en0h1326ge23.pdf)
- Watts says check valves are a compliance requirement for ASSE 1017 applications, to prevent thermal siphoning into the cold line. MANUFACTURER, a characterization to verify against the standard **(snippet)** — [Watts TMV reference](https://www.watts.com/resources/references-tools/thermostatic-mixing-valves)
- Scale makes mixing valves stick or erratic over time. A forum poster notes there is no way to predict a service interval without site records. Caleffi markets scale-resistant polymer parts. FORUM-ANECDOTE and VENDOR-MARKETING **(snippet)** — [Heating Help](https://forum.heatinghelp.com/discussion/comment/1850170/)
- Failure can go either direction: TMVs "will fail and potentially allow full hot" (trade article), and a hospital audit found several TMVs faulty or poorly set. TRADE-PRESS and PEER-REVIEWED **(snippet)** — [Plumbing Engineer Oct 2021 p.64](https://digital.plumbingengineer.com/Plumbing-Engineer-October-2021/64/); [Royal Adelaide / Campbelltown audit (PHRP)](https://www.phrp.com.au/wp-content/uploads/2014/10/NB92004.pdf)
- A Brooklyn condo case: a newly installed DHW mixing valve plus a new digital aquastat. The author states that in most systems with a mixing valve the pump must run virtually 24/7 to control temperature. TRADE-PRESS **(read)** — [Habitat, "Valve Fix"](https://www.habitatmag.com/Publication-Content/Bricks-Bucks/2019/2019-July/Valve-Fix)

#### (C) Recirculation hydraulics
- Parallel paths take the path of least resistance. In an unbalanced system the highest-resistance (usually the farthest) riser gets too little flow, others get excessive flow, and the result is energy loss, pipe erosion, pump failure and long waits at remote fixtures. PEER-REVIEWED (ACEEE, PG&E lab study, 36-unit full-scale rig) **(read)** — [ACEEE SSB24 balancing paper](https://aceee.org/sites/default/files/proceedings/ssb24/pdfs/Best%20Practices%20for%20Hot%20Water%20Distribution%20Systems%20in%20Multifamily%20Buildings-A%20Comparative%20Evaluation%20of%20Balancing%20Methods.pdf)
  - Same paper: automatic constant-flow balancing valves did not always meet targets because their flow-control range is limited and they are strongly affected by pump speed controls.
  - Same paper: field-measured recirculation losses exceed model predictions, attributed to imperfect insulation, unbalanced recirculation, and/or hot/cold cross flows.
- Bock (PHCP Pros, 2024), a practitioner-engineer's list of design/balancing faults behind low return temperature. TRADE-PRESS **(read)** — [PHCP Pros, DHW Return Design](https://www.phcppros.com/articles/19678-dhw-return-design-doing-it-right-and-the-risks-of-doing-it-wrong):
  - No balancing, or balancing valves in series that interact.
  - Manual-valve interaction.
  - Balancing valve placed after the last fixture, leaving downstream pipe unmaintained.
  - Common return main not included in flow calculations.
  - Excessive loop temperature loss. Example: a 115 F distribution temperature allows a loss of at most 10 F.
  - Velocity outside about 2-3 ft/s: too low means stagnation, too high means erosion.
  - Fitting losses underestimated (30-50% of pipe friction).
  - Thermostatic balancing valves working outside their hydraulic range.
  - Undersized pump.
  - No balancing report or verification.
- Pump / aquastat: in the Brooklyn condo case the aquastat's on and off setpoints were reversed, so the pump never started. The board's plumber had prescribed a new pump and new check valves, which cost $680 and were not needed. TRADE-PRESS **(read)** — [Habitat](https://www.habitatmag.com/Publication-Content/Bricks-Bucks/2019/2019-July/Valve-Fix)
- 23-story NYC downfeed building, 20-minute waits. Practitioner-proposed causes: undersized circulator, something changed (circulator failure or air in the lines), unbalanced risers, and a check valve after the pump not seating (copper reamings held it open, so cold water backed into the return and showers ran tepid). Risers joined a manifold without check valves. Installing ball valves per branch and balancing fixed it ("working very good now"). FORUM-ANECDOTE **(read)** — [Heating Help thread](https://forum.heatinghelp.com/discussion/comment/768202)
- Without check valves, a recirculation pump can pull hot water from one riser's return and push it into another riser's cold or low-pressure lines. FORUM-ANECDOTE **(snippet)** — [Heating Help](https://forum.heatinghelp.com/discussion/comment/768192)
- No return loop at all: a 9-story condo with 15-20 minute waits at upper floors had no dedicated recirculation. TRADE-PRESS **(snippet)** — [Habitat, Sept 2022](https://www.habitatmag.com/Publication-Content/Problem-Solved/2022/2022-September/Cutting-Waste-and-Long-Waits-for-Hot-Water-in-a-Nine-Story-Condo)
- Air-binding and debris: forum threads report an air-locked or debris-jammed pump with a cold discharge pipe, and a flow-check valve that opens only by hand. FORUM-ANECDOTE **(snippet)** — [Heating Help](https://forum.heatinghelp.com/discussion/comment/1872438/). Generic field checks (inlet vs outlet pipe temperature, bleed test) come from consumer HVAC sites and are lower grade.
- Velocity / erosion-corrosion: oversized pumps and undersized lines drive excessive velocity. Turbulence below bends, elbows and tees strips the oxide film, producing pinholes. The author recommends below 3 fps. The CDA guidance quoted is 4-5 fps for hot water below 140 F and 2-3 fps above 140 F. Pinhole leaks reduce flow and temperature. Problems can stay hidden for years if the system runs below its design flow. TRADE-PRESS **(read)** — [Consulting-Specifying Engineer, 2007](https://www.csemag.com/?p=5368). The velocity limits conflict between sources (3, 4-5, 5 fps), and the author notes corrosion can occur below 5 fps with poor water chemistry.
- Pinhole leaks in return piping were part of a Caleffi-presented case (a 40-year-old recirculation problem threatening a large subsidized multifamily project). Only the webinar announcement is available, with no findings. VENDOR-MARKETING **(snippet)** — [Caleffi announcement](https://www.caleffi.com/en-us/news-events/07-08-2019/coffee-caleffitm)
- Dead legs and low-flow runs are named in the CDC toolkit (above).

#### (D) Hot/cold crossover, cold-side and pressure effects
- Crossover = the combination of a faulty fixture valve (or an open circuit where hot and cold join) plus a pressure imbalance between the hot and cold subsystems. It most often occurs when a shower or faucet cartridge wears out. Symptoms: long wait times, sudden rapid temperature fluctuations (called the "most common symptom"), lukewarm water, or no hot water. It can be asymptomatic and thus go unrepaired. Changes such as adding recirculation controls or temperature reset can unmask it. Staff then raise setpoints or bypass pump controls. PEER-REVIEWED (ACEEE Summer Study 2016, Enovative / CEC) **(read)** — [Ayala & Zobrist, ACEEE 2016](https://www.aceee.org/files/proceedings/2016/data/papers/1_59.pdf)
- The same paper's lab-validated detection methods:
  - Pressure-gauge method: shut the cold feed to the heater, drain the hot side via a fixture, close it, and watch whether hot-side pressure rebuilds.
  - Water-flow method: same setup; flow never stops and eventually turns cold if there is crossover.
  - Eatherton method: heat one shower valve's hot side, open a nearby lavatory hot tap, and feel whether the shower valve body cools.
  - Water-meter method: works only in some buildings.
  - Temperature-differential (supply vs return logging) was judged "invalid" as a detector, though it can be indicative.
  - The pump-control method was discarded.
  - Fix evidence: replacing shower valves, adding check valves on risers or supply lines, or replacing cartridges.
  - One site's pumps controls "that had previously been bypassed" were reactivated without problems after the fix.
  - Source for fixes and site data: [Ayala, ACEEE HWF 2017 slides](https://aceee.org/sites/default/files/pdf/conferences/hwf/2017/Ayala_Session4A_HWF17_2.28.17.pdf) **(read, PDF text I extracted)**
- Locating the source is hard and "not always a mixing valve" (HWF 2017 slides, same link). The Cooperator article lists faulty check valves and a defective sink upstream on a riser as sources, and notes that crossover and imbalance are sometimes confused. TRADE-PRESS **(read)** — [Cooperator](https://cooperatornews.com/article/dont-get-your-building-into-hot-water)
- Crossover cools the return, inflates the loop load, and prompts setpoint increases and pump-control overrides. California Housing Partnership crossover guidance. VENDOR/NGO guidance **(read)** — [CHPC / CHP crossover page](https://calhousingpartnership.org/?p=4310)
- Pressure-driven crossover is the leading explanation for field recirculation losses running 1.1-2.3x idealized calculations (24.1-99.9 W/apartment, mean 62.5 W). PEER-REVIEWED / program report **(read, abstract page only)** — [ETCC multifamily recirculation survey](https://www.etcc-ca.com/reports/multifamily-domestic-hot-water-recirculation-survey)
- Crossover from a worn-cartridge path also bypassed solar preheat: in a Bronx building, over 80% of hot water bypassed the rooftop solar panels. TRADE-PRESS **(read)** — [Cooperator](https://cooperatornews.com/article/dont-get-your-building-into-hot-water)
- Booster / pressure items: pressure above 30 psi at a top-floor fixture, boosters cycling every few seconds, and VFDs left in hand / bypass mode, flagged as problem indicators. A boiler pump running when the boiler is off can pull heat through. TRADE-PRESS **(read)** — [Cooperator](https://cooperatornews.com/article/dont-get-your-building-into-hot-water)
- Fluctuating supply pressure is a listed cause of mixing-valve instability (Taco and Powers above).

#### (E) Fixture level
- Worn single-lever cartridges and failed fixture check stops (crossover path), plus clogged mixing-valve strainers and reversed supplies at fixture valves (see Taco, via snippet). Recommended mitigations in the Enovative research (via a search summary): check valves before shower valves or on risers, isolation valves around shower valves, and pressure-balance / thermostatic shower valves with integral check stops. PEER-REVIEWED **(snippet)** — summary of [ACEEE 2016](https://www.aceee.org/files/proceedings/2016/data/papers/1_59.pdf) and Enovative work.
- Electronic sensor faucets and low-flow fixtures are named as Legionella-risk fixtures, not as cause of lukewarm complaints. STANDARD-adjacent **(read)** — [CDC](https://www.cdc.gov/control-legionella/php/toolkit/potable-water-systems-module.html)

#### (F) Demand and capacity
- Low-flow fixtures worsen distribution heat loss and delay in large buildings. VENDOR / TRADE-PRESS **(snippet)** — [Thermon](https://thermon.com/topics/hot-water-temperature-maintenance-for-commercial-hot-water-systems/)
- Simultaneous-draw tank drop (boiler-fed indirect, above). No dedicated commercial peak-demand sizing evidence found.

#### (G) Controls / schedules / human changes / Legionella-driven setpoint changes
- NREL / Building America piping report (via a search summary): controls that limit recirculation pump operation are frequently disabled because occupants complain about waits, so pumps run continuously. TRADE-PRESS / government report **(snippet)** — [Building America piping report](https://www1.eere.energy.gov/buildings/publications/pdfs/building_america/solar-hot-water-piping-heat-multifamily.pdf)
- Cooperator: overridden or malfunctioning controls, compensating for the coolest apartment with higher setpoints or more pump flow. TRADE-PRESS **(read)** — [Cooperator](https://cooperatornews.com/article/dont-get-your-building-into-hot-water)
- The Brooklyn lesson: ask "what changed, when, and why" (new mixing valve, new aquastat, recent plumbing jobs). TRADE-PRESS **(read)** — [Habitat](https://www.habitatmag.com/Publication-Content/Bricks-Bucks/2019/2019-July/Valve-Fix)
- UK hospital (Bath) Legionella inquest: the return line ran at 35-40 C (should be around 60 C) because a loop pump had broken. Monthly checks were taken at a kitchen sink at the other end of the ward and missed it. Out-of-date system diagrams contributed. TRADE-PRESS reporting on a coroner's finding **(snippet)** — [Envirotec](https://envirotecmagazine.com/2016/03/01/bath-hospital-legionella-inquest-pinpoints-failures/)
- A Royal Adelaide audit concluded that maintenance rarely conducts scheduled outlet temperature checks and relies on complaints to focus attention. PEER-REVIEWED **(snippet)** — [PHRP NB92004](https://www.phrp.com.au/wp-content/uploads/2014/10/NB92004.pdf)
- Scald-driven lowering of setpoints conflicts with Legionella-control temperatures: a survey of building water managers (via a search summary) found more than 85% of buildings meet scald-risk temperature guidance, while roughly two-thirds to three-quarters do not meet opportunistic-pathogen temperature guidance. PEER-REVIEWED **(snippet)** — [Drexel record](https://researchdiscovery.drexel.edu/esploro/outputs/journalArticle/Practitioners-Perspective-on-the-Prevalent-Water/991019167963804721). I found no source directly documenting setpoint raise / lower as a cause of hot-water complaints.

### Inferences (my reasoning, not sourced facts)

**Cause matrix.** "Floors/fixtures" describes the symptom pattern the mechanism would produce. "Readings" describes the plant or loop signature I would expect. Verify each against a physical model before use.

| # | Cause | Family | Symptom variants it would produce | Readings it should move | Commonly confused with |
|---|---|---|---|---|---|
| 1 | Heater / source setpoint too low or wrong | A | All floors, all day; lukewarm | Tank / HX outlet low; MV hot inlet low (at or below set + 15-25 F); return low | Mixing-valve set low; failed element |
| 2 | Element / burner / HX output loss (failure, scale, sediment, controls lockout) | A | All floors; worse at peak (recovery) | Outlet drops under load; firing / amp draw abnormal; HX approach grows | Undersized storage; demand peak |
| 3 | Sensor / aquastat failure at the plant | A / G | Whole building; can be intermittent | Controller reading differs from a reference thermometer | Setpoint low; pump control fault |
| 4 | Dip tube failure / stratification short-circuit | A | Lukewarm; short hot supply | Mid-tank temperatures low relative to outlet | Sediment; undersized storage |
| 5 | Storage undersized / demand peak | F | Peak-only; runs out; recovers | Tank temps drop on draw; return normal off-peak | Element failure; mixing-valve starvation |
| 6 | Mixing valve set too low or drifted | B | All floors; cold side normal | MV outlet below intended; hot inlet fine | Source setpoint low |
| 7 | Mixing valve fouled / stuck / liming of checkstops or strainers | B | Hunting, low flow, lukewarm at high flow | MV outlet unstable; large pressure drop across strainer / checkstop | Pressure problem; pump issue |
| 8 | Hot supply to the MV too close to set point (margin lost) | A / B | Worse at peak | Hot inlet minus set point below the manufacturer minimum | Sizing; setpoint low |
| 9 | Recirculation pump failed / off / wrong rotation / air-bound | C | Slow arrival at far fixtures; lukewarm at ends; often building-wide | Return temp falls toward ambient; pump amps or flow absent | Aquastat fault; crossover |
| 10 | Pump control fault (timer, aquastat reversed, setback, BAS override, VFD in hand) | C / G | Time-of-day pattern; recent change | Pump off when it should be on; return temp low only at certain hours | Pump failure |
| 11 | Pump undersized or oversized (too little flow, or velocity and erosion) | C | Remote risers lukewarm; or pinholes, noise | Low delta-P or flow; high velocity | Imbalance |
| 12 | Check valve stuck open, reversed, missing, or debris-held | C | Return cools when the pump is off; cross-riser flow | Return line flow reverses or cold backs in; asymmetric pump effect | Crossover |
| 13 | Balancing valve closed, drifted, mis-set, scaled, or out of its range | C | One riser or branch cold; others hot (a classic "one riser" signature) | Branch return temp far below others | Closed isolation valve; crossover |
| 14 | Isolation valve closed or partially closed | C | One riser, floor group, or a whole loop | Zero flow past valve; temperature step across it | Balancing valve |
| 15 | Dead legs / missing return / no loop | C | Long waits at specific fixtures; slow arrival | None at the plant; fixture-specific | Cartridge, flow restrictor |
| 16 | Insulation loss / wet or missing insulation | C | Far fixtures; worse in cold rooms | Long-run temperature drop larger than design | Low flow; balancing |
| 17 | Flow velocity / erosion-corrosion / pinhole leak | C | Slow loss of performance; wet spots; leaks | Makeup demand; pressure drop | Pump issue |
| 18 | Hot/cold crossover (worn cartridges, failed check stops, pressure imbalance) | D | Fluctuating temperature; lukewarm; slow arrival; also warm cold taps | Return line has cold dips; hot side repressurizes with cold feed isolated; warm cold water | Imbalance; pump failure |
| 19 | Low or unstable cold-water supply pressure / PRV problems | D | Hunting, flow loss, worse at peak | Static and dynamic pressure down; cold vs hot pressure imbalance | MV fault; crossover |
| 20 | Closed-system thermal expansion / failed expansion tank | D | Pressure spikes, T&P weeping; usually not a hot-water-temperature cause per se | Pressure swings with firing | Booster issue |
| 21 | Fixture cartridge, aerator, stop, restrictor, or tempering at fixture | E | One fixture only | Fixture hot side OK upstream, poor at outlet | Crossover |
| 22 | Schedule setback / energy-saving pump or temperature reset | G | Time-of-day, mornings, weekends | Setpoint or pump state follows schedule | Pump failure |
| 23 | Legionella-motivated setpoint change (raised or lowered) | G | Raised: scald complaints (hot); lowered: lukewarm | Setpoint history | Source or MV setpoint |
| 24 | HPWH defrost, ambient lockout, swing-tank misconfiguration, return-to-primary mixing | A | Intermittent or seasonal; building-wide | Compressor off, resistance heating on, tank destratified | Element failure; setpoint |
| 25 | Solar / preheat bypass or mismatched staging | A / D | Lower than expected hot supply | Preheat tank isn't contributing | Crossover |

**Multi-cause interactions the sources support:**
- Crossover masks and defeats recirculation controls, which pushes staff to raise setpoints and bypass the aquastat. That makes a cause-G condition (override) a downstream effect of cause 18 (ACEEE 2016, CHPC).
- An imbalance and a crossover look alike; the Cooperator piece says so explicitly.
- An undersized pump and a velocity / erosion-corrosion problem trade off against each other (Bock; CSE).
- A new mixing valve plus a new aquastat (a confounded change) is a Brooklyn pattern (Habitat).
- The temperature margin requirement (hot supply at least 15-25 F above MV set point, per Powers) means a modest drop at the plant can show up as an MV outlet drop, so causes 1, 2 and 8 are chained.

### Gaps
- Full text of ASHRAE G12-2020, Standard 188, the ASPE Design Handbook / Pipeline, CIBSE / HVCA guides, PHCC and IAPMO publications: not accessed. The ASHRAE return-temperature value (120 vs 124 F) is unresolved.
- Commercial OEM service manuals (A. O. Smith / Lochinvar / Rheem / Cleaver-Brooks / PVI / Armstrong boilers or tanks, Grundfos / Taco pump guides, Symmons, Leonard): only snippets or none. Taco's mixing-valve PDF was unreadable.
- HPWH defrost / lockout and solar / preheat: no field-documented link to hot-water complaints found.
- Direct sources on BAS overrides, schedule setbacks, and Legionella-motivated setpoint changes as complaint causes are thin (inference from the crossover and NREL material only).
- The cause matrix above is mine; no source offers a unified taxonomy.

---

## Q2. Which causes do practitioners say are most common?

### Takeaway
Practitioner claims converge on hydraulic imbalance (one balancing consultant: about 95% of his call-outs) and crossover through worn fixture cartridges, with pump / aquastat / control faults and recent-change effects as the usual "surprise" causes. Plain mixing-valve failure and heater element failure are rarely ranked first in the commercial / multifamily sources I could read, but I found no neutral ranking.

### Cited Findings
- Aaron Bock, PE (PHCP Pros 2024): when called in for inadequate temperature at a fixture or area, building teams blame low setpoint, undersized pumps, or wrongly chosen mixing valves. In about 95% of his cases the loop was not properly balanced or not balanced at all, and other fixes are less likely to succeed. This is one consultant's self-reported experience, not a sampled statistic. TRADE-PRESS **(read)** — [PHCP Pros](https://www.phcppros.com/articles/19678-dhw-return-design-doing-it-right-and-the-risks-of-doing-it-wrong)
- Ayala & Zobrist: worn shower / faucet cartridges are the most common crossover source, and crossover's most common symptom is rapid temperature fluctuation. PEER-REVIEWED **(read)** — [ACEEE 2016](https://www.aceee.org/files/proceedings/2016/data/papers/1_59.pdf)
- Cooperator (NYC co-op / condo trade press) names worn mixing cartridges and faulty check valves as crossover sources, and says imbalance from original design or later patchwork is the other big distribution problem. TRADE-PRESS **(read)** — [Cooperator](https://cooperatornews.com/article/dont-get-your-building-into-hot-water)
- Habitat's Brooklyn author: a plumber diagnosed missing / failed check valves and a dead pump, and the real cause was reversed aquastat setpoints. The author says overcharging for unnecessary work happens "all the time," with no data. Lesson offered: first find out what changed. TRADE-PRESS **(read)** — [Habitat](https://www.habitatmag.com/Publication-Content/Bricks-Bucks/2019/2019-July/Valve-Fix)
- Powers (manufacturer) lists, in order of its own table, mis-set max temperature, a failed thermal motor, a low hot supply, stuck checkstops from liming, and a mis-set PRV differential. The table has no frequency ranking. MANUFACTURER **(read)** — [Powers TI430-420](https://www.watts.com/dfsmedia/0533dbba17714b1ab581ab07a4cbb521/35401-source/6508945)
- Forum practitioners on the 23-story case lead with undersized circulator, "something changed," imbalance, and check-valve failure. A separate Heating Help respondent says the first thing to check is hot-to-cold crossover. FORUM-ANECDOTE **(read the first; snippet for the second)** — [thread 768202](https://forum.heatinghelp.com/discussion/comment/768202)
- Audit finding (hospitals): maintenance relies on complaints rather than scheduled outlet temperature checks; faulty or mis-set TMVs were found, mostly in the oldest wing. PEER-REVIEWED **(snippet)** — [PHRP NB92004](https://www.phrp.com.au/wp-content/uploads/2014/10/NB92004.pdf)
- A heating-forum compilation search "central hot water lukewarm" could not confirm a single most-common cause. A stuck TMV did not surface as a top cause. FORUM-ANECDOTE / search synthesis — [Heating Help search results](https://forum.heatinghelp.com/discussion/comment/943362/)

### Inferences
- Bock's 95% figure comes from a design-stage / punch-list setting (newly built, never balanced). It likely overstates balancing's share in an aging building where a component has since failed or been changed. The "what changed" heuristic from Habitat points the other way.
- Sources disagree on emphasis: Bock deprioritizes setpoint, pump size and mixing valves, while the Habitat case turned on a control setting and Powers' table is entirely mixing-valve causes. These reflect each author's vantage point (designer vs building consultant vs manufacturer), not different truths.

### Gaps
- Plumbing & Mechanical (PME), Contracting Business, and Plumbing Engineer articles that rank causes: not found. Plumbing Zone not reached. Heating Help only partially reached via search snippets.
- No survey of operators or service companies ranking the causes.

---

## Q3. Are there published frequency distributions or case-study compilations?

### Takeaway
There is one real prevalence number: roughly half (about 50-52%) of about 100 sampled California multifamily buildings had hot/cold crossover in the central DHW distribution (not a statistically significant sample, per the authors). There is no published cause-by-cause distribution of hot-water complaints, and only scattered case studies.

### Cited Findings
- CEC-funded study of more than 100 multifamily buildings: over 50% exhibited crossover failures in central DHW distribution. A later summary says crossover "may be in as many as 52%." The authors say the sample of about 100 buildings was chosen to resemble California stock but was "not a statistically significant sample size." PEER-REVIEWED (ACEEE) **(read)** — [ACEEE 2016](https://www.aceee.org/files/proceedings/2016/data/papers/1_59.pdf); the 52% figure is **(snippet)**.
- The same paper: the frequency of crossover "is not sufficiently documented." Crossover flows may account for 5-10% of multifamily hot-water energy (Sachs et al. 2011), and replacing every shower cartridge in a 104-unit community saved $23,328 or 62% (Pfaff 2009). The authors note this variation shows too little data. PEER-REVIEWED **(read)** — [ACEEE 2016](https://www.aceee.org/files/proceedings/2016/data/papers/1_59.pdf)
- HWF 2017 follow-up: gas-valve hours fell on average 10% after crossover repairs at 6 completed sites (range -2.5% to 17%). The slides note finding the source is hard, "not always a mixing valve." PEER-REVIEWED / conference slides **(read)** — [Ayala HWF 2017](https://aceee.org/sites/default/files/pdf/conferences/hwf/2017/Ayala_Session4A_HWF17_2.28.17.pdf)
- Field recirculation losses were 24.1-99.9 W per apartment (mean 62.5), 1.1-2.3x idealized calculation; no clear correlation to building characteristics. PEER-REVIEWED / program report **(read)** — [ETCC survey](https://www.etcc-ca.com/reports/multifamily-domestic-hot-water-recirculation-survey)
- Earlier monitoring: between 23% and 70% of supplied heat per apartment was lost in recirculation and distribution (Bohm 2013: 13 apartment buildings and 2 offices). In 28 multifamily buildings, average DHW efficiency was 35% and average recirculation loss fraction 33% (Zhang 2013). These are energy, not complaint, statistics. PEER-REVIEWED (as quoted in the SSB24 paper) **(read)** — [ACEEE SSB24](https://aceee.org/sites/default/files/proceedings/ssb24/pdfs/Best%20Practices%20for%20Hot%20Water%20Distribution%20Systems%20in%20Multifamily%20Buildings-A%20Comparative%20Evaluation%20of%20Balancing%20Methods.pdf)
- A Nicor Gas / NREL Brooklyn demand-control retrofit (two ~50-unit buildings) logged complaints for follow-up; three phone-in complaints in one building were about excessive waits. A tiny sample. TRADE-PRESS / report **(snippet)** — [Nicor Demand-Based Water report](https://WWW.NICORGAS.COM/content/dam/southern-co-gas/shared/pdf/business/rebates-and-assessments/public-project-reports/Demand-Based-Water.pdf)
- Case compilations by type (all single-site): Brooklyn aquastat (Habitat 2019), 23-story NYC downfeed (Heating Help), 9-story condo with no return (Habitat 2022), UK Bath hospital pump failure (Envirotec), Royal Adelaide TMV audit (PHRP), Bronx crossover bypassing solar (Cooperator).
- Statistics on failure rates for thermostatic balancing valves, TMVs, or recirculation pumps in the field: none found.

### Inferences
- The crossover prevalence is of a latent condition (many buildings have it without noticeable symptoms). It should not be read as "50% of complaints are crossover." For a prior on complaint cause, it only says crossover is common enough to be a standing candidate in multifamily stock with single-lever shower valves.
- The prevalence figure comes from California multifamily low-rise stock; transfer to US commercial / high-rise is unverified.

### Gaps
- No complaint-log tallies by cause from any utility, REIT, hospital system or service company. NREL / LBNL / CEC searches returned none. A CEC Title 24 CASE report for central DHW was not read.
- The full ETCC lab report (balancing-valve performance) is behind a form; the Caleffi case-study outcome was not recoverable.

---

## Q4. How do the causes cluster, and which are mutually distinguishable by cheap readings?

### Takeaway
A sensible split is by where the heat is lost relative to the loop: plant (A/B/F), loop hydraulics (C), cold-side leakage into the hot loop (D), fixture (E), and human / controls changes (G). The sources support a handful of cheap discriminating readings, but few are published as diagnostic trees; most discriminators below are my inference.

### Cited Findings (readings that sources describe)
- Mixing valve hot-supply margin: the hot inlet should be at least 25 F above the set point for the Powers Hi/Lo (15 F for the 1430). A low hot inlet therefore separates "plant" from "valve" causes. MANUFACTURER **(read; snippet for 1430)** — [Powers TI430-420](https://www.watts.com/dfsmedia/0533dbba17714b1ab581ab07a4cbb521/35401-source/6508945)
- Mixing valve outlet stable but creeping high overnight points to the return pump running constantly or miss-piped return, not to a failed valve. MANUFACTURER **(read)** — [Powers TI430-420](https://www.watts.com/dfsmedia/0533dbba17714b1ab581ab07a4cbb521/35401-source/6508945)
- Crossover vs everything else: shut the cold feed to the heater and open a hot tap. If water keeps flowing and turns cold, or hot-side pressure rebuilds after draining, cold is entering through a fixture. PEER-REVIEWED lab-validated **(read)** — [ACEEE 2016](https://www.aceee.org/files/proceedings/2016/data/papers/1_59.pdf)
- Pinpointing a crossover fixture: the Eatherton method (feel a hot shower-valve body cool when a nearby lavatory hot tap opens). PEER-REVIEWED **(read)** — same paper.
- Supply / return temperature logging was judged not reliable as a stand-alone detector for crossover but "can be indicative." PEER-REVIEWED **(read)** — same paper.
- Location pattern is itself a discriminator: "are complaining tenants on upper floors near the mechanical room or spread throughout?" distinguishes distribution from supply problems. FORUM-ANECDOTE **(read)** — [thread 768202](https://forum.heatinghelp.com/discussion/comment/768202)
- Recent-change history: new pump, valve, aquastat or plumbing work should be checked first. TRADE-PRESS **(read)** — [Habitat](https://www.habitatmag.com/Publication-Content/Bricks-Bucks/2019/2019-July/Valve-Fix)
- Return temperature measurement matters: a UK hospital's return-line temperature (35-40 C) caught a dead pump that sampling at a sink had missed. TRADE-PRESS **(snippet)** — [Envirotec](https://envirotecmagazine.com/2016/03/01/bath-hospital-legionella-inquest-pinpoints-failures/)
- Hidden recirculation piping makes direct measurement of temperature distribution hard in the field. PEER-REVIEWED abstract **(read)** — [ETCC lab report page](https://etcc-ca.com/reports/lab-testing-balancing-valve-performance-multi-family-central-recirculation-system)
- Sources disagree on one point: Bock says balancing is the root cause in about 95% of his cases, while the Habitat and Heating Help cases show a single failed or mis-set component (aquastat, check valve) was the cause. The sources do not reconcile this; it likely reflects new-construction vs in-service populations.

### Inferences (my proposed discriminators; not from a source)
- **Plant vs distribution**: compare heater outlet / MV hot inlet temperature against MV outlet and against the return. If the hot inlet is low, causes 1-5 and 8 are in play. If it is normal and the MV outlet is on target but the return is low, go to family C or D.
- **Pump state vs control state** separates causes 9 and 10: pump amps / flow and the aquastat / BAS command (stuck, reversed, scheduled off).
- **One riser vs all risers**: if only one riser's return temperature is low, balancing valve (13), isolation valve (14), and riser-local crossover are candidates; if all, pump, setpoint, or MV.
- **Return temperature with the pump forced on vs off** separates a flow problem (9-14) from a heat-loss problem (16) from crossover (18), in which the return cools in dips.
- **Crossover test (cold feed isolated) is the single cheapest test that cleanly separates family D from C**, per the validated methods above.
- **Peak-only vs all day**: peak-only favors 5, 8, 19 and MV starvation; all day favors setpoint, pump, balancing.
- **Hot-only vs hot+cold**: warm cold-tap water (or temperature fluctuation) points to crossover; normal cold side points elsewhere.
- **Single fixture vs many**: fixture-only (21) is excluded cheaply with a bucket test at the fixture hot supply upstream of the cartridge.
- **Time-of-day and recent-change history** quickly point to G.

### Gaps
- I found no published decision tree or conditional-probability table for these discriminators, in standards or elsewhere. The matrix in Q1 and the discriminators here are untested hypotheses.
- Typical expected readings (normal delta-T across a healthy loop in °F, normal flow per riser): the 0.5 gpm per riser baseline appears in the SSB24 lab study and a 10 F maximum loss budget in Bock. I did not find validated field norms for commercial buildings.
- Coverage of heat-pump water heater diagnostics (compressor state, defrost) and solar preheat as discriminators: absent.
