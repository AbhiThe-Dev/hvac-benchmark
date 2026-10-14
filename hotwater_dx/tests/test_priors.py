import json

import numpy as np

from hotwater_dx import causes as C
from hotwater_dx import priors as PR


def test_prior_quality_is_controlled_by_rho_and_shrink():
    rng = np.random.default_rng(0)
    w = rng.dirichlet([0.5] * 16)
    u = PR.standardised(np.log(w))
    e = PR.orthogonal_noise(u, rng)
    assert abs(np.corrcoef(u, e)[0, 1]) < 1e-9 and abs(e.std() - 1) < 1e-9
    for rho in (-1.0, -0.4, 0.0, 0.5, 1.0):
        p = PR.make_prior(w, rho, 1.0, e)
        assert abs(p.sum() - 1) < 1e-12
        assert abs(np.corrcoef(np.log(p), np.log(w))[0, 1] - rho) < 1e-9
    assert np.allclose(PR.make_prior(w, 1.0, 1.0, e), w / w.sum())
    shrunk = PR.make_prior(w, 1.0, 0.5, e)
    assert np.allclose(shrunk, 0.5 * w + 0.5 / len(w))
    assert np.allclose(PR.make_prior(w, 0.7, 0.0, e), 1 / len(w))


def test_spearman_handles_ties_and_sign():
    assert abs(PR.spearman([1, 2, 3, 4], [10, 20, 30, 40]) - 1) < 1e-12
    assert abs(PR.spearman([1, 2, 3, 4], [4, 3, 2, 1]) + 1) < 1e-12
    assert abs(PR.spearman([1, 1, 2, 3], [1, 1, 2, 3]) - 1) < 1e-12


def test_source_agreement_uses_the_frozen_bars(tmp_path):
    M = np.arange(len(C.IDS), dtype=float)
    ranks = [np.arange(len(C.IDS), 0, -1, dtype=float) for _ in range(3)]            # every run ranks the high-M causes as most frequent
    a = PR.source_agreement(dict(M=M, L=ranks))
    assert a["usable"] and a["M_vs_L"] > 0.99 and abs(max(a["weights"].values()) / min(a["weights"].values()) - PR.CFG["SOURCES"]["max_ratio"]) < 1e-6
    rng = np.random.default_rng(1)
    noise = [rng.permutation(len(C.IDS)).astype(float) + 1 for _ in range(3)]
    assert not PR.source_agreement(dict(M=M, L=noise))["usable"]
    assert PR.source_agreement(dict(M=M, L=[]))["status"] == "pending"


def test_read_sources_needs_all_causes_in_each_ranking(tmp_path):
    (tmp_path / "data" / "prior_sources").mkdir(parents=True)
    import shutil
    from pathlib import Path
    shutil.copy(Path(__file__).resolve().parents[1] / "data" / "oem_claims.csv", tmp_path / "data" / "oem_claims.csv")
    full = [{"cause_id": c, "rank": i + 1} for i, c in enumerate(C.IDS)]
    (tmp_path / "data" / "prior_sources" / "L_1.json").write_text(json.dumps(full))
    (tmp_path / "data" / "prior_sources" / "L_2.json").write_text(json.dumps(full[:-1]))      # incomplete: ignored
    s = PR.read_sources(tmp_path)
    assert len(s["L"]) == 1 and s["M"].shape == (len(C.IDS),) and s["M"].sum() > 0
