"""A confirm step by a visit to the air handler, exactly as frozen in FANCONF2_NOTES.md (read that first; this file implements it and changes nothing in it).

  .venv/bin/python doc_mismatch/live_demo_bldg11/study_fanconfirm2.py                       # the registered run; refuses to run if FANCONF2_NOTES.md changed since it was frozen
  .venv/bin/python doc_mismatch/live_demo_bldg11/study_fanconfirm2.py --smoke --out DIR     # plumbing check (4 visits per family): prints timing and gates only, never accuracy

Outputs (results/docmismatch/fanconfirm2_study/): report.md, summary.json. The Mortar Brick files must be in data_cache/ (not part of the repository); nothing here is committed or deployed.
"""
import argparse
import hashlib
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import study_fanconfirm as C  # noqa: E402
import study_fanmix as FM  # noqa: E402
import study_folding as F  # noqa: E402
import study_mix as MX  # noqa: E402
from docmismatch.troubleshoot.v1 import data as D  # noqa: E402
from docmismatch.troubleshoot.v1.engine import Obs, Question  # noqa: E402
from docmismatch.troubleshoot.v2.joint import MAX_CHECKS_PER_COMPLAINT, JointModel  # noqa: E402
from docmismatch.troubleshoot.v2.policies import PriorSession  # noqa: E402

PROTOCOL, FROZEN = HERE / "FANCONF2_NOTES.md", HERE / "FANCONF2_NOTES.sha256"
OUT = HERE.parent.parent / "results" / "docmismatch" / "fanconfirm2_study"
LS, FAN = FM.LS, FM.FAN
REAL, WORLDS, FAMILIES = FM.REAL, FM.WORLDS, FM.FAMILIES
CHECK = "ahu_visit"
OPEN_THR = 0.05
JS = {"TODAY": FM.ARMS["TODAY"], "FAN": FM.ARMS["FAN"], "FANV": FM.ARMS["FAN"], "FANO": FM.ARMS["FAN"]}
ARMS = tuple(JS)
STORED = {k: v for k, v in C.STORED.items() if k[0] in ("TODAY", "FAN")}


def run_ticket_confirm2(cases, oracle, js, confirm=True, open_thr=None):
    """`study_folding.run_ticket_v(..., "base")` step for step and, with `confirm`, one extra step per room: if the room's leading cause is fan off or low static, `ahu_visit` has not been answered for its
    handler in this visit and is available (and, with `open_thr`, the other of the two causes still has at least that probability), take it once as the room's own check; later rooms get it through the
    routine's air-handler memo; the room then continues its loop."""
    model = JointModel(cases, js)
    at, memo, low_static_seen = None, {}, set()
    guess, concluded, per_room_min, own_static, checks = [], [], [], [], 0
    asks, violations, skipped = {}, 0, 0
    for i, case in enumerate(cases):
        sess = PriorSession(case, (model.causes[i], model.marg0[i]))
        sess.at = at
        for (a, name), word in memo.items():
            if a == case.ahu:
                sess.log.append(Obs(name, case.doc, word, 0.0))
        if case.ahu in low_static_seen:
            sess.log.append(Obs("static_at_box", case.doc, "abnormal", 0.0))
        own = 0

        def ask(ck, target, i=i, case=case):
            return oracle.ask_ahu(case.ahu, ck) if ck.subject == "ahu" else oracle.ask_room(i, ck, target)

        def after(ck, word, case=case):
            if ck.subject == "ahu":
                memo[(case.ahu, ck.name)] = word
            elif ck.name == "static_at_box" and word == "abnormal":
                low_static_seen.add(case.ahu)

        def loop(own, sess=sess, ask=ask, after=after):
            while own < MAX_CHECKS_PER_COMPLAINT:
                step = sess.next_step()
                if step is None:
                    break
                if isinstance(step, Question):
                    raise RuntimeError(f"the tool asked {step.key!r}")
                ck = step.check
                word = ask(ck, step.target)
                assert word in ck.words                                         # gate G4
                sess.report(word)
                own += 1
                after(ck, word)
            return own

        own = loop(own)
        if confirm:
            ranked = sess.status()["ranked"]
            top = ranked[0][0]
            other = LS if top == FAN else FAN
            p_other = dict(ranked).get(other, 0.0)
            if top in (FAN, LS) and (case.ahu, CHECK) not in memo and (open_thr is None or p_other >= open_thr):
                if CHECK not in {c.name for c in case.checks}:
                    skipped += 1
                else:
                    ck = sess._check(CHECK)
                    if D.availability(ck, sess.view(), sess._eq(ck)).state == "unavailable" or any((o.check, o.target) == (ck.name, case.doc) for o in sess.log):
                        skipped += 1
                    else:
                        asks[case.ahu] = asks.get(case.ahu, 0) + 1
                        word = ask(ck, case.doc)
                        assert word in ck.words
                        sess.report(word, check=ck.name, target=case.doc)
                        own += 1
                        after(ck, word)
                        own = loop(own)
        st = sess.status()
        guess.append(st["ranked"][0][0])
        concluded.append(bool(st["concluded"]))
        per_room_min.append(float(sess.elapsed))
        own_static.append(any(o.check == "static_at_box" and o.minutes > 0 for o in sess.log))
        checks += own
        at = sess.at
    return dict(minutes=float(sum(per_room_min)), per_room_min=per_room_min, own_static=own_static, n_checks=checks, guess=guess, concluded=concluded, asks=asks, violations=violations, skipped=skipped)


