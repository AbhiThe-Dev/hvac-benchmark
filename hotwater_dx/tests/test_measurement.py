import numpy as np

from hotwater_dx import measurement as M


def test_clamp_reads_low_on_hot_pipe_and_ir_reads_lower_still():
    r = np.random.default_rng(0)
    clamp = np.mean([M.temp(130, "clamp", 70, r) for _ in range(3000)])
    ir = np.mean([M.temp(130, "ir", 70, r) for _ in range(3000)])
    assert clamp < 130 and ir < clamp                 # bare copper pulls IR toward ambient


def test_difference_of_two_clamp_readings_is_less_noisy_than_independent():
    r = np.random.default_rng(1)
    diff = np.std([np.subtract(*M.temp_pair(120, 110, "clamp", 70, r)) for _ in range(4000)])
    indep = np.std([M.temp(120, "clamp", 70, r) - M.temp(110, "clamp", 70, r) for _ in range(4000)])
    assert diff < 0.7 * indep


def test_seeded_reproducibility():
    assert M.temp(100, "probe", 70, np.random.default_rng(5)) == M.temp(100, "probe", 70, np.random.default_rng(5))
