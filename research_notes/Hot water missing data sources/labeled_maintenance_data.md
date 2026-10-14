# Open, commercially-usable datasets with CAUSE / RESOLUTION / COMPONENT information for hot-water problems

*Research date: 2026-10-07. This is a research inventory, not legal advice. Where terms are ambiguous I mark UNCLEAR. All record counts below come from my own live API queries on 2026-10-07 unless otherwise attributed; text-match counts (LIKE '%HOT WATER%') include false positives and are upper bounds.*

**Bottom line:** No open dataset I found records a clean "root cause of the hot-water complaint" field. The best open material falls into two classes:
1. **Component-level or repair-action text** attached to enforcement or emergency-repair records (Philadelphia violation code titles, NYC HPD emergency-repair work orders with cost, Chicago inspector comments, SF/Seattle complaint and NOV text). These give component frequencies, repair actions and in one case dollar cost.
2. **Complaint-level volume and recurrence data** with only process-outcome statuses (NYC HPD complaints, 850k+ "no hot water" rows). Good for (a) base rates of complaint type, (d) recurrence by building, and dates for time-to-close, but not cause.

None gives labour hours. Cost exists only in NYC HPD OMO/HWO emergency-repair records.

---

## Ranked table

| # | Dataset | URL | License as found | Commercial-OK verdict | Hot-water records (my counts) | Cause / resolution info quality | Effort |
|---|---|---|---|---|---|---|---|
| 1 | NYC HPD Open Market Order (OMO) Charges (emergency repair work orders, with award $) | https://data.cityofnewyork.us/resource/mdbu-nrqn | No license field on dataset; NYC Open Data Law "no restrictions" + Terms of Use (could not open terms page) | UNCLEAR (likely YES; see notes) | 514,707 rows total; descriptions containing "hot water" 39,416; "water heater" 32,454; "boiler" 34,041 (overlapping, include utility-restoration and generic "heat & hot water related work") | MEDIUM: work type (PLUMB/HEAT/UTIL/GC), free-text scope ("remove old non-working water heater and install new 75..."), award $ and dates. Repair action + cost, not diagnosis | Low (Socrata API/CSV) |
| 2 | Philadelphia L&I Violations (property maintenance code) | https://phl.carto.com/api/v2/sql (table `violations`); catalog at OpenDataPhilly | License not confirmed (OpenDataPhilly page 404 to me) | UNCLEAR | ~2,541 rows with water-heating-related code titles (2007 to 2026) | MEDIUM: code title is component-level ("INT-WATERHEATER REPAIR-RES", "INT-WATER HEATER VALVES-RES", "INT-WATER MAINTAIN HEAT-RES"), resolution code field, but 1,714 of ~2,500 water-heating rows have null resolution | Low (SQL API) |
| 3 | NYC HPD Housing Maintenance Code Violations | https://data.cityofnewyork.us/resource/wvxf-dwi5 | No license field; same NYC terms | UNCLEAR (likely YES) | 238,024 NOV descriptions with "HOT WATER"; by class: A 355, B 21,146, C 216,521 | LOW-MEDIUM: order text ("PROVIDE HOT WATER AT ALL HOT WATER FIXTURES", "HOT WATER EXCEEDING MAXIMUM TEMPERATURE LIMIT"), class, dates, close date. Symptom-level, not cause | Low |
| 4 | NYC HPD Housing Maintenance Code Complaints and Problems | https://data.cityofnewyork.us/resource/ygpa-z7cr | No license field | UNCLEAR (likely YES) | 16,359,442 rows total (2001 to present). Hot-water problem codes: NO HOT WATER 851,671; NO HEAT AND NO HOT WATER 739,785; NO HEAT& HOT WATER 771,288; SCALDING HOT WATER 34,937 (+1,933 variant); NO COLD/HOT WATER ONE ROOM 13,957 | LOW for cause: only process outcomes ("verified corrected", "unable to gain access", "inspected, violations issued"). BEST for complaint base rates, building-wide vs apartment-only, recurrence (94,175 distinct buildings with NO HOT WATER) and time-to-close | Low (bulk very large; filter server-side) |
| 5 | NYC HPD Handyman Work Order (HWO) Charges | https://data.cityofnewyork.us/resource/sbnd-xujn | No license field | UNCLEAR (likely YES) | 3,593 with "hot water" in description | MEDIUM-LOW: same structure as OMO (work type, description, approved $, charge $) | Low |
| 6 | San Francisco DBI Complaints (all divisions) | https://data.sfgov.org/resource/gm2e-bten (now data.sf.gov) | Open Data Commons PDDL 1.0 (read from the dataset's API metadata) | YES | 6,026 complaints with "hot water" in text; 1,238 of those also say boiler or heater | LOW-MEDIUM: free-text complaint ("Water boiler problem - inconsistent/no hot water"), date filed, date abated, status. Cause only when tenant names it | Low |
| 7 | San Francisco DBI Notices of Violation (NOV items) | https://data.sfgov.org/resource/nbtm-fbw5 | PDDL 1.0 (API metadata) | YES | 5,958 NOV item descriptions mentioning hot water or water heater | MEDIUM: inspector-written item text ("immediately restore use of hot water", "provide covered vents ... for water heater combustion air", "provide ... capacity of hot water heater") | Low |
| 8 | Seattle Code Complaints and Violations | https://data.seattle.gov/resource/ez4a-iug7 | "Public Domain" (API metadata: `license: PUBLIC_DOMAIN`) | YES | 1,519 complaints with "hot water"; 341 also mention boiler or heater | LOW-MEDIUM: free-text complaint, last inspection result. Some tenants state plumber/boiler history | Low |
| 9 | Chicago Building Violations | https://data.cityofchicago.org/resource/22u3-xenr | License field empty on dataset; City of Chicago Data Terms of Use page returned HTTP 403 to me | UNCLEAR | "WATER HEATER" in description: 459 rows (408 with inspector comments); "HOT...WATER" in description: 2,102 (1,906 with comments); 2.03M rows total (2006 to present) | MEDIUM for water heaters: inspector comments name the defect ("BROKEN WATER HEATER FLUE IN BASEMENT", "BACK PITCHED WATER HEATER FLUE"). Hot-water-to-fixtures comments are terse ("LOW HOT WATER PRESSURE - APT 1") | Low |
| 10 | CDC National Outbreak Reporting System (Legionella setting, water system) | https://www.cdc.gov/nors/data/index.html ; data.cdc.gov | ODI certificate lists CC0 (an older third-party record; not confirmed on data.cdc.gov) | UNCLEAR (CC0 reported) | Not counted; outbreak-level, not repair-level | LOW: etiology and water-system contributing factors at outbreak level, not component repairs | Medium |
| 11 | Queensland QBuild work register (completed maintenance work orders, 2017 to 2026) | https://www.data.qld.gov.au/dataset/building-and-asset-services-work-register | CC BY 4.0 (read from CKAN API: `license_id: CC-BY-4.0`) | YES-WITH-ATTRIBUTION (license verified; contents NOT verified) | Unknown: CSV download was blocked by an AWS WAF bot challenge, which I did not attempt to bypass | Unknown (third-party snippet describes "maintenance work by type"; not confirmed) | Medium; needs a browser download |

