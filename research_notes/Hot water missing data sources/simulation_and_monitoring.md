# Open, commercially-usable simulation tools and monitoring datasets for central DHW recirculation systems

Not legal advice. Research date: 2026-10-07. Method: license files and repository/record pages were opened where reachable. Several PDFs (Eawag WaterHub paper, Polytechnique thesis full text, LBNL-4830E, Hatam 2024) came back as unreadable binary, so only their abstracts or catalogue pages were used. "UNVERIFIED" marks claims that rest on a search-engine snippet or secondary summary and not on an opened primary page.

## Ranked inventory

Ranking = usefulness for building a DHW recirculation fault simulator and calibrating a diagnostic model, after the commercial-use screen.

| # | Item | URL | License (as found) | Commercial-OK verdict | What it provides | Effort |
|---|------|-----|--------------------|-----------------------|------------------|--------|
| 1 | SINTEF Norway DHW dataset (12 buildings incl. 4 apartment buildings) | https://data.mendeley.com/datasets/m3xy22pf4j/2 | CC BY 4.0 (dataset page and Data in Brief article) | YES (attribution) | Real measured hot-water distribution temp, circulation-return temp, circulation return flow, circulation heat-loss power, consumed flow; 2 s and hourly CSVs; documents faulty non-return valves | Low-medium (CSV; plant-room measurements only, no riser data) |
| 2 | Modelica Buildings Library (LBNL) | https://github.com/lbl-srg/modelica-buildings | 3-clause BSD plus an added "enhancements" clause | YES (read the grant-back clause) | Stratified tank, PlugFlowPipe/Pipe with heat loss, CheckValve with leakage, 3-way valves, pumps, junctions | Medium-high (build the DHW loop yourself; no ready DHW example found) |
| 3 | NREL/Building America Forbell Street central DHW dataset (OpenEI 4762) | https://data.openei.org/submissions/4762 | CC BY 4.0 (OpenEI page) | YES (attribution) | Two multifamily buildings, recirc controls vs constant recirc; two .xlsx files (~20 MB, ~16 MB) | Medium (channel contents UNVERIFIED; files not opened) |
| 4 | WNTR (Sandia) / EPANET | https://github.com/sandialabs/WNTR | Revised BSD (WNTR); MIT (bundled EPANET) | YES | Hydraulic/water-age network solver in Python; no thermal model in core | Medium-high for temperature (needs EPANET-MSX or custom code) |
| 5 | EnergyPlus | https://github.com/NREL/EnergyPlus | "BSD-3-like" with product-naming clause | YES (naming clause) | WaterHeater (mixed/stratified), WaterUse:Equipment/Connections, plant loops, pipes. Recirc pump not modeled as a distinct flow (community report) | High for faults; weak recirc physics |
| 6 | IDEAS (KU Leuven) | https://github.com/open-ideas/IDEAS | BSD-3 | YES | Modelica building/district library; DHW content not confirmed | Medium-high |
| 7 | AixLib (RWTH EBC) | https://github.com/RWTH-EBC/AixLib | 3-clause BSD | YES | Modelica building library; DHW content not confirmed | Medium-high |
| 8 | TRANSFORM (ORNL) | https://github.com/ORNL-Modelica/TRANSFORM-Library | Apache-2.0 | YES | General thermal-hydraulic Modelica library; Dymola required per README | High |
| 9 | OpenStudio / OpenStudio-HPXML | https://github.com/NREL/OpenStudio, https://github.com/NREL/OpenStudio-HPXML | BSD-style with OpenStudio trademark clause | YES (naming) | Per-dwelling model with Hot Water Distribution "Recirculation" option; residential scale | Medium; not a central-plant fault tool |
| 10 | ResStock / ComStock software and EULP data | https://registry.opendata.aws/nrel-pds-building-stock/ | Software: BSD-style (trademark clause). Data: registry lists "ComStock License" and "ResStock License" (links to those software license files) | Likely YES; data license text not separately confirmed | Stock-level service-water-heating load profiles (15-min) | Low, but aggregate load only; no loop physics |
| 11 | Swedish 648-apartment DHW dataset | https://researchdata.se/en/catalogue/dataset/2025-298 | CC BY-SA 4.0 | YES with ShareAlike obligations on derived data | 1-min cumulative DHW litres per apartment, 8 buildings, 22-25 days (Feb-Mar 2021); no recirc info in README | Low; draw-profile calibration only |
| 12 | Carleton/Québec 12 annual draw profiles | https://carleton.ca/sbes/publications/hot-water-demand-profiles-downloadable/ | No formal license; "only ask that you cite" the paper | Probably OK but ambiguous (no license text); get written confirmation | 5-min draw profiles from 73 Québec houses | Low; single-family |
| 13 | WaterHub Modelica package | https://github.com/modelica-3rdparty/WaterHub | GPL-3.0 | CAUTION (copyleft) | Household water-system Modelica blocks; "still under construction" | Not recommended for a proprietary product |
| 14 | DHWcalc (Univ. Kassel) | https://www.uni-kassel.de/maschinenbau/en/institute/thermische-energietechnik/fachgebiete/solar-und-anlagentechnik/downloads | No license found (free download) | UNCLEAR; ask authors | Stochastic DHW draw-profile generator | Low if cleared |
| 15 | BDG2 | https://github.com/buds-lab/building-data-genome-project-2 | CC BY-SA 4.0 (LICENSE file) | YES with ShareAlike | 3,053 meters, 1,636 buildings; no DHW meter evident | Not useful for DHW |
| 16 | Mortar (code / data) | https://github.com/gtfierro/mortar, https://huggingface.co/datasets/gtfierro/mortar | Code BSD-3-Clause; dataset card states no license | Code OK; dataset UNCLEAR | Brick models + HVAC time series; no confirmed hot-water points | Not useful for DHW |
| 17 | Boppe et al. 2016 hospital hot water study | https://publications.polymtl.ca/4798/ | CC BY-NC-ND (per search summary, UNVERIFIED) | NO | Continuous temperature and flow monitoring of a hospital HWDS | Exclude |
| 18 | Larouche 2016 thesis (DHW/solar FDD, TRNSYS) | https://publications.polymtl.ca/2092/ | "Tous droits réservés" | Method reference only; do not reuse text/data | Two-level rule-check + simulation FDD concept | Reference only |

