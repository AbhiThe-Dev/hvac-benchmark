from pathlib import Path

from hotwater_dx import matrix as MX


def test_thresholds_hash_matches_the_preregistration():
    text = (Path(__file__).resolve().parents[1] / "PREREGISTRATION.md").read_text()
    assert MX.thresholds_hash() in text


def test_engine_stress_hash_matches_the_preregistration():
    from hotwater_dx import stress

    text = (Path(__file__).resolve().parents[1] / "PREREGISTRATION.md").read_text()
    assert stress.frozen_hash() in text


def test_sensitivity_hash_matches_the_preregistration():
    from hotwater_dx import sensitivity

    text = (Path(__file__).resolve().parents[1] / "PREREGISTRATION.md").read_text()
    assert sensitivity.config_hash() in text


def test_adversary_hash_matches_the_preregistration():
    from hotwater_dx import adversary

    text = (Path(__file__).resolve().parents[1] / "PREREGISTRATION.md").read_text()
    assert adversary.frozen_hash() in text


def test_conditioning_hash_matches_the_preregistration():
    from hotwater_dx import conditioning

    text = (Path(__file__).resolve().parents[1] / "PREREGISTRATION.md").read_text()
    assert conditioning.frozen_hash() in text


def test_tenants_hash_matches_the_preregistration():
    from hotwater_dx import tenants

    text = (Path(__file__).resolve().parents[1] / "PREREGISTRATION.md").read_text()
    assert tenants.frozen_hash() in text


def test_oem_hash_and_briefs_match_the_preregistration():
    import hashlib

    from hotwater_dx import oem

    root = Path(__file__).resolve().parents[1]
    text = (root / "PREREGISTRATION.md").read_text()
    assert oem.frozen_hash() in text
    for name in ("reader_brief.md", "verifier_brief.md"):
        assert hashlib.sha256((root / "data" / name).read_text().encode()).hexdigest() in text


def test_novelty_and_priors_hashes_match_the_preregistration():
    import hashlib

    from hotwater_dx import novelty, priors

    root = Path(__file__).resolve().parents[1]
    text = (root / "PREREGISTRATION.md").read_text()
    assert novelty.frozen_hash() in text and priors.frozen_hash() in text
    assert hashlib.sha256((root / "data" / "prior_sources" / "prompts.json").read_bytes()).hexdigest() in text
