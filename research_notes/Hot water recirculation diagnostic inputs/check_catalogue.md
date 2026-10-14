# Physical checks for diagnosing hot-water / recirculation problems in commercial and multifamily buildings: catalogue, thresholds, pitfalls, timing, safety, remote vs physical

**How to read this file.**
- Every sourced claim carries a grade: STANDARD / GUIDANCE-DOC / MANUFACTURER / TRADE-PRESS / FORUM-ANECDOTE / VENDOR-MARKETING. Government agency documents (VA, CDC, CPSC) are graded GUIDANCE-DOC.
- Provenance tags: **[READ]** means I opened and read the document text. **[FETCHED-SUMMARY]** means a fetch tool returned a model summary of the page, not raw text. **[SNIPPET]** means the claim rests on a web-search result summary and I did not open the page. Treat [SNIPPET] items as leads to verify, not as verified facts.
- Items marked **ANALYST** (in Inferences sections only) are my synthesis or unsourced estimates, not findings.
- Firm vs rule of thumb: "FIRM" means a published numeric limit from a standard, regulator, or government directive. "ROT" means rule of thumb, design convention, or one author's preference.
- **Not accessed:**
  - ASHRAE Guideline 12-2020 and Standard 188 full text (paywalled). I read only Addendum b, which is free.
  - ASSE/IAPMO 1017, 1070 and 1071 text (paywalled). I used a 2009 Watts comparison chart.
  - The ASPE Design Handbook.
  - Full ETCC reports (behind a form).
  - The Maine and NJ-hosted PDFs were readable only partly. The "NJ" URL actually returned VHA Directive 1061.

---

## 1. Who publishes the standard procedures and thresholds, and what are the numbers?

### Takeaway
There is no single authoritative "check procedure" document. Temperature targets come from ASHRAE Guideline 12 / Standard 188 (paywalled), the CDC toolkit (which paraphrases G12), and the VA Directive 1061. Field procedures are scattered across manufacturer manuals, trade-press articles, and forums. The key conflict is the minimum hot-water distribution/return temperature:

| Source | Minimum circulating hot-water temperature |
|---|---|
| CDC toolkit | 120°F |
| VA Directive 1061 | 124°F |
| Plumbing Engineer (Hiller series) | 120–130°F band |
| PHCP Pros commissioning series | "ASHRAE recommends >122°F" |

The model should make the return-temperature limit a parameter, not a constant.

### Cited Findings