Verdict key: the rejected list at the bottom covers datasets that do not belong in this ranking.

---

## Per-dataset notes

### 1. NYC HPD Open Market Order (OMO) Charges (mdbu-nrqn)
- **What it is.** Per the dataset description: "work orders created through HPD's Emergency Repair Program, Alternative Enforcement Program and Demolition programs and fees assessed against properties." Work is done when an owner fails to correct a hazardous condition after an HPD violation. Source: https://data.cityofnewyork.us/api/views/mdbu-nrqn.json
- **Fields (32):** OMOID, OMONumber, BuildingID, Boro, HouseNumber, StreetName, Apartment, Zip, Block, Lot, LifeCycle, WorkTypeGeneral, OMOStatusReason, OMOAwardAmount, OMOCreateDate, NetChangeOrders, OMOAwardDate, IsAEP, IsCommercialDemolition, ServiceChargeFlag, FEMAEventID, FEMAEvent, OMODescription, lat/long, BBL/BIN, etc. (same API).
- **Work-type breakdown (my query):** GC 289,382; DELEAD 120,861; UTIL 38,958; PLUMB 20,526 (avg award $2,601); HEAT 15,977 (avg $2,270). Date range 1998-07-13 to 2026-10-06; 514,707 rows total.
- **Hot-water signal (my queries on `omodescription`, case-insensitive substring):** "hot water" 39,416 (avg award $715); "water heater" 32,454 (avg $383); "boiler" 34,041 (avg $1,181). Many of these are UTIL orders ("nationalgrid provide gas to boiler/hot water heater", award $0 or $1) or generic GC text ("heat & hot water related work"), so filter by WorkTypeGeneral = PLUMB/HEAT and award > 0 for real repairs. A real repair example: PLUMB, $3,380, "...properly remove old non-working water heater and install with new 75..." (2021-11-01). The description field is truncated at about 150 characters in the API output I saw, so verify full text length before relying on it.
- **Useful for:** (b) component frequency (water heater vs boiler vs gas/electric restoration), (c) COST per emergency repair (rare in open data), (d) recurrence by BuildingID. Cause is only implied by the repair action ("non-working water heater") and by the violation that triggered the order.
- **Bias:** NYC multifamily buildings where owners failed to comply with a violation, so it over-represents neglected or financially distressed buildings and emergency-level failures. Not representative of well-managed commercial buildings.
- **License / terms:** No license field in the dataset metadata (`license: null`). Dataset attribution is "Department of Housing Preservation & Development (HPD)". See "NYC terms" section below.
- **PII:** Building and apartment addresses present. Owner names are not in this table. Plan on dropping address/apartment columns.

