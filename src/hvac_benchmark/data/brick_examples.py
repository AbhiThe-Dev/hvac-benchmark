"""Fallback Brick example models, used only if the primary Figshare source
is unreachable. Pulled from the official brickschema/Brick GitHub repository
at a pinned tag so the source revision is reproducible and citable.

This path is a contingency, not a substitute data source: results built from
it must be labeled distinctly from the primary LBNL FDD models, and the
pipeline records why the fallback was triggered.
"""

from __future__ import annotations

import logging

import requests

from .cache import FileCache, ProvenanceRecord

logger = logging.getLogger(__name__)

PINNED_TAG = "v1.3.1"
RAW_BASE = f"https://raw.githubusercontent.com/BrickSchema/Brick/{PINNED_TAG}/examples"

# A small, hand-picked set of official multi-equipment example buildings
# that exercise feeds/hasPoint/hasPart relationships, matching the shape of
# models this benchmark targets.
EXAMPLE_FILES = (
    "soda_hall.ttl",
    "ex_shacl_shapes.ttl",
)


def fetch_brick_examples(cache: FileCache, reason: str) -> list[tuple[str, bytes, ProvenanceRecord]]:
    results = []
    session = requests.Session()
    try:
        for name in EXAMPLE_FILES:
            logical_name = f"brick_example__{name}"
            url = f"{RAW_BASE}/{name}"
            if cache.has(logical_name):
                data = cache.get_bytes(logical_name)
                prov = cache.get_provenance(logical_name)
            else:
                resp = session.get(url, timeout=30)
                if resp.status_code != 200:
                    logger.warning("could not fetch fallback example %s: HTTP %d", url, resp.status_code)
                    continue
                data = resp.content
                prov = cache.put(
                    logical_name,
                    data,
                    source="brick_examples_fallback",
                    archive_url=url,
                    archive_entry_name=name,
                    archive_entry_crc32=0,
                    license="BSD-3-Clause (BrickSchema/Brick)",
                    citation=f"BrickSchema/Brick {PINNED_TAG} examples/{name}",
                    source_revision=PINNED_TAG,
                    fallback_reason=reason,
                )
            results.append((logical_name, data, prov))
    finally:
        session.close()
    return results