Not usable commercially or not confirmed: TRNSYS (proprietary, not assessed here), ETCC/CEC/PG&E reports (see below), vendor data.

---

## Key question 1: Which simulators can model a recirculation loop (heater, storage, mixing valve, pump, risers, heat loss, check valves, draws), how hard is fault injection, and do any DHW FDD studies use them?

### Takeaway
The Modelica Buildings Library (BSD-3) has the individual physical components needed (stratified tank, heat-losing pipes, check valve with leakage, 3-way valves, pumps, junctions), but no ready-made DHW recirculation example or thermostatic mixing valve was found, so you would assemble it yourself; most faults are parameter or signal overrides in such a model. EnergyPlus has fixture draws and water heaters but is documented by community sources as weak at modelling the recirculation flow itself. No published simulation-based FDD study of a central DHW recirculation loop was found.

### Cited Findings
- The Modelica Buildings Library is "available under a 3-clause BSD-license" (README); its legal.html is the Modelica Buildings Library License, a revised 3-clause BSD with copyright by the Modelica Association, IBPSA and UC/LBNL — [GitHub README](https://github.com/lbl-srg/modelica-buildings), [legal.html](https://raw.githubusercontent.com/lbl-srg/modelica-buildings/master/Buildings/legal.html)
- Added clause in that license: no obligation to provide fixes, and if you "publicly release enhancements, or provide them to Lawrence Berkeley National Laboratory without a separate written license" you grant a non-exclusive, royalty-free, perpetual license to use, modify, distribute and sublicense them (paraphrased from the fetch) — [legal.html](https://raw.githubusercontent.com/lbl-srg/modelica-buildings/master/Buildings/legal.html). Practical reading: keep fault-injection extensions private, or accept the grant-back if published.
- `Buildings.Fluid.Storage` contains `Stratified` (default 2 segments), `StratifiedEnhanced` (4+ segments) and `StratifiedEnhancedInternalHex` — [Buildings.Fluid.Storage docs](https://simulationresearch.lbl.gov/modelica/releases/latest/help/Buildings_Fluid_Storage.html)
- `Buildings.Fluid.FixedResistances` contains `CheckValve` ("small reverse flows can still occur"; leakage ratio `l` sets closed-state flow), `Pipe` (finite-volume with optional heat loss), `PlugFlowPipe` / `PlugFlowPipeDiscretized` (transport delay plus wall inertia; "suited to long pipes such as district heating and cooling"), `Junction`, `PressureDrop`, `HydraulicDiameter` — [Buildings.Fluid.FixedResistances docs](https://simulationresearch.lbl.gov/modelica/releases/latest/help/Buildings_Fluid_FixedResistances.html)
- PlugFlowPipe heat-loss model assumptions: uniform cross-section temperature, no axial conduction, steady-state loss, losses only in design flow direction (relevant to reverse-flow/crossover faults) — [v6.0.0 docs via search result](https://simulationresearch.lbl.gov/modelica/releases/v6.0.0/help/Buildings_Fluid_FixedResistances_BaseClasses.html)
- Valves available: `TwoWayLinear`, `TwoWayEqualPercentage`, `TwoWayPressureIndependent`, `ThreeWayLinear`, `ThreeWayEqualPercentageLinear`, `ThreeWayTable` and others; the package page lists no thermostatic valve model — [Buildings.Fluid.Actuators.Valves docs](https://simulationresearch.lbl.gov/modelica/releases/latest/help/Buildings_Fluid_Actuators_Valves.html)
- The library also has `Buildings.Experimental.DHC.Loads` with models for thermal and domestic hot water demand prediction — [search result](https://simulationresearch.lbl.gov/modelica/releases/v8.1.2/help/Buildings_Experimental_DHC_Loads.html) (contents not opened)
- IDEAS is "licensed by KU Leuven and 3E under a BSD 3 license"; AixLib is under a "3-clause BSD-license"; TRANSFORM is Apache-2.0 and the README says Dymola is required — [IDEAS](https://github.com/open-ideas/IDEAS), [AixLib](https://github.com/RWTH-EBC/AixLib), [TRANSFORM](https://github.com/ORNL-Modelica/TRANSFORM-Library). None of the three pages mention DHW components (not verified deeper).
- EnergyPlus: "available under a BSD-3-like license"; LICENSE.txt allows redistribution and use with or without modification, but clause (4) bars using the EnergyPlus name in a company or product name, advertising or promotion without DOE consent; standalone redistributions must be called "EnergyPlus version X" — [GitHub](https://github.com/NREL/EnergyPlus), [LICENSE.txt](https://raw.githubusercontent.com/NREL/EnergyPlus/develop/LICENSE.txt)
- EnergyPlus WaterUse:Equipment mixes hot and cold water to a target temperature; WaterUse:Connections groups equipment and provides plant-loop connections; the I/O reference group page has no recirculation-loop content — [I/O reference 9.3](https://bigladdersoftware.com/epx/docs/9-3/input-output-reference/group-water-systems.html)
- Community (Unmethours) reports: EnergyPlus cannot model a constant-flow recirculation pump as such; workaround is adding hand-calculated pump power as water-heater parasitic load; plant loop flow equals only the drawn flow; loop heat loss only matters with non-adiabatic pipes — [Unmethours 97375](https://unmethours.com/question/97375/modeling-dhw-recirculation-loop-in-energyplus), [Unmethours 29692](https://unmethours.com/question/29692/dhw-recirculation-in-energyplus). This is community Q&A, not vendor documentation; check your target version.
- OpenStudio and OpenStudio-HPXML licenses are BSD-style with trademark clauses (no use of "OpenStudio"/"OS" for modified versions or endorsement) — [OpenStudio LICENSE](https://raw.githubusercontent.com/NREL/OpenStudio/develop/LICENSE.md), [OS-HPXML LICENSE](https://raw.githubusercontent.com/NREL/OpenStudio-HPXML/master/LICENSE.md). OS-HPXML docs list Hot Water Distribution with Standard and Recirculation options (per dwelling) — [docs](https://openstudio-hpxml.readthedocs.io/en/v0.10.0-beta/hpxml_to_openstudio.html)
- WNTR: Revised BSD (Sandia/NTESS), bundled EPANET under MIT — [LICENSE.md](https://raw.githubusercontent.com/sandialabs/WNTR/main/LICENSE.md). WNTR "includes capability to simulate water quality" but no temperature extension was found; building-plumbing temperature work used EPANET-MSX (Hatam et al. 2024, 22-showerhead system with one thermostatic mixing valve, modelled temperatures matched monitoring "overall" with some underestimation) — [Hatam 2024 PDF (abstract only readable)](https://publications.polymtl.ca/59371/1/2024_Hatam_Modeling_Temperature_Fluctuations_during_Intermittent.pdf). PPMtools is an open-source premise-plumbing tool on WNTR/EPANET (license not checked) — [search result, Burkhardt 2023](https://ascelibrary.com/doi/10.1061/JWRMD5.WRENG-5888)
- WaterHub Modelica package is GPL-3.0, "Modelica Package for the modeling of household-level water systems", docs say "still under construction" — [modelica-3rdparty/WaterHub](https://github.com/modelica-3rdparty/WaterHub), [docs](https://waterhub.readthedocs.io/en/latest/). A Modelica 2019 conference paper from Eawag describes a WaterHub library plus a Python draw-profile generator ([PDF](https://www.eawag.ch/fileadmin/Domain1/Abteilungen/eng/projekte/nest/article_modelica19.pdf)); I could not read the PDF and could not confirm that the Eawag library and the GitHub repo are the same code.
- Fault-injection/FDD precedent found: a 2016 Polytechnique Montréal master's thesis proposes two-level automatic fault detection for solar DHW systems (rule checking, then daily TRNSYS simulation vs measurement), validated on ~3 years of data from one Montréal system; faults are generic (component selection, installation, maintenance), not recirculation faults, and the thesis is "all rights reserved" — [PolyPublie record](https://publications.polymtl.ca/2092/)
- A Galway/TU Munich approach builds a qualitative diagnostic model from a first-principles Modelica model with consistency-based diagnosis, tested on air-handling units, not water loops — [search result](https://researchrepository.universityofgalway.ie/server/api/core/bitstreams/9b034fb2-eb68-47db-9d29-90c0d4b7e2ce/content) (not opened)
- Recirculation fault rules appear in a patent (alerts for water too hot, too cold, pump runs without stopping, pump never runs) — [US 9195242](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9195242). Patent text is a taxonomy source only; check freedom-to-operate before copying any claimed method.
- A Czech paper proposes software on a recirculation metering system to flag failures such as leaks, tested on real data — [KTU journal](https://eejournal.ktu.lt/index.php/elt/article/view/9136) (abstract only)
- A model-based FDD/fault-tolerant control simulation for a high-rise hot-water heating system (not DHW) injected sensor, heater-efficiency and partially blocked control-valve faults — [MetaTOC listing](https://www.metatoc.com/papers/31486-fault-tolerant-control-strategies-for-a-high-rise-building-hot-water-heating-system) (abstract-level only)
- A multifamily DHW heat-pump physics model validated on three field measurements and applied to virtual buildings of 8 to 192 apartments, with an externally reheated recirculation loop performing best — [Purdue IRACC 2012](https://docs.lib.purdue.edu/iracc/1175) (software not stated; license not checked)

### Inferences
- Faults map onto Modelica parameters/inputs without new component code: closed balancing valve = raise a `PressureDrop` resistance in a riser branch; pump off = mover on/off signal; setpoint change = tank/controller parameter; mixing valve stuck = fix a 3-way valve position input; check-valve leak/crossover = raise `CheckValve` leakage `l` or add a parallel leak path. These are my inferences from the component list, not demonstrated in a paper.
- Because `PlugFlowPipe` models heat loss only in the design flow direction, reverse-flow (crossover) fault scenarios should use `Pipe` (finite volume) or be checked against that limitation.
- Because the Buildings valves package shows no thermostatic mixing valve, you will probably need a controlled 3-way valve plus a temperature controller to represent one.
- EnergyPlus is a poor first choice for loop-level recirculation faults given the community-reported limits.
- The absence of any DHW-recirculation FDD simulation paper in my searches suggests a genuine literature gap, but absence of search hits is not proof.

### Gaps
- No ready-made Modelica DHW recirculation example (tank + pipes + pump + TMV) was found; I did not browse the Buildings `Examples` packages exhaustively.
- DHW content of AixLib and IDEAS was not verified (their README pages say nothing about it).
- EnergyPlus recirculation capability is known only from community answers; the current I/O reference was not checked for newer pipe/recirc features.
- TRNSYS (proprietary), PipeFlow-type codes, Pyomo/Julia pipe thermal models, and CIBSE-free tools were not searched in depth.
- The Eawag WaterHub paper could not be read; link between it and the GPL-3.0 repo is unconfirmed.
- OS-HPXML's draw-schedule generator details and license of its schedule code were not confirmed.

---

## Key question 2: Which real measured DHW datasets exist (even small), and what are their licenses?

### Takeaway
One strong open dataset exists: SINTEF's Norwegian dataset (CC BY 4.0) with 1-2 s distribution/circulation temperatures and circulation flow for 12 buildings including 4 apartment buildings. The NREL Forbell dataset (CC BY 4.0) is a second lead but its column content is unverified. Draw-profile datasets (Swedish, Québec) exist but carry no recirculation data. Most California/NYSERDA/BPA multifamily recirculation monitoring appears in gated or copyright-unspecified reports with no confirmed raw data release.

### Cited Findings
- SINTEF dataset: 12 Norwegian buildings (4 hotels, 4 nursing homes, 4 apartment buildings in greater Oslo), measured in the heating plant for at least 6 weeks with clamp-on ultrasonic flow meters and type-T thermocouples on pipe walls, 1 s sampling averaged to 2 s — [Data in Brief via PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8220317/)
- Variables: cold-water inlet temp, hot-water distribution temp, consumed hot-water flow and power; circulation return temp (T_hwc), circulation return flow (V_hwc) and circulation heat-loss power (P_hwc) for most buildings; hourly energy in a second dataset. Return data missing for NH2; AB4 has return temperature but no return flow and its circulation data was "poor quality and high uncertainty" — [PMC8220317](https://pmc.ncbi.nlm.nih.gov/articles/PMC8220317/)
- The same article states some systems "had faulty non-return valves, which caused periods of negative flow and higher cold-water temperatures" — a real, undeliberate check-valve fault signature in measured data — [PMC8220317](https://pmc.ncbi.nlm.nih.gov/articles/PMC8220317/)
- Apartment-building layouts: AB1 (9 floors, circulation in basement only), AB2 (renovated, circulation branches in every shaft), AB3 (4 floors, basement-only circulation), AB4 (old small tubes) — [PMC8220317](https://pmc.ncbi.nlm.nih.gov/articles/PMC8220317/)
- Mendeley record: "CC BY 4.0", DOI 10.17632/m3xy22pf4j.2, version 2 published 5 April 2024, authors Walnum and Sørensen (SINTEF) — [Mendeley Data](https://data.mendeley.com/datasets/m3xy22pf4j/2). Timestamps CET with DST; flow data unfiltered and noisy (per article).
- NREL Forbell dataset: "Control Strategies to Reduce the Energy Consumption of Central Domestic Hot Water Systems", DOI 10.25984/2204257, two .xlsx files (1101 Forbell ~19.5 MB, 922 Forbell ~15.8 MB), license linked to CC BY 4.0; site footer says "Content is available under Creative Commons Attribution 4.0 unless otherwise noted" — [OpenEI 4762](https://data.openei.org/submissions/4762)
- Forbell study findings: DHW fuel use fell 7% (demand control), 2% (temperature modulation), 15% (both); pump runtime cut to 14 minutes or less per day; compared against constant recirculation — [OSTI 1263778](https://www.osti.gov/biblio/1263778). The report's sensor list and logging interval could not be fetched (host errors), and the xlsx files were not downloaded (download requires user permission).
- Swedish dataset: 648 apartments in 8 multifamily buildings, cumulative DHW litres at 1-min resolution (jet turbine meters, linear-interpolated), Feb-Mar 2021, 22-25 days per building, public access, CC BY-SA 4.0, DOI 10.58062/zg8w-gp13; README does not mention recirculation — [researchdata.se](https://researchdata.se/en/catalogue/dataset/2025-298), [README](https://hh.open.care.snd.se/downloads/public/2025-298/1/documentation/README.txt)
- Québec draw profiles: 12 annual profiles at 5-min resolution from 73 houses; terms: "We only ask that you cite the above-mentioned paper" (Edwards, Beausoleil-Morrison, Laperrière, Solar Energy 111, 2015, DOI 10.1016/j.solener.2014.10.026) — [Carleton](https://carleton.ca/sbes/publications/hot-water-demand-profiles-downloadable/)
- LBNL-4830E compiles hot-water draw data from 10 studies (recording interval 1 min or less; single-family units) — [search result summary](https://eta-publications.lbl.gov/sites/default/files/hot_water_draw_patterns_in_single-family_houses_findings_from_field_studies_lbnl-4830e.pdf); PDF unreadable here, download/licensing of the underlying data not confirmed.
- ComStock/ResStock data on AWS: license shown as "ComStock License" and "ResStock License" linking to the software license files; ComStock and ResStock LICENSE files are BSD-style with name/trademark restrictions — [AWS registry](https://registry.opendata.aws/nrel-pds-building-stock/), [ResStock LICENSE](https://raw.githubusercontent.com/NREL/resstock/develop/LICENSE.md), [ComStock LICENSE](https://raw.githubusercontent.com/NREL/ComStock/main/LICENSE.txt). The registry page does not itself mention water heating; load profiles are 15-min and cover "all major ... end uses" (water heating is a named end use per NREL planning slides in [search results](https://www.nrel.gov/docs/fy21osti/79099.pdf), not opened). Your suggestion that these are CC BY 4.0 was not confirmed on the AWS page; OpenEI mirrors state CC BY 4.0 by default.
- BDG2: LICENSE file is Creative Commons Attribution-ShareAlike 4.0; 3,053 meters, 1,636 buildings; listed meter types are electricity, heating and cooling water, steam, irrigation; no DHW meter mentioned — [GitHub](https://github.com/buds-lab/building-data-genome-project-2), [LICENSE](https://raw.githubusercontent.com/buds-lab/building-data-genome-project-2/master/LICENSE)
- Mortar: dataset card describes anonymized Brick models and time series, mostly 15-minute, with no license field and no confirmed hot-water points; the mortar GitHub repo is BSD-3-Clause — [HF card](https://huggingface.co/datasets/gtfierro/mortar), [GitHub](https://github.com/gtfierro/mortar)
- Innsbruck dataset (district-heated multifamily house, CC BY 4.0) covers space heating and DHW consumption profiles for a Polysun model; recirculation not mentioned — [researchdata.uibk.ac.at](https://researchdata.uibk.ac.at/records/9g2w6-dkb15)
- California ETCC "Multifamily Domestic Hot Water Recirculation Survey" (ET24SWE0061): recirculation loss 24.1-99.9 W per apartment (average 62.5), field losses 1.1-2.3x idealized calculations; PDF gated behind a form and terms; no license or raw-data statement — [ETCC](https://www.etcc-ca.com/reports/multifamily-domestic-hot-water-recirculation-survey)
- UC Davis West Village central HPWH (10.5-ton, 16 months monitored, annual COP 2.12, used to validate a TRNSYS model): OSTI technical report, no license or raw-data statement on the page — [OSTI 1358064](https://www.osti.gov/biblio/1358064)
- A 2022 MDPI Sustainability paper (Ecotope authors) measured a CO2 HPWH swing-tank retrofit in a 60-unit multifamily building, aimed at recirculation loop temperature maintenance — [MDPI 14/13/8048](https://www.mdpi.com/2071-1050/14/13/8048) (403 on fetch; only search-snippet level, UNVERIFIED; MDPI is typically CC BY but not confirmed here)
- Hospital studies: Boppe et al. 2016 (10-storey hospital, continuous temperature and flow monitoring of the hot water distribution loops) is "CC BY-NC-ND" per search summary (UNVERIFIED) — [PolyPublie 4798](https://publications.polymtl.ca/4798/); Bédard et al. 2015 monitored temperature and heat loss at control points in five healthcare facilities, with only some systems having continuous series — [INRS repository](https://espace.inrs.ca/id/eprint/3147/)
- A U.S. EPA dataset on Legionella and temperature in bathroom samples is on data.gov under the EPA ScienceHub license (sampling data, not loop time series) — [catalog.data.gov](https://catalog.data.gov/dataset/annual-variations-and-effects-of-temperature-on-legionella-spp-and-other-potential-opportu)
- Brick: the core Brick schema repo is described as BSD-licensed; no hot-water/recirculation example model was found — [search result](https://github.com/BrickSchema/brick-example-server)

### Inferences
- For calibrating a simulator's healthy-vs-faulty temperature behavior, the SINTEF dataset is the only confirmed open source with circulation return temperature and flow at second-level resolution under a clearly commercial-compatible license. It covers plant-room measurements only, so riser/branch temperatures are not available.
- The Forbell workbooks are an open, CC BY lead for loop behavior under different control strategies, but whether they contain loop temperatures is unknown until opened; they are likely daily/aggregated "EA Analysis" workbooks given their file names (inference).
- CC BY-SA datasets (Swedish, BDG2) are not blockers for commercial use, but derived datasets or published derived models may inherit ShareAlike; a legal check is warranted before training a distributed model on them.
- The Québec profiles and DHWcalc lack formal licenses, so use needs written author confirmation before relying on them in a product.

### Gaps
- Forbell xlsx contents (columns, interval, presence of loop supply/return temps) not verified; files not downloaded.
- No open raw monitoring data was found for the California (ETCC/CEC/PG&E), NYSERDA, BPA/NEEA/Ecotope, or EPRI multifamily CHPWH studies; only reports. CEC final reports (e.g., CEC-500-2023-006, CEC-500-2024-054) were listed in search results but not opened for data appendices.
- No open DHW recirculation time-series was found on Zenodo, Dryad, Figshare, EDI, or data.gov beyond the above; searches were broad but search-engine limited and not repository-native, so a native search on those sites is still worth doing.
- Hospital Legionella papers' data-availability statements were not checked.
- The Ayala/Zobrist (CEC) report was not located; the search did not return it.

---

## Key question 3: Is there anything that quantifies real loop temperature distributions for healthy vs faulty systems to calibrate a simulator?

### Takeaway
Only fragments exist: the SINTEF dataset contains real measured loop-return temperatures and a documented real check-valve fault (negative flow, higher cold-water temperature), and the ETCC survey quantifies recirculation heat loss and its excess over design calculations (cold-water crossover and insulation defects). No source found gives labeled healthy-vs-faulty loop temperature distributions.

### Cited Findings
- Real fault evidence in open data: faulty non-return valves producing periods of negative flow and higher cold-water temperatures in some SINTEF buildings — [PMC8220317](https://pmc.ncbi.nlm.nih.gov/articles/PMC8220317/)
- Field-measured recirculation losses 1.1-2.3x idealized calculations; attributed mainly to insulation imperfections and cold-water crossover; no clear link to building characteristics — [ETCC](https://www.etcc-ca.com/reports/multifamily-domestic-hot-water-recirculation-survey)
- Cold-water crossover lowers returning loop temperatures and inflates distribution load — [TECH Clean CA CHPWH case study (search result)](https://techcleanca.com/documents/2279/2023_CHPWH_Case_Study_Pt_1_v230720_2.pdf) (not opened)
- Recirculation return water in a California return-to-primary demonstration is typically 105-115 F — [ETCC return-primary report (search result)](https://www.etcc-ca.com/reports/return-primary-central-hpwh-system-field-demonstration) (only snippet-level; UNVERIFIED)
- Legionella/temperature studies treat water below roughly 55 C as problematic (hot) and above 25 C as problematic (cold) in building systems — [Hatam 2024 abstract](https://publications.polymtl.ca/59371/1/2024_Hatam_Modeling_Temperature_Fluctuations_during_Intermittent.pdf)
- Pilot-scale study across set points 39-58 C found set point critical for suppressing L. pneumophila in continuously recirculating lines and at distal taps — [PMC4666224](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4666224/) (search snippet only)
- A hospital longitudinal study reports that sanitary hot water at 55 C minimum was significantly better than 50 C only where systems are suitably sized and have recirculation — search summary (study not identified; UNVERIFIED)

### Inferences
- The SINTEF CSVs could be mined to extract the distribution of T_hwc minus T_hw (loop temperature drop) and its relation to circulation flow, giving a healthy baseline and a check-valve-fault example for tuning a simulator.
- ETCC's 62.5 W/apartment mean and 24-100 W range can be used as a plausibility band for simulated healthy-loop heat loss, but it is a report-level statistic from California only, and the underlying data is not released.

### Gaps
- No labeled fault vs healthy time series was found anywhere in open sources.
- No quantified distribution of riser/branch return temperatures (per-riser) from real systems was found.
- Balancing-valve and mixing-valve fault signatures in measured data were not located.
- Full details of the ETCC report (site count, sensors) are behind a gated download.

---

## Still missing
- A published, open DHW recirculation simulator model (tank + loop + risers + TMV + check valves) with validation data.
- Any simulation-based FDD paper specifically for central DHW recirculation loops.
- Open raw monitoring data from California, NYSERDA, BPA/NEEA, Ecotope, and EPRI multifamily central HPWH studies.
- Per-riser temperature data for a multi-riser system.
- Formal license for DHWcalc, the Québec draw profiles, and the Eawag WaterHub library; the dataset license for ComStock/ResStock EULP as distinct from the software license.
- Brick/Haystack/BuildingSync sample models for DHW recirculation systems.
- Direct inspection of Forbell xlsx columns (needs user permission to download).