### 2. Philadelphia L&I Violations (Carto `violations` table)
- **Access:** SQL API, e.g. `https://phl.carto.com/api/v2/sql?q=SELECT ... FROM violations WHERE ...` (verified working). Columns seen: casenumber, casecreateddate, casetype, casestatus, violationnumber, violationdate, violationcode, violationcodetitle, violationstatus, violationresolutiondate, violationresolutioncode, address, unit_type, opa_owner, etc. Total `complaints` table 1,066,488 rows (separate table).
- **Hot-water-relevant code titles (my query, top counts among titles containing "WATER"):** PLUMBING SYSTEMS- WATER HEATING 526; INT-WATER HEATING SYSTEM-RES 505; PLUMBING SYS-WATER HEATING 371; INT-WATERHEATER REPAIR-RES 339; INT-WATER HEATER VALVES-RES 329; INT-WATER MAINTAIN HEAT-RES 317; UTILITIES-RESTORE WATER-RES 628.
- **Rows matching "WATER HEAT" / "WATERHEAT" / "HOT WATER" / "MAINTAIN HEAT" in the title:** 2,541 (2007-01-02 to 2026-10-04).
- **Resolution field:** among the water-heating-titled rows, `violationresolutioncode` = null 1,714; COMPLIED - OWNER REPAIR 382; CLOSED - ADMINISTRATIVELY 37; CLOSED - REISSUED/REWRITTEN 17; CLOSED - STOP PROCESSING 15; COMPLIED - BY ENFORCEMENT ACTION 8. So roughly 1 in 6 rows records a repair-type resolution, which is a closure outcome, not a cause.
- **Useful for:** (b) a built-in component taxonomy (water heater repair vs valves vs supply vs "maintain heat") with no NLP needed; (d) recurrence by parcel/address. Not for (c).
- **Bias:** Philadelphia residential rental stock, enforcement-driven.
- **License:** Not confirmed. The OpenDataPhilly dataset page URL I tried returned 404 and I could not retrieve a license statement. Mark UNCLEAR and check the current OpenDataPhilly dataset page ("Licenses and Inspections Violations") before use.
- **PII:** `opa_owner` (owner names) and addresses are in the table; drop them.

