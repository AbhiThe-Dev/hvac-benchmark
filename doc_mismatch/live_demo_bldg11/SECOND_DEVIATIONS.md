# Deviations from SECOND_NOTES.md (logged before the corrected run)

## D1: gate G1 compared a rounded reference with a tolerance equal to the rounding half-width

What was seen: the first run reported G1 FAIL for the two SHIPPED arms (W0 and W1) and **REGISTERED OUTCOME: NO RESULT**, with the new harness printing exactly the reference values (W0 shipped 23.8% / 332 min against the earlier 23.8% / 332; W1 shipped 11.2% / 303 against 11.2% / 303). The two mixed arms passed.
Why: the earlier run (`demo_composition.py`) printed accuracies to one decimal. 285 right rooms of 1200 is exactly 23.75% and 135 of 1200 exactly 11.25%; the gate asked for |new - 23.8| <= 0.05, and |23.75 - 23.8| = 0.0500000000000007 in floating point, so a reproduction to the last digit failed by arithmetic. The harness itself was not at fault.
What changed, in the script only: G1 now compares the new numbers rounded the way the reference was printed (accuracy to one decimal, minutes to a whole number) with equality. Nothing else changed; the first run's other numbers (Scenario A and B) were seen before this correction and are identical in the corrected run.
