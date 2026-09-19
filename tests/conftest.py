from pathlib import Path

import pytest

from hvac_benchmark.data.cache import FileCache
from hvac_benchmark.data.ontology import BrickOntology

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def ontology() -> BrickOntology:
    """Reuses the project's on-disk Brick ontology cache (already populated
    by a prior data-acquisition run); does not hit the network if present."""
    cache = FileCache(REPO_ROOT / "data_cache")
    return BrickOntology.load(cache)
