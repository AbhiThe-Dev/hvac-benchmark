"""Downstream detector: per-documented-edge logit -> case score = max edge logit.

All variants share the same MLP head and training recipe; they differ only in
what feeds it (see VARIANTS). "Pretrained" = results/pretrain/encoder;
"scratch"/"random" = identical architecture and vocabulary, random init.
"""

from __future__ import annotations

import hashlib
import json
import os
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn

from .data import SLOT_NAMES, load_base
from .encoder_io import EncoderKit, edge_z, frozen_features, row_indices, zero_shot_scores
from .features import FEATURE_NAMES, N_FEATURES, case_doc, case_rows
from .rules import true_doc

N_RAND_SEEDS = 5
STRUCT_COLS = [i for i, n in enumerate(FEATURE_NAMES) if n.startswith("slot=") or n in ("has_par_alt", "has_child_alt", "extra_owner", "card_violation", "orphan_slot")]

VARIANTS: dict[str, dict] = {
    "evidence_only": dict(ev=True, z=None),
    "struct_only": dict(ev=False, z=None),
    "struct+random_frozen": dict(ev=False, z="frozen_rand"),
    "struct+pretrained_frozen": dict(ev=False, z="frozen_pre"),
    "struct+scratch_finetuned": dict(ev=False, z="ft_scratch"),
    "struct+pretrained_finetuned": dict(ev=False, z="ft_pre"),
    "ev+random_frozen": dict(ev=True, z="frozen_rand"),
    "ev+pretrained_frozen": dict(ev=True, z="frozen_pre"),
    "ev+scratch_finetuned": dict(ev=True, z="ft_scratch"),
    "ev+pretrained_finetuned": dict(ev=True, z="ft_pre"),
}
FROZEN_Z = {"frozen_pre", "frozen_rand"}
# sensitivity run: drop the absolute log-error columns, keep only scale-free margins/ranks/closure
SCALEFREE = os.environ.get("DOCMISMATCH_FEATURES") == "scalefree"
SCALEFREE_COLS = [i for i, n in enumerate(FEATURE_NAMES) if not n.endswith("_logerr")]


@dataclass
class CaseData:
    case: dict
    X: np.ndarray
    y: np.ndarray
    kinds: list[str]
    slots: list[str]
    ex: object  # GraphExample
    idx: tuple  # (src, dst, rel, ok) tensors
    Zpre: np.ndarray | None = None
    Zrand: dict | None = None  # seed -> array
    zs_present: np.ndarray | None = None
    zs_masked: np.ndarray | None = None


def prepare(cases: list[dict], kit: EncoderKit, zero_shot: bool = True, log=print) -> dict[str, CaseData]:
    bases = {}
    out = {}
    rand_models = {s: kit.fresh(1000 + s) for s in range(N_RAND_SEEDS)}
    for i, c in enumerate(cases):
        b = bases.setdefault(c["topology_id"], load_base(c["topology_id"]))
        rows = case_rows(b, c)
        ex = kit.example(b, case_doc(b, c), c["case_id"])
        idx = row_indices(ex, rows)
        cd = CaseData(c, np.stack([r["x"] for r in rows]), np.array([r["y"] for r in rows], dtype=np.float32),
                      [r["kind"] for r in rows], [r["slot"] for r in rows], ex, idx)
        cd.Zpre = frozen_features(kit.pretrained, ex, rows).astype(np.float32)
        cd.Zrand = {s: frozen_features(m, ex, rows).astype(np.float32) for s, m in rand_models.items()}
        if zero_shot:
            cd.zs_present, cd.zs_masked = zero_shot_scores(kit.pretrained, ex, rows)
        out[c["case_id"]] = cd
        if (i + 1) % 30 == 0:
            log(f"  prepared {i + 1}/{len(cases)}")
    return out


class _Rows:
    """View of a CaseData restricted to supported rows (for standardization statistics)."""

    def __init__(self, cd, idx):
        self.X = cd.X[idx]


