"""Fetch and cache the MORTAR testbed's real Brick building models from
Hugging Face, the same way `figshare.py` / `fetch.py` fetch and cache the
LBNL FDD corpus.

Source: the `gtfierro/mortargraphs` Hugging Face dataset -- 44 anonymized,
independent real-building Brick models (`bldg1.ttl` .. `bldg44.ttl`) plus one
additional building (`smc.ttl`), one file per building, no cross-file merging
needed (unlike the LBNL RTU_Exp/RTU_Sim case). Files are small (tens to a few
hundred KB each), so plain HTTP GETs are used -- no ranged ZIP extraction
like `zip_range.py` is needed here.

The dataset backs Fierro, Pritoni, AbdelBaky, Raftery, Peffer, Thomson, and
Culler, "Mortar: An Open Testbed for Portable Building Analytics", ACM
Trans. Sen. Netw. 16, 1 (2020), https://doi.org/10.1145/3366375 (originally
presented at BuildSys 2018).

**License status: commercial use confirmed by direct correspondence with the
MORTAR maintainers (project owner emailed the MORTAR team, September 2026;
response granted permission to use the anonymized building data for this
project, including commercial use).** The Hugging Face mirror itself still
has no dataset card, no LICENSE file, and no README (checked directly
against its API and raw file listing), and the MORTAR *software* repositories
(`gtfierro/mortar`, `SoftwareDefinedBuildings/mortar`) being BSD-3-Clause
covers the query/analytics platform, not the building metadata -- so this
permission rests on the email exchange, not a public license grant. Retain
the actual correspondence on file in case of audit; every provenance record
for this source carries a citation string repeating this caveat (and the
confirmation) verbatim so it travels with the data rather than living only
in a PR description or chat log.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from .cache import FileCache, ProvenanceRecord

logger = logging.getLogger(__name__)

HF_DATASET_REPO = "gtfierro/mortargraphs"
# Pinned to a specific commit, not just "main", so re-runs are reproducible
# and the exact bytes fetched are citable -- same discipline as
# ontology.py's BRICK_VERSION_TAG pin.
HF_REVISION = "8844574c5ba0f18a77e0e383b5d1e4484262a61e"
HF_RAW_BASE = f"https://huggingface.co/datasets/{HF_DATASET_REPO}/resolve/{HF_REVISION}"

# Hand-verified against the pinned revision's file listing (via the HF API)
# rather than discovered dynamically at run time, matching
# building_grouping.py's explicit/reviewed-rather-than-inferred style: 44
# independent anonymized buildings numbered 1..44 with no gaps, plus one
# additional building `smc`.
MORTAR_FILENAMES: tuple[str, ...] = tuple(f"bldg{i}.ttl" for i in range(1, 45)) + ("smc.ttl",)

LICENSE_STATUS = "commercial-use-confirmed-via-correspondence"  # see module docstring
LICENSE_CAVEAT = (
    "Fierro et al., 'Mortar: An Open Testbed for Portable Building Analytics', "
    "ACM Trans. Sen. Netw. 16(1), 2020 (https://doi.org/10.1145/3366375; BuildSys 2018). "
    "Mirrored via Hugging Face dataset gtfierro/mortargraphs, which has no dataset card, "
    "LICENSE file, or README. The MORTAR software repos are BSD-3-Clause but that covers "
    "the platform, not this building metadata. COMMERCIAL USE CONFIRMED: the project owner "
    "obtained direct email confirmation from the MORTAR maintainers (September 2026) that "
    "commercial use of this building metadata is permitted. This rests on that "
    "correspondence, not a public license grant -- retain the email on file."
)


@dataclass(frozen=True)
class FetchedMortarModel:
    logical_name: str
    filename: str
    data: bytes
    provenance: ProvenanceRecord


def _raw_url(filename: str) -> str:
    return f"{HF_RAW_BASE}/{filename}"


def _get_with_retry(session: requests.Session, url: str, max_retries: int) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, timeout=60)
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as exc:
            last_error = exc
            logger.warning("MORTAR fetch attempt %d/%d failed for %s: %s", attempt, max_retries, url, exc)
    raise RuntimeError(f"could not fetch {url} after {max_retries} attempts") from last_error


def fetch_all_mortar_graphs(cache: FileCache, max_retries: int = 3) -> list[FetchedMortarModel]:
    """Fetch every MORTAR building file, using the on-disk cache when present
    so repeat runs do not re-hit the network."""
    session = requests.Session()
    results: list[FetchedMortarModel] = []
    try:
        for filename in MORTAR_FILENAMES:
            logical_name = f"mortar__{filename}"
            if cache.has(logical_name):
                data = cache.get_bytes(logical_name)
                prov = cache.get_provenance(logical_name)
            else:
                url = _raw_url(filename)
                data = _get_with_retry(session, url, max_retries)
                prov = cache.put(
                    logical_name,
                    data,
                    source="mortar_huggingface",
                    archive_url=url,
                    archive_entry_name=filename,
                    archive_entry_crc32=0,
                    license=LICENSE_STATUS,
                    citation=LICENSE_CAVEAT,
                    source_revision=HF_REVISION,
                )
            results.append(
                FetchedMortarModel(logical_name=logical_name, filename=filename, data=data, provenance=prov)
            )
    finally:
        session.close()
    return results
