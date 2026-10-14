# Hot-water model inputs: what step 1 (sources) and step 2 (FMUCD work orders) gave (2026-10-07)

## Step 2: FMUCD real work orders (3,731,442 orders, hash verified; extract of 107,331 unplanned orders in results/docmismatch/hotwater/extract.csv)
Frame: unplanned (UPM) orders coded plumbing (D20) whose text matches a hot-water *complaint* regex (6,033 orders, 11 universities; a regex frame, so complaints worded differently are missed).
Sample: 440 (up to 40 per university), labelled independently by two Claude models (opus, sonnet); NOT expert-verified, errors may be correlated.
- Agreement: hot-water complaint 99.5%, symptom 95%, scope 93%, cause-stated 97% (kappa 0.71), recurrence 100%.
- Symptom mix (campus text): no hot water ~85%, lukewarm/slow/uneven ~6-7%, crossover ~3%, low flow/pressure 2-3%, too hot ~1%.
- Scope: single unit/fixture ~56%, multi-unit/floor ~16-18%, building-wide ~9%, unspecified ~18-20%.
- CAUSE STATED IN THE TEXT: 4.1% (both labelers) to 6.9% (one). Of ~18-29 orders, heater/plant dominates, then recirc pump, fixture valve/cartridge. Far too few for cause priors; the corpus has no closing note.
- Filed under component: water heater ~61%, pipe & fittings ~17%, sink ~11% (filing, not cause).
- Labor hours per order (labelled hot-water complaints): median ~1.5 h, p75 3 h, p90 ~9 h; by scope medians 1.5 (single), 2.65 (multi), 2.0 (building-wide), means 3.5-6 h. (Per ORDER, not per check.)
- Recurrence (6,033 complaints, 3,470 with building+date): 12.7% are preceded by another complaint at the SAME BUILDING within 7 days, 21.6% within 30, 31.8% within 90, 51.9% within 365. Building-level on campuses, not same-plant; includes some same-event duplicates (489 same-day pairs).
- Cost: median total cost ~$76, p90 ~$527 (n=3,305).

## Step 1: sources (research_notes/Hot water recirculation diagnostic inputs/)
See the four notes. No published cause-frequency distribution; no component failure-rate data; no open-source DHW fault simulator; no DHW BAS point census; temperatures disagree between sources (120 vs 124 F return floor).
