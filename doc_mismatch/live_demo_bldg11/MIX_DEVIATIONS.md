# Logged deviations from MIX_PROTOCOL.md (the protocol itself is untouched; its hash is in MIX_PROTOCOL.sha256)

## D1 (2026-10-11): gate G1a failed on a gate reference that Addendum 41 had already found to be wrong

**Registered outcome: NO RESULT.** The first full run of `study_mix.py` stopped on a failed gate, as the protocol requires, before any accuracy, minutes or label was computed or written
(only the gate lines were printed). G1b, G5 and the other gates passed; G1a failed.

**What failed and why.** MIX_PROTOCOL.md's G1 says "`study_tau`'s gates reproduce Addendum 30's stored per-event results and Exploratory note E2's numbers". I implemented it by calling
`study_tau.gate_g2()` and `study_tau.gate_g3()`. `gate_g2` passed (the default path reproduces Addendum 30's stored per-event results exactly, first 200 events). `gate_g3` failed: the routine at
`tau` 0.95 and `min_rate` 0.02, T3-noattr, primary cell gave 56.6 min / 81.0% against E2's 58.3 / 80.4%. This is the failure Addendum 41 already logged as a mistake in the gate's reference, not
in the code: E2's numbers come from event stream `[30, 0, 0, i]` (cell index 0), while `gate_g3` draws the primary cell's own stream (index 6); `scripts/92_tau_g3_check.py` (sha256 1611de55...)
reproduces E2's numbers exactly on E2's stream and shows the sweep's code path identical to the old one. I wrote the protocol's G1 on top of that gate without remembering the logged deviation.

**What changes.** G1a is read as `study_tau.gate_g2()` (unchanged, passes) plus the corrected E2 check of `scripts/92_tau_g3_check.py` at `min_rate` 0.02 on E2's stream (implemented in
`study_mix.gate_e2_corrected`), instead of `study_tau.gate_g3()`. The report shows the registered gate's failure, the corrected gate's result, and a banner that the numbers are reported under this
deviation and are not the registered result.

**Disclosure.** The decision to deviate was taken after seeing only the gate lines of the failed run: no result number of this study (S1, S2 or S3) had been computed or seen. Unlike Addendum 41's
deviation, it was therefore not made after reading part of the results. Nothing else in the protocol, the arms, the predictions, the bars or the labels is changed.
