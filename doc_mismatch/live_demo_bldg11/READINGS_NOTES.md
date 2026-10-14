# Graded readings: what was built, what was predicted before the run (EXPLORATORY, not a registered protocol)

Written and hashed (`READINGS_NOTES.sha256`) before `study_readings.py` was run for the first time. The project's confirmatory rules (frozen protocol, gates) are NOT claimed here:
this is a first look, to decide whether a registered study is worth writing.

## The idea

Today a reading check is a yes/no question ("is the static pressure abnormal?"). The engine already accepts a number plus an expected value, but it only uses the number to
decide normal/abnormal and then treats the answer like any other yes/no. **Graded readings** use how far off the number is, not just which side of the tolerance it falls on.

No new numbers are introduced. For a reading check with a two-sided tolerance (`tol` or `rel_tol`), let `z = |reading - expected| / tolerance` (so `z <= 1` is "normal").
The catalogue's own rates fix the shape: with `bg` the chance of "abnormal" when the check does not see the cause, the instrument/process noise is a half-normal with
`P(z > 1) = bg`; for a cause the check sees with rate `p`, the same noise is shifted so that `P(z > 1) = p`. A reading is then scored by its density under each cause.
Integrating that density over `z > 1` returns the catalogue's rate, so the graded model agrees with the binary one on the yes/no question (tested).

Assumption that is mine, not measured: the readings are (folded) Gaussian around the expected value. One-sided checks (a minimum, e.g. inlet static) and checks without a tolerance stay yes/no.
Direction (above or below) is not used.

Off by default (`make_case_v1(..., graded=True)`); the default path is byte-identical (tested).

## Study

Single complaints on the bldg11 point map (as `levers.py`/`pay_time.py` earlier), n = 1500 per cell, draws a pure function of (seed, visit, world, who, check, target).
Arms: **binary** (numeric readings classified against the tolerance, then used as yes/no: today's path) against **graded**, on identical draws. Worlds: W0 (checks as the tool assumes),
W1 (every rate moved 25% toward 0.5; the tool still assumes W0). Reading draws come from a numeric world: matched (the Gaussian above) and mismatched (fault severity varies from visit
to visit, lognormal sigma 0.5, and heavier tails: Student t with 4 degrees of freedom at equal variance). Entry cost sensitivity: +0.5 min per numeric reading.

## Predictions (made before the first run)

- P0 (sanity): in the matched world, the binary arm reproduces the existing yes/no baseline (73.6% / 46 min at W0 on 1500 visits): within 2 accuracy points and 3 minutes. If not, no result.
- P1: matched world, W0: graded beats binary by +1 to +6 accuracy points; minutes within 8% of binary.
- P2: matched world, W1: graded still gains, but the confidently-wrong share rises by at least 1 point against binary (the graded model is the more confident one when the checks are worse than assumed).
- P3: mismatched world: the graded gain is at most half of the matched-world gain (at W0).
- P4: no cell reaches 80% accuracy at W0 (the ceiling analysis says 82-86% for everything).
- P5: the 0.5 min/reading entry cost changes minutes by less than 3.
