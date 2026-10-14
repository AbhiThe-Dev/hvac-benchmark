# Field sources for real-world tests of the troubleshooting tool (2026-10-08)

A search for real cases the tool (v0 / v1 / v2, `TROUBLESHOOT_V2.md`) could be run against: YouTube service calls, written case studies, and O&M / ASHRAE material. **This is a source list, not a result.** Nothing here has been run through the tool, and none of it validates or calibrates a placeholder number.

## What a usable test case needs

1. A complaint at a room or VAV (too hot / too cold / no air), or a symptom that maps to one.
2. The checks the technician made, in order, with what each showed.
3. The final root cause, ideally inside the catalogue (`v1/causes.py`: 14 causes, plus `econ_fault` outside it).
4. Time per step (only the videos can give this, and only roughly, from chapter marks).

Verification codes used below: **V** = I read it (page, description, chapter list); **S** = search-result snippet only, not read; **N** = found but not opened.

## A. YouTube: real narrated calls (best fit)

**Update 2026-10-08 (later): auto-caption transcripts were pulled for #1-#4** and read; see section E. Rows #1-#4 are now narration-verified; everything else below is still title, description and chapters only (V), and the chapter titles are YouTube-generated summaries, not the technician's words. Raw transcripts (unedited ASR, 15-second buckets) are in the session scratchpad, `captions/<video id>/transcript.txt`; they are not in the repo.

