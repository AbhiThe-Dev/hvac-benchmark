"""Case-level detector (S-C) study: does DR change transfer, with / without the pretrained encoder (`results/pretrain/encoder`)?

Arms train `classify.train_predict` on their own buildings' cases (hard + clean); test cases come from the blind test suites under a given telemetry.
Variants: evidence_only, ev+scratch_finetuned, ev+pretrained_frozen, ev+pretrained_finetuned (same head, same recipe; identical splits for every variant).
Unseen season: training cases whose evidence window is in the removed season are dropped; the test cases scored are those in that season.
"""

from __future__ import annotations

import multiprocessing as mp
import pickle
from pathlib import Path

import numpy as np

from ..classify import make_split, prepare, train_predict
from ..encoder_io import EncoderKit
from ..active.pools import SEASON_OF_WINDOW
from .pools import DR_DIR, sensor_setting
from .verifier_eval import cases_for

VARIANTS = ("evidence_only", "ev+scratch_finetuned", "ev+pretrained_frozen", "ev+pretrained_finetuned")
OUT = DR_DIR / "classifier"
_KIT = None
_DATA = None


def tagged(cases: list[dict], tel: str) -> list[dict]:
    """copies of `cases` with the telemetry setting of their building attached; case_id suffixed by telemetry so one data dict can hold several"""
    out = []
    for c in cases:
        d = dict(c)
        d["sensor"] = sensor_setting(c["topology_id"], tel)
        d["telemetry"] = tel
        d["base_case_id"] = c["case_id"]
        d["case_id"] = f"{c['case_id']}@{tel}"
        out.append(d)
    return out


def _prep_init():
    global _KIT
    import torch
    torch.set_num_threads(1)
    _KIT = EncoderKit()


def _prep_chunk(chunk):
    return prepare(chunk, _KIT, zero_shot=False, log=lambda *a, **k: None)


def prepare_parallel(cases: list[dict], procs: int, chunk: int = 24) -> dict:
    chunks = [cases[i:i + chunk] for i in range(0, len(cases), chunk)]
    out = {}
    with mp.get_context("spawn").Pool(procs, initializer=_prep_init) as P:
        for r in P.imap_unordered(_prep_chunk, chunks):
            out.update(r)
    return out


def _init(path):
    global _KIT, _DATA
    import torch
    torch.set_num_threads(1)
    _KIT = EncoderKit()
    _DATA = pickle.load(open(path, "rb"))


def _task(t):
    key, variant, seed, train_ids, score_ids = t
    return key, variant, seed, train_predict(variant, seed, train_ids, score_ids, _DATA, _KIT)


def run_tasks(tasks: list, data_pickle: Path, procs: int) -> dict:
    out = {}
    with mp.get_context("spawn").Pool(procs, initializer=_init, initargs=(str(data_pickle),)) as P:
        for key, v, s, sc in P.imap_unordered(_task, tasks, chunksize=1):
            out[(key, v, s)] = sc
    return out


def season_of(c: dict) -> int:
    return SEASON_OF_WINDOW[c["evidence_window"]]
