# False-alarm rate of the control-system readings from real trend data (exploratory; FALSE_ALARM_NOTES.md hashed before any value was read)

Only the false-alarm side can be measured here (no labelled faults). Any fault in the data raises the measured rate, so these are upper bounds on the true rate; the per-equipment median is the robust summary.

## bas_airflow: measured airflow vs its recorded setpoint (bldg30, 1-minute data, about a year)

**NOT MEASURABLE with this data.** The recorded `Air_Flow_Setpoint` of the 99 boxes takes 1 to 8 distinct values over the year (median 4; 25 boxes exactly one, 44 at most three), where a live setpoint needs a median of at least 50. These are configured limits, not the setpoint a box tracks, so measured airflow against them says nothing about false alarms. No airflow rate is reported. (A first run without this gate printed 95% and a verdict; it was an artifact, see FALSE_ALARM_DEVIATIONS.md D1.)

No downloaded building records a live airflow setpoint, so the catalogue's 5% for `bas_airflow` has no real-data check here.

## bas_static: duct static vs a PROXY for its setpoint (no building records the setpoint)

Running samples only; abnormal = more than 20% off the proxy. A = the handler's long-run median while running (over-states if the setpoint is reset); B = median of the surrounding two hours (under-states: a persistent low static is absorbed). Catalogue assumes 3%.

| building | handlers | running samples | proxy A | proxy B |
|---|---|---|---|---|
| bldg1 | 2 | 248,669 | 27.1%, 16.0% | 1.0%, 0.1% |
| bldg8 | 1 | 127,558 | 35.1% | 0.6% |
| bldg15 | 2 | 307,070 | 26.3%, 13.3% | 0.6%, 0.6% |
| bldg40 | 2 | 376,652 | 5.1%, 6.8% | 0.2%, 0.1% |

Median over 7 handlers: proxy A 16.0%, proxy B 0.6%. Verdict (called only if both agree): A OPTIMISTIC, B CONSERVATIVE -> **NOT CALLED (the two proxies disagree)**.

### Post hoc (added after the first run): the rate against a proxy whose window grows

| window around each reading | 2 h | 6 h | 24 h | 7 days | whole record (proxy A) |
|---|---|---|---|---|---|
| median over handlers | 0.6% | 1.4% | 3.1% | 7.9% | 16.0% |
| range over handlers | 0.1% to 1.1% | 0.2% to 4.7% | 0.4% to 14.2% | 0.6% to 19.3% | 5.1% to 35.1% |

## Predictions (written before the first value was read)

- F1 (airflow pooled above 5%, median box above 5%): NOT TESTABLE (the recorded setpoint is not live; FALSE_ALARM_DEVIATIONS.md D1)
- F2 (static proxy A median above 5%, proxy B median below 5%): HELD (A 16.0%, B 0.6%)
- F3 (high-load third has a lower airflow share than the low-load third): NOT TESTABLE (same reason)