def run_arm(arm, cl, orc):
    if arm == "FANV":
        return run_ticket_confirm2(cl, orc, JS[arm], True, None)
    if arm == "FANO":
        return run_ticket_confirm2(cl, orc, JS[arm], True, OPEN_THR)
    return F.run_ticket_v(cl, orc, JS[arm], "base")


def run_chunk(args):
    fam, bld, wi, lo, hi = args
    visits, cases, checks = FM.family_visits(fam, bld, range(lo, hi))
    a = list(WORLDS.values())[wi][1]
    out = []
    for visit in visits:
        cl = [cases[r] for r in visit["rooms"]]
        orc = MX.FamOracle(visit, cl, wi, a, checks)
        rec = {}
        for arm in ARMS:
            r = run_arm(arm, cl, orc)
            rec[arm] = dict(guess=[tuple(g) for g in r["guess"]], conc=[bool(c) for c in r["concluded"]], own=[bool(x) for x in r["own_static"]], minutes=float(r["minutes"]),
                            n_asks=sum(r.get("asks", {}).values()), max_asks=max(r.get("asks", {}).values(), default=0), violations=r.get("violations", 0))
        out.append((visit, rec, "ahu_visit" in {c.name for c in checks}))
    return args, out


def collect(results):
    by = {}
    for args, out in results:
        by.setdefault((args[0], args[1], args[2]), []).append((args[3], out))
    res = {}
    for key, chunks in by.items():
        trip = [p for _, out in sorted(chunks, key=lambda c: c[0]) for p in out]
        pairs = [(p[0], p[1]) for p in trip]
        d = {"visits": [p[0] for p in pairs], "truth": [tuple(c) for p in pairs for c in p[0]["causes"]], "seg": np.array([s for p in pairs for s in p[0]["seg"]]),
             "visit": np.array([i for i, p in enumerate(pairs) for _ in p[0]["rooms"]]), "has_check": all(p[2] for p in trip)}
        for arm in ARMS:
            g = [tuple(x) for p in pairs for x in p[1][arm]["guess"]]
            d[arm] = dict(guess=g, ok=np.array([x == t for x, t in zip(g, d["truth"])]), conc=np.array([c for p in pairs for c in p[1][arm]["conc"]]),
                          own=np.array([c for p in pairs for c in p[1][arm]["own"]]), vmin=np.array([p[1][arm]["minutes"] for p in pairs]),
                          n_asks=sum(p[1][arm]["n_asks"] for p in pairs), max_asks=max(p[1][arm]["max_asks"] for p in pairs), violations=sum(p[1][arm]["violations"] for p in pairs))
        res[key] = d
    return res


