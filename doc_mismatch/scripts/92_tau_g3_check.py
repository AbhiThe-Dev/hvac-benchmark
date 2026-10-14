"""Addendum 41, logged deviation: gate G3's reference was drawn on the wrong event stream; this is the corrected check.

Exploratory note E2's stored numbers (routine, T3-noattr: 78.1 min / 82.3% at min_rate 0.003 and 58.3 min / 80.4% at 0.02) come from `study_minrate_ext.primary_sweep`, which draws its
events from stream `[30, 0, 0, i]` (cell index 0) with the PRIMARY cell's world parameters; Addendum 41's G3 compared them with the primary cell's own stream (cell index 6), which differs by
sampling noise (56.6 min / 81.0% at 0.02). This script reproduces E2's numbers on E2's stream with both the old code path and the sweep's new one, and shows the two are identical.

  .venv/bin/python doc_mismatch/scripts/92_tau_g3_check.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from docmismatch.troubleshoot.v2 import study_joint as J  # noqa: E402
from docmismatch.troubleshoot.v2 import study_minrate as MR  # noqa: E402
from docmismatch.troubleshoot.v2 import study_tau as T  # noqa: E402
from docmismatch.troubleshoot.v2 import world2 as W  # noqa: E402

cells = J.all_cells()
pidx = next(i for i, c in enumerate(cells) if c.is_primary)
wp, bld = cells[pidx].params(), W.make_building2()
cases_all = W.make_cases(bld)
ok_all = True
for stream, label in ((0, "E2's own stream (cell index 0, primary world parameters)"), (pidx, f"the primary cell's own stream (cell index {pidx}); what G3 used")):
    events = [W.draw_event(stream, i, wp, cases_all) for i in range(1000)]
    for mr, ref in ((0.003, (78.1, 0.823)), (0.02, (58.3, 0.804))):
        old = MR.run_variant_events(T.E.EXT_ARM, mr, events, wp, bld)
        new = T.run_variant(T.E.EXT_ARM, T.BASE_TAU, mr, "tool_ticket_memo2", events, wp, bld)
        same = all(np.array_equal(old[k], new[k]) for k in ("minutes", "checks", "acc", "wc"))
        m, a = float(new["minutes"].mean()), float(new["acc"].mean())
        match = round(m, 1) == ref[0] and round(a, 3) == ref[1]
        print(f"{label}: min_rate {mr}: {m:.1f} min / {a:.1%} | E2's {ref[0]} / {ref[1]:.1%}: {'REPRODUCED' if match else 'differs'} | sweep code path identical to the old one: {same}")
        ok_all &= same
        if stream == 0:
            ok_all &= match
print("corrected G3 (plumbing reproduces E2 exactly on E2's stream; new path identical to the old):", "PASS" if ok_all else "FAIL")
