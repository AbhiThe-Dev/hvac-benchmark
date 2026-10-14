# Technician interview guide: how call-outs actually go

Internal. 45 minutes, one technician or service lead at a time. Aim for 3+ companies and 12+ coded call-outs before drawing conclusions.

## 0. What each block is for

We are missing four things, and each one currently sits in the code as an assumption. The interview replaces them with observations.

| Block | We learn | Replaces / feeds |
|---|---|---|
| Recent call-outs | The real order of checks, minutes per check, where time is lost | The assumed "traversal" search policy that stands in for a technician in `hvac_benchmark`; the baseline any test-saving claim is measured against |
| Cause mix | How often each complaint ends in each cause, and how often the drawings or labels were wrong | Symptom-to-cause priors (`symptom_pipeline`); how large a share of call-outs our topology machinery can address at all |
| Cost of checks | Minutes, access, disruption and reliability of each common check | The assumed costs and hit rates in `active/physical.py` (duct trace 12, box override 6; 0.95-0.98 true-positive) and the sensor cost tiers in `active/engine.py` |
| First hour on site | What is in hand at the start: drawings, controls, trends, a person who knows the building | Whether any passive-data layer applies in the buildings that matter (pre-2000) |

## 1. Before you start

- **Pick call-outs the way the technician remembers them, not the way you want them.** Ask for the last 3-5 comfort or airflow complaints, in order, then add one that "dragged" and one where the drawings were wrong, if there was one. Memorable cases alone overstate how often drawings are wrong.
- **Consent.** Say what you will do with the answers, ask permission to take notes (audio only if they say yes), and promise no names or addresses in anything written. Nothing is attributed to their company.
- **Don't lead.** Never say "the tool would...", "documentation problems" or "topology" until block 6. Their words for the cause come first.

## 2. Script (45 minutes)

**Intro and consent (3 min).** "I'm building a decision aid that suggests the next check on an HVAC call-out. I want to base it on how the work really goes. There are no wrong answers, I'm not evaluating you, and I won't record names or addresses."

**Background (4 min).**
- Your role, years in the field, the kinds of buildings you service.
- Roughly how many call-outs a week, and what share are in buildings built before 2000?
- What controls do those buildings usually have: pneumatic, early digital, a building automation system with graphics? Are trends ever stored?

**Recent call-outs (20 min, about 5 min each).** For each one, fill the record sheet in section 3, using these probes in order:
1. What was the complaint, in the caller's words? Which building type and age?
2. Before you arrived, what did you know? On site in the first hour, what could you actually get: drawings, a controls screen, a person who knew the building?
3. Walk me through what you checked, in order. For each: why that one, how long, what it told you.
4. When did you first suspect the real cause? What sent you the wrong way?
5. Did you use the drawings or labels? Were they right? If not, how many minutes did that cost?
6. What was it in the end, and how long did the whole thing take?
7. If you could have known one thing at the start, what would it have been?

**Cause mix (5 min).** "Think of your last 20 comfort or airflow complaints. Roughly how many ended in: something failed or stuck / a control or schedule problem / a bad sensor / something connected or labeled differently than the drawings / capacity or balancing / occupant or other?" Then: "How often are the drawings, labels or the controls screen not what you find? What does that cost you?"

**Cost of checks (5 min).** Fill the table with them, letting them add rows.

| Check | Minutes | Needs access or a second person? | Disrupts occupants? | How often does it mislead? |
|---|---|---|---|---|
| Read the thermostat or controls-screen point | | | | |
| Command a box or damper to a set state and watch | | | | |
| Look at the damper or valve position in person | | | | |
| Trace the duct or pipe | | | | |
| Measure airflow or supply temperature | | | | |
| Shut something off and see what stops | | | | |
| *(their own)* | | | | |

**Reaction to the idea (5 min).** Show one made-up example: "Complaint: room 204 too warm. Drawings say box 2-04 serves it. Suggested next check: command that box to full cooling and watch the room, because most other causes would not respond." Ask: Would you follow that, ignore it, or want to know why? What would you tell the tool up front? Where would you use it (phone, tablet, printed)? What would make you stop trusting it?

**Close (3 min).** Ask for a ticket sample (fields in ONE_PAGER.md), a ride-along, and one person to talk to next. Thank them.

## 3. Call-out record sheet (one per call-out; code within 24 hours)

| Field | Notes |
|---|---|
| ID | Anonymous, e.g. C-03 |
| Building type, age band, system type | e.g. school, 1970s, VAV with hot-water reheat |
| Controls | Pneumatic / early digital / BAS with graphics / BAS with stored trends |
| Complaint (their words) | Keep the wording |
| In hand at the start | Drawings? Which controls views? Person who knew the building? |
| Checks in order | check / minutes / what it told them |
| First suspected the real cause at step | |
| Root-cause category | Use section 4 |
| Documentation detour (minutes) | Time lost because drawings or labels were wrong, **even if that was not the root cause** |
| Total minutes | |
| The one thing they wish they had known first | Verbatim |

## 4. Cause categories and coding rules

Primary cause: the thing that, once fixed, resolved the complaint. If two, code the first fix that resolved it.

- **LAYOUT:** something is connected, served or labeled differently than documented (the wrong box, a rerouted duct or pipe, a mislabeled point).
- **EQUIPMENT:** failed, stuck or worn (actuator, damper, valve, coil, fan, pump).
- **CONTROL:** setpoint, schedule, sequence, or an override left on.
- **SENSOR:** drifting, failed or badly placed.
- **CAPACITY / BALANCE:** undersized, out of balance.
- **OCCUPANT / OTHER.**

Code the documentation detour separately from the cause. A call-out that ends in a stuck damper but cost 40 minutes because the drawing pointed at the wrong box is still evidence for what we're building.

## 5. After the interviews

Compute over all coded call-outs (and any ticket sample):

1. Share where the root cause is LAYOUT, and share with a documentation detour of 10+ minutes.
2. Median number of checks and minutes to the root cause.
3. Concentration: for each complaint type, the share covered by its top three causes.
4. Spread of check costs: the most expensive common check divided by the cheapest.

**Set these decision rules before the first interview, so the answers can't move them.** The numbers below are placeholders for you to change:

| If we find | It means |
|---|---|
| LAYOUT causes plus detours are under 10% of call-outs | Our topology machinery addresses a small slice; rethink toward broader fault troubleshooting |
| Median call-out takes 3 checks or fewer | Little headroom for a decision aid to save anything |
| Top three causes cover under 60% of a complaint type, and check costs differ by under 5x | Ordering checks by likelihood and cost gains little there |
| None of these hold | The idea is worth pursuing; the measured mix and costs replace our assumptions |

**Caveats to carry into the write-up.** This is a handful of interviews from people who agreed to talk, recalling from memory. Treat it as a way to find out where we are wrong, not as a measured rate.