**Temperature targets**
- CDC Legionella Control Toolkit (based on ASHRAE G12): store hot water above 140°F (60°C). Ensure circulating hot water does not fall below 120°F (49°C). Recirculate continuously where possible. Cold water below 77–113°F, with growth possible down to 68°F. Thermal remediation (heat shock) is not recommended for potable systems. GUIDANCE-DOC, FIRM as a guideline limit. [READ] — [CDC PDF](https://www.cdc.gov/control-legionella/media/pdfs/Control-Toolkit-Potable-Water.pdf); [CDC module page](https://www.cdc.gov/control-legionella/php/toolkit/potable-water-systems-module.html)
- CDC monitoring guidance: measurement frequency is set by performance, and increased when readings are variable. No fixed interval is given. Install TMVs as close to fixtures as possible. Flush low-flow runs and dead legs at least weekly. Clean and maintain TMVs, aerators, showerheads and tanks regularly. GUIDANCE-DOC. [READ] — [CDC PDF](https://www.cdc.gov/control-legionella/media/pdfs/Control-Toolkit-Potable-Water.pdf)
- ASHRAE Guideline 12-2020 Addendum b, section 5.3.1(e): alternate heat sources such as self-regulating heat trace may be used alone or with recirculation "to maintain hot water consistently at or above 120°F (49°C)" throughout the system, including pipes returning to the water heater. This is the only primary ASHRAE G12 text I could read, and it confirms 120°F as G12's "recommended minimum temperature" for the distribution system. STANDARD (guideline, free addendum). [READ] — [ASHRAE Addendum b](https://www.ashrae.org/file%20library/technical%20resources/standards%20and%20guidelines/standards%20addenda/g12_2020_b_20210408.pdf)
- VHA Directive 1061 (Aug 2014), Appendix A. [READ] — [VHA Directive 1061 (copy hosted at nj.gov)](https://nj.gov/health/cd/documents/topics/Legionnaires'/prevention-legionella-potablewater.pdf). GUIDANCE-DOC, FIRM for VA facilities:
  - Storage tanks at least 140°F.
  - Instantaneous and semi-instantaneous heat exchanger discharge at least 130°F.
  - Distribution piping at least 124°F (51.1°C), measured "prior to any temperature-reducing mixing valve".
  - Delivered outlet temperature at most 110°F.
  - Cold water at or below 67°F.
  - Monitor temperature at: incoming supply, storage tanks, hot discharge at the source, hot return proximal to the source, return of circulation loops, and representative outlets (loop or branch, hydraulic remoteness, flow).
  - Flush irregular-use or low-flow fixtures at least twice per week.
  - Mixing valves and anti-scald devices must be tested and serviced at least annually per manufacturer instructions, documented, and more often if water quality warrants.
  - Emergency showers and eyewashes: 60–100°F.
  - Emergency "super heat and flush": 160–170°F with at least 30 minutes of flushing at each outlet. This conflicts with the CDC's "thermal remediation not recommended".
  - The Directive's own text notes the 124°F rationale is Legionella inhibition. My search summary says the directive was amended in 2024 and I did not confirm whether 124°F survived. [SNIPPET]
- Plumbing Engineer / PHCP Pros (Hiller) says the 124°F figure is *not* in G12-2020. [FETCHED-SUMMARY] TRADE-PRESS:
  - G12-2020 recommends heater outlet at or above 140°F for any heater with storage, including semi-instantaneous units.
  - Stratification rationale: a semi-instantaneous unit's outlet can read 130°F or more while its bottom sits at 85–110°F.
  - The author argues 120–130°F supply and return is preferable, because temperatures well above 130°F speed disinfectant decay and corrosion.
  - Key fixture targets: 120°F or more at the fixture, and one minute or less time-to-tap.
  - Drop legs: ASHRAE 90.1-2020 requires insulation on at least the first 10 ft of each drop leg.
  - Uninsulated ½–¾ in copper cools from 135°F to 105°F in under 25 minutes at 65–70°F ambient.
  - Source: [PHCP Pros, Legionella cost-effective control part 3](https://phcppros.com/articles/14203-legionella-cost-effective-control-part-3)
- Deppmann (B&G rep) writes that "ASHRAE Guideline 12 … suggests a minimum of 124°F for the hot water return temperature" and 140°F supply with fixture thermostatic valves. This conflicts with the CDC and G12-addendum 120°F figures and with Hiller's statement above. TRADE-PRESS/VENDOR. [READ] — [Deppmann RLD PDF](https://www.deppmann.com/wp-content/uploads/2019/01/RLD_MMM_Temperature-Balancing-Valves-in-Domestic-Water-Recirculation-Systems.pdf)
- PHCP Pros commissioning series (Part 4): ASHRAE recommends storage at least 140°F and "all distribution sections above 122°F". The author targets about 124°F using an ASSE 1017 TMV. Place a gauge on the return line before the cold inlet at the heater, "the lowest-temperature point". Example TMV setpoints: about 144°F if distribution loses 20°F, about 134°F if it loses 10°F. TRADE-PRESS. [FETCHED-SUMMARY] — [PHCP Pros Part 4](https://www.phcppros.com/articles/19045-commissioning-and-troubleshooting-dhw-systems-part-4)
- Illinois DPH adopted 124°F as a minimum distribution temperature citing VA 1061 (per a search summary). [SNIPPET] — [Illinois DPH response to comments](https://dph.illinois.gov/content/dam/soi/en/web/idph/files/77-iac-890-dph-response-to-comments.pdf)
- CMS memo QSO-17-30 requires a water management program with facility-chosen control limits and documented corrective actions. It sets no hot-water temperature. CMS does not require Legionella cultures. GUIDANCE-DOC. [SNIPPET] — [PSQH on CMS memo](https://www.psqh.com/analysis/the-pipes-are-calling-cms-revises-legionella-requirements/)

**Scald limits and device standards**
- Time to permanent (2nd/3rd-degree) burn, adult, from a US CPSC-compiled chart based on Moritz and Henriques 1946. GUIDANCE-DOC. [FETCHED-SUMMARY]; the page's column headers are garbled, so the column assignment is interpreted:

| Water temp | Time to permanent burn |
|---|---|
| 116°F | about 45 min (pain threshold) |
| 122°F | 5 min |
| 131°F | 25 s |
| 140°F | 5 s |
| 149°F | 2 s |
| 154°F | 1 s |

  Source: [A.O. Smith/State Technical Bulletin 34](https://www.hotwater.com/info-center/technical-bulletins/bulletin-34.html)
- VHA 1061: 110°F outlet minimizes scald risk for most adults. Risk rises significantly at 117°F. At 140°F, second-degree burns can occur in about 3 s. [READ] — [VHA 1061](https://nj.gov/health/cd/documents/topics/Legionnaires'/prevention-legionella-potablewater.pdf)
- Watts' 2009 comparison of ASSE standards. MANUFACTURER chart of standard requirements, 1017-2003 edition, so possibly superseded. [READ] — [Watts ASSE comparison](https://www.watts.com/dfsmedia/0533dbba17714b1ab581ab07a4cbb521/18234-source/f-asse-stdcompare):
  - **ASSE 1017** (temperature-activated mixing valves for distribution, i.e. "master" valves): minimum adjustable range 105–120°F. Outlet tolerance ±3°F to ±7°F depending on valve size. 25°F hot-water-increase test. Minimum tested flow 50% of flow at 10 psid. No cold-water-failure test in the 2003 edition (the chart says "Not applicable").
  - **ASSE 1016** (shower valves): outlet maximum 120°F. On cold-water failure, flow is under 0.5 gpm within 5 s before reaching 120°F.
  - **ASSE 1070** (point-of-use limiting devices) and **ASSE 1071** (emergency-equipment mixing valves, outlet 65–95°F): the chart lists a cold-water failure shut-down criterion for each, in the form "flow not exceeding 0.2–0.5 gpm before 120°F". The column alignment was scrambled in extraction, so do not use these figures without checking the standards. 1070 devices are described in the trade press as capping delivered water at 120°F. [FETCHED-SUMMARY] — [Plumber Magazine, Jan 2026](https://www.plumbermag.com/editorial/2026/01/tips-for-mixing-valves)
- Mixing valve field maintenance tips (Plumber Magazine). TRADE-PRESS. [FETCHED-SUMMARY] — [Plumber Magazine](https://www.plumbermag.com/editorial/2026/01/tips-for-mixing-valves):
  - Verify outlet temperature with an accurate digital thermometer at the outlet test port, at stable high-demand flow.
  - Keep normal flow in the central two-thirds of the rated range.
  - Acceptable pressure drop is roughly 5–30 psi.
  - Check valves are required on both supplies.
  - Annual inspection.
  - Creep (gradual outlet rise) means oversizing or scale on the piston.
  - Swings mean an undersized valve or failed check valves allowing crossflow.
  - Incomplete shut-off means scale on seats.

### Inferences
- **ANALYST:** For the model, encode the target as a configurable `t_min_circulating` with default 120°F (CDC, G12 addendum) and an alternate 124°F (VA, some state rules). Flag which jurisdiction or facility type selects each. Do not claim G12 itself says 124°F; the evidence for that is only vendor and trade secondary sources, and Hiller explicitly disputes it.
- **ANALYST:** Scald-limit checks (outlet 110–120°F) and Legionella-limit checks (circulating 120–124°F or more) are two different thresholds on two different pipe segments: pre-mixing-valve distribution vs post-mixing-valve outlet. A check catalogue entry must state which side of the mixing valve it measures on.

### Gaps
- Primary text of G12-2020 sections 5.3 and 5.4 (temperature control, monitoring) and of Standard 188: paywalled and not obtained. Exact G12 monitoring frequencies are unknown to me.
- Current ASSE 1017/1070/1071 test methods and the post-2009 editions: not obtained.
- Whether VHA 1061 (2024 amendment) still says 124°F: unverified.

---

## 2. Check catalogue

### Takeaway
Most of what a catalogue needs (target values, tools, pitfalls) is supported for temperature, mixing-valve, balancing-valve, flow/ΔT, and pressure checks. It is thin on practitioner-stated durations, riser "temperature walk" procedures, check-valve tests for commercial systems, and thermal-balancing-valve verification. For those I found only manufacturer descriptions, forum anecdotes, or nothing. The sourced facts per check come first, followed by a synthesis table of attributes (location, tool, time, safety class) in Inferences. Time and safety class entries there are ANALYST estimates and unsourced.

### Cited Findings (by check)

**C1. Heater setpoint and actual outlet temperature**
- Storage at or above 140°F (60°C). Semi-instantaneous or instantaneous exchanger discharge at or above 130°F (VA) or at or above 140°F (G12 per Hiller). GUIDANCE-DOC. [READ] — [VHA 1061](https://nj.gov/health/cd/documents/topics/Legionnaires'/prevention-legionella-potablewater.pdf); [FETCHED-SUMMARY] — [PHCP Pros](https://phcppros.com/articles/14203-legionella-cost-effective-control-part-3)
- Measuring the "hot water discharge at the hot water source equipment" is a mandatory monitoring point in VHA 1061. [READ] — [VHA 1061](https://nj.gov/health/cd/documents/topics/Legionnaires'/prevention-legionella-potablewater.pdf)

**C2. Tank stratification (multiple temperatures)**
- Electric heaters have an element slightly above the tank bottom, creating a cool layer. Gas and oil heaters heat from the bottom up and do not. GUIDANCE-DOC (Maine CDC). [SNIPPET] — [Maine CDC water-heater checklist](https://www1.maine.gov/dhhs/mecdc/sites/maine.gov.dhhs.mecdc/files/epi/legionella-water-heater-checklist.pdf)
- A patent describes a cool pocket below the lower element at about 85–105°F. Not authoritative. [SNIPPET]
- Plumbing Engineer: semi-instantaneous heater bottom can be 85–110°F while the outlet reads 130°F or more. TRADE-PRESS. [FETCHED-SUMMARY] — [PHCP Pros](https://phcppros.com/articles/14203-legionella-cost-effective-control-part-3)
- NJ DOH sampling guidance names the drain valve at or near the bottom of the heater as a bulk-water sampling point (1 L sample). GUIDANCE-DOC. [SNIPPET] — [NJ DOH sampling guidance](https://nj.gov/health/cd/documents/topics/legion/Environmental%20_Legionella_Sampling_and_Testing_Guidance.pdf)
- I found no published procedure that specifies "N sensors at heights X" for stratification checking, and no tolerance for acceptable top-to-bottom spread. See Gaps.

**C3. Mixing valve inlet/outlet temps and cold-water bypass behaviour**
- Master mixing valves (ASSE 1017) temper stored water (often 140°F or more) to about 120°F or lower for distribution. TRADE-PRESS/MANUFACTURER. [SNIPPET] — [CSE Magazine](https://www.csemag.com/mixing-valves-what-are-they-and-how-do-they-work/)
- Outlet verification with a digital thermometer at the outlet test port, at stable high-demand flow, then adjust the locked cap to target. Log setpoint and high-limit. Tolerance not given in that article; the Watts chart gives ±3 to ±7°F for 1017 valves by size (see section 1). TRADE-PRESS. [FETCHED-SUMMARY] — [Plumber Magazine](https://www.plumbermag.com/editorial/2026/01/tips-for-mixing-valves)
- Powers (Watts) says a licensed contractor must perform annual maintenance on master valves. Cleaning and inspection frequency depends on local water conditions. MANUFACTURER. [SNIPPET] — [Powers LFSH1430 manual](https://www.manualsdir.com/manuals/592983/powers-sh1430-hi_lo-master-tempering-valves-lfsh1430-hi_lo-master-tempering-valves.html)
- Powers describes the LFSH1430 single-seat design as giving "virtual shut down" on cold-water failure. MANUFACTURER. [SNIPPET]
- I did not find a specific, citable "cold-water bypass test" under that name for master valves. In the standards "cold water bypass" is a lab requirement: the minimum flow the valve must pass when the hot side is lost, or the flow limit when cold is lost. Do not present it as a standard field test.

**C4. Mixing valve thermal-shutdown / failure-mode test**
- Powers ES150 (emergency tempering valve, a different product class) manual steps. MANUFACTURER. [SNIPPET] — [Powers/Watts ES150 manual](https://watts.ca/dfsmedia/0533dbba17714b1ab581ab07a4cbb521/36472-source/es-p-sf-es150-ttrc):
  1. Check outlet temperature against the factory 85°F setting.
  2. Close the cold checkstop and confirm flow stops right away.
  3. Reopen cold, close the hot checkstop, and confirm adequate cold flow.
  4. Reopen hot and confirm the temperature returns to setpoint.
  5. Lock and tag.
  This product-specific procedure suggests the general method for master valves: isolate cold, observe outlet temperature and flow. I did not find an equivalent Powers master-valve procedure.
- Foreign analogue: NSW Health approval spec tests thermal shut-off with cold isolation. A UK approval document field check: isolate the cold supply to the TMV, wait 5 s, and if flow continues confirm outlet is below 46°C. This is non-US, non-ASSE and not valid for US 1017 acceptance. GUIDANCE-DOC (foreign). [SNIPPET] — [NSW Health spec](https://www.health.nsw.gov.au:443/environment/legionellacontrol/Documents/warm-water-approval-spec-part-a.pdf)
- VA requires annual test and service of mixing valves/anti-scald devices per manufacturer instructions. [READ] — [VHA 1061](https://nj.gov/health/cd/documents/topics/Legionnaires'/prevention-legionella-potablewater.pdf)

**C5. Recirculation return temperature (at heater, at loop ends, at each riser return)**
- Place a gauge on the return line before the cold inlet at the heater (lowest-temperature point, key control location). TRADE-PRESS. [FETCHED-SUMMARY] — [PHCP Pros Part 4](https://www.phcppros.com/articles/19045-commissioning-and-troubleshooting-dhw-systems-part-4)
- VHA requires monitoring "hot water return proximal to the hot water source equipment" and "water at the return of circulation loops". [READ] — [VHA 1061](https://nj.gov/health/cd/documents/topics/Legionnaires'/prevention-legionella-potablewater.pdf)
- Plumbers' forum case: riser returns at far ends were 37–42°C, with no balancing valves on return pipework and each tap tee'd to its own return. Poster suspected short-circuiting, with stagnant areas elsewhere. FORUM-ANECDOTE, UK. [SNIPPET] — [Plumbers Forums](https://www.plumbersforums.net/goto/post?id=954752)

**C6. Loop ΔT and design ΔT (flow implication)**
- Flow formula: GPM = BTU/h / (ΔT × 500). Common design practice is ΔT = 10°F, so GPM = BTU/h / 5000. Caleffi says ΔT is "the temperature difference of the recirculating water between the heat source and the furthest fixture in each circuit". Heat loss in return lines downstream of balancing valves is excluded. MANUFACTURER. [READ] — [Caleffi ThermoSetter 1164](https://s3.amazonaws.com/s3.supplyhouse.com/product_files/Caleffi-116441AC-UserGuide.pdf)
- PHCP Pros (CircuitSolver article): common design ΔT of 5°F (GPM = BTU/h / 2500), or 10°F (÷5000). Smaller ΔT requires higher flow. TRADE-PRESS/VENDOR. [FETCHED-SUMMARY] — [PHCP Pros](https://www.phcppros.com/articles/14497-thermostatically-balanced-dhwr-systems-benefits-and-design-considerations)
- Deppmann worked example: 25,200 BTU/h / (10 × 500) = 5.04 gpm, with the target that the last fixture is no more than 10°F cooler than supply. The author says the quick formula is conservative. TRADE-PRESS. [SNIPPET] — [Deppmann Part 1](https://www.deppmann.com/blog/monday-morning-minutes/domestic-hot-water-recirculation-systems-design-flow-rate/)
- Plumbing Engineer: some manufacturers prefer a 10–20°F supply-to-return difference. At peak draw the return can come within 1–2°F of supply. TRADE-PRESS. [FETCHED-SUMMARY] — [PHCP Pros Part 4](https://www.phcppros.com/articles/19045-commissioning-and-troubleshooting-dhw-systems-part-4)
- The design ΔT depends on the author, the loop, and the minimum-temperature criterion. It is ROT, not a code number. G12/188 give temperature floors, not a ΔT.
- Measured field heat losses in California multifamily buildings were 1.1–2.3 times idealized calculations (24.1 to 99.9 W per apartment, mean 62.5 W). Likely causes: insulation imperfections and cold-water crossover. GUIDANCE-DOC (ETCC study summary). [FETCHED-SUMMARY] — [ETCC multifamily DHW recirculation survey](https://www.etcc-ca.com/reports/multifamily-domestic-hot-water-recirculation-survey)

**C7. Pump status, amps, rotation, air-bound**
- Confirm correct rotation and open isolation valves at commissioning. TRADE-PRESS. [FETCHED-SUMMARY] — [PHCP Pros Part 4](https://www.phcppros.com/articles/19045-commissioning-and-troubleshooting-dhw-systems-part-4)
- Heuristics from forums and consumer-facing guides, all FORUM-ANECDOTE/VENDOR-MARKETING quality. [SNIPPET]:
  - Amps over about 1.5 times nameplate suggest a locked rotor or air.
  - Loosen the bleed screw with the pump running to test for air vs a seized impeller.
  - Compare outlet and inlet pipe temperature.
  - Integral check valves in circulators can trap air.
  - Source: [HeatingHelp forum](https://forum.heatinghelp.com/discussion/comment/1836311/); [Liberty Home Guard](https://www.libertyhomeguard.com/circulation-pump-troubleshooting/)
- I found no manufacturer (Taco, Bell & Gossett, Grundfos, Armstrong) troubleshooting document for DHW recirculators retrievable in this session.

**C8. Pump head and flow vs curve**
- Pump selection principle: size to offset heat loss to the farthest fixture on each circuit. An undersized pump lets water cool. Oversizing raises cost, erosion, and noise. MANUFACTURER/VENDOR. [FETCHED-SUMMARY] — [PHCP Pros](https://www.phcppros.com/articles/14497-thermostatically-balanced-dhwr-systems-benefits-and-design-considerations)
- Copper Development Association velocity limits via PHCP Pros: cold 8 ft/s; hot up to about 140°F 5 ft/s; routinely above 140°F 2–3 ft/s. Use lower for ½ in and smaller. TRADE-PRESS citing CDA. [FETCHED-SUMMARY] — [PHCP Pros Part 4](https://www.phcppros.com/articles/19045-commissioning-and-troubleshooting-dhw-systems-part-4)
- Armstrong's fixed-orifice balancing valves have a fixed Cv, so you measure differential pressure across the valve and read flow. Variable-orifice valves take about twice as long to set. MANUFACTURER (trade-press by an Armstrong employee). [READ] — [Armstrong, Mechanical Business Dec 2008](https://armstrongfluidtechnology.com/~/media/documents/sales-and-marketing/white-papers/mb-article_when-its-hot_its-hot_december-2008.pdf?la=es-us)
- No published method specific to a field head-and-flow-vs-curve check was found. The general approach is: measure differential pressure across the pump with gauges at the taps, read head, and enter the curve. See Gaps.

**C9. Aquastat / timer / controller**
- Typical control: an aquastat on the return stops the circulator at a high setpoint and restarts it at a low one, plus an optional timer to stop it overnight. MANUFACTURER. [READ] — [Armstrong, Mechanical Business Dec 2008](https://armstrongfluidtechnology.com/~/media/documents/sales-and-marketing/white-papers/mb-article_when-its-hot_its-hot_december-2008.pdf?la=es-us)
- Hospitality surveys found systems on 24/7, in one case with the aquastat set so high it could never turn the pump off. Building staff often raise the return setpoint past supply, defeating the control. TRADE/GUIDANCE (DOE/ARIES-related). [SNIPPET] — [NREL/ARIES control strategies](https://research-hub.nrel.gov/en/publications/control-strategies-to-reduce-the-energy-consumption-of-central-do/)
- A compliance document requires pump operation limited to 10 minutes after each activation, running until return reaches no more than 10°F above initial pipe temperature or 102°F. [SNIPPET] — [Title 24 NRCI form](https://images1.energycodeace.com/download/42571/file_path/fieldList/2013-NRCI-PLB-02-HighRiseResHotelMotel-MultifamilyCentral-HWSystemDistribution.pdf). Jurisdiction-specific; do not generalize.
- PHCP Pros: operators often change setpoints or upsize pumps without knowing the engineer's intent. The author recommends posted signage. TRADE-PRESS. [FETCHED-SUMMARY] — [PHCP Pros Part 4](https://www.phcppros.com/articles/19045-commissioning-and-troubleshooting-dhw-systems-part-4)

**C10. Check valve tests (crossover, reversal, equalisation)**
- Crossover test (water-heater-rescue.com, a hobbyist/consultant site; residential): turn off power, shut the cold supply to the heater, open a hot tap. Flow should stop in seconds. If it keeps running, either the isolation valve is leaking or a cross-connection exists. Then shut stops one at a time to find it. Advises against adding a check valve on the heater cold inlet. FORUM-ANECDOTE/TRADE. [FETCHED-SUMMARY] — [Water Heater Rescue](https://www.waterheaterrescue.com/troubleshooting/tanklets/cross-connections.html)
- Forum guidance: recirculation return needs a check valve; stuck-open valve gives backflow, usually first noticed at distal fixtures. A mixing-valve failure typically shows at multiple fixtures; a recirc check-valve problem tends to appear after a pump is added or gets worse when the pump runs. FORUM-ANECDOTE. [SNIPPET] — [HeatingHelp](https://forum.heatinghelp.com/discussion/comment/1894209/)
- ETCC field study names cold-water crossover (pressure imbalance pushing cold into the hot loop) as a likely cause of elevated loop losses. GUIDANCE-DOC. [FETCHED-SUMMARY] — [ETCC](https://www.etcc-ca.com/reports/multifamily-domestic-hot-water-recirculation-survey)
- I found no authoritative commercial procedure for "temperature-equalisation" tests or for isolating a failed riser check valve.

**C11. Thermal balancing valve setting verification and "riser temperature walk"**
- Thermostatic balancing valves (Caleffi ThermoSetter, B&G Temp Setter) modulate flow to hold a set temperature at the valve. They never fully close. MANUFACTURER. [READ] — [Caleffi 1164](https://s3.amazonaws.com/s3.supplyhouse.com/product_files/Caleffi-116441AC-UserGuide.pdf); [READ] — [Deppmann RLD](https://www.deppmann.com/wp-content/uploads/2019/01/RLD_MMM_Temperature-Balancing-Valves-in-Domestic-Water-Recirculation-Systems.pdf)
- Caleffi 1164: adjustable 105–150°F, factory 135°F, Cv 0.35 min / 2.1 max, design Cv 0.69 at ΔT=10°F inlet-to-setpoint, max differential pressure 15 psi. Optional dry-well for a slide-in thermometer or remote sensor, and an optional check valve. Its instructions say "Do not set at temperatures >120°F if anti-scald valves are not installed at the fixtures." MANUFACTURER. [READ] — [Caleffi 1164](https://s3.amazonaws.com/s3.supplyhouse.com/product_files/Caleffi-116441AC-UserGuide.pdf)
- B&G Temp Setter: setpoint adjustable 98–150°F; bypass option for disinfection; Deppmann says responsibility for setting should be assigned in the spec. VENDOR/MANUFACTURER. [READ] — [Deppmann RLD](https://www.deppmann.com/wp-content/uploads/2019/01/RLD_MMM_Temperature-Balancing-Valves-in-Domestic-Water-Recirculation-Systems.pdf)
- Verification procedure: neither manufacturer document gives a "walk the risers and read each valve" procedure. The Caleffi valve provides a dry-well and gauge for local reading. The valve outlet temperature at or near setpoint implies the valve is throttling at minimum flow; a reading well below setpoint implies the valve is wide open and the branch is not delivering. This reading of valve behaviour follows from the manufacturer's operating description, but I did not find it written as a field procedure. See Inferences.
- Manual-balancing weakness: traditional balancing valves set nearly closed and fail "as soon as a tap is opened". MANUFACTURER/TRADE. [SNIPPET] — [Modern Building Services](https://modbs.co.uk/news/fullstory.php/aid/4867/Achieving_efficient_and_safe_recirculating_hot-water_systems_.html)

**C12. Balancing procedure (ASHRAE G12 / ASPE)**
- Armstrong worked example (four-storey, three units per floor): set each floor's distal-unit circuit balancing valve to 0.5 gpm design flow, balancing from the top floor down, then balance floors against each other (1.5 gpm each), and finally the main valve (6 gpm total). MANUFACTURER. [READ] — [Armstrong](https://armstrongfluidtechnology.com/~/media/documents/sales-and-marketing/white-papers/mb-article_when-its-hot_its-hot_december-2008.pdf?la=es-us)
- Armstrong says fixed-orifice valves with a known Cv speed the process: set the differential pressure that corresponds to the required flow. [READ] (same source)
- The published procedure for ASHRAE Guideline 12 / ASPE was not accessible (paywalled). Hiller's article series states no balancing procedure. [FETCHED-SUMMARY]

**C13. Strainer / filter pressure drop**
- Caleffi: flush the pipes before installing, and fit strainers of sufficient capacity at the inlet. [READ] — [Caleffi 1164](https://s3.amazonaws.com/s3.supplyhouse.com/product_files/Caleffi-116441AC-UserGuide.pdf)
- Plumber Magazine: acceptable mixing valve pressure drop about 5–30 psi, with full-port isolation valves. TRADE-PRESS. [FETCHED-SUMMARY] — [Plumber Magazine](https://www.plumbermag.com/editorial/2026/01/tips-for-mixing-valves)
- No source found giving a strainer ΔP alarm threshold specific to DHW systems. See Gaps.

**C14. Scale and sediment (exchanger ΔT, flush, hardness)**
- Armor (Lochinvar) product data lists a maximum water hardness of 15 grains for AWH models. MANUFACTURER. [SNIPPET] — [Lochinvar Armor product summary](https://assets.lochinvar.com/damroot/Original/10013/Armor%20Product%20Summary%20AWH-PS-03%20part%201.pdf)
- Lochinvar scale fact sheet: scale is proportional to water volume and temperature. MANUFACTURER. [SNIPPET] — [Lochinvar scale sheet](https://www.lochinvar.com/news/NewsFile_686210_FS-SCALE-01.pdf)
- One grain per gallon is about 17 mg/L. GUIDANCE-DOC (Penn State Extension, via search summary). [SNIPPET]
- The Maine CDC instructions for flushing a tank: turn off energy, run a hot tap about 10 minutes, attach a hose to the drain valve, open the drain, and take care because sediment can clog the drain. GUIDANCE-DOC (residential). [READ, partial] — [Maine CDC water heater page](https://www1.maine.gov/dhhs/mecdc/sites/maine.gov.dhhs.mecdc/files/epi/legionella-water-heater-checklist.pdf)
- A patent describes detecting scale by the difference between heat-exchange surface temperature and water temperature, with no numeric limit. Not authoritative. [SNIPPET]
- No standard numeric exchanger ΔT limit exists in my sources. Forum posts quote 25°F or 55°F limits for specific units. FORUM-ANECDOTE, unverified.

**C15. Static and dynamic pressure at the plant; PRV outlet pressure**
- A PRV is required where static supply pressure exceeds 80 psi (IPC 604.8, UPC 608.2 per a study guide). Typical setpoints 40–60 psi (A.O. Smith bulletin); forum experts quote 65 psi. GUIDANCE-DOC/FORUM. [SNIPPET] — [A.O. Smith Technical Bulletin 45](https://www.hotwater.com/info-center/technical-bulletins/bulletin-45.html); [open-exam-prep study guide](https://open-exam-prep.com/study-guides/journeyman-plumber/water-supply-distribution/pressure-boosters-prvs). Verify the adopted code edition.
- A PRV with a check valve or backflow preventer creates a closed system, so expansion raises pressure. The A.O. Smith bulletin describes a gauge test: install a dead-hand gauge on the drain valve, heat the water, and watch pressure. MANUFACTURER. [SNIPPET]
- Diagnosing PRV "creep": outlet pressure rising at no flow can be thermal expansion or seat leak-by. Isolate the expansion tank and repeat. FORUM-ANECDOTE. [SNIPPET] — [HeatingHelp](https://forum.heatinghelp.com/discussion/comment/1848614/)

**C16. Time-to-hot at the far fixture (draw test)**
- Commissioning method: start a timer, record temperature about every 5 s until it stabilizes, and record time to maximum, maximum temperature, and flow (gpm). TRADE-PRESS. [FETCHED-SUMMARY] — [PHCP Pros Part 4](https://www.phcppros.com/articles/19045-commissioning-and-troubleshooting-dhw-systems-part-4)
- Benchmarks: under 10 s ideal; 10–30 s moderately acceptable; over 30 s generally unacceptable. This is described as an ASPE performance rating in a search summary. ROT, not code. TRADE-PRESS. [FETCHED-SUMMARY] (same article); the ASPE attribution is [SNIPPET] only.
- Delays over 15 minutes can occur at remote fixtures if the pump has failed or branches are badly balanced. TRADE-PRESS. [FETCHED-SUMMARY] (same article)
- WaterSense New Homes inspection test: collect no more than 0.6 gal before hot water is delivered, defined as a rise of at least 10°F, using a marked bucket. That is about 24 s for a lavatory faucet. It is a residential test. GUIDANCE-DOC. [SNIPPET] — [PNNL WaterSense hot water delivery](https://basc.pnnl.gov/information/watersense-hot-water-delivery-requirements)
- Hiller: key target is one minute or less time-to-tap and at least 120°F at the fixture. TRADE-PRESS. [FETCHED-SUMMARY] — [PHCP Pros](https://phcppros.com/articles/14203-legionella-cost-effective-control-part-3)

**C17. Fixture-level checks (cartridge, single-lever crossover)**
- Hot-to-cold crossover through faucet cartridges when the recirc loop is pressurized: forum report that certain faucets allow hot-to-cold flow when recirculation runs. FORUM-ANECDOTE. [SNIPPET] — [HeatingHelp](https://forum.heatinghelp.com/discussion/comment/1894209/)
- Cold-water tap hot-water test: hot water at a cold tap for only a minute or two near the heater may be convection and not valve failure; heat traps address this. FORUM/TRADE. [FETCHED-SUMMARY] — [Water Heater Rescue](https://www.waterheaterrescue.com/troubleshooting/tanklets/cross-connections.html)
- No manufacturer procedure for the cold/hot equalisation test of single-lever faucets was found. See Gaps.
- CDC: low-flow and electronic-sensor faucets raise Legionella risk; clean aerators, showerheads and hoses regularly. GUIDANCE-DOC. [READ] — [CDC PDF](https://www.cdc.gov/control-legionella/media/pdfs/Control-Toolkit-Potable-Water.pdf)

**C18. Expansion tank precharge**
- Procedure (Taco technician via forum, plus consumer blog): isolate the tank; drain the system side to 0 psi; measure the air side at the Schrader valve with a tire gauge; set the precharge equal to static (cold-fill) pressure; water at the Schrader valve means a failed bladder, so replace. FORUM-ANECDOTE, hydronic/residential origin. [SNIPPET] — [Steve Jenkins](https://www.stevejenkins.com/blog/2013/12/testing-and-replacing-a-hot-water-expansion-tank/); [HeatingHelp](https://forum.heatinghelp.com/discussion/comment/1625938)
- Zurn: set precharge equal to line pressure, not above 80 psi. MANUFACTURER. [SNIPPET] — [Zurn ISWTTA](https://res.cloudinary.com/dzhpkjoqj/Zurn/ISWTTA-pdf.pdf)
- Factory precharge values reported inconsistently (12 vs 20 psi): measure, don't assume. FORUM-ANECDOTE.
- Symptoms of a waterlogged tank: T&P/PRV discharge. [SNIPPET]

**C19. Energy / gas input (gas pressure)**
- Lochinvar's service handbook lists a gas pressure gauge or manometer as a required tool; digital manometers of ±20.00 in. w.c., resolution 0.01 in. w.c., are suggested. Armor product data lists inlet gas pressure min 4.0 in. w.c. and max 14.0 in. w.c. for natural gas. MANUFACTURER. [SNIPPET] — [Lochinvar Service Handbook](https://assets.lochinvar.com/damroot/Original/10014/588065100324835%20%20Service%20Handbook%202020.pdf)
- Manifold pressure values are model specific and I did not find them. Inlet and manifold are different readings.

**C20. Heat pump water heater lockout**
- CO2 (R-744) commercial heat pump water heaters cannot accept hot return water. A trim tank (electric resistance, sized to recirculation load) is piped in series, and the return feeds the trim tank. If it fails or is bypassed, the heat pump can see wrong return temperatures and lock out. TRADE-PRESS (Deppmann). [SNIPPET] — [Deppmann HPWH part 6](https://www.deppmann.com/?p=21091)
- Flow-sensor logic: a constantly running recirc pump can keep a heat pump cycling (installer report). FORUM-ANECDOTE.
- NREL estimate: 75% loss reduction if the loop is insulated. [SNIPPET] — [NREL](https://nrel.gov/docs/legosti/old/1198.pdf)
- No Sanden or Colmac fault-code or lockout table was found. See Gaps.

**C21. BAS trend checks**
- Control strategies to look for: timer, return-temperature aquastat, demand control, supply setpoint modulation. DOE/ARIES combined strategy achieved a 15% fuel reduction with pump runtime of 14 minutes per day or less. GUIDANCE-DOC (DOE/NREL). [SNIPPET] — [NREL/ARIES](https://research-hub.nrel.gov/en/publications/control-strategies-to-reduce-the-energy-consumption-of-central-do/)
- VHA 1061 calls for continuous temperature monitoring at source discharge, source return, and loop returns. [READ] — [VHA 1061](https://nj.gov/health/cd/documents/topics/Legionnaires'/prevention-legionella-potablewater.pdf)
- Candidate trend rules in the search output were synthesized by the search tool, not drawn from a source. I list them as ANALYST in Inferences.

**C22. Data-logger deployment**
- Onset HOBO pipe sensor SD-TEMP-P-06 (for MX1104/MX1105 multi-channel loggers): $94 list, ±0.15°C from 0–70°C, response typically under 1 min to 90% on a pipe. VENDOR-MARKETING. [SNIPPET] — [Onset SD-TEMP-P-06](https://www.onsetcomp.com/products/sensors/sd-temp-p-06)
- Onset TMC6-HE pipe/bolt-on probe: $69, −40 to 100°C, 3 min typical response in 1 m/s air. VENDOR-MARKETING. [SNIPPET] — [TEquipment HOBO series](https://www.tequipment.net/HOBO-by-Onset/series_hobo-logger-series)
- TidbiT MX2203/MX2204: ±0.2°C, $170–$180. VENDOR-MARKETING. [SNIPPET] — [TEquipment MX2204](https://www.tequipment.net/HOBO-by-Onset/MX2204/Temperature-Dataloggers/?b=y)
- Fluke 80PK-8/80PK-10 Type K pipe clamps about $240–$343, repeatability 1°F; Fluke 54-2 B dual-input logging thermometer about $520 (500 points); Fluke 1524 about $2,500–$2,900. VENDOR-MARKETING. [SNIPPET] — [Fluke 80PK-10](https://flukecal.com/en-us/product/accessories/probes/fluke-80pk-10)
- Fieldpiece pipe-clamp spec: ±4°F, improving to ±1°F after field calibration. Insulate the clamp. MANUFACTURER. [SNIPPET] — [Fieldpiece ATC1](https://s3.amazonaws.com/s3.supplyhouse.com/product_files/ATC1-user.pdf)
- No published practitioner guidance on logging duration or placement for DHW loops was found.

### Inferences (ANALYST synthesis; times and safety classes are unsourced estimates to be validated)

**Catalogue attribute table.** Location codes: MR = mechanical room, RS = riser, FX = fixture, RF = roof, BAS = remote. "Remote?" says whether a BAS or logger can supply the reading. Time is an estimate for one technician already on the spot, excluding travel.

| ID | Check | Measured / where | Tool | Normal vs abnormal (grade) | Discriminates | Loc. | Time (est.) | Safety class | Remote? |
|---|---|---|---|---|---|---|---|---|---|
| C1 | Setpoint + actual heater outlet | Outlet pipe, setpoint dial/BAS | Contact probe or clamp thermocouple, BAS | storage at least 140°F; HX discharge at least 130–140°F (FIRM-VA / G12-per-Hiller) | burner/element/HPWH output, setpoint drift | MR | 5–10 min | Scald, hot surfaces | Yes if BAS has sensor |
| C2 | Stratification | Outlet, mid, drain/bottom | Probes, drain sample | bottom near outlet; bottom 85–110°F abnormal (ROT) | Cool-layer tank, short-circuiting, poor mixing | MR | 15–30 min | Scald at drain, hot discharge | Partly (multi-point tank sensors) |
| C3 | Mixing valve in/out | Hot in, cold in, mixed out | 3 probes or clamps | Out within ±3–7°F of setpoint (1017 lab tolerance, ROT in field) | Valve drift, scale, bad checks | MR | 10–20 min | Scald | Yes if valve outputs logged |
| C4 | Mixing valve shutdown | Outlet flow/temp with cold isolated | Probe, hose/bucket | Flow drops to a trickle, outlet not above setpoint+limit | Failed element, stuck piston | MR | 15–30 min | Scald, isolation, lockout of valves | No |
| C5 | Return temp: heater and riser/loop returns | Return pipe at heater and each riser | Clamp probes, dry-wells, BAS | At least 120°F (CDC/G12) or at least 124°F (VA) | Short-circuit, low flow, balancing, heat loss | MR/RS | 5 min each point | Hot surfaces | Yes if sensors exist |
| C6 | Loop ΔT (supply minus return) | Supply and return at the plant | 2 probes, BAS | Design 5–10°F (ROT). Measured ΔT well above design implies flow below design (physics) | Low flow, fouled strainer, bad pump | MR | 10 min (plus stabilization) | Hot surfaces | Yes |
| C7 | Pump status/amps/rotation/air | Pump, motor | Clamp meter, bleed screw | Amps vs nameplate (ROT) | Pump failure, air | MR | 10–20 min | Electrical, hot water at bleeder | Partly (status, amps) |
| C8 | Pump head vs curve | Suction and discharge pressure | Two gauges | On-curve | Wrong pump, fouling, closed valves | MR | 15–30 min | Pressure | No |
| C9 | Aquastat/timer/controller | Setpoints, schedule | Readout, thermometer | Setpoint below supply and inside the intended band | Overridden control, wrong schedule | MR | 5–10 min | Electrical | Yes |
| C10 | Check valve / crossover | Heater isolated; hot tap flow; riser temps | Observation, probes | Flow stops within seconds (FORUM) | Crossover, stuck check | MR then FX | 20–60 min | Isolation/lockout of heater, scald | No |
| C11 | Thermal balancing valve verification | Valve outlet temperature | Dry-well gauge, clamp probe | Near valve setpoint at minimum flow; well below = open and starved (derived from operating description) | Valve failed, branch starved, wrong setpoint | RS | 5–10 min per valve | Scald | Partly |
| C12 | Balancing check | Flow or ΔP per valve | Differential pressure meter | Fixed-orifice valve ΔP corresponds to design flow | Mis-set valves, imbalance | MR/RS | 5–10 min per valve | Pressure | No |
| C13 | Strainer ΔP | Pressure either side | Two gauges | Rising ΔP over baseline (no sourced limit) | Fouled strainer, low flow | MR | 5–10 min | Pressure | Partly |
| C14 | Scale/sediment | Exchanger approach, flush, hardness | Probes, test kit | Hardness vs maker maximum (e.g. 15 gpg Armor) | Scale, reduced output | MR | 20–60 min | Scald, hot discharge | Partly |
| C15 | Plant pressure | Static and dynamic, PRV outlet | Gauge | PRV outlet 40–80 psi (ROT; code limit 80 psi) | PRV drift, thermal expansion | MR | 10 min | Pressure | Partly |
| C16 | Time-to-hot draw test | Fixture temp vs time | Stopwatch, probe | Under 10 s ideal, over 30 s unacceptable (ROT) | Whole-branch dead or poor flow | FX | 5–10 min per fixture | Scald | No |
| C17 | Fixture cartridge/crossover | Fixture stops | Hands, thermometer | Cold tap warm only briefly | Local crossover vs system | FX | 10–20 min | Scald | No |
| C18 | Expansion tank precharge | Schrader valve | Tire gauge | Equals static pressure | Waterlogged tank | MR | 10–15 min | Pressure, isolation | No |
| C19 | Gas pressure | Inlet/manifold | Manometer | Per model manual | Starved burner | MR | 10–15 min | Gas, combustion | Partly |
| C20 | HPWH lockout | Return and trim tank temperature, faults | Probes, controller | Per maker | HPWH locked out by hot return | MR/RF | 15–30 min | Electrical, refrigerant | Yes (BAS faults) |
| C21 | BAS trends | Supply, return, pump status | BAS | See rules below | Many | BAS | 15–60 min | none | Yes |
| C22 | Logger deployment | Return pipes, selected fixtures | Loggers | Per above | Time-of-day effects | MR/RS/FX | 30–90 min install; 3–7 day record (ROT) | Access, scald | Yes after install |

**Derived physics (ANALYST).** Because flow = loss / (500 × ΔT), a measured loop ΔT far above the design 5–10°F implies actual flow is below design, assuming loss equals design loss. A measured ΔT near zero with the pump running implies either very high flow, a bypass, or a stuck-open path. Do not use ΔT alone, since heat loss may also be higher than designed (the ETCC study found 1.1–2.3 times).

**Candidate BAS trend rules (ANALYST, not sourced):**
1. Return temperature below the minimum for an extended period.
2. Pump runtime far above a controlled-loop benchmark (the 14 min/day figure is from a specific demand-control study, so use it only for similar control).
3. Return within a few degrees of supply while the pump runs (aquastat bypassed).
4. Pump running when unoccupied.
5. Supply setpoint changed off schedule.
6. Pump on with no temperature response.

**Riser temperature walk (ANALYST).** From the manufacturer operating descriptions, I would build the check as: read the temperature at each riser return or thermal valve and compare with the setpoint; any riser well below setpoint is starved. No source gives a threshold or protocol. Treat as an unvalidated method.

### Gaps
- No source for stratification thresholds, riser temperature walk procedure, strainer ΔP limit, pump head-vs-curve method, DHW exchanger ΔT limit, or equalisation tests at fixtures.
- No ASHRAE G12 or ASPE balancing procedure text (paywalled).
- No Sanden or Colmac HPWH fault tables. No Taco, B&G or Grundfos DHW pump troubleshooting documents. No Symmons, Leonard or Powers master-valve field-test document. Search coverage did not reach these manuals.

---

## 3. Measurement pitfalls that cause false normals and false abnormals

### Takeaway
The biggest sourced pitfalls are infrared reading of bare copper, poor thermal contact of clamp sensors, ambient and insulation effects, and the fact that a surface reading is not water temperature. Most pitfalls in this list have no practitioner source specific to DHW, so they are physics-based inferences marked as such.

### Cited Findings
- Polished metal has low emissivity and reflects surrounding radiation, so IR thermometers misread. A forum post quoting an engineering table gives polished copper about 0.023–0.052 vs oxidized copper about 0.78. Workarounds: high-emissivity tape or paint on the spot. FORUM-ANECDOTE/VENDOR. [SNIPPET] — [HeatingHelp](https://forum.heatinghelp.com/discussion/comment/1471123/); [ICS Schneider on IR and bare metal](https://www.ics-schneider.de/infrarot-thermometer-auf-blankem-metall-emissionsgrad-reflexion-und-messfleck-richtig-beherrschen/?lang=en)
- Contact sensors: contact quality is the main error source. Use thermal paste or dough, insulate over the sensor, and validate against a reference on site. A purpose-built contact thermometer for insulated pipe uses a spring sleeve and an insulating buffer and is rated 20–120°C for 20–90 mm pipe. VENDOR-MARKETING. [SNIPPET] — [OEG TermoQuick](https://www.oeg.net/termoquick-contact-thermometer-516004232); [CFM metrology paper](https://cfmetrologie.edpsciences.org/10.1051/metrology/20150015007)
- Clamp thermocouple accuracy is ±4°F as shipped and ±1°F after field calibration (Fieldpiece). Fluke publishes ±1°F repeatability only. MANUFACTURER. [SNIPPET] — [Fieldpiece ATC1 manual](https://s3.amazonaws.com/s3.supplyhouse.com/product_files/ATC1-user.pdf); [Fluke 80PK-10](https://flukecal.com/en-us/product/accessories/probes/fluke-80pk-10)
- Stagnant-water and drop-leg effects: uninsulated ½–¾ in copper cools 135°F → 105°F in under 25 min and below 85°F in about an hour; insulated pipe takes 2–3 hours. A reading taken at a drop leg that has not been flushed reflects cooldown, not loop temperature. TRADE-PRESS (Hiller citing cooldown data). [FETCHED-SUMMARY] — [PHCP Pros](https://phcppros.com/articles/14203-legionella-cost-effective-control-part-3)
- Stratification: an outlet-only reading can read normal while the tank bottom is in the growth range. TRADE-PRESS. [FETCHED-SUMMARY] — [PHCP Pros](https://phcppros.com/articles/14203-legionella-cost-effective-control-part-3)
- Time-of-day: pumps on timers or demand controls cycle, so a single return reading depends on whether the pump just ran. Return can reach within 1–2°F of supply at peak draw. TRADE-PRESS. [FETCHED-SUMMARY] — [PHCP Pros Part 4](https://www.phcppros.com/articles/19045-commissioning-and-troubleshooting-dhw-systems-part-4)
- Mixing valve outlet test: measure at stable high-demand flow; low-flow operation causes creep. TRADE-PRESS. [FETCHED-SUMMARY] — [Plumber Magazine](https://www.plumbermag.com/editorial/2026/01/tips-for-mixing-valves)
- VA requires thermometers and probes used to verify bath temperature be calibrated and validated. GUIDANCE-DOC. [READ] — [VHA 1061](https://nj.gov/health/cd/documents/topics/Legionnaires'/prevention-legionella-potablewater.pdf)
- The Caleffi thermal valve passes a minimum flow even at setpoint, so a valve outlet reading near setpoint does not itself prove the branch beyond it is warm. MANUFACTURER. [READ] — [Caleffi 1164](https://s3.amazonaws.com/s3.supplyhouse.com/product_files/Caleffi-116441AC-UserGuide.pdf)

### Inferences (ANALYST)
- **False normals:** IR on shiny copper (reads low or reflects ambient); outlet-only heater reading; return reading just after a pump cycle; single-time-point logger snapshot; reading the valve outlet but not the branch end; temperature at the TMV outlet rather than the pre-TMV distribution.
- **False abnormals:** IR on shiny copper near a hot object (reads high); clamp on a pipe with a dead leg stub or fitting; uninsulated clamp in a cold mechanical room (reads low); drop-leg temperature measured after stagnation; measuring with the pump off; thermometer at a tee on a bypass.
- Reading ΔT with two clamps whose individual errors are ±2°C can swamp a ΔT of a few degrees, so cross-check both clamps on the same pipe first. This follows from the manufacturer accuracy figures but is not stated by a source for DHW.

### Gaps
- No quantitative IR error study for DHW pipe was found. No published field study on false-normal rates by method.

---

## 4. Time per check and tool costs

### Takeaway
I found almost no practitioner-stated durations. The sourced timing facts are the 5-second sampling interval for a draw test, the 10-minute tank flush (residential), the 24 s WaterSense lavatory benchmark, and Armstrong's remark that variable-orifice valves take about twice as long to set. All other times in the catalogue table are my estimates. Tool prices come from vendor listings.

### Cited Findings
- Draw test: record temperature about every 5 s until stable. TRADE-PRESS. [FETCHED-SUMMARY] — [PHCP Pros Part 4](https://www.phcppros.com/articles/19045-commissioning-and-troubleshooting-dhw-systems-part-4)
- Tank flush: run a hot tap about 10 minutes first to cool the tank. GUIDANCE-DOC (Maine, residential). [READ, partial] — [Maine CDC](https://www1.maine.gov/dhhs/mecdc/sites/maine.gov.dhhs.mecdc/files/epi/legionella-water-heater-checklist.pdf)
- Variable-orifice balancing valves take about twice as long to set as fixed-orifice. MANUFACTURER. [READ] — [Armstrong](https://armstrongfluidtechnology.com/~/media/documents/sales-and-marketing/white-papers/mb-article_when-its-hot_its-hot_december-2008.pdf?la=es-us)
- VA super-heat flush: at least 30 minutes at every outlet. GUIDANCE-DOC. [READ] — [VHA 1061](https://nj.gov/health/cd/documents/topics/Legionnaires'/prevention-legionella-potablewater.pdf)
- Tool costs (all VENDOR listings, prices vary and date unknown): HOBO pipe sensor $69–$96; TidbiT $170–$185; Fluke 80PK pipe clamps about $240–$343; Fluke 54-2 B about $520; Fluke 1524 about $1,700–$2,900; gas manometer (UEI EM200 / TPI 620, per Lochinvar). [SNIPPET] — [Onset](https://www.onsetcomp.com/products/sensors/sd-temp-p-06); [Fluke](https://flukecal.com/en-us/product/accessories/probes/fluke-80pk-10); [TEquipment](https://www.tequipment.net/HOBO-by-Onset/series_hobo-logger-series)

### Inferences (ANALYST)
- The "Time (est.)" column in section 2 is my estimate. It should be treated as a prior to be replaced by technician-supplied durations from the pilot, not as a sourced value.

### Gaps
- No manufacturer or practitioner source for the time to perform: mixing valve shutdown test, balancing a riser, expansion tank check, or pump curve check. No logger duration guidance for DHW.

---

## 5. Which checks are destructive or risky, and the stated safeguards

### Takeaway
Sourced safety content is thin and mostly about scald. The sourced safeguards: mixing-valve annual testing by licensed staff, caution about scald during any thermal remediation, power-off before pump-impeller checks, and isolating the tank before precharge. Lockout, hot work and confined-space classes in the catalogue are my classification, not sourced.

### Cited Findings
- VA warns of significant scald risk during super-heat-and-flush (160–170°F) and states mixing valves must be considered; it positions this as emergency remediation only. GUIDANCE-DOC. [READ] — [VHA 1061](https://nj.gov/health/cd/documents/topics/Legionnaires'/prevention-legionella-potablewater.pdf). Contrast: CDC says thermal remediation is not recommended. [READ] — [CDC](https://www.cdc.gov/control-legionella/media/pdfs/Control-Toolkit-Potable-Water.pdf)
- Burn times at 140°F: about 5 s to permanent burn (CPSC chart). GUIDANCE-DOC. [FETCHED-SUMMARY] — [A.O. Smith Bulletin 34](https://www.hotwater.com/info-center/technical-bulletins/bulletin-34.html)
- Powers manuals: master valve maintenance by a licensed contractor; unauthorized adjustment can disable the valve. MANUFACTURER. [SNIPPET] — [Powers manuals](https://www.manualsdir.com/manuals/592983/powers-sh1430-hi_lo-master-tempering-valves-lfsh1430-hi_lo-master-tempering-valves.html)
- Crossover test: turn off power to an electric heater, set a gas heater to pilot, then shut the cold supply. TRADE/FORUM. [FETCHED-SUMMARY] — [Water Heater Rescue](https://www.waterheaterrescue.com/troubleshooting/tanklets/cross-connections.html)
- Expansion tank: isolate and drain before checking precharge; do not recharge a tank that shows water at the valve. FORUM-ANECDOTE. [SNIPPET] — [Steve Jenkins](https://www.stevejenkins.com/blog/2013/12/testing-and-replacing-a-hot-water-expansion-tank/)
- Pump impeller spin check: disconnect power first. FORUM-ANECDOTE. [SNIPPET] — [HeatingHelp](https://forum.heatinghelp.com/discussion/comment/1836311/)
- Caleffi: do not set above 120°F if anti-scald valves are not installed at the fixtures. MANUFACTURER. [READ] — [Caleffi 1164](https://s3.amazonaws.com/s3.supplyhouse.com/product_files/Caleffi-116441AC-UserGuide.pdf)
- Raising the heater or TMV setpoint to fix a wait-time complaint is a known operator behavior that creates scald risk. TRADE-PRESS. [FETCHED-SUMMARY] — [PHCP Pros Part 4](https://www.phcppros.com/articles/19045-commissioning-and-troubleshooting-dhw-systems-part-4)

### Inferences (ANALYST; not sourced)
Proposed safety classes for the catalogue:
- **Scald:** C1–C6, C10, C14, C16, C17, C22 (any draw or drain of water above 120°F).
- **Isolation/lockout:** C4, C10, C18, C12 (isolating valves, shutting cold supply to heater, closing riser stops). This also includes loss of service to occupants, so schedule it.
- **Electrical (pumps, heaters, trim tank):** C7, C9, C20.
- **Pressure:** C8, C13, C15, C18. Opening drains under pressure.
- **Gas/combustion:** C19.
- **Legionella aerosol:** any flush or draw of tepid water at showers or high-pressure drains (C2 drain sample, C14 flush, C16 at showers), per CDC's concern about aerosol exposure. This is a classification; CDC and VA do not name specific field checks.
- **Working at height / confined space / hot work:** roof HPWH or equipment access, riser shafts, and soldered repairs. No sourced procedures were found.
- The least invasive checks (C1, C5, C6 with clamps, C9, C21, C22) can be done without isolating or draining anything; the model could prefer them first.

### Gaps
- No OSHA or manufacturer lockout/tagout document specific to DHW checks was retrieved. No incident data on scald injuries during diagnostics.

---

## 6. Which checks can be done remotely or from BAS data vs only physically

### Takeaway
Only temperature and pump-status checks are credibly remote, and only where sensors exist. Everything that requires moving valves, reading local gauges, or fixtures must be physical. VA 1061 prescribes continuous monitoring at source discharge, source return, and loop returns, which defines the minimum sensor set a building covered by it should have.

### Cited Findings
- VA: temperature in hot and cold systems "needs to be monitored continuously" at source discharge, source return, loop returns, and representative outlets. GUIDANCE-DOC. [READ] — [VHA 1061](https://nj.gov/health/cd/documents/topics/Legionnaires'/prevention-legionella-potablewater.pdf)
- Control strategies visible in BAS: timer, return aquastat, demand, supply modulation. In one study the combined strategy ran the pump 14 minutes or less per day. GUIDANCE-DOC. [SNIPPET] — [NREL/ARIES](https://research-hub.nrel.gov/en/publications/control-strategies-to-reduce-the-energy-consumption-of-central-do/)
- A thermal balancing valve's dry-well accepts a remote sensor. MANUFACTURER. [READ] — [Caleffi 1164](https://s3.amazonaws.com/s3.supplyhouse.com/product_files/Caleffi-116441AC-UserGuide.pdf)
- ETCC field monitoring used measured loop losses to find excess loss. GUIDANCE-DOC. [FETCHED-SUMMARY] — [ETCC](https://www.etcc-ca.com/reports/multifamily-domestic-hot-water-recirculation-survey)

### Inferences (ANALYST)
- Remote-capable if sensors exist: C1, C3, C5, C6, C9, C20, C21. Pump status and (with a VFD or current sensor) amps for C7.
- Physical-only: C2 (except tanks with multi-point sensors), C4, C8, C10, C11 (unless remote sensors are fitted), C12, C16, C17, C18, C19 (except boiler gas-train controllers that report pressure).
- Logger deployment (C22) converts a physical-only check into a time series; the clip-on logger therefore substitutes for missing BAS points at about $70–$200 per point plus labor.
- Fault patterns (ANALYST): a BAS trend can distinguish "pump or control" problems from "balancing or crossover" problems, because the former shows pump status or return anomalies at the plant while the latter often shows normal plant data but cool distal risers. This is a hypothesis for the model, not a sourced result.

### Gaps
- No source quantifying how many commercial buildings have DHW return sensors in BAS. No study of BAS-based DHW fault detection accuracy was retrieved.

---

## Source quality summary
- Strongest, read in full: VHA Directive 1061 (2014); CDC toolkit PDF; ASHRAE G12 Addendum b; Caleffi 1164 data sheet; Armstrong balancing article; Watts ASSE comparison chart (2009); Deppmann/B&G blog.
- Medium, fetched summaries only: PHCP Pros articles (Hiller, Part 4 commissioning, thermostatically balanced systems); A.O. Smith/State Bulletin 34; Plumber Magazine mixing valve tips; ETCC summary; Water Heater Rescue.
- Weakest: forum posts (HeatingHelp, Plumbers Forums), residential blogs, vendor price listings, and search-summary-only items.
- Key conflicts to surface to the report writer: (1) 120°F vs 124°F vs 120–130°F circulating-water floor, and whether 124°F is in G12; (2) thermal disinfection: CDC "not recommended" vs VA "emergency super-heat"; (3) design ΔT 5°F vs 10°F; (4) heater minimum outlet 130°F (VA, exchangers) vs 140°F (G12 per Hiller).
