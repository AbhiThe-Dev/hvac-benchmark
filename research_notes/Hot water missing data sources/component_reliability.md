# Open / public-domain, commercially usable reliability data for central domestic hot water (DHW) components

Compiled 2026-10-07. Not legal advice. Licence verdicts are my reading of what each page or PDF showed; none were confirmed with the rights holder.

**How to read the grades and verdicts**
- Grades: GOVT-PUBLIC-DOMAIN, PEER-REVIEWED-OA, INDUSTRY-REPORT, VENDOR-CLAIM, SNIPPET-ONLY.
- SNIPPET-ONLY means I did not open the primary document, or could not read the relevant table. I only saw a search summary. Treat these as leads, not citable facts.
- Verdicts: YES, YES-WITH-ATTRIBUTION, NO, UNCLEAR.
- A "YES" for a US federal report assumes it is a pure federal work. Contractor-authored DOE/PNNL/INL/ORNL reports are normally released for public use, but check each one for a third-party copyright notice.
- Numbers (facts) are generally not copyrightable. Tables, figures and prose are. "NO" below means "do not copy the table or text". It does not mean you cannot cite a single figure with attribution.

---

## 1. Ranked source list (best first) with licence verdicts

Ranking weighs relevance to DHW, whether I read the primary document, whether the number is a measurement or an assumption, and licence clarity.

