# Checkpoint (written by the parent session, 2026-09-21 ~15:02 CDT) — work paused because the user closed their laptop

## State
* Protocol: `doc_mismatch/PREREGISTRATION.md` (binding). DEV real = 30 days (baseline + Inc_Eco), SEALED real = 32 days (OA_damper + SA_bias), sealed sim = `seal_S1..S4`. Nothing sealed has been loaded: `results/docmismatch/active/sealed_access.log` does not exist.
* Data added: `data_cache/timeseries/rtu_faults/` (48 ORNL fault-run days, CC BY 4.0, provenance + license note in `data_cache/timeseries/LICENSES.md`). Loaders: `src/docmismatch/active/real_data.py`.
* Sim expansion finished (dev_E..H, seal_S1..S4; `doc_mismatch/sim_expansion_report.md`, manifest `results/docmismatch/active/sim_manifest.json`; 51 tests passed at that point).
* Modelling agent (id a65094c4f2481df81, "Build calibrated reliability and abstention") was STOPPED mid-run at the user's request without having written its own checkpoint. Its code edits are on disk in `src/docmismatch/active/` and `scripts/` (incl. `scripts/20_final_eval.py`); it had a dev evaluation running (`scripts/20_final_eval.py --data real-dev-nested`) that was killed, so its partial output is incomplete and must be rerun.
## To resume
1. Resume the modelling agent with SendMessage to `a65094c4f2481df81` (a send resumes it from its transcript): ask it to write `doc_mismatch/CHECKPOINT_modeling.md` first, re-run the killed dev job, and continue toward the frozen configuration + `scripts/20_final_eval.py`.
2. Before any sealed evaluation: check the tests (`cd doc_mismatch && ../.venv/bin/python -m pytest tests -q`), the frozen manifest under `results/docmismatch/active/frozen/`, and that `sealed_access.log` is empty/absent. Then run the sealed evaluation exactly once per pre-registration.
