"""Single evaluation entry point of the readiness study (PREREGISTRATION.md).

  20_final_eval.py --freeze                          write results/docmismatch/active/frozen/{config.json,manifest.json} (SHA-256 of src/docmismatch/active/*.py)
  20_final_eval.py --data real-dev-nested            leave-one-SEASON-out over the 30 real DEV days (every fold fully nested)
  20_final_eval.py --data sim-dev-loto               leave-one-TOPOLOGY-out over the simulated DEV topologies
  20_final_eval.py --data real-sealed [--rehearsal]  fit the frozen configuration on ALL real DEV data, score the SEALED real days ONCE
  20_final_eval.py --data sim-sealed  [--rehearsal]  fit on ALL sim DEV topologies, score the SEALED simulated topologies ONCE
  20_final_eval.py --data rehearsal                  real-sealed --rehearsal AND sim-sealed --rehearsal (a DEV season / DEV topology as pseudo-sealed, config refit WITHOUT it)

Sealed modes: refuse unless the frozen manifest hash matches the source tree; load data only through the ledgered loaders (sealed_access.log); write a
one-shot marker and refuse to run a second time for the same frozen configuration. With --rehearsal nothing sealed is loaded.
Outputs: results/docmismatch/active/final/<data>[_rehearsal].{md,json} (C1-C4 with >=1000-resample cluster bootstrap for every layer: none | legacy | new).
Options: --procs N (parallel workers), --layers none,legacy,new, --holdout UNIT (rehearsal unit), --variant V (DEV modes only), --nboot N.
"""
import argparse, copy, hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
from docmismatch.active import readiness as R
from docmismatch.active import evalkit as K

OUT = R.ACT / "final"


def freeze(cfg):
    R.FROZEN.mkdir(parents=True, exist_ok=True)
    cf = R.FROZEN / "config.json"
    cf.write_text(json.dumps(cfg, indent=1, sort_keys=True))
    man = dict(created=time.strftime("%Y-%m-%d %H:%M:%S"), code=R.code_manifest(), config_sha256=hashlib.sha256(cf.read_bytes()).hexdigest(),
               preregistration_sha256=hashlib.sha256((ROOT / "PREREGISTRATION.md").read_bytes()).hexdigest(), sim_manifest=R.sim_manifest(),
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (R.FROZEN / "manifest.json").write_text(json.dumps(man, indent=1, sort_keys=True, default=str))
    print("frozen:", cf, "\n", json.dumps({k: v for k, v in man.items() if k != 'code'}, default=str)[:400])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", choices=["real-sealed", "sim-sealed", "real-dev-nested", "sim-dev-loto", "rehearsal"])
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--rehearsal", action="store_true")
    ap.add_argument("--holdout", default=None)
    ap.add_argument("--procs", type=int, default=1)
    ap.add_argument("--layers", default="none,legacy,new")
    ap.add_argument("--variant", default=None)
    ap.add_argument("--nboot", type=int, default=None)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    if a.freeze:
        cfg = copy.deepcopy(R.DEFAULT_CFG)
        if a.variant:
            cfg["variant"] = a.variant
        return freeze(cfg)
    if not a.data:
        ap.error("--data or --freeze required")
    layers = tuple(a.layers.split(","))
    sealed_mode = a.data in ("real-sealed", "sim-sealed") and not a.rehearsal
    if a.data == "rehearsal":
        for d in ("real-sealed", "sim-sealed"):
            sys.argv = [sys.argv[0], "--data", d, "--rehearsal", "--procs", str(a.procs), "--layers", a.layers] + (["--nboot", str(a.nboot)] if a.nboot else [])
            main()
        return
    if sealed_mode:
        cfg = R.frozen_check()
        marker = R.FROZEN / f"sealed_run_{a.data}.done"
        if marker.exists():
            raise SystemExit(f"REFUSED: {a.data} was already scored once with this frozen configuration ({marker}); see PREREGISTRATION.md section 6")
    else:
        try:
            cfg = R.frozen_check() if a.rehearsal else copy.deepcopy(R.DEFAULT_CFG)
        except SystemExit as e:
            print("WARNING (rehearsal on an unfrozen tree):", e)
            cfg = copy.deepcopy(R.DEFAULT_CFG)
        if a.variant and not a.rehearsal:
            cfg["variant"] = a.variant
    if a.nboot:
        cfg["boot"] = a.nboot
    assert cfg["boot"] >= 1000, "pre-registration requires >= 1000 bootstrap resamples"
    t0 = time.time()
    kind = "real" if a.data.startswith("real") else "sim"
    if a.data == "real-dev-nested":
        rows, info = R.run_nested("real", cfg, procs=a.procs, layers=layers)
    elif a.data == "sim-dev-loto":
        rows, info = R.run_nested("sim", cfg, procs=a.procs, layers=layers)
    elif a.data == "real-sealed":
        hold = int(a.holdout) if (a.rehearsal and a.holdout is not None) else (1 if a.rehearsal else None)
        rows, info = R.run_sealed_real(cfg, procs=a.procs, layers=layers, rehearsal_unit=hold)
    else:
        hold = a.holdout if (a.rehearsal and a.holdout) else ("vav_2ahu_2loops" if a.rehearsal else None)
        rows, info = R.run_sealed_sim(cfg, procs=a.procs, layers=layers, rehearsal_unit=hold)
    primary = "day" if kind == "real" else cfg["sim_primary"]
    ev = K.evaluate(rows, primary, nboot=cfg["boot"], seed=0)
    tag = a.data + ("_rehearsal" if a.rehearsal else "") + (f"_{a.tag}" if a.tag else "")
    OUT.mkdir(parents=True, exist_ok=True)
    ne = len({(r["ep"], r["rep"]) for r in rows if r["layer"] == layers[0] and r["policy"] == "active" and r["setting"] == primary})
    nc = len({r["cluster"] for r in rows})
    head = (f"{tag}: {ne} episodes ({nc} clusters = {'days' if kind == 'real' else 'event groups'}); config variant={cfg['variant']}, tau={cfg['tau']}, primary setting `{primary}`; "
            f"elapsed {time.time()-t0:.0f}s; info={json.dumps(K.to_jsonable(info), default=str)[:400]}")
    md = K.to_markdown(ev, f"Readiness evaluation: {tag}", layers_to_show=[l for l in layers if l in ev])
    (OUT / f"{tag}.md").write_text(head + "\n\n" + md)
    (OUT / f"{tag}.json").write_text(json.dumps(K.to_jsonable(dict(config=cfg, info=info, eval=ev)), indent=1))
    print(head)
    for lay in layers:
        if lay not in ev:
            continue
        o = ev[lay]
        c2 = o["C2"]["all"]["all"]
        print(f"[{lay}] C2 overall {c2['status']} acc={K.fmt(c2['acc'])} cov={K.fmt(c2['coverage'])} | C3 {o['C3'].get('status')} | C4 {o['C4']['status']} | C1 " +
              ", ".join(f"{b}:{v.get('status','n/a')}" for b, v in o["C1"].items()))
    if sealed_mode:
        (R.FROZEN / f"sealed_run_{a.data}.done").write_text(time.strftime("%Y-%m-%d %H:%M:%S") + "\n")


if __name__ == "__main__":
    main()
