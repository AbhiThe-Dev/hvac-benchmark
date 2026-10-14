# hotwater_dx

Standalone project (no imports from the HVAC projects in this repository). Step 1: a physics-derived
cause x check matrix for "hot water not hot / lukewarm / slow / uneven" complaints in commercial and
multifamily buildings with central domestic hot water and a recirculation loop.

Everything this package produces is PHYSICS-MODEL OUTPUT, NOT FIELD EVIDENCE. See PREREGISTRATION.md.

    uv sync && uv run pytest -q
    uv run python scripts/01_validate_model.py
    uv run python scripts/02_build_matrix.py

Results summary: RESULTS.md. Pre-registration and scorecard: PREREGISTRATION.md.