class Head(nn.Module):
    def __init__(self, n_x: int, zdim: int, proj: int = 16, hidden: int = 64, drop: float = 0.25):
        super().__init__()
        self.zdim = zdim
        if zdim:
            self.norm = nn.LayerNorm(zdim)
            self.proj = nn.Sequential(nn.Dropout(0.2), nn.Linear(zdim, proj), nn.ReLU())
        self.mlp = nn.Sequential(nn.Linear(n_x + (proj if zdim else 0), hidden), nn.ReLU(), nn.Dropout(drop), nn.Linear(hidden, 1))

    def forward(self, x, z=None):
        if self.zdim:
            x = torch.cat([x, self.proj(self.norm(z))], dim=1)
        return self.mlp(x).squeeze(-1)


CLIP = os.environ.get("DM_CLIP", "1") == "1"      # variance floor + clipping of standardized inputs
SUPPORT_MASK = os.environ.get("DM_SUPPORT", "1") == "1"
MIN_REGIME_SUPPORT = 10  # training rows needed for a (slot, has_par_alt, has_child_alt) feature regime to be trusted
_IA = FEATURE_NAMES.index("has_par_alt")
_IC = FEATURE_NAMES.index("has_child_alt")


def regime_support(train_ids: list[str], data: dict[str, "CaseData"]) -> set:
    """Feature regimes a head may be scored on. A row's margin/rank features only mean something in the regime
    (slot, has a same-class alternative owner?, has a same-class alternative member?) it was trained in. If a regime
    never occurs (or almost never) in training, every margin feature there was constant, and the head extrapolates
    arbitrarily - in either direction (test rows WITH alternatives where training had none, or WITHOUT where
    training always had some). Rows in unsupported regimes are dropped from training and from scoring."""
    if not SUPPORT_MASK:
        return {"ALL"}
    cnt: dict = {}
    for i in train_ids:
        cd = data[i]
        for sl, x, k in zip(cd.slots, cd.X, cd.kinds):
            if k == "edge":
                key = (sl, int(x[_IA] > 0), int(x[_IC] > 0))
                cnt[key] = cnt.get(key, 0) + 1
    return {k for k, n in cnt.items() if n >= MIN_REGIME_SUPPORT}


def row_keep(cd: "CaseData", sup: set) -> np.ndarray:
    if "ALL" in sup:
        return np.arange(len(cd.slots))
    slots_ok = {k[0] for k in sup}
    out = []
    for i, (sl, x, k) in enumerate(zip(cd.slots, cd.X, cd.kinds)):
        ok = (sl, int(x[_IA] > 0), int(x[_IC] > 0)) in sup if k == "edge" else sl in slots_ok
        if ok:
            out.append(i)
    return np.array(out, dtype=np.int64)


def unsupported_positive(cd: "CaseData", sup: set) -> bool:
    """A corrupted edge lives in a regime the head was not trained on -> case is not scorable for this fold."""
    kept = set(row_keep(cd, sup).tolist())
    return any(y > 0 and i not in kept for i, y in enumerate(cd.y))


def _stats(cds: list[CaseData], cols: list[int]):
    X = np.concatenate([cd.X[:, cols] for cd in cds])
    # v1 floored sd at 1e-3: a column that is constant in training but non-zero at test became ~1000 sigma
    return X.mean(0), np.maximum(X.std(0), 0.1 if CLIP else 1e-3)


