"""symptom_pipeline: symptom-informed ranking of HVAC topology discrepancies.

A sibling package to `hvac_benchmark` and `physics_pipeline`. It never
modifies either: it imports `hvac_benchmark`'s policies, priors, Bayesian
update functions, and observation simulator unchanged, and (optionally, for
data generation only) imports `physics_pipeline`'s extraction/rewiring/fault
primitives. See README.md for scope and CHANGELOG.md for what is
implemented versus stubbed in this version.
"""

__version__ = "0.2.1"
