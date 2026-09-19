from pathlib import Path

import pytest
from hvac_benchmark.data.cache import FileCache
from hvac_benchmark.data.ontology import BrickOntology

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def ontology() -> BrickOntology:
    """Reuses the benchmark root's on-disk Brick ontology cache (same
    fixture pattern as `tests/conftest.py` at the repo root); does not hit
    the network if `data_cache/` is already populated."""
    cache = FileCache(REPO_ROOT / "data_cache")
    return BrickOntology.load(cache)