| Rank | Source | What it gives | Grade | Commercial use |
|---|---|---|---|---|
| 1 | [PNNL-22921, Widder & Baechler 2013, "Impacts of Water Quality on Residential Water Heating Equipment" (CEC docket copy)](https://efiling.energy.ca.gov/GetDocument.aspx?tn=74366) | Only open document I found that reproduces a failure-mode split for tank water heaters (IBHS 2007, 700 claims). Also the water-quality (hardness, softened water, anode) effects on life. | GOVT-PUBLIC-DOMAIN (a DOE lab report that restates an INDUSTRY-REPORT) | YES. Cite PNNL, and credit IBHS as the underlying study. |
| 2 | [DOE final rule, Commercial Water Heating Equipment, 88 FR 69686 (6 Oct 2023), sections IV.F.5-6](https://www.govinfo.gov/content/pkg/FR-2023-10-06/html/2023-20392.htm) | Commercial lifetimes, repair-rate assumptions per subsystem, heat-exchanger failure assumptions. These are modelling inputs, not measurements. | GOVT-PUBLIC-DOMAIN | YES |
| 3 | [INL/EXT-21-65055, "Industry-Average Performance for Components and Initiating Events at U.S. Commercial Nuclear Power Plants: 2020 Update"](https://nrcoe.inl.gov/publicdocs/AvgPerf/AvgPara2020.pdf) | Real event-count-based failure rates (per hour, per demand) for check valves, motor-driven pumps, strainers/filters, heat exchangers, relief valves. Nuclear-plant population, 2006-2020. | GOVT-PUBLIC-DOMAIN | YES, but transfer is a large stretch (see section 4) |
| 4 | [NBSIR 78-1460, Sushinsky 1978, "The Degradation of Gas-Fired Water Heaters" (NIST/NBS)](https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nbsir78-1460.pdf) | Failure mechanism (corrosion-induced tank leak), life range, anode state, water-composition effects. Small specimen set, 1978. | GOVT-PUBLIC-DOMAIN | YES |
| 5 | [CDC MMWR 65(22), 2016, "Deficiencies in Environmental Control Identified in Outbreaks of Legionnaires' Disease"](https://www.cdc.gov/mmwr/volumes/65/wr/mm6522e1.htm) | Share of outbreak investigations with equipment failure vs process failure vs human error. Specific mentions of water-heater setpoint/actual-temperature mismatch and mixing-valve placement. | GOVT-PUBLIC-DOMAIN | YES. The page I opened carries no explicit public-domain statement. CDC authorship implies it. |
| 6 | [Hartley, McCarthy & Greenwood 2011, Eplasty 11:e49, hospital hot-water outlet audit (PMC3236657)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3236657) | Only open field audit I found where mixing valves were found faulty or mis-set. No denominator. | PEER-REVIEWED-OA | YES-WITH-ATTRIBUTION. CC BY per the Europe PMC full-text record (the CC BY 2.0 link). |
| 7 | [Mui, Wong & Hui 2012, Bldg Serv Eng Res Technol 33(2):181-190 (PolyU record)](https://research.polyu.edu.hk/en/publications/downtime-of-in-use-water-pump-installations-for-high-rise-residen/) | Measured pump-installation MTTF and failure counts, 46 Hong Kong high-rise residential buildings, 2005-2007. | PEER-REVIEWED (repository record shows an accepted manuscript; no open licence seen) | UNCLEAR. Journal is SAGE. Cite the numbers with attribution; do not copy text or figures. |
| 8 | [Robison, Cohan & True 1996, ACEEE Summer Study, "Measure Lifetime Derived from a Field Study of Age at Replacement"](https://www.aceee.org/files/proceedings/1996/data/papers/SS96_Panel3_Paper16.pdf) | Only open field-derived median age at replacement for tank water heaters (n=164 electric, n=39 gas). | INDUSTRY-REPORT (conference paper) | UNCLEAR. ACEEE proceedings. Numbers can be cited with attribution. |
| 9 | [ASHRAE Handbook (Applications) 2019, ch. 38, Tables 3-4, as shown on handbook.ashrae.org](https://handbook.ashrae.org/Handbooks/A19/IP/a19_ch38/a19_ch38_ip.aspx) | Median service life with sample counts (TRP-1237 / Abramson 2005 data) plus the older Akalin 1978 table. | INDUSTRY-REPORT | UNCLEAR / likely NO for reproducing the tables. ASHRAE copyright. Short attributed citations of individual figures are common practice. Ask ASHRAE for permission if you ship the table. |
| 10 | [NAHB / Bank of America Home Equity, "Study of Life Expectancy of Home Components" (Feb 2007; PDF hosted by NSF)](https://standards.nsf.org/higherlogic/ws/public/download/348/NAHB%202007%20StudyUseful%20Life%20of%20Home%20Components.pdf) | Expert-survey life expectancies (residential). | INDUSTRY-REPORT | UNCLEAR. NAHB copyright. The document says it is "a general guideline only". No licence text seen. |
| 11 | [ASHRAE Equipment Life Expectancy chart, as hosted by Shipley Energy (a 2012 Word file)](https://www.shipleyenergy.com/wp-content/uploads/2025/09/ASHRAE_Chart_HVAC_Life_Expectancy.pdf) | The widely circulated Akalin 1978 medians (boilers, burners, pumps, controls, actuators, shell-and-tube HX). | INDUSTRY-REPORT, third-party copy | NO to redistribute the copy. The numbers are the 1978 values that ASHRAE itself calls outdated (see item 9). |
| 12 | [DOE/NREL "Commercial Building Hot Water Strategies: A Short Guide"](https://betterbuildingssolutioncenter.energy.gov/sites/default/files/attachments/Hot%20Water%20Strategies%20Guide.pdf) | One sentence: median gas-fired boiler life 24-35 years, citing the ASHRAE chart. Adds no new data. | GOVT-PUBLIC-DOMAIN | YES |
| 13 | [FEMP O&M Best Practices Guide (WBDG copy)](https://www.wbdg.org/FFC/DOE/DOECRIT/femp_omguide.pdf) | I downloaded and searched the full text. It has the bathtub-curve concept and steam-trap failure percentages (15-60% failed open without a programme). It has no failure rates or service-life figures for water heaters, DHW pumps, mixing valves or check valves. | GOVT-PUBLIC-DOMAIN | YES. Useful as a negative finding. |
| 14 | [Rada Controls technical bulletin Ref 288 (dated 10/03/2026 as printed), high-chloramine supplies](https://www.radacontrols.com/media/etnkvrl2/mandatory-procedure-for-rada-mixers-in-high-chlorine-water-supplies-final-update.pdf) | Manufacturer statements on TMV seal/cartridge degradation and test intervals. No field failure statistics. | VENDOR-CLAIM | NO |
| 15 | [ETCC "Multifamily DHW Recirculation Survey" (2026)](https://www.etcc-ca.com/reports/multifamily-domestic-hot-water-recirculation-survey) | Recirculation heat-loss numbers only. It reports no component failure data on the landing page (I did not see the PDF). | INDUSTRY-REPORT | NO ("All rights reserved", download gated by terms) |
| 16 | Quanterion NPRD-2016 / EPRD / FMD; DNV OREDA; IEEE 493 | Largest generic mechanical failure-rate databases. Proprietary. [Quanterion NPRD-2016](https://www.quanterion.com/quanterion-announces-the-2016-edition-of-the-nonelectronic-parts-reliability-data-publication-nprd-2016/) was listed at $850. [OREDA handbook](https://oreda.com/handbook) was listed at NOK 4,000 per volume. I did not open IEEE 493. | (proprietary) | NO |

---

## 2. Component table: every usable number found

**Column notes.** "Type" says what the number measures:
- **SHARE** = share of failures or claims by mode.
- **RATE** = failures per unit-time or per demand.
- **LIFE** = age at retirement or replacement.
- **ASSUMPTION** = a modelling input, not an observation.

Geography is US unless stated.

### 2a. Tank water heaters (residential, and commercial where stated)

| Component / mode | Number | Type | Definition of "failure" and sample | Geography / building | Source | Grade | Commercial use |
|---|---|---|---|---|---|---|---|
| Tank leak or burst | **69%** of water-heater water-loss claims | SHARE | Homeowners' insurance claims with water damage; n=700. | US homes | [PNNL-22921 s.2.2.3, Fig 2.7, citing IBHS 2007](https://efiling.energy.ca.gov/GetDocument.aspx?tn=74366) | GOVT-PUBLIC-DOMAIN (secondary) | YES, attribute IBHS |
| Unknown / supply line / valve malfunction / other | **13% / 10% / 7% / 1%** | SHARE | Same 700 claims. The chart's legend order is "Leak or burst, Unknown, Supply line, Valve malfunction, Other" and the values read 69/13/10/7/1. I matched the two by order; the figure text was not labelled per value. | same | same | same | same |
| Age at failure (claims) | mean **10.7 years**, range 1-30; average cost $4,444 per incident after deductible | LIFE | Same claims. | same | same | same | same |
| Median age at replacement | **Electric 14.3 yr (n=164); gas 12.6 yr (n=39)** | LIFE | Plumbers logged serial numbers of units being removed over about 4 weeks (305 logged, 203 usable). Age from serial-number date codes, weighted for stock growth, logistic fit. Includes 7 of 164 electrics replaced before total failure. Confidence limits printed in the paper were garbled in my text extraction. | Portland General Electric territory, Oregon | [Robison et al. 1996](https://www.aceee.org/files/proceedings/1996/data/papers/SS96_Panel3_Paper16.pdf) | INDUSTRY-REPORT | UNCLEAR (cite with attribution) |
| Typical operating life | "approximately **8 to 10 years**"; range "<3 to >20 years"; "the primary normal failure mode is a corrosion induced leak" | LIFE + mode | Cited from a secondary reference in the report. The NBS report itself tested about 10 specimens, mostly used, from scale-prone cities. | US gas-fired residential | [NBSIR 78-1460 s.7.1](https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nbsir78-1460.pdf) | GOVT-PUBLIC-DOMAIN | YES |
| Anode state | "Most anodes in the water heaters tested were completely disintegrated." | observation | Used specimens, qualitative. | same | same | same | YES |
| Corrosion vs temperature | Corrosion rate doubles for each 11 C rise over 49-82 C | mechanism | From a reference cited in NBS; no study sample. | same | same | same | YES |
| Life vs dissolved solids | NBS Fig. 6, "Water Heater Life as a Function of the TDS Level". The curve is a figure in a scanned PDF; I could not read values. | LIFE | Not extracted. | same | same | same | YES (needs manual digitising) |
| Average lifetime used by DOE | **Commercial gas storage 10 yr; residential-duty gas storage 12 yr; tankless 17 yr; circulating water heaters and hot-water supply boilers 25 yr.** Consumer gas water heaters 14.5 yr and consumer boilers 26.6 yr. | LIFE (ASSUMPTION built from literature review) | DOE used lifetime distributions, with weighted averages. AHRI, Bradford White and PHCC said the commercial values are too long. | US commercial | [88 FR 69686, Table IV.21 and IV.F.6](https://www.govinfo.gov/content/pkg/FR-2023-10-06/html/2023-20392.htm) | GOVT-PUBLIC-DOMAIN | YES |
| Combustion-system repair rate | **0.5% per year** | RATE (ASSUMPTION) | "Assumed typical failure rate" for key CWH subsystem. Probability of repair applies through life; only one major repair considered. | US commercial gas | same | same | YES |
| Controls repair rate | **1% per year**; **2% per year** for high-efficiency controls on condensing units | RATE (ASSUMPTION) | same | same | same | same | YES |
| Heat exchanger (commercial gas circulating water heaters / hot-water supply boilers) | Up to **50%** of condensing HX replaced, mean failure year 15; **17%** of non-condensing HX replaced, mean failure year 20 | SHARE + LIFE (ASSUMPTION) | Taken from a 1994 Gas Research Institute report on residential furnaces/boilers (GRI-94/0175). DOE says it found no better source. | same | same | same | YES. Weak, boiler-derived, 30 years old. |
| Median service life, electric potable hot-water heaters | **>21 yr** (n=304 units, 36 replaced) | LIFE (right-censored median) | ASHRAE TRP-1237 database, seeded with 163 commercial office buildings. ">" because most units had not yet been replaced. | US commercial offices | [ASHRAE Handbook A19 ch. 38, Table 3](https://handbook.ashrae.org/Handbooks/A19/IP/a19_ch38/a19_ch38_ip.aspx) | INDUSTRY-REPORT | UNCLEAR |
| Life expectancy (expert survey) | Water heaters: **gas 10, electric 11, tankless 20+** years; boilers: **gas 21, electric 13** | LIFE (expert opinion) | Summer 2006 telephone survey of manufacturers, trade associations and researchers. First-owner residential use. | US residential | [NAHB 2007, Table 1](https://standards.nsf.org/higherlogic/ws/public/download/348/NAHB%202007%20StudyUseful%20Life%20of%20Home%20Components.pdf) | INDUSTRY-REPORT | UNCLEAR |
| Water-quality effects on tank life | Softened water: tank life "reduced by 50 percent or more". Heavy scale and sediment: life reduced 25-40%. Summary table: lifetime reduction "up to 50-60%" under poor water quality and maintenance. Extremely hard water on tankless: "<2 years" without deliming. | LIFE modifier | These are secondary citations (Weingarten & Weingarten 1992, a practitioner source; Konigsberg 2011, an NMSU extension piece). PNNL did no new measurement. | US residential | [PNNL-22921 s.2.2, 2.3, summary table](https://efiling.energy.ca.gov/GetDocument.aspx?tn=74366) | GOVT-PUBLIC-DOMAIN (secondary of weak sources) | YES |
| Scale film and corrosion | Thin scale film (<1/16 in) cut steel corrosion rate by **33%** after 3 weeks in 290 mg/L hardness water | lab result | Corrosion-cell test by a manufacturer's lab (A.O. Smith bulletin). | lab | same | same | YES (vendor-origin) |
| Electric element vs scale | Qualitative: scale and sediment do not harm tank or efficiency until sediment buries the bottom element; then the element overheats and has a shorter life. | mechanism | Battelle study (Paul et al. 2010) as summarised by PNNL. | lab | same | same | YES. No rate. |
| Tankless gas heater in hard water | Efficiency fell 80% to 72% in 1.6 years, then failed on a clogged pressure sensor or control until deliming | observation | Battelle accelerated lab test, as summarised by PNNL. | lab | same | same | YES. Small sample. |
| HPWH prototypes (lab) | 19 hybrid HPWH prototypes tested; production-pilot units about 2,600 cycles with no failure incidents; earlier units had a refrigerant leak, a lower-element failure and control-board replacements | observation | Accelerated life test, not field. | lab, Oak Ridge | [ORNL/TM-2016/104](https://info.ornl.gov/sites/publications/files/Pub61784.pdf) | GOVT-PUBLIC-DOMAIN | YES. Low relevance to central tank DHW. |

### 2b. Boilers, burners, heat exchangers, indirect tanks

| Component | Number | Type | Definition and sample | Source | Grade | Use |
|---|---|---|---|---|---|---|
| Steel gas-fired hot-water boiler | median **>22 yr** (n=117, 24 replaced) | LIFE (censored) | ASHRAE TRP-1237, commercial offices | [ASHRAE A19 ch.38 T3](https://handbook.ashrae.org/Handbooks/A19/IP/a19_ch38/a19_ch38_ip.aspx) | INDUSTRY-REPORT | UNCLEAR |
| Boilers, steel water-tube / fire-tube / cast iron / electric | **24 / 25 / 35 / 15 yr**; burners **21 yr**; shell-and-tube HX **24 yr** | LIFE | Akalin 1978, from a 1976 survey. ASHRAE says these may be outdated and "not statistically relevant". | [ASHRAE A19 ch.38 T4](https://handbook.ashrae.org/Handbooks/A19/IP/a19_ch38/a19_ch38_ip.aspx); [chart copy](https://www.shipleyenergy.com/wp-content/uploads/2025/09/ASHRAE_Chart_HVAC_Life_Expectancy.pdf) | INDUSTRY-REPORT | UNCLEAR |
| Gas-fired boiler | median **24-35 years** | LIFE | Restates the ASHRAE chart | [DOE/NREL Hot Water Strategies Guide](https://betterbuildingssolutioncenter.energy.gov/sites/default/files/attachments/Hot%20Water%20Strategies%20Guide.pdf) | GOVT-PUBLIC-DOMAIN | YES |
| Heat exchanger, nuclear plant (water-to-water) | Internal leakage (small): mean **2.76E-07 /h** (61 events in 2.23E8 h); external leakage (small): **1.90E-07 /h** (38 events); plugging (non-standby, CCW): **3.01E-07 /h** (8 events) | RATE | Event counts from US commercial nuclear plants, 2006-2020 | [INL/EXT-21-65055](https://nrcoe.inl.gov/publicdocs/AvgPerf/AvgPara2020.pdf) | GOVT-PUBLIC-DOMAIN | YES |
| Boiler incidents | "79%" of reported boiler accidents tied to low-water condition and operator error/poor maintenance | SHARE of incidents | I saw only secondary blogs (Nationwide Boiler, undated). I could not open the National Board report. Counts are of reportable accidents, not failures. | [Nationwide Boiler blog](https://www.nationwideboiler.com/boiler-blog/preventing-catastrophe.html) | SNIPPET-ONLY | NO. Not usable as a prior. |

### 2c. Recirculation and other pumps

| Component | Number | Type | Definition and sample | Source | Grade | Use |
|---|---|---|---|---|---|---|
| Pumps (ASHRAE medians, 1978) | base-mounted **20**, pipe-mounted **10**, sump/well **10**, condensate **15**, centrifugal **25** yr; electric motors **18**; motor starters **17** | LIFE | Akalin 1978 | [ASHRAE A19 ch.38 T4](https://handbook.ashrae.org/Handbooks/A19/IP/a19_ch38/a19_ch38_ip.aspx); [chart copy](https://www.shipleyenergy.com/wp-content/uploads/2025/09/ASHRAE_Chart_HVAC_Life_Expectancy.pdf) | INDUSTRY-REPORT | UNCLEAR |
| Fresh-water booster pump installations, Hong Kong high-rise residential | MTTF **1.24 yr**; 709 failures; downtime 8,990 h; availability **90%** | RATE (installation-level) | Failures logged in 46 buildings over 3 years (2005-2007). Unit of analysis (pump set vs pump) is not clear from the abstract. | [PolyU record](https://research.polyu.edu.hk/en/publications/downtime-of-in-use-water-pump-installations-for-high-rise-residen/) | PEER-REVIEWED (no open licence seen) | UNCLEAR |
| Seawater flushing pump installations, same study | MTTF **0.46 yr**; 2,081 failures; availability **78%** | RATE | same | same | same | UNCLEAR. Corrosive service, not comparable to DHW. |
| Motor-driven pump, normally running | Fails to run: mean **2.26E-06 /h** (129 events in 5.68E7 h; about 2% per year if run continuously); fails to start: **7.86E-04 /demand** (89 events in 125,005 demands) | RATE | US nuclear plants 2006-2020 | [INL/EXT-21-65055](https://nrcoe.inl.gov/publicdocs/AvgPerf/AvgPara2020.pdf) | GOVT-PUBLIC-DOMAIN | YES, with a large transfer caveat |
| Motor-driven pump, standby | Fails to start **5.88E-04 /demand** (227 events in 410,593 demands); fails to run >1 h **8.12E-06 /h** (92 events); external leakage (small) **1.98E-07 /h** (59 events) | RATE | same | same | same | YES |
| Circulator seal / bearing / motor shares | **None found** from an open source. A vendor claims bearings about 45% and mechanical seals about 30% of centrifugal pump failures; I could not trace its dataset. | SHARE | (untraceable) | [reliamag.com](https://reliamag.com/guides/pump-reliability-mtbf-statistics/) | SNIPPET-ONLY / VENDOR-CLAIM | NO |

### 2d. Valves: mixing valves, check valves, balancing valves, PRVs, relief valves

| Component | Number | Type | Definition and sample | Source | Grade | Use |
|---|---|---|---|---|---|---|
| TMVs found faulty in a hospital audit | **3 TMVs faulty and replaced** (about A$310 each, 2 h labour); other problem outlets fixed by resetting the adjusting screw (about 30 min each); Table 1 lists **10 problem outlets** | counts without denominator | Royal Adelaide Hospital. Outlet temperatures audited in 95 outlets (23 taps, 23 showers, 49 hand stations). 39 taps (36%) were above 50 C. The paper does not give the number of TMVs installed, and its tap counts do not add up cleanly. | [Hartley et al. 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3236657) | PEER-REVIEWED-OA | YES-WITH-ATTRIBUTION |
| TMV continuous monitoring | 220 TMVs monitored for 3+ years (Apr 2013 - May 2017); 865 faucet samples; paper reports **no TMV failure or drift statistics** | negative finding | Sydney hospital under 5 years old | [IJERPH 2019, 16(8):1332, Sydney hospital TMV monitoring (PMC6518245)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6518245/) | PEER-REVIEWED-OA | YES-WITH-ATTRIBUTION (CC BY 4.0) |
| TMV audit failure (one UK model) | One tee-type TMV3 model failed audit tests (temperature stability against pressure change and reduced flow); two test instances 3.4 C above the shower maximum (45.4 C) | product-level finding | NHS England alert NHSE/I-2020/005; Scottish notice SAN(SC)21/04. I did not open the PDFs, only a search summary. | [NHS England alert](https://www.iheem.org.uk/wp-content/uploads/2020/12/NHSEI-2020-005-ALERT-RWC-TMV3-audit-failure-FINAL.pdf); [Scottish notice](https://www.nss.nhs.scot/media/1312/sansc2104.pdf) | SNIPPET-ONLY | UNCLEAR |
| TMV cartridge / check-valve seal degradation | Chloramine 0.5-1.0 mg/L: seals "begin to degrade over longer periods"; 1.0-2.0 mg/L: "higher risk of premature failure"; >2.0 mg/L: "rapid degradation" of EPDM. Test every 6-8 weeks; in high-chlorine sites replace cartridges and check valves at no more than 6 months. | manufacturer guidance | Not field data | [Rada bulletin Ref 288](https://www.radacontrols.com/media/etnkvrl2/mandatory-procedure-for-rada-mixers-in-high-chlorine-water-supplies-final-update.pdf) | VENDOR-CLAIM | NO |
| Check valve (nuclear plants) | Fails to close **1.23E-04 /demand** (5 events in 44,791 demands); fails to open **1.12E-05 /demand** (0 events); internal leakage (small) **7.25E-08 /h** (58 events in 8.07E8 h); external leakage (small) **4.34E-09 /h** (3 events); spurious operation **6.20E-10 /h** (0 events) | RATE | US nuclear plants 2006-2020 | [INL/EXT-21-65055](https://nrcoe.inl.gov/publicdocs/AvgPerf/AvgPara2020.pdf) | GOVT-PUBLIC-DOMAIN | YES, transfer caveat |
| Safety relief valve | Spurious operation **7.38E-08 /h** (4 events); other modes are in the same report | RATE | BWR/PWR plant relief valves, not T&P valves | same | same | YES, low relevance |
| Spring relief valves (SRS shop) | Over 7,000 certified test records, about 1,200 valves per year; abstract gives no numbers. A search snippet quoted 1-1.5% initial failure probability and 1E-08 to 1E-07 /h useful-life rate; I could not confirm those numbers. | RATE | [Gross & Harris 2009, OSTI 948122](https://www.osti.gov/biblio/948122) | GOVT-PUBLIC-DOMAIN (abstract read); numbers SNIPPET-ONLY | YES for the source; do not use the unverified numbers |
| Backflow assemblies (check-valve based) | Oregon 2023 utility summaries show about 2-9% of tested assemblies failing; a Montana city reported 9.25% (2014 newspaper). I could not identify assembly type or whether initial tests or retests. | SHARE of tested | Search summary of [Oregon drinking-water annual summary PDFs](https://yourwater.oregon.gov/docs/asrs/00081_2023.pdf); my own fetch returned only a blank form | SNIPPET-ONLY | UNCLEAR |
| Balancing valves | No failure rate. A PG&E lab test (ACEEE 2024) found automatic balancing valves did not always meet target performance, and results depended on recirculation pump speed controls. | performance | [ACEEE SSB24 paper](https://aceee.org/sites/default/files/proceedings/ssb24/pdfs/Best%20Practices%20for%20Hot%20Water%20Distribution%20Systems%20in%20Multifamily%20Buildings-A%20Comparative%20Evaluation%20of%20Balancing%20Methods.pdf) (search summary only) | SNIPPET-ONLY | UNCLEAR |
| Valve actuators | Hydraulic **15**, pneumatic **20**, self-contained **10** yr (chart copy); the handbook version lists gas or electric **13** | LIFE | Akalin 1978 | [ASHRAE A19 ch.38 T4](https://handbook.ashrae.org/Handbooks/A19/IP/a19_ch38/a19_ch38_ip.aspx) | INDUSTRY-REPORT | UNCLEAR |
| PRVs, expansion tanks | **No usable number found anywhere** | | | | | |

### 2e. Controls, sensors, aquastats, fixtures, strainers

| Component | Number | Type | Definition and sample | Source | Grade | Use |
|---|---|---|---|---|---|---|
| Controls | Pneumatic **20**, electric **16**, electronic **15** yr (Akalin 1978). TRP-1237: pneumatic **>18** (n=101, 25 replaced), electronic **>7** (n=68, 6 replaced). | LIFE | see ASHRAE rows | [ASHRAE A19 ch.38 T3-4](https://handbook.ashrae.org/Handbooks/A19/IP/a19_ch38/a19_ch38_ip.aspx) | INDUSTRY-REPORT | UNCLEAR |
| Thermostats (residential) | **35 yr** | LIFE (expert) | NAHB 2007: "Thermostats usually are replaced before the end of" life. A space-heating thermostat, not an aquastat or tank thermostat. | [NAHB 2007](https://standards.nsf.org/higherlogic/ws/public/download/348/NAHB%202007%20StudyUseful%20Life%20of%20Home%20Components.pdf) | INDUSTRY-REPORT | UNCLEAR |
| BAS sensing faults | LBNL fault prevalence study: 8 data partners, 317 buildings, 3,660 AHUs, 53,865 air terminal units, 7,974 RTUs, 182 defined faults; "a wide array of sensing-related" faults seen. The percentages are in a chart image I could not read. Data come from FDD software reports, not verified field faults. | SHARE (not extracted) | [LBNL BTO peer review slide, Crowe 2023](https://www.energy.gov/sites/default/files/2023-05/bto-peer-2023-fault-prevalence-lbnl-crowe.pdf) | GOVT-PUBLIC-DOMAIN | YES. Not DHW. |
| Faucets and fixtures | Lavatory **20+**, tub/shower **20+**, kitchen **15**, bar/hospitality **15**, toilets/bidets **10** ("new cartridges or seals") | LIFE (expert) | NAHB 2007 | [NAHB 2007](https://standards.nsf.org/higherlogic/ws/public/download/348/NAHB%202007%20StudyUseful%20Life%20of%20Home%20Components.pdf) | INDUSTRY-REPORT | UNCLEAR |
| Strainers / filters (nuclear) | Self-cleaning filter plugging **1.51E-06 /h** (32 events in 2.16E7 h) | RATE | US nuclear plants | [INL/EXT-21-65055](https://nrcoe.inl.gov/publicdocs/AvgPerf/AvgPara2020.pdf) | GOVT-PUBLIC-DOMAIN | YES, low relevance |
| Aquastats, tank thermostats, igniters, elements | **No usable number found.** | | | | | |

### 2f. Cause-category evidence from Legionella outbreak investigations (not equipment rates)

| Item | Number | Source | Grade | Use |
|---|---|---|---|---|
| 2000-2014 North America | 27 land-based outbreaks; 23 had enough data. Process failures 15 (65%); human errors 12 (52%); **equipment failures 8 (35%)**; unmanaged external changes 8 (35%) in the table (7 in the text). Temperatures in the Legionella growth range in 12 (52%). Inadequate disinfectant in 16 (70%). | [MMWR 65(22)](https://www.cdc.gov/mmwr/volumes/65/wr/mm6522e1.htm) | GOVT-PUBLIC-DOMAIN | YES |
| Same, specific items | "A hot water heater's actual temperature was lower than its thermostat setting" (2 outbreaks); one heater's setpoint lowered from the contractor's original; one case of skipped periodic draining; TMVs installed near the heater, not the faucet, leaving long pipe runs in the growth range. Recirculation, check valves and expansion tanks were not mentioned. | same | same | YES |
| 2015-2019 CDC investigations | n=14 investigations, 82 deficiencies: process failures 67 (about 81%); human errors 12 (15%); **equipment failures 3 (4%)**; unmanaged external changes 0. Named items are plumbed devices (cooling tower, hot tub, storage tank, fountain, sink), not water-heater parts. | [Microorganisms 2021, PMC7824450](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7824450/) | PEER-REVIEWED-OA (CC BY 4.0) | YES-WITH-ATTRIBUTION |

### 2g. Recalls and incidents (counts without denominators)

| Item | Number | Source | Grade | Use |
|---|---|---|---|---|
| Honeywell V5130 gas valve (LP water heaters, 1984) | about 64 explosion incidents, 16 deaths, about 35 injuries | [CPSC](https://www.cpsc.gov/Recalls/1984/honeywell-v5130-gas-valve-announcing-issuance-of-complaint) | SNIPPET-ONLY | YES for the source; not a rate |
| White-Rodgers LP thermostats (1980) | about 600,000 in use; pilot-knob damage left the safety valve open; CPSC made no defect finding | [CPSC](https://www.cpsc.gov/Recalls/1981/Explosion-Hazard-Results-In-Repair-Program-For-600000-LP-Gas-Water-Heaters-Following-Settlement-Of-Penalty-At-420000) | SNIPPET-ONLY | same |
| Watts 140X-9 T&P valves (2009) | about 900 sold, no incidents reported | [CPSC](https://www.cpsc.gov/Recalls/2009/temperature-and-pressure-relief-valves-for-large-water-heaters-recalled-by-watts) | SNIPPET-ONLY | same |

---

## 3. Key question 1: best distribution of tank water heater failure modes, by age and hardness

### Takeaway
The only open, quantitative failure-mode split for tank water heaters is the IBHS 2007 insurance-claims analysis (n=700, 69% tank leak or burst, 13% unknown, 10% supply line, 7% valve malfunction, 1% other, mean age at failure 10.7 years), reproduced in a DOE-lab report. It describes water-damage claims, not "no hot water" service calls. Nothing open splits failures into element vs thermostat vs burner vs igniter vs scale, and nothing is open by age band or hardness band.

### Cited Findings
- 69% of 700 water-heater water-loss claims were leaks in the heater or burst tanks; the legend order is leak/burst, unknown, supply line, valve malfunction, other, with values 69/13/10/7/1. Average age at failure was 10.7 years (range 1-30), and the average cost was $4,444 after deductible. — [PNNL-22921](https://efiling.energy.ca.gov/GetDocument.aspx?tn=74366)
- The IBHS primary report ("At the Forefront: Emerging Issues in Property Loss, Water Heater Failure Risks", 2007) was not opened. A 2012 IBHS press release described slow leaks and sudden bursts as the most common failures, followed by supply-line failures, with no percentages. — secondary: [Canadian Underwriter](https://canadianunderwriter.ca/news/claims/an-oft-forgotten-risk), [PropertyCasualty360](https://propertycasualty360.com/2017/11/30/what-causes-a-water-heater-to-leak-or-rupture) (search summaries only)
- A trade summary claims "about 75% had died by age 12". I saw it only in a search summary and could not trace it to IBHS. — SNIPPET-ONLY
- For gas-fired tanks, NBS (1978) says failure "is typically a water heater tank leak" and the "primary normal failure mode is a corrosion induced leak". Anode disintegration without replacement lets corrosion attack the tank through glass-lining imperfections. — [NBSIR 78-1460 s.7.1](https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nbsir78-1460.pdf)
- NBS says heavy scale on electric elements "will promote a reduction in operating lifetime through element burnout". It gives no rate. — [NBSIR 78-1460 s.2](https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nbsir78-1460.pdf)
- Hardness effects, all secondary and mostly qualitative:
  - Soft water: tank life can drop by 50% or more.
  - Scale and sediment: life drops 25-40%.
  - Electric tanks: scale does not reduce tank life until sediment buries the bottom element, which then overheats.
  - A thin scale film cut lab corrosion rate by 33%.
  — [PNNL-22921](https://efiling.energy.ca.gov/GetDocument.aspx?tn=74366)
- PNNL states that "local water quality is the primary cause of premature failure", citing Weingarten & Weingarten 1992. I did not find that source, and it appears to be a practitioner publication, not a controlled study. — [PNNL-22921](https://efiling.energy.ca.gov/GetDocument.aspx?tn=74366)
- Median age at replacement: electric 14.3 yr (n=164), gas 12.6 yr (n=39). — [Robison et al. 1996](https://www.aceee.org/files/proceedings/1996/data/papers/SS96_Panel3_Paper16.pdf)
- The commercial picture (DOE): lifetime 10 years for commercial gas storage, 12 for residential-duty storage; assumed annual repair probability of 0.5% for combustion systems and 1% for controls, with only one major repair in life. — [88 FR 69686](https://www.govinfo.gov/content/pkg/FR-2023-10-06/html/2023-20392.htm)
- No open source I found gives igniter, thermocouple or burner failure shares. A search for warranty-claim breakdowns found only marketing blogs, which I did not use.

### Inferences
- If your model's complaint is "tank leaks" or "end-of-life", 69% is usable only as a within-claims split. A "no hot water" or "lukewarm" complaint in a central system is mostly a different population (elements, thermostats, burners, controls, recirc imbalance), where leak is rare relative to its share of claims.
- Age dependence can be sketched, not fitted. The mean age at failure of about 10.7 years (claims) and medians of 12.6-14.3 years (replacement) bracket a wear-out curve. No open source gives Weibull shape parameters. DOE's LCC workbook and TSD chapter 8 use lifetime distributions, which I did not open.
- Hardness: the open literature agrees on direction only. Hard water hurts elements and tankless exchangers; very soft water hurts anodes and glass-lined tanks. No usable multiplier exists by hardness band. Use as a qualitative feature, not a fitted likelihood.

### Gaps
- No open breakdown of non-leak failure modes (element, thermostat/aquastat, gas valve, igniter, burner, flue, T&P) with counts.
- No age-banded or hardness-banded failure counts.
- NBS Figure 6 (life vs TDS) exists but is a figure in a scanned PDF; I did not digitise it.
- DOE TSD chapter 8 and appendix 8F (the literature review behind the lifetimes, citing BOMA, San Francisco Apartment Association and National Grid sources) were not opened. They may contain lifetime distribution parameters.
- IBHS primary report not opened; its sample frame and definition of "failure" are unverified.

---

## 4. Key question 2: recirculation pumps, mixing valves, check valves, balancing valves, aquastats/sensors

### Takeaway
Only generic or non-DHW rates are open. Pump rates come from nuclear plants and Hong Kong high-rise water-supply pumps; check-valve rates come from nuclear plants; mixing valves have anecdotal audit findings and no rates; balancing valves, aquastats and DHW temperature sensors have nothing quantitative that I could find. TMV drift is documented as a mechanism (seals, scale, mis-setting), not measured as a percentage.

### Cited Findings
- Recirculation/booster pumps:
  - Hong Kong fresh-water pump installations: MTTF 1.24 yr, 709 failures, 90% availability, 46 buildings over 2005-2007. — [PolyU](https://research.polyu.edu.hk/en/publications/downtime-of-in-use-water-pump-installations-for-high-rise-residen/)
  - Nuclear motor-driven pumps, normally running: fail-to-run mean 2.26E-06 per hour (129 events, 5.68E7 h); fail-to-start 7.86E-04 per demand. — [INL 2020](https://nrcoe.inl.gov/publicdocs/AvgPerf/AvgPara2020.pdf)
  - FEMP's guide has no pump failure data. — [FEMP O&M guide](https://www.wbdg.org/FFC/DOE/DOECRIT/femp_omguide.pdf)
- Mixing valves:
  - Royal Adelaide audit: 3 TMVs found faulty and replaced; other outlets fixed by resetting the adjusting screw; staff say maintenance relies on complaints, not scheduled temperature checks. — [Hartley et al. 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3236657) (the "relies on complaints" statement is from the paper's discussion as summarised in a search result; the 3-TMV and reset counts I read in the full text)
  - A 220-TMV Sydney monitoring study reported no drift or failure statistics. — [PMC6518245](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6518245/)
  - Manufacturer guidance links chloramine above 2 mg/L to rapid EPDM seal degradation in TMV cartridges and check valves. — [Rada](https://www.radacontrols.com/media/etnkvrl2/mandatory-procedure-for-rada-mixers-in-high-chlorine-water-supplies-final-update.pdf) (VENDOR-CLAIM)
  - CDC outbreak reports mention TMVs installed far from the faucet, not TMV failure. — [MMWR](https://www.cdc.gov/mmwr/volumes/65/wr/mm6522e1.htm)
- Check valves:
  - Nuclear check valve fail-to-close 1.23E-04 per demand, internal leakage 7.25E-08 per hour. — [INL 2020](https://nrcoe.inl.gov/publicdocs/AvgPerf/AvgPara2020.pdf)
  - Practitioner article: a swing check valve can limescale open and let a recirc loop pull water and sediment backward; opinion only. — [HeatingHelp](https://heatinghelp.com/industry-news/coffee-with-caleffi-troubleshooting-hot-water-recirculation-a-case-study/) (search summary only)
- Balancing valves: lab finding that automatic balancing valves did not always meet targets; no field failure rates. — [ACEEE 2024](https://aceee.org/sites/default/files/proceedings/ssb24/pdfs/Best%20Practices%20for%20Hot%20Water%20Distribution%20Systems%20in%20Multifamily%20Buildings-A%20Comparative%20Evaluation%20of%20Balancing%20Methods.pdf) (search summary only)
- Aquastats and sensors: no DHW-specific rates found. Generic BAS data show sensing faults are common but unquantified in the slide. — [LBNL 2023](https://www.energy.gov/sites/default/files/2023-05/bto-peer-2023-fault-prevalence-lbnl-crowe.pdf). An OxMaint "14 of 46 sensors drifted more than 3 F" claim is unsourced and I excluded it.
- A Building America webinar noted a monitored system where pump and fan running gave the impression of operation while the compressor was not running. Qualitative only. — [DOE](https://www.energy.gov/eere/buildings/articles/building-america-webinar-central-multifamily-water-heating-systems) (search summary only)
- Fixtures: NAHB gives 15-20+ years and notes toilets need new cartridges or seals at about 10 years. — [NAHB 2007](https://standards.nsf.org/higherlogic/ws/public/download/348/NAHB%202007%20StudyUseful%20Life%20of%20Home%20Components.pdf)

### Inferences
- The nuclear MDP and check-valve rates can supply only a rough ordering. Pump fail-to-run at about 2% per year (running continuously) is plausible-order-of-magnitude for a well-maintained industrial pump, but DHW recirc pumps run in scale- and oxygen-rich water without nuclear QA. Treat as a floor, not a prior.
- For a technician-guided model, the likely high-frequency DHW causes (TMV mis-set or fouled, check valve passing, recirc imbalance, crossover) appear in the open literature only as mechanisms and anecdotes. These need expert elicitation or your own work-order data.

### Gaps
- No open TMV in-service failure percentage, calibration-drift distribution, or failed-thermal-element share.
- No open check-valve fouling or leak-by percentage specific to DHW recirc loops. The backflow-assembly failure rates are a lead (state and utility cross-connection reports), but I could not read assembly types.
- No balancing-valve, aquastat or tank-sensor rates.
- No circulator seal/bearing/motor failure-mode split from an open source.

---

## 5. Key question 3: field-inspection studies reporting % of mixing valves or check valves found failed

### Takeaway
I found none that report a percentage with a denominator. The closest are one hospital audit with counts but no valve total, one 220-valve monitoring study with no failure statistics, and utility backflow-assembly test summaries that I could not interpret.

### Cited Findings
- Royal Adelaide Hospital: 3 TMVs faulty and replaced; 10 problem outlets listed in Table 1; denominator for TMVs not reported. — [Hartley et al. 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3236657)
- Sydney hospital: 220 TMVs under continuous temperature logging for about 4 years. Only 4 of 865 samples were L. pneumophila positive, and the paper reports no TMV failure or temperature-excursion counts. — [PMC6518245](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6518245/)
- UK: a product-level audit failure for one TMV3 model, not a fleet failure rate. — [NHS England alert](https://www.iheem.org.uk/wp-content/uploads/2020/12/NHSEI-2020-005-ALERT-RWC-TMV3-audit-failure-FINAL.pdf) (SNIPPET-ONLY)
- Backflow assemblies: roughly 2-9% fail annual tests in a few Oregon utility summaries and one Montana newspaper item. — [Oregon summaries](https://yourwater.oregon.gov/docs/asrs/00081_2023.pdf) (SNIPPET-ONLY; I could not read the table)
- Open MDPI Pathogens (2020) data show Legionella-positive sample rates falling after TMV-fitted sensor faucets were replaced in three hospitals (for example 17.9% to 3.6%). That is contamination, not valve failure. — [PMC7350366](https://pmc.ncbi.nlm.nih.gov/articles/PMC7350366) (search summary only)

### Inferences
- UK HTM 04-01 TMV in-service test records are where real fleet failure percentages live, but they sit in trust-level records, not the open literature. A Freedom of Information request is a plausible route (suggested by a search result; untested).

### Gaps
- Hospital water-management audits and CEC "crossover" studies: nothing found with valve-level failure percentages.
- ASHRAE 188 / Guideline 12 audit data are not public.

---

## 6. Key question 4: what each number measures, and whether it can serve as a cause prior

### Takeaway
Most numbers here are lifetimes or counts of events, not complaint-conditional cause probabilities. Only a share-of-failures table drawn from a sample that matches your complaint population can serve as a prior. None of the open sources does; IBHS comes closest, but its sampling frame (insurance water-loss claims) over-represents leaks.

### Cited Findings (what each type measures)
- **IBHS 69/13/10/7/1:** share among 700 water-damage claims. It conditions on a water-damage claim being filed, so tank leak and burst are over-represented relative to all failures. — [PNNL-22921](https://efiling.energy.ca.gov/GetDocument.aspx?tn=74366)
- **ASHRAE ">21 yr", ">22 yr":** right-censored medians. Most units had not yet been replaced, so the true median is above the printed value. The table's "number replaced" column (36 of 304; 24 of 117) shows how censored the data are. — [ASHRAE A19 ch.38](https://handbook.ashrae.org/Handbooks/A19/IP/a19_ch38/a19_ch38_ip.aspx)
- **ASHRAE Akalin medians (24, 25, 20 ...):** from a 1976 survey; ASHRAE says the values may be outdated and not statistically relevant. — [same](https://handbook.ashrae.org/Handbooks/A19/IP/a19_ch38/a19_ch38_ip.aspx)
- **NAHB:** opinions of manufacturers and trade groups, not field failures. The report calls itself "a general guideline only". — [NAHB 2007](https://standards.nsf.org/higherlogic/ws/public/download/348/NAHB%202007%20StudyUseful%20Life%20of%20Home%20Components.pdf)
- **Robison et al.:** age at replacement, not at failure. Replacement can be voluntary or premature, and older units from defunct brands drop out because serial codes could not be read. — [ACEEE 1996](https://www.aceee.org/files/proceedings/1996/data/papers/SS96_Panel3_Paper16.pdf)
- **DOE repair rates (0.5%, 1%, 2% per year):** modelling assumptions with no cited data. DOE itself says the heat-exchanger inputs rest on a 1994 boiler report and it found nothing better. — [88 FR 69686](https://www.govinfo.gov/content/pkg/FR-2023-10-06/html/2023-20392.htm)
- **INL rates:** events per demand or per hour for specific nuclear-grade components, with hourly rates dominated by 2006-2020 EPIX/RADS reports. — [INL 2020](https://nrcoe.inl.gov/publicdocs/AvgPerf/AvgPara2020.pdf)
- **CDC MMWR:** share of outbreak investigations with at least one deficiency in each category (categories overlap; 11 of 23 had two or more). It is not a share of failures. Equipment failure was 35% of investigations in 2000-2014 but 4% of deficiencies in 2015-2019. — [MMWR](https://www.cdc.gov/mmwr/volumes/65/wr/mm6522e1.htm); [Microorganisms 2021](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7824450/)
- **HK pumps:** MTTF of installation-level failures in high-rise water-supply service, so a shorter-lived, harsher duty than DHW recirc.

### Inferences
- **Usable as a weak prior:** IBHS mode shares (for leak-type complaints only, with the claims bias noted).
- **Usable as a lifetime or age-feature input:** DOE lifetimes, Robison medians, NBS range, and ASHRAE TRP-1237 counts (if you correct for censoring).
- **Cannot serve as a cause prior:** all NAHB and Akalin lifetimes (opinion/old survey), DOE repair rates (assumptions), INL rates (wrong population), CDC categories (Legionella, not complaints), and recall counts (no denominators).
- **Conversion caution:** a median life is not a constant hazard rate, and dividing 1/life gives a per-year rate only under an exponential assumption that wear-out components violate.

### Gaps
- No source gives P(cause | complaint) for any hot-water complaint type.
- No source gives per-component rates for DHW service conditions (scale, 120-140 F, chloramines, intermittent duty).

---

## 7. What is still missing even after this search

1. **Component-level failure-mode shares for tank water heaters** (element vs thermostat vs gas valve vs igniter vs burner vs tank), by age and water hardness. Likely locations: manufacturer warranty claims, utility replacement programmes, service-company CMMS data. None are open.
2. **TMV field performance**: percent failed in-service test, drift distribution, share of failures by cause (thermal element, check-valve seal, fouling, mis-set). UK in-service test records exist but are not published in aggregate.
3. **Recirculation components**: circulator MTBF and failure modes in DHW service; check-valve fouling and leak-by rates; balancing-valve failure; aquastat and tank/loop sensor drift. Nothing open.
4. **PRVs and expansion tanks**: nothing quantitative found. A forum claim that most residential tanks are precharged wrongly has no survey behind it.
5. **Weibull or hazard-curve parameters** for water heaters, boilers and pumps. DOE's LCC workbook and TSD chapter 8 / appendix 8F probably have lifetime distributions and a literature list (BOMA, San Francisco Apartment Association, National Grid, LBNL, NREL). I did not open them.
6. **Primary IBHS 2007 report** (sample frame, definitions) and the **National Board incident report** (cause categories by equipment type): neither opened; only secondary summaries seen.
7. **Digitised NBS Figure 6** (life vs TDS) and any other figure data locked in scanned PDFs.
8. **Complaint-conditional data**: no open dataset links a hot-water complaint (cold, lukewarm, slow, too hot, fluctuating) to its confirmed cause. Municipal 311/HPD complaint data record the complaint, not the cause. This is the data your priors actually need.
9. **Proprietary but real**: NPRD/EPRD (about $850 for NPRD-2016), OREDA (NOK 4,000 per volume), IEEE 493, ASHRAE's full TRP-1237 report, BOMA/IFMA benchmarks, and the ETCC multifamily recirculation PDFs. All NO for redistribution.
10. **Items I could not read**: NREL domains returned a network error from my sandbox, so the 1984 NREL "Survey of Failure Modes from 122 Residential Solar Water Heaters" (about 47% of systems with at least one reliability problem in two years; differential controllers caused most repairs over $50) is SNIPPET-ONLY. It may be the best open pump/controller/sensor failure tally for solar-loop analogues. [NREL record](https://research-hub.nrel.gov/en/publications/survey-of-failure-modes-from-122-residential-solar-water-heaters/). Also unreadable: the ASCE 2023 dormitory plumbing work-order study (43,704 work orders; "temperature regulation" among the costliest and most frequent problem types; paywalled; [ASCE](https://ascelibrary.com/doi/abs/10.1061/JPCFEV.CFENG-4330)), and the ISEC 2019 paper on 877,668 campus work orders (plumbing 5-21% of work orders by institution, no hot-water component breakdown; [ISEC FAM-03](https://www.isec-society.org/ISEC_PRESS/ISEC_10/pdf/FAM-03.pdf)).
11. **Savannah River generic component database** (WSRC-TR-93-262 Rev. 1, [OSTI 752209](https://www.osti.gov/biblio/752209)) is a public-domain table of pump, valve and relief-valve rates, but the PDF is a poor scan and my text extraction was unreadable. A manual read would be needed.
12. **Excluded as unreliable**: restoration-company and SEO blogs with unsourced statistics, OxMaint vendor pages, and a "2022 utility field test: 43% of PRVs out of tolerance" claim I could not trace.