def train_predict(variant: str, seed: int, train_ids: list[str], score_ids: list[str], data: dict[str, CaseData], kit: EncoderKit,
                  epochs_frozen: int = 60, epochs_ft: int = 25) -> dict[str, float]:
    torch.set_num_threads(1)
    spec = VARIANTS[variant]
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    cols = (SCALEFREE_COLS if SCALEFREE else list(range(N_FEATURES))) if spec["ev"] else STRUCT_COLS
    tr = [data[i] for i in train_ids]
    sup = regime_support(train_ids, data)
    keep = {}

    def kp(cd):
        k = keep.get(id(cd))
        if k is None:
            k = row_keep(cd, sup)
            keep[id(cd)] = k
        return k

    mu, sd = _stats([_Rows(cd, kp(cd)) for cd in tr], cols)
    zmode = spec["z"]
    enc = None
    if zmode == "ft_pre":
        enc = kit.pretrained_copy()
    elif zmode == "ft_scratch":
        enc = kit.fresh(seed)
    zdim = 4 * kit.dim if zmode else 0
    head = Head(len(cols), zdim)
    params = [{"params": head.parameters(), "lr": 2e-3, "weight_decay": 1e-3}]
    if enc is not None:
        params.append({"params": enc.parameters(), "lr": 1e-3, "weight_decay": 1e-5})
    opt = torch.optim.AdamW(params)
    posw = torch.tensor(8.0)

    def xt(cd):
        z = (cd.X[kp(cd)][:, cols] - mu) / sd
        if CLIP:
            z = np.clip(z, -6.0, 6.0)
        return torch.from_numpy(z.astype(np.float32))

    def zt(cd, train_enc=False):
        if zmode == "frozen_pre":
            return torch.from_numpy(cd.Zpre[kp(cd)])
        if zmode == "frozen_rand":
            return torch.from_numpy(cd.Zrand[seed % N_RAND_SEEDS][kp(cd)])
        if zmode in ("ft_pre", "ft_scratch"):
            src, dst, rel, ok = cd.idx
            h = enc.encode(cd.ex)
            return edge_z(enc, h, src, dst, ok)[torch.from_numpy(kp(cd))]
        return None

    if zmode in ("ft_pre", "ft_scratch"):
        head.train(); enc.train()
        for _ in range(epochs_ft):
            order = rng.permutation(len(tr))
            for start in range(0, len(order), 4):
                loss = 0.0
                for j in order[start : start + 4]:
                    cd = tr[j]
                    logit = head(xt(cd), zt(cd))
                    loss = loss + nn.functional.binary_cross_entropy_with_logits(logit, torch.from_numpy(cd.y[kp(cd)]), pos_weight=posw, reduction="mean")
                opt.zero_grad(); (loss / 4).backward(); opt.step()
        head.eval(); enc.eval()
    else:
        X = torch.cat([xt(cd) for cd in tr])
        Y = torch.from_numpy(np.concatenate([cd.y[kp(cd)] for cd in tr]))
        Z = torch.cat([zt(cd) for cd in tr]) if zmode else None
        head.train()
        for _ in range(epochs_frozen):
            perm = torch.from_numpy(rng.permutation(len(X)))
            for s in range(0, len(X), 512):
                b = perm[s : s + 512]
                logit = head(X[b], Z[b] if Z is not None else None)
                loss = nn.functional.binary_cross_entropy_with_logits(logit, Y[b], pos_weight=posw)
                opt.zero_grad(); loss.backward(); opt.step()
        head.eval()
    out = {}
    with torch.no_grad():
        for cid in score_ids:
            cd = data[cid]
            out[cid] = float(head(xt(cd), zt(cd)).max())
    return out


def zero_shot_case_scores(data: dict[str, CaseData], mode: str) -> dict[str, float]:  # no training, so no slot-support mask
    """Anomaly = -plausibility logit of the least plausible documented edge (pretrained decoder, no training)."""
    out = {}
    for cid, cd in data.items():
        s = cd.zs_masked if mode == "masked" else cd.zs_present
        s = s[~np.isnan(s)]
        out[cid] = float(-s.min()) if False else float((-s).max())
    return out


def make_split(cases: list[dict], train_topos: list[str], seed: int = 0) -> dict[str, list[str]]:
    """train/val over train_topos: clean windows 6,7 -> val; corrupted cases: ~25% of leakage groups -> val."""
    train, val = [], []
    by_tf: dict[tuple, set] = {}
    for c in cases:
        if c["topology_id"] in train_topos and c["label"] == 1:
            by_tf.setdefault((c["topology_id"], c["corruption_type"]), set()).add(c["group_id"])
    val_groups = set()
    for key, gs in by_tf.items():
        ordered = sorted(gs, key=lambda g: hashlib.sha1(f"{seed}|{g}".encode()).hexdigest())
        n_val = max(1, len(ordered) // 4) if len(ordered) >= 3 else 0
        val_groups |= set(ordered[:n_val])
    for c in cases:
        if c["topology_id"] not in train_topos:
            continue
        if c["label"] == 0:
            (val if c["evidence_window"] in (6, 7) else train).append(c["case_id"])
        else:
            (val if c["group_id"] in val_groups else train).append(c["case_id"])
    return {"train": train, "val": val}