### 3. NYC HPD Housing Maintenance Code Violations (wvxf-dwi5)
- 41 columns incl. violationid, buildingid, class (A/B/C/I), inspectiondate, novdescription, novissueddate, currentstatus, currentstatusdate, violationstatus, rentimpairing (API metadata + sample rows).
- Sample NOV text (verbatim, short): "PROVIDE HOT WATER AT ALL HOT WATER FIXTURES KITCHEN AND BATHROOM, APT. 1, REAR BUILDING." and "ABATE THE NUISANCE CONSISTING OF HOT WATER EXCEEDING MAXIMUM TEMPERATURE LIMIT". Class C (immediately hazardous) dominates the hot-water subset (216,521 of 238,024).
- **Info quality:** the violation is the inspector's finding of the symptom, not a cause. Close dates allow time-to-correct estimates (violation to closed). Useful with #4 to measure how often a complaint becomes a verified violation.
- **License:** none in metadata. See NYC terms.

### 4. NYC HPD Complaints and Problems (ygpa-z7cr)
- 33 columns; key ones: received_date, problem_id, complaint_id, building_id, unit_type, space_type, type (EMERGENCY etc.), major_category (HEAT/HOT WATER), minor_category (APARTMENT ONLY / ENTIRE BUILDING), problem_code, complaint_status, problem_status, status dates, status_description, problem_duplicate_flag, complaint_anonymous_flag, BBL/BIN. I pulled sample rows; dataset updates daily.
- **Hot-water problem codes and counts (verified by my group-by query):** NO HOT WATER 851,671; NO HEAT AND NO HOT WATER 739,785; NO HEAT& HOT WATER 771,288; SCALDING HOT WATER 34,937; SCOLDING HOT WATER 'DIRE' 1,933; NO COLD/HOT WATER SUPPLY TO ONE ROOM ONLY 13,957. Distinct building_id with NO HOT WATER: 94,175.
- **Status text:** the top `status_description` values for hot-water rows are generic outcomes: building-wide condition corrected (688,098), tenant verified corrected (396,550), tenant reported restored (318,082), could not access apartment (274,387), inspected no violation (187,854), inspected violations issued (100,825). These counts were produced by a summarising fetch of my group-by query and should be re-run before citation. There is NO cause, component or repair field.
- **Use:** (a) only as the complaint-universe denominator and for apartment-only vs building-wide split (which maps onto "shared plant" vs "local" causes), (d) recurrence, and time-to-close. Pair with #1/#5 (HPD's own emergency repairs by BuildingID/BBL) to link complaint to eventual repair type.
- **PII:** apartment numbers, addresses, BBL; "complaint_anonymous_flag" exists. No complainant names in the fields I saw.