| # | Video | Min | Verified | Catalogue fit | Why it fits / limits |
|---|---|---|---|---|---|
| 1 | [Everything HVACR: office and cubicle area too cold in the morning, Trane VAV controls](https://www.youtube.com/watch?v=QW2BUsT085k) | 16 | V desc + chapters (Fixing space setpoints 0:00, Analyzing cold VAV boxes 1:00, Configuring device addresses 3:35, Adjusting box settings 6:45, Explaining operation 9:01, Finalizing 10:57) | `controller_config`, `zone_sensor_setpoint`, possibly `controller_comms` | The best v2 shape found: a multi-space building where only 2 areas complain. Real fix is controller setup, not hardware. |
| 2 | [Nighthawk HVAC, VAV's Electric Heat Not Heating EP160](https://www.youtube.com/watch?v=avYHEiu140A) | 7 | V desc, no chapters | `reheat_fail` (electric: burnt wires, open fuse) | Tenant complaint, two VAVs on one suite, BAS read first ("both receiving a call for heat but discharge temperature too low"), then "I located the units". Matches the T3 flow and the locate step. Two boxes failing together hints at a shared electrical feed, which the tool does not model. |
| 3 | [Everything HVACR: No Heat Service call, Trane VAV issues, SC Controls](https://www.youtube.com/watch?v=C6sMPDEDHEU) | 10 | V chapters (overview 0:00, identifying VAV issue 1:07, diagnosing damper 2:38, replacing actuator 5:18, final check 9:06) | `actuator_fail` | Clean complaint to cause in about 3 minutes of diagnosis. The YouTube search summary also mentions a failed discharge-air temperature probe (not verified). |
| 4 | [Everything HVACR: Trane VAV system with duct static pressure problems](https://www.youtube.com/watch?v=7lvjK7EYbpo) | 12 | V desc + chapters | AHU-level, near `low_static` | Cause is a **failed static-pressure transducer** reading wrong. The catalogue's `low_static` is real low pressure, so a bad static *sensor* is a gap, not a match. Useful as exactly that test. |
| 5 | [Everything HVACR: 20 Ton Trane package unit, VAV, static pressure and VFD issues](https://www.youtube.com/watch?v=WnpOTOeR3aU) | 21 | V desc + chapters (pulley and VFD adjustments 4:30-15:17) | `low_static` (fan or drive) | Upstream cause. Mostly one long adjustment, so thin on the check-order question. |
| 6 | [Nighthawk HVAC: Two Calls, VAV not heating and noisy exhaust fan EP52](https://www.youtube.com/watch?v=qAyxi9x0f9M) | 5 | V chapters (VAV box 0:00-2:55) | probably `reheat_fail` | Only the first ~3 minutes are relevant. Description gives no cause. |
| 7 | [Everything HVACR: Old VAV system damper not working](https://www.youtube.com/watch?v=YF4xhQNzGNI) and [VAV with Trane controls, intermittent cooling](https://www.youtube.com/watch?v=CGaUWWw2hsM) | 5 / 5 | desc only ("Building automation" / one line) | unknown | Short; descriptions say nothing about the cause. Worth a look only if the top ones disappoint. |
| 8 | [BEST Center, Lab 2: VAV System Troubleshooting (Nirenberg)](https://www.youtube.com/watch?v=oohVdcGI7e0) | 15 | V desc only | unknown | A training lab at a BAS workshop, so likely a bench with planted faults. That would give known ground truth but is not a field call. Content not checked. |
| 9 | [Nighthawk HVAC: Varitrac System Not Cooling, locate the RTU EP89](https://www.youtube.com/watch?v=VxM8PKaYs4g) | 12 | V chapters | v0 only, first ~1.3 min | Uses the BAS to find which RTU is not cooling the hallway (the "which unit serves this space" step), then goes to breaker, wiring and compressor, which is out of scope. |
| 10 | [Everything HVACR: abandoned VAV box cooling a storage room turned conference room](https://www.youtube.com/watch?v=rLkRmqbudRQ) | 28 | V desc + chapters | v0 flavor (room use differs from design), but it is install work | Documentation drift, not a diagnosis. Low priority. |
| 11 | [Everything HVACR: Trane package water-source heat pump, VAV static pressure](https://www.youtube.com/watch?v=ANGLve3AkIs) | 28 | V chapters (tracing faulty static tubing 2:43) | partial | Mostly building negative pressure and static tubing. Mostly outside the catalogue. |

Already reviewed (`TROUBLESHOOT_V2.md`, Sep 28): [VAV Not Cooling EP173](https://www.youtube.com/watch?v=Z-bmPdL7_Wo) (stuck-low economizer), plus the three HVACR VIDEOS refrigeration calls (out of scope) and the Control Field Pro explainer (AI-generated).

Skipped on purpose: Trane Voyager "not cooling" (a rooftop high-pressure alarm, refrigeration domain), and the many YouTube Shorts (seconds long, no diagnosis).

## E. What the four transcripts actually show (read 2026-10-08)

These are auto-generated captions of edited videos. Timings are video time, not on-site time; each video skips parts of the call. Nothing was run through the tool.

**#1 Everything HVACR, cold in the morning (QW2BUsT085k).** The call proper runs 1:00-16:00 after a 45-second "what I found" clip.
- Complaint: two boxes, "206 and 232", running cold in the morning, fine mid-afternoon. No room names; the owner reported it.
- Order: connect to the Trane Tracer SC; state hypotheses (morning/daytime warm-up, supply-air reset); find the zone area and read its schedule (occupied 5 a.m.) and unoccupied heating setpoint (raised 63.1 to 66); then **try to find the boxes in the BAS**.
- **Documentation mismatch, in the technician's own words (3:30-5:15).** Box "206" is "what it was labeled on the back of the stack so that could be wrong"; neither 206 nor 232 shows up in the BAS; he opens the Devices tree and checks the rotary address on the thermostat; concludes "I think it's just labeled wrong"; the unit labelled 206 turns out to be room 250, and a 232 is elsewhere. About 1.75 minutes of an ~15-minute call. This is the clearest real instance of v0's question that I found.
- Causes found (several): the zone's local-setpoint point was out of service; maximum/cooling-minimum temperature limits clamped the setpoint (71, raised); the occupant had the single-setpoint thermostat at 74-75, so with a 1.5° differential the box stayed in heating mode; a no-reheat box had a nonzero heating airflow setpoint. Then at the rooftop: discharge setpoint reset to 59 against a typical 55, the economizers disabled, and an outdoor-air sensor in the sun reading about 65 against 45-50. The technician deliberately did not chase the rooftop items ("don't want to cause another problem").
- Catalogue fit: `zone_sensor_setpoint` and `controller_config` for the boxes (good); the rooftop items (discharge reset, outdoor sensor, economizer) are upstream and **not in the catalogue**. No outcome check: "they'll probably call tomorrow."

**#2 Nighthawk EP160 (avYHEiu140A).** The video starts mid-call ("I've already verified that I have air flow"); the tenant complaint is only in the description.
- Order: BAS first. Box T212 shows heat stage on, damper 58%, discharge 62.8°F, so "not coming on". Box T117 "doesn't have a graphic" so he reads a point list (also 62°F, heat on). Then physically locate both ("assuming I can find them").
- At the box: contactors open; 24 V present; three-phase supply present on all pairs; high limit tripped (reset); 14 A on one circuit and none on another; about 100 V on the load side, so a fuse is open; power off, continuity test, one dead fuse (25 A, 600 V) replaced, burnt wire repaired. Second box: one small heating circuit, about 70°F discharge, melting wire found and repaired.
- Time: BAS ~1.5 min (0:15-1:45), box 212 ~3.5 min (1:45-5:15), box 117 ~1.25 min (5:15-6:30).
- Catalogue fit: `reheat_fail` (electric element and connections). Both boxes failed together after recent fuse replacements, suggesting a shared electrical cause. The tool has no electrical layer.

**#3 Everything HVACR, No Heat, Trane VAV (C6sMPDEDHEU).** Boxes 36 and 37, fan-powered with electric heat; edited follow-up (heater already tested the day before).
- **He reads the air handler first and rules it out** (1:15-2:30): discharge 60°F against an active setpoint 59.8 with a 10° reset, no alarms, "instead of going to the rooftop because it's doing what it's supposed to... we need to stick with our VAV box". This is the shared-parent read the tool is built around.
- At the box: heat at 100%; one box has a **failed discharge-air probe** (no reading), the other discharges 67°F; damper command 0% but the damper is stuck about halfway, so too much cold air; actuator bearings failing and stripping a plastic gear. Replaced the actuator; discharge 83°F afterwards. About 2.5 min of BAS then about 4 min at the box.
- Catalogue fit: `actuator_fail`; the failed probe is a second, separate sensing fault. It is ambiguous from the captions which of the two boxes had which fault.

**#4 Everything HVACR, duct static pressure (7lvjK7EYbpo).** Not a complaint-driven call: no room or zone symptom is described. This is a repeat visit; the first call (compressor "froze up") is not shown.
- The cue was a single implausible BAS number ("either the duct is gone or that's a bad number"). Cause: a broken rain-bird outdoor reference fitting let rain into the tubing and the static transducer; the drive "ramps the blower all the way down to a minimum" when it cannot read static. Fix: new transducer, reference fitting and tubing with a drip leg; static back at the 1.9 setpoint, supply fan 16%.
- Catalogue fit: **a gap, not a match.** The downstream effect is `low_static` (starved boxes), but the cause is a wrong static *sensor*, and the cue is a plausibility check on one AHU reading that the tool has no check for. Parts took about two weeks, so on-site minutes are not the story here.

**Reading across the four.** (1) Only #1 and #2 have a complaint-to-box path the tool's v1 can be run on; #3 is similar but edited; #4 is not. (2) #1 and #3 both show the technician reading the AHU first to decide whether to stay at the box. (3) Only #1 has a documentation mismatch. (4) #1 and #4 both involve upstream facts the catalogue lacks (discharge reset, outdoor sensor, economizer; static-sensor failure). (5) Two of four have more than one fault in the same visit, while the tool assumes one first-order cause per complaint.

## F. Replay of #1 and #2 through the live v2 tool (2026-10-08)

Encoded as `field_cases/cold_morning.json` and `field_cases/ep160.json`, frozen by hash, run by `scripts/88_field_cases.py`, registered and reported as **Addendum 38** in `PREREGISTRATION_DR.md`; outputs in `results/docmismatch/field_cases/`. All six registered predictions held and both cases are labelled ALIGNED at k = 6, but read the qualifiers there: the "right cause" results are near-true by construction (the answered checks are the technician's own diagnostic readings), the cold-morning 99% is partly my encoding counting one reading twice (79% without it), and n = 2. What is informative: the tool opens with an air handler static read in both calls (neither technician read an air handler first) unless many quiet neighbours are assumed; 31-43% of the checks it recommends have no counterpart in the video, and those take about half its minutes; no check in the catalogue could surface the cold-morning call's mislabelled box; the EP160 session stalls at 94-95% with the right cause leading.

**Head-to-head against the technicians (Addendum 39, same day; `scripts/89_field_compete.py`, results in `results/docmismatch/field_compete/`).** The tool worked the same two complaints with the same symptoms, answered by the video where it shows a check and by the catalogue's own model otherwise (1000 worlds, home-field), and was compared on steps to a diagnosis. **The technician needed fewer steps in both calls** (4 against a median of 11 in the cold-morning call and 7 in EP160; the tool needed no more steps than he did in 0% of worlds), and the tool was almost never wrong and confident (0%). The cold-morning gap is overstated by an inconsistency in my frozen design: made consistent (exploratory), the tool's median is 6 steps and it is right 99% of the time. In EP160 the tool's second and third steps are the technician's first two, and `reheat_fail` already leads after three steps, but it goes on to seven. Minutes are not scored. Two of seven registered predictions failed (P3, P6); see the addendum.

**Working time at the technicians' own pace (Addendum 40, same day; `scripts/90_field_pace.py`, results in `results/docmismatch/field_pace/`).** Priced at his observed pace (BAS read 0.5 / 0.75 / 1.25 minutes, FAST / CENTRAL / SLOW), the tool takes about **10% longer in the cold-morning call (4.95 against 4.5 minutes) and 24% longer in EP160 (5.25 against 4.25)**: a TIE on the registered rule, not a technician win, because the tool's extra steps are cheap BAS reads. Neither label is robust: across FAST to SLOW the ratio runs 0.58 to 1.84 and 0.82 to 2.06. Like-for-like (adding the physical confirmation he made and the tool usually does not ask for), EP160 is about twice as long (8.5 against 4.25). All eight registered predictions held. The pace rests on two physical and four BAS observations.

## B. Written real cases

| Source | Verified | Catalogue fit | Notes |
|---|---|---|---|
| [NEBB "War Stories": hospital maternity-ward built-up AHU](https://www.nebb.org/?p=13290) | V | Symptom matches `low_static` (fan at 60 Hz, static 1.3" against 2.0" setpoint, several VAVs 100% open and short of max CFM, discharge 61°F against 52°F); **cause is outside the catalogue** (return fan wired backward after VFDs were moved) | Best written fit for the shared-parent idea: one AHU read explains many zones. A good test of what the tool concludes when the true cause is not in its list. No time given. |
| [ACHR News: The unintended death spiral (overridden minimum OA damper)](https://www.achrnews.com/articles/166549-the-unintended-death-spiral-lessons-from-an-overridden-minimum-outdoor-air-damper-setting) | V | Upstream; near `econ_fault` but the cause is a minimum-OA override (10% vs 50%), which the `econ_fault` description does not cover | Complaints looked like zone problems (unmet static, under-delivered airflow); cause was AHU configuration. The override came from misdiagnosing a chilled-water problem. Two visits years apart. |
| [CSE: Incomplete testing and lack of design review](https://www.csemag.com/incomplete-testing-and-lack-of-design-review/) | V | `controller_config` (occupied/unoccupied) | **20 of 100 perimeter fan-powered boxes** inoperative because BAS code held them unoccupied; tenant comfort problems. Found by retro-commissioning, not by a complaint. The count is the rare real base rate for a config cause. |
| [Copper Tree / Kaizen: Winnipeg federal office VAV](https://www.coppertreeanalytics.com/case-studies/kaizen-implementation-for-vav-zone-unit-troubleshooting/) | V | `damper_mech` / `actuator_fail` (stuck open) | Vendor page; the root cause is not confirmed and no counts or times are given. Weak ground truth. |
| [ACHR / ES: Malfunction at the museum](https://www.achrnews.com/articles/157682-malfuntion-at-the-museum) | V | Outside the catalogue (supply-duct heat gain), no VAV | Careful hypothesis elimination (leaky reheat valves, return-damper leakage, duct gain). Useful only as a **negative control**: does the tool overstate confidence on a complaint whose cause it cannot name? |
| [HPAC: The Blame Game](https://www.hpac.com/iaq-ventilation/article/20926317/the-blame-game) | V | Outside the catalogue (condensate trap depth after an airflow change) | Technician spent two days; the cause was elsewhere. Another negative control. |

## C. Documentation-mismatch evidence (v0: which box serves this room?)

Real instances that the drawings or BAS point at the wrong box or room. These show the premise is real; none is a worked diagnosis.

- Carleton University, Health Sciences Building audit: the flow reading for the VAV serving rooms 2301 and 2302 was mislabelled as room 2303's. **S**, from a search snippet; the PDF would not parse (binary), so not read. [PDF](https://carleton.ca/bprc/wp-content/uploads/2019-07-10-Ava-Bebbington-and-Manav-Shah-Health-Sciences-Building-Audit.pdf)
- Woodbury County (Iowa) health building, 2017 automation proposal: supply-terminal tags were unclear or tied to old room numbers; consultant offered to draw new location maps. **S**; the PDF is an image scan, not read. [PDF](https://www.woodburycountyiowa.gov/files/contracts/resource_consulting_engineers_llc_siouxland_district_health_hvac_automation_proposal_2017-05-09_67383.pdf)
- Cal Poly SURP VAV analysis: a building-wide zone map had to be built before the VAV data could be tied to rooms. **S**; the host has a certificate error, not fetched. [link](https://surp.calpoly.edu/?p=7501)
- A BMS graphics review (csemag project profile) found equipment missing or mapped to the wrong place on the BMS layout. **S**.

## D. O&M and ASHRAE material

- **ASHRAE Engineer's Notebook: poor fit.** The column (four ASHRAE Fellows, monthly, since 2013) is design and energy oriented; the VAV pieces I found are Taylor's "VAV Box Duct Design" (inlet/outlet duct options, oversized reheat coils). I found no diagnostic case in it. Titles only, not full text. **Note:** the ASHRAE page I fetched carried a banner prohibiting entering its content into AI tools without permission, so I stopped fetching ASHRAE-hosted pages. Check that policy before putting ASHRAE text through the tool or into this repo.
- ASHRAE Journal, "Diagnosing hot/cold complaints" (Jan 2004, vol. 46 no. 1, S157-163): the one ASHRAE title about complaints. **N**, not read (likely paywalled).
- [PNNL O&M Best Practices, VAV systems](https://www.pnnl.gov/projects/om-best-practices/variable-air-volume-systems): **V**. Maintenance checklist and trend indicators only; no troubleshooting order, no cases, no frequencies. The tool already cites it.
- PNNL Building Re-tuning (chapter 7 terminal units; Georgia Tech TSRB case; federal buildings retrospective of 26 buildings): trend-based "rogue zone" and static-pressure rules (more than 25% of dampers wide open in cooling means static is probably too low). **S** only; the case PDF would not parse. Trend-driven, not complaint-driven, so a weaker fit.
- Manufacturer symptom-to-cause sheets (Belimo VAV Compact troubleshooting; Trane CCP troubleshooting part IV): **S**. Could serve as a published reference procedure to compare the tool's check order against.
- Excluded: oxmaint.com / ifactoryapp.com pages. Marketing blogs whose headline statistics have no source.

## Honest limits

- Videos are selected for being interesting; written cases are selected for being publishable. Neither samples calls the way a work-order log does. The only unselected real complaint data on hand is the 600 work orders from Addendum 32.
- Time per step is available only roughly (video chapters). No written case states minutes.
- Most videos do not show the whole AHU to VAV to room tree, so a building file for the tool would have to be built from what is on screen.
- The tool's catalogue misses several real causes seen here: a failed AHU static sensor (#4), a reversed return fan (NEBB), a minimum-OA override (ACHR).

## Next step

Retrospective tests on about 6 sources: #1, #2, #3, #4 above, plus NEBB and CSE. To avoid leaking the answer, freeze the encoding first (building tree as stated, answers to each check as shown on screen, tier, complaint) before reading the root cause, then compare the tool's first recommended check, its leading cause, and the technician's order and minutes. n is about 6, so this can show whether the tool's reasoning is plausible; it cannot calibrate anything.

Transcripts for #1-#4 are done (section E). The remaining videos (#5-#11) have no transcripts yet; the same method works (turn captions on in the player, read the player's own caption request) and costs a few minutes each, but ads can interrupt it.
