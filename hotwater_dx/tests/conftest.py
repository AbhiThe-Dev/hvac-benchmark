import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from hotwater_dx.params import nominal_design  # noqa: E402
from hotwater_dx.plant import build_plant  # noqa: E402


@pytest.fixture
def plant():
    d = nominal_design()
    return build_plant(d, np.random.default_rng(7))
