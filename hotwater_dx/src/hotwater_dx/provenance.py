"""Provenance tags and the disclaimer stamped on every output.

Every number in this package is tagged with where it came from:
  SOURCE       a number read in a cited source (see SOURCES in sources.py)
  PHYSICS      derived from a conservation law or an identity (e.g. Btu/h = 500 * gpm * dT)
  ANALYST      the author's engineering estimate; a range, never a measurement
  PLACEHOLDER  a value that must be replaced by field data or elicitation before it is relied on
"""

PROV = ("SOURCE", "PHYSICS", "ANALYST", "PLACEHOLDER")

DISCLAIMER = ("PHYSICS-MODEL OUTPUT, NOT FIELD EVIDENCE. Produced by a small steady-state loop model with "
              "analyst-chosen parameter ranges; it says what the model implies, not what happens in buildings.")
