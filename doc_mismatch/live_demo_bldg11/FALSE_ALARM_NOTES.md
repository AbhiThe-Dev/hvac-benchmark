# False-alarm rate of the control-system readings, from real trend data (EXPLORATORY; written and hashed before any value was read)

## Question

The catalogue assumes `bas_static` ("is duct static more than 20% off its setpoint?") reads abnormal 3% of the time and `bas_airflow` ("does measured airflow miss its setpoint by more than 10%?")
5% of the time when the equipment is fine (`bg`). Are those near what real equipment does?

## What the data can and cannot say

- Only the false-alarm side (`bg`). The hit rates need labelled faults; none of the downloaded buildings has them.
- "Fine" is not labelled either: any fault in the data raises the measured rate, so the measured rate is an upper bound on the true false-alarm rate, and the per-equipment median is the robust summary.
- Census (metadata only, done before this note): a recorded airflow SETPOINT exists only in bldg30 (99 boxes, 1-minute data, about a year). No building records a static-pressure setpoint.
  So: `bas_airflow` is measured against the real setpoint (bldg30). `bas_static` can only be measured against a PROXY for the setpoint: proxy A = the handler's long-run median while running (over-states the rate when
  the setpoint is reset), proxy B = the median of the surrounding two hours (under-states it: a persistent low static is absorbed). The truth lies between them, if the setpoint behaves as these proxies assume.
- The clock is UTC and the buildings are anonymised, so occupied hours are found from the data (setpoint at least 20% of that box's maximum for airflow; running = static above half its typical running level for static), never from the clock.

## Measures (fixed now)

1. Airflow: for every box and every sample with setpoint >= 20% of the box's own maximum setpoint (the condition of the cited rule: within 10% above 20% of maximum), the share of samples with |flow - setpoint| > 10% of setpoint.
   Reported: pooled; per-box median and inter-quartile range; share of boxes above 5% (the catalogue's rate); the same by load tercile of the setpoint (high load is the "hot afternoon" case).
2. Static: for every handler with data, samples while running, the share with |static - proxy| > 20% of the proxy, for proxies A and B. Per handler, then the median over handlers.
3. A snapshot caveat is stated, not modelled: the technician reads one screen once; 1-minute samples are treated as such readings.

## Predictions (before the first value was read)

- F1: bldg30 airflow, pooled share outside +-10%: above the catalogue's 5% (I expect 10% to 35%); the median box is above 5%.
- F2: static, proxy A: median over handlers above 5% (I expect 5% to 30%). Proxy B: median over handlers below 5%.
- F3: the high-load tercile has a lower airflow share than the low-load tercile (the tracking is tighter at high flow).

## Decision rule (fixed now)

For each check, call the catalogue's `bg` OPTIMISTIC if the measured per-equipment median is above twice `bg`, REASONABLE if between half and twice `bg`, CONSERVATIVE if below half of it.
For static, the verdict is reported separately for proxy A and proxy B and is only called if both agree.
