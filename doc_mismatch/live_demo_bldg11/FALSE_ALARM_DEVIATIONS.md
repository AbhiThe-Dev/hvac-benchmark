# Deviations from FALSE_ALARM_NOTES.md (logged before the corrected run)

## D1: the airflow "setpoint" in bldg30 is not a live setpoint; the airflow measurement is not possible with this data

What was seen: the first run of `measure_false_alarm.py` (as specified in the notes) printed, for `bas_airflow`, 95.1% of eligible samples outside +-10% of the recorded setpoint (median box 97.7%, 100% of
boxes above the catalogue's 5%) and the verdict OPTIMISTIC. That output was written to `results/docmismatch/false_alarm/report.md` and is wrong as a finding.

Why it is wrong (found by a data-validity check, no rate computed): the stream `Air_Flow_Setpoint` of each of the 99 boxes takes between 1 and 8 distinct values over a year (25 boxes exactly 1, median 4) and changes in
about 0.005% of consecutive samples. A VAV box's live airflow setpoint follows zone demand and changes continuously, so these streams are configured limits or schedule levels (for example a maximum), not the setpoint
the box is tracking. Measured airflow against a constant is not a tracking error, so the 95% says nothing about false alarms. The notes' census (metadata only) could not see this: it showed the class, not the values.

What changed, in the script only: a validity gate. The airflow measurement is reported only if the median number of distinct setpoint values per box is at least 50 (a live setpoint); otherwise the report says
NOT MEASURABLE, shows the gate's numbers and computes no airflow rate. Predictions F1 and F3 become NOT TESTABLE. The static measure, the decision rule and F2 are unchanged. The first-run numbers above are kept
here for transparency only; they are not a result.

The notes file is not edited (its hash stands).