def gate_g2(n=10):
    bad, tot = 0, 0
    for fam, bld in (("A-LS", "bldg11"), ("A-FAN", "bldg15"), ("S2", "demo"), ("B", "bldg11")):
        visits, cases, checks = FM.family_visits(fam, bld, range(n))
        for visit in visits:
            cl = [cases[r] for r in visit["rooms"]]
            for wi, (wn, a) in enumerate(WORLDS.values()):
                orc = MX.FamOracle(visit, cl, wi, a, checks)
                for js in (JS["TODAY"], JS["FAN"]):
                    x, y = F.run_ticket_v(cl, orc, js, "base"), run_ticket_confirm2(cl, orc, js, False)
                    tot += 1
                    bad += not ([tuple(u) for u in x["guess"]] == [tuple(u) for u in y["guess"]] and [bool(u) for u in x["concluded"]] == [bool(u) for u in y["concluded"]] and x["minutes"] == y["minutes"])
    return bad == 0, f"the confirm replica with the step switched off equals run_ticket_v on {tot} visit-world-setting runs: {'identical' if not bad else f'{bad} DIFFER'}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    smoke = args.smoke
    if not smoke and hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() != FROZEN.read_text().split()[0]:
        sys.exit("FANCONF2_NOTES.md changed since it was frozen: refusing to run")
    out = Path(args.out) if args.out else OUT
    t0 = time.time()
    g2, g3, g4 = gate_g2(2 if smoke else 10), FM.gate_g3(smoke), FM.gate_g4()
    print(f"gates before the run ({time.time() - t0:.0f}s): G2 {g2[0]} | G3 {g3[0]} | G4 {g4[0]}", flush=True)
    step = 4 if smoke else FM.CHUNK
    tasks = []
    for fam, bld in FAMILIES:
        n = FM.n_visits(fam, smoke)
        for w, (wi, _) in WORLDS.items():
            for lo in range(0, n, step):
                tasks.append((fam, bld, wi, lo, min(lo + step, n)))
    results = []
    with ProcessPoolExecutor(max_workers=9) as ex:
        for i, r in enumerate(ex.map(run_chunk, tasks)):
            results.append(r)
            if (i + 1) % 20 == 0 or i + 1 == len(tasks):
                print(f"  {i + 1}/{len(tasks)} chunks, {time.time() - t0:.0f}s", flush=True)
    if smoke:
        print("smoke run: plumbing only, accuracy deliberately not printed")
        return
    wname = {v[0]: k for k, v in WORLDS.items()}
    res = collect([((a[0], a[1], wname[a[2]], a[3], a[4]), o) for a, o in results])
    g1, g1ok = [], True
    for (arm, fam), want in STORED.items():
        for b, (acc, mins) in want.items():
            st = C.stats(res[fam, b, "W0"], arm)
            ok = f"{st['acc']:.1f}" == f"{acc:.1f}" and f"{st['minutes']:.0f}" == f"{mins:.0f}"
            g1ok &= ok
            g1.append(f"- G1 {arm} on {fam} {b} W0 reproduces the FANMIX study: **{'PASS' if ok else 'FAIL'}** ({st['acc']:.1f}% / {st['minutes']:.0f} min; stored {acc}% / {mins})")
    must_fire = [(f, b) for f in ("A-LS", "A-FAN") for b in REAL] + [("S3", "demo")]
    fired = {k: res[k[0], k[1], "W0"]["FANV"]["n_asks"] for k in must_fire}
    g5 = all(d["has_check"] for d in res.values()) and all(v > 0 for v in fired.values()) and max(res[k][a]["max_asks"] for k in res for a in ("FANV", "FANO")) <= 1 and sum(res[k][a]["violations"] for k in res for a in ("FANV", "FANO")) == 0
    gates_ok = g1ok and g2[0] and g3[0] and g4[0] and g5
    L = ["# A confirm step by a visit to the air handler (exploratory; FANCONF2_NOTES.md hashed before any run; demos, pilot and shipped defaults untouched)", "",
         "Simulated causes and answers (the visit families are mine); real Mortar layouts for A-LS, A-FAN and B, the first demo's synthetic 3 x 8 building for S1-S4. W0 = checks as the tool assumes, W1 = every rate 25% toward 0.5. "
         "TODAY = low-static mixture 5/15/50/90%; FAN = TODAY + fan-off mixture; FANV = FAN + one visit to the air handler (`ahu_visit`: 19 minutes in the catalogue; abnormal 0.92 under fan off, 0.10 under low static) before an upstream conclusion; "
         "FANO = FANV only when the other of fan off / low static still has at least 5%. 'asks/visit' = confirm visits per visit. Nothing committed or deployed.", "", "## Gates", "", *g1,
         f"- G2 {g2[1]}: **{'PASS' if g2[0] else 'FAIL'}**", f"- G3 composition: **{'PASS' if g3[0] else 'FAIL'}** ({g3[1]})", f"- G4 {g4[1]}: **{'PASS' if g4[0] else 'FAIL'}**",
         f"- G5 `ahu_visit` in every check list; FANV asked it in every required family ({', '.join(f'{f} {b} {v}' for (f, b), v in fired.items())} confirm visits in W0); at most once per handler per visit; never after it was answered: **{'PASS' if g5 else 'FAIL'}**", ""]
    if not gates_ok:
        L += ["**REGISTERED OUTCOME: NO RESULT (a gate failed).**", ""]
    names = {"A-LS": "A-LS: 4 low-static rooms on the larger handler + 2 own-fault rooms", "A-FAN": "A-FAN: 4 fan-off rooms on the larger handler + 2 own-fault rooms", "B": "B: registered composition (50 shared / 50 local visits)",
             "S1": "S1: fan off, the model's own world (each of 8 rooms complains at 90%)", "S2": "S2: fan off, 2-4 of 8 rooms complain + 2 own-fault rooms", "S3": "S3: low static, 2-4 of 8 rooms + 2 own-fault rooms", "S4": "S4: 6 own-fault rooms, no shared cause"}
    for fam in ("A-LS", "A-FAN", "B", "S1", "S2", "S3", "S4"):
        L += [f"## {names[fam]}", "", "| building | answers | arm | accuracy | shared-cause rooms | minutes / visit | asks / visit | wrong and confident | with the hedge | false fan-off | fan-off rooms called fan off | vs TODAY: accuracy (95% CI); minutes (95% CI) |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for f_, bld in [x for x in FAMILIES if x[0] == fam]:
            for w in WORLDS:
                d = res[fam, bld, w]
                for arm in ARMS:
                    s = C.stats(d, arm)
                    dd = ""
                    if arm != "TODAY":
                        g, gci, dm, dmci = FM.paired(d, arm, "TODAY")
                        dd = f"{g:+.1f} ({gci[0]:+.1f}, {gci[1]:+.1f}); {dm:+.0f} ({dmci[0]:+.0f}, {dmci[1]:+.0f})"
                    L.append(f"| {bld} | {w} | {arm} | {s['acc']:.1f}% | {s['shared']:.1f}% | {s['minutes']:.0f} | {d[arm]['n_asks'] / len(d['visits']):.2f} | {s['wc']:.1f}% | {s['wc_h']:.1f}% | {s['false_fan']:.1f}% | "
                             + (f"{s['fan_right']:.0f}%" if fam in ("A-FAN", "S1", "S2") else "-") + f" | {dd} |")
        L.append("")
    S_ = lambda fam, b, arm, w="W0": C.stats(res[fam, b, w], arm)                          # noqa: E731
    P_ = lambda fam, b, arm, w="W0": FM.paired(res[fam, b, w], arm, "TODAY")               # noqa: E731

    def judge(arm):
        q = {}
        v1 = {b: (S_("A-LS", b, arm)["false_fan"], P_("A-LS", b, arm)[0]) for b in REAL}
        q["V1"] = (all(v[0] <= 2 and abs(v[1]) <= 3 for v in v1.values()), ", ".join(f"{b} false {v[0]:.1f}%, {v[1]:+.1f}" for b, v in v1.items()))
        v2 = {b: (S_("A-FAN", b, arm)["shared"], S_("A-FAN", b, "FAN")["shared"]) for b in REAL}
        q["V2"] = (all(v[0] >= v[1] - 2 for v in v2.values()), ", ".join(f"{b} {v[0]:.1f}% vs FAN {v[1]:.1f}%" for b, v in v2.items()))
        v3 = {(f_, b): (P_(f_, b, arm)[0], S_(f_, b, arm)["wc"] - S_(f_, b, "TODAY")["wc"]) for f_, b in (("B", "bldg15"), ("B", "bldg11"), ("S3", "demo"), ("S4", "demo"))}
        q["V3"] = (all(abs(v[0]) <= 2 and v[1] <= 1 for v in v3.values()), ", ".join(f"{f_} {b} {v[0]:+.1f}, wc {v[1]:+.1f}" for (f_, b), v in v3.items()))
        v4 = P_("S1", "demo", arm)
        q["V4"] = (abs(v4[0]) <= 3, f"{v4[0]:+.1f} ({v4[1][0]:+.1f}, {v4[1][1]:+.1f}); minutes {v4[2]:+.0f} on {S_('S1', 'demo', 'TODAY')['minutes']:.0f}")
        v5 = {(f_, b): (S_(f_, b, arm)["minutes"] - S_(f_, b, "TODAY")["minutes"], S_(f_, b, "TODAY")["minutes"]) for f_, b in [("A-LS", x) for x in REAL] + [("B", "bldg15"), ("B", "bldg11")]}
        q["V5"] = (all(dm <= 0.10 * base for dm, base in v5.values()), ", ".join(f"{f_} {b} {dm:+.0f} ({100 * dm / base:+.0f}%)" for (f_, b), (dm, base) in v5.items()))
        return q

    qv, qo = judge("FANV"), judge("FANO")
    ff = {a: np.mean([S_("A-LS", b, a)["false_fan"] for b in REAL]) for a in ("FAN", "FANV", "FANO")}
    mm = {a: np.mean([S_("A-LS", b, a)["minutes"] for b in REAL]) for a in ("FAN", "FANV", "FANO")}
    red = (ff["FAN"] - ff["FANO"]) / (ff["FAN"] - ff["FANV"]) if ff["FAN"] > ff["FANV"] else float("nan")
    cost = (mm["FANO"] - mm["FAN"]) / (mm["FANV"] - mm["FAN"]) if mm["FANV"] > mm["FAN"] else float("nan")
    qo["V6"] = (bool(red >= 0.7 and cost <= 0.7), f"false fan-off FAN {ff['FAN']:.1f}%, FANV {ff['FANV']:.1f}%, FANO {ff['FANO']:.1f}% (FANO removes {100 * red:.0f}% as many as FANV); extra minutes over FAN: FANV {mm['FANV'] - mm['FAN']:+.0f}, FANO {mm['FANO'] - mm['FAN']:+.0f} ({100 * cost:.0f}% of FANV's)")
    text = {"V1": "A-LS: false fan-off at most 2% and accuracy within 3 points of TODAY", "V2": "A-FAN: fan-off rooms at least FAN's minus 2", "V3": "B, S3, S4: within 2 points of TODAY, wrong-and-confident at most +1",
            "V4": "S1: within 3 points of TODAY", "V5": "minutes within +10% of TODAY in A-LS and B", "V6": "FANO removes at least 70% as many false calls as FANV at no more than 70% of its extra minutes"}
    L += ["## Predictions for FANV (written before any run)", ""] + [f"- {k} ({text[k]}): **{'HELD' if qv[k][0] else 'FAILED'}** ({qv[k][1]})" for k in sorted(qv)] + [""]
    L += ["## The same predictions for FANO (V1-V5), and V6", ""] + [f"- {k}: **{'HELD' if qo[k][0] else 'FAILED'}** ({qo[k][1]})" for k in sorted(qo)] + [""]

    def label(q, extra=False):
        if not gates_ok:
            return "NO RESULT (a gate failed)"
        need = ["V1", "V2", "V3", "V4", "V5"] + (["V6"] if extra else [])
        if all(q[k][0] for k in need):
            return "WORTH ADOPTING WITH THE FAN-OFF MIXTURE"
        if q["V1"][0] and q["V2"][0] and not q["V5"][0] and all(q[k][0] for k in ("V3", "V4")):
            return "TRADES TIME FOR SAFETY"
        return "NOT WORTH IT AS TESTED (" + ", ".join(k for k in need if not q[k][0]) + " failed)"
    L += ["## Decision rule applied", "", f"- FANV: **{label(qv)}**", f"- FANO: **{label(qo, True)}**", ""]
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text("\n".join(L))
    (out / "summary.json").write_text(json.dumps(dict(gates_ok=bool(gates_ok), fanv=label(qv), fano=label(qo, True), fanv_q={k: bool(v[0]) for k, v in qv.items()}, fano_q={k: bool(v[0]) for k, v in qo.items()},
                                                  protocol_sha256=hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()), indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    main()
