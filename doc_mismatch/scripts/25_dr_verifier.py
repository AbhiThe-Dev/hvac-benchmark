"""S-V evaluation of the DR study (see PREREGISTRATION_DR.md sec 4/6). One cached pickle of decision rows per (arm, fold).

  physics_pipeline/.venv/bin/python doc_mismatch/scripts/25_dr_verifier.py --arms baseline,noise_only,regime,full,full_x3 --folds seen,unseen,days --procs 9 [--policies active,random] [--suites T1_in_range,...] [--dev]
--dev: leave-one-training-building-out sanity on the TRAINING buildings only (no test building touched); writes verifier_dev/.
"""
import json, pickle, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active import readiness as RD  # noqa: E402
from docmismatch.dr import verifier_eval as V  # noqa: E402

arg = lambda k, d: (sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d)  # noqa: E731
ARMS = arg("--arms", "baseline,noise_only,regime,full,full_x3").split(",")
FOLDS = arg("--folds", "seen,unseen,days").split(",")
PROCS = int(arg("--procs", "1"))
POL = tuple(arg("--policies", "active,random").split(","))
DEV = "--dev" in sys.argv
SUITES = arg("--suites", "T1_in_range,T2_regime,T3_control,T4_topology,T5_climate,T6_compound").split(",")
PRIMARY_TEL = "estimated"
OTHER_TEL = ("legacy", "wide", "wide_distractors")


def main():
    cfg = V.make_cfg(POL)
    ids = V.spec_ids()
    A = V.arms()
    out_dir = V.OUT if not DEV else V.OUT.parent / "verifier_dev"
    out_dir.mkdir(parents=True, exist_ok=True)
    for arm in ARMS:
        train = A[arm]["train"]
        tel = A[arm]["tel"]
        tcases = V.cases_for(train)
        for fold in FOLDS:
            variants = [("seen", None), ] if fold == "seen" else [(f"unseen_s{s}", s) for s in range(4)] if fold == "unseen" else [("days", None)]
            for name, s in variants:
                f = out_dir / f"rows_{arm}_{name}.pkl"
                if f.exists():
                    print("cached", f.name, flush=True)
                    continue
                t0 = time.time()
                if DEV:  # sanity: hold out each training building in turn is what the inner records already do; here just score the training buildings' odd windows
                    test_sets = {}
                elif fold == "days":
                    test_sets = {}
                else:
                    test_sets = {}
                pools = {t: {r: V.load_pool(t, r, tel) for r in V.REPS} for t in train}
                if fold == "days":
                    kind = V.DRKind(cfg, train, pools, tcases, train_parity=0, test_parity=1)
                    eps, ov = V.test_episodes(train, tel, tcases)
                    test_sets = {"train_bldgs|days": eps}
                else:
                    kind = V.DRKind(cfg, train, pools, tcases, drop_season=s, only_season=s)
                    ov = {}
                    if not DEV:
                        tels = [PRIMARY_TEL] + (list(OTHER_TEL) if fold == "seen" else [])
                        for su in SUITES:
                            for te in tels:
                                eps, o = V.test_episodes(ids[su], te, V.cases_for(ids[su]))
                                test_sets[f"{su}|{te}"] = eps
                                ov.update({f"{su}|{te}|{k}": v for k, v in o.items()})
                print(f"[{arm}/{name}] train={len(train)} bldgs, test sets={len(test_sets)}, eps={sum(len(v) for v in test_sets.values())}", flush=True)
                if not test_sets:
                    continue
                fold_rec = V.run_fold(kind, cfg, train, test_sets, PROCS)
                rows = RD.apply_layers(fold_rec, cfg, layers=("none", "new"))
                f.write_bytes(pickle.dumps(dict(rows=rows, beta=fold_rec["beta"], overlap=ov, arm=arm, fold=name, cfg=cfg, n_inner=len(fold_rec["inner"]), n_outer=len(fold_rec["outer"]))))
                print(f"[{arm}/{name}] done {time.time() - t0:.0f}s rows={len(rows)}", flush=True)


main()