### 5. NYC HPD Handyman Work Order (HWO) Charges (sbnd-xujn)
- Fields seen: hwoid, hwonumber, buildingid, worktypegeneral, hwostatusreason, hwocreatedate, hwodescription, hwoapprovedamount, salestax, adminfee, chargeamount, datetransferdof. 3,593 rows with "hot water" in `hwodescription`. Description says it contains work orders for emergency repairs when an owner fails to correct a hazardous condition (https://data.cityofnewyork.us/api/views/sbnd-xujn.json). Smaller-job analogue of #1, with cost.

### 6/7. San Francisco DBI Complaints (gm2e-bten) and Notices of Violation (nbtm-fbw5)
- **License text (from the datasets' own API metadata):** `Open Data Commons Public Domain Dedication and License`, termsLink http://opendatacommons.org/licenses/pddl/1.0/ . PDDL places no restriction on commercial use. Source: https://data.sf.gov/api/views/gm2e-bten.json and https://data.sf.gov/api/views/nbtm-fbw5.json
- **Complaint fields:** complaint_number, date_filed, date_1st_nov_issued, last_inspection_date, date_abated, block/lot, complaint_description, status, receiving_division, assigned_division, analysis_neighborhood.
- **Sample (verbatim, short):** "Water boiler problem - inconsistent/no hot water. bed bug infestation." ; "Apartment has been without hot water for 2 and half days starting on 1-1-22. the landlord informed customer that hot water would be restored by 1-3-22..."
- **NOV items:** nov_category_description + nov_item_description (inspector text). Counts as above.
- **Value:** moderate, since text is symptom-first. `date_filed` to `date_abated` gives duration to resolution (useful for (c) time, though calendar days not labour hours). Small relative to NYC. Bias: SF older multifamily and SRO hotels.

### 8. Seattle Code Complaints and Violations (ez4a-iug7)
- License per API metadata: "Public Domain" (`license: PUBLIC_DOMAIN`, attribution City of Seattle). Source: https://data.seattle.gov/api/views/ez4a-iug7.json
- Fields: recordnum, recordtype, description (free text), opendate, lastinspdate, lastinspresult, statuscurrent, address, lat/long.
- Sample (verbatim, short): "No hot water last Sat. (12-6), yesterday or today. Plumbers have been out to look at boiler, but still not working properly." 1,519 hot-water-mentioning complaints; 341 also mention boiler or heater.
- Text includes tenants' names or contact details in some records (I saw "will live name and number for contact" in a different complaint), so run PII scrubbing.

### 9. Chicago Building Violations (22u3-xenr)
- Fields (32): violation code, status, description, inspector comments, ordinance, inspection status/category, department bureau (BOILER / CONSERVATION etc.), address. 
- Hot-water-relevant violation titles (my group-by, "WATER" in title): PROVIDE HOT WATER TO FIXTURES 1,095; PRV FLUE FOR HOT WATER HEATER 309; OBTAIN PERMIT FOR HOTWATER HTR 163; PROVIDE HOT/COLD WATER TO SINK 386.
- Inspector-comment samples (verbatim): "BROKEN WATER HEATER FLUE IN BASEMENT. DANGEROUS AND HAZARDOUS" ; "LOW HOT WATER PRESSURE - APT 1".
- **License:** dataset metadata has no license; description only says the data "should not be used for real estate transactions". City of Chicago Data Terms of Use page (https://www.chicago.gov/city/en/narr/foia/data_disclaimer.html) returned HTTP 403 and the curl output contained only page CSS, so I could not read the terms. UNCLEAR.
- Mostly safety-code items (flue, permits), so component detail is better than for NYC, but little on supply failures.

### 10. CDC NORS (Legionella)
- CDC says NORS data are available "in BEAM Dashboard" and "for download at data.cdc.gov"; the public set is a streamlined subset and fuller data goes through NORSAdmin@cdc.gov (https://www.cdc.gov/nors/data/index.html, as summarised by search). An ODI record lists CC0 but is old (https://certificates.theodi.org/en/datasets/34380). Outbreak-level only; no repair information. Marginal for this product; included for completeness.

### 11. Queensland QBuild work register (CC BY 4.0)
- CKAN metadata (verified via API): title "QBuild work register", license "Creative Commons Attribution 4.0", description "Completed maintenance work orders undertaken by QBuild", CSV resources from 2017-18 through 2025-26 (https://www.data.qld.gov.au/api/3/action/package_show?id=building-and-asset-services-work-register).
- **Not verified:** field list, whether trade/problem descriptions exist, count of hot-water jobs. The downloads returned HTTP 202 with `x-amzn-waf-action: challenge` (bot challenge) and an empty body. I did not try to bypass it. A human can download the CSVs in a browser. Government (schools, housing, health) buildings in Queensland, Australia; climate and system mix differ from US.

---

## NYC terms (relevant to datasets 1, 3, 4, 5)
- I could not open the NYC Open Data Terms of Use page (https://www.nyc.gov/html/data/terms.html returned Access Denied via curl and 404 via the fetch tool), and the nyc.gov/main/terms-of-use page I did open does not address datasets (it says "All rights are reserved" for City site materials).
- A search-result summary of that page states that use is subject to NYC.gov terms plus "any additional terms of use defined by entities providing data", and that the City gives no warranty of completeness or accuracy. I could not verify this wording on the page itself.
- A search-result summary of the Open Data Law (Local Law 11 of 2012, amended by Local Law 251 of 2017) says the law requires public data sets to be offered without use restrictions, and that the portal FAQ says there are no restrictions on use. I did not confirm the codified text (https://intro.nyc/local-laws/2012-11 ; https://intro.nyc/local-laws/2017-251 ; the 2017 file came back as an unreadable PDF).
- None of the four HPD datasets has a license field (`license: null`, `licenseId: null` in their API metadata), and HPD attribution is "Department of Housing Preservation & Development (HPD)" with attribution link http://www.nyc.gov/html/hpd/html/pr/HPD-Open-Data.shtml (violations dataset) .
- **Verdict: UNCLEAR, leaning YES.** Get counsel to read the live Terms of Use and the Admin Code section on open data before relying on it. NYC data also carries a general "no warranty" disclaimer.

---

## Candidates considered and REJECTED (or not usable)

| Candidate | Reason |
|---|---|
| HUD REAC / NSPIRE physical inspection data (HUD USER "Physical Inspection Scores", https://www.huduser.gov/portal/datasets/pis.html ; https://www.hud.gov/stat/mfh/inspection-scores) | Public files are property-level scores (Excel/PDF), not deficiency records. Search results found no public item-level (water heater) deficiency file; the NSPIRE inspection report goes to the property, not the public. NAHRO reported only 635 NSPIRE inspections published in the first release and that HUD replaces older vintages. License check on HUD USER page failed (page returned empty to my fetch). Could be obtained by FOIA (not verified). NO for cause stats. |
| Boston Building and Property Violations (https://data.boston.gov/dataset/building-and-property-violations1) | License is PDDL (YES for commercial), but `description` is a code-section label ("Unsafe and Dangerous"); only 5 rows contain "water" in my group-by. No hot-water content. Boston 311 (also PDDL) not examined for hot water. |
| LAHD Property Look-Up for Violations (data.lacity.org cr8f-uc4j) | Metadata has no license and the description disclaims accuracy; I did not find hot-water-specific content. Not verified further. |
| DHS/FEMA "Facilities Request Details" (https://catalog.data.gov/dataset/facilities-request-details) | License link is usa.gov/government-works, but the only resource is an SSO portal URL (sso.fema.net), not a download; no record count; federal office space. Not obtainable. |
| Montgomery County MD "DGS Facilities Maintenance Work Order Completion Status" | Monthly aggregate counts, license "not specified" per a search snippet. No hot-water detail. |
| UK social-landlord / council repairs (data.gov.uk, OGL) | Searches found only aggregate KPIs (e.g. City of York "KPI" and "Tenant Satisfaction Measures", OGL-UK-3.0) and asset/leasehold-charge files (Oxford leasehold repairs 2015/16, Colchester assets). No job-level repair dataset with fault description and completion detail found. Barnet "Work orders completed" is road and pavement repairs. Inconclusive rather than proven absent; individual housing associations were not enumerated. FOI requests are a possible route (not verified). |
| FMUCD (Mendeley Data, already held) | Already in hand; cause text in about 4-7% of orders per the requester. Not re-checked. |
| CPSC NEISS (injury surveillance; US public domain label per a catalog entry) | Records ED injuries, 400-character narratives, not repairs, cause of outage or cost. Useful only for scald-risk context. Catalog license: http://www.usa.gov/publicdomain/label/1.0/ |
| Water heater failure datasets (NEII, utility rebate programs, insurer claims) | Search found no open failure-mode dataset; only forensic/insurer commentary (e.g. "one out of every ten water-damage claims" traced to hot water tank or washing machine failure, per a forensic consultant page, https://www.sites.google.com/site/metropolitanforensics/cause-origin-investigations-hot-water-tank-and-washing-machine-failures). Not a dataset. NEII/utility data not located. |
| Kaggle / Zenodo / Mendeley CMMS datasets | Searches surfaced FMUCD only. Research papers (D'Orazio et al., about 12,000 Italian maintenance requests in 23 buildings; Bortolini and Forcada, 6,830 requests in 46 buildings, per search summaries) did not link openly licensed data that I could confirm. Not directly checked on Kaggle (I did not search Kaggle's catalog itself). |
| Chicago Park District Facilities Work Order Management (sya9-5zxj) | Aggregate performance metrics, not work orders. |
| NYCHA work orders | I found no NYCHA-published work order dataset on NYC Open Data (the only NYCHA maintenance dataset is HPD violations at NYCHA properties, im9z-53hg, same schema as #3). NYCHA's Maximo work orders have been obtained only by request (per a search summary of audit and Public Advocate sources). |
| Legionella investigation tables (journal supplements) | Not systematically searched; any would be paper-specific with their own licenses. Gap. |

---

## Gaps and what I could not verify
- Exact current wording of NYC Open Data Terms of Use, Chicago Data Terms of Use, and Philadelphia's dataset license (pages blocked or 404). Counsel should read these.
- QBuild CSV contents (blocked by bot challenge).
- Whether Philadelphia "complaints" table has hot-water descriptions (not examined).
- Boston 311, LA 311, and other 311 datasets: not examined for hot-water text beyond what is above.
- None of these sources gives labour hours.
- Legionella outbreak tables, utility water-heater replacement data, and public-housing-authority or school-district work orders were not found as open datasets; absence is not proof.
- Counts are text-match counts and include false positives; several counts for NYC `status_description` come from a summarised fetch and should be re-queried before citing.

## Sources (principal)
- NYC HPD Complaints metadata/API: https://data.cityofnewyork.us/api/views/ygpa-z7cr.json ; https://data.cityofnewyork.us/resource/ygpa-z7cr.json
- NYC HPD Violations: https://data.cityofnewyork.us/resource/wvxf-dwi5.json
- NYC HPD OMO / HWO: https://data.cityofnewyork.us/resource/mdbu-nrqn.json ; https://data.cityofnewyork.us/resource/sbnd-xujn.json
- Chicago Building Violations: https://data.cityofchicago.org/resource/22u3-xenr.json ; https://data.cityofchicago.org/api/views/22u3-xenr.json
- SF DBI: https://data.sf.gov/resource/gm2e-bten.json ; https://data.sf.gov/resource/nbtm-fbw5.json
- Seattle: https://data.seattle.gov/resource/ez4a-iug7.json ; https://data.seattle.gov/api/views/ez4a-iug7.json
- Philadelphia Carto SQL: https://phl.carto.com/api/v2/sql
- Boston: https://data.boston.gov/api/3/action/package_show?id=building-and-property-violations1
- HUD: https://www.hud.gov/stat/mfh/inspection-scores ; https://www.huduser.gov/PORTAL/node/6626 ; https://www.hud.gov/reac/nspire-terms
- CDC NORS: https://www.cdc.gov/nors/data/index.html
- QBuild: https://www.data.qld.gov.au/api/3/action/package_show?id=building-and-asset-services-work-register
- NYC law context: https://intro.nyc/local-laws/2012-11 ; https://intro.nyc/local-laws/2017-251 ; https://www.nyc.gov/main/terms-of-use
