# Deviations from LBNL_PFPU_NOTES.md (logged before the corrected run)

## D1: the fault is in the SOUTH box, not the west box the documentation names

What was seen: the first run measured the west box as the notes specified. Every hit rate came out exactly 0.00 (including a damper stuck fully closed), which is not credible. The per-box table of the same run
(printed to find the cause) showed that the west box was never flagged while the SOUTH box was flagged in every damper-stuck and airflow-bias file (about 100%) and in the stuck-closed reheat file (0.51).
That outcome table was therefore seen BEFORE the box was corrected; the first-run west-box numbers are not a result.

Independent identification of the faulted box (no check rate involved): in `PFPU_VAVDMPRStuck_0%.csv` and `PFPU_VAVDMPRStuck_100%.csv` the damper position of box S is exactly constant in Operate mode
(0.0 and 1.0, standard deviation 0) while the other three boxes keep moving (standard deviation 0.01 to 0.05); in the fault-free file all four move. The documentation's statement that the fault is imposed in the
west box (variables followed by `_W`) does not match the files.

What changed, in the script only: the faulted box is found at run time from that footprint (the box whose damper position is constant in both stuck-damper files, asserted to be the same single box) and used in place of "W";
the healthy boxes are the other three. The checks, thresholds, mapping, sampling, decision rule and predictions P1-P5 are unchanged; the predictions are judged on the corrected box.

Added after seeing the per-box table, labelled post hoc in the report: for `bas_reheat`, a looser reading that counts any |valve position - command| > 0.10 whether or not heat is called for (a valve stuck open while no heat is called for is "not following its command" but not
"heat called for and not responding"). It is a sensitivity, not part of the verdict.
