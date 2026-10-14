"""The scripted world of the bldg11 demo: given the scripted truth, what does each check read?

The rule is deliberately plain and is NOT a measurement of anything: a check reads POSITIVE (abnormal / yes) exactly when the catalogue's own probability of a positive reading under the
scripted cause is at least one half. So the world answers the way the tool believes the checks behave. That makes the tool look as good as it can look on this script, which is the point of a
demo and also its limit: it cannot show the tool being fooled by a noisy reading. Noisy readings are what a simulation of many visits is for, not this walk-through.
"""

from __future__ import annotations

import json
from pathlib import Path

from docmismatch.troubleshoot.v1 import catalogue as K
from docmismatch.troubleshoot.v1.engine import CaseV1

SCENARIO = Path(__file__).with_name("scenario.json")


def load_scenario(path: Path = SCENARIO) -> dict:
    return json.loads(path.read_text())


def truth_cause(truth: str) -> tuple:
    """'low_static' -> ('low_static',);  'wrong:VAVRM5503' -> ('wrong', 'VAVRM5503')"""
    return tuple(truth.split(":")) if ":" in truth else (truth,)


class ScriptedWorld:
    def __init__(self, scenario: dict, cases: list[CaseV1]):
        self.scenario, self.cases = scenario, cases
        self.causes = [truth_cause(c["truth"]) for c in scenario["complaints"]]
        self.ahu_state = dict(scenario["ahu_truth"])
        self.context = dict(scenario["context"])

    def room(self, i: int, ck: K.CheckV1, target: str) -> str:
        """What check `ck` on `target` reads for complaint `i`."""
        p = K.p_pos(ck, self.causes[i], target, self.cases[i].doc)
        return ck.words[0] if p >= 0.5 else ck.words[1]

    def ahu(self, ahu_id: str, ck: K.CheckV1) -> str:
        """What an air-handler check reads: the catalogue's detection level for the scripted state of that air handler (the false-alarm rate when it is fine)."""
        state = self.ahu_state.get(ahu_id, "ok")
        p = ck.bg if state == "ok" else ck.detects.get(state, ck.bg)
        return ck.words[0] if p >= 0.5 else ck.words[1]

    def answer(self, i: int, ck: K.CheckV1, target: str) -> str:
        return self.ahu(self.cases[i].ahu, ck) if ck.subject == "ahu" else self.room(i, ck, target)
