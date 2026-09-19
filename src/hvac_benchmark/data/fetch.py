"""Top-level acquisition: resolve the Figshare collection, extract every
Brick model file from each archive via ranged reads, and cache them.

Falls back to bundled Brick example models only if the primary Figshare
source is unreachable after retries, recording the reason and the git
revision/tag of the example models used.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from . import figshare, zip_range
from .cache import FileCache, ProvenanceRecord

logger = logging.getLogger(__name__)

BRICK_EXTENSIONS = (".ttl", ".n3", ".rdf", ".jsonld", ".nt", ".xml")


@dataclass(frozen=True)
class FetchedModel:
    logical_name: str
    archive_title: str
    data: bytes
    provenance: ProvenanceRecord


def _looks_like_brick(name: str) -> bool:
    lower = name.lower()
    return lower.endswith(BRICK_EXTENSIONS) and "ttl" in lower or lower.endswith((".n3", ".jsonld", ".nt"))


def fetch_all_brick_models(cache: FileCache, max_retries: int = 3) -> list[FetchedModel]:
    """Fetch every Brick model file across all articles in the collection.

    Uses the on-disk cache when present so repeat runs do not re-hit the
    network. Raises the last network error if the collection cannot be
    resolved at all after retries (callers should catch this to trigger the
    documented Brick-example fallback).
    """
    session = requests.Session()
    last_error: Exception | None = None
    articles: list[figshare.FigshareArticle] = []
    for attempt in range(1, max_retries + 1):
        try:
            articles = figshare.list_collection_source_articles(session=session)
            break
        except (requests.RequestException, figshare.FigshareError) as exc:
            last_error = exc
            logger.warning("figshare collection resolution attempt %d/%d failed: %s", attempt, max_retries, exc)
    else:
        raise RuntimeError(f"could not resolve Figshare collection after {max_retries} attempts") from last_error

    results: list[FetchedModel] = []
    for article in articles:
        for f in article.files:
            if not f.name.lower().endswith(".zip"):
                continue
            try:
                entries = _list_entries_with_retry(f.download_url, session, max_retries)
            except zip_range.ZipRangeError as exc:
                logger.warning("could not list entries for %s: %s", f.download_url, exc)
                continue

            brick_entries = [
                e
                for e in entries
                if e.name.lower().endswith((".ttl", ".n3", ".jsonld", ".nt"))
            ]
            for entry in brick_entries:
                logical_name = f"{article.id}__{entry.name}".replace(" ", "_")
                if cache.has(logical_name):
                    data = cache.get_bytes(logical_name)
                    prov = cache.get_provenance(logical_name)
                else:
                    data = _extract_with_retry(f.download_url, entry, session, max_retries)
                    prov = cache.put(
                        logical_name,
                        data,
                        source="figshare",
                        archive_url=f.download_url,
                        archive_entry_name=entry.name,
                        archive_entry_crc32=entry.crc32,
                        license=article.license,
                        citation=article.citation or article.doi,
                    )
                results.append(
                    FetchedModel(
                        logical_name=logical_name,
                        archive_title=article.title,
                        data=data,
                        provenance=prov,
                    )
                )
    session.close()
    return results


def _list_entries_with_retry(url: str, session: requests.Session, max_retries: int) -> list[zip_range.ZipEntry]:
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            return zip_range.list_entries(url, session)
        except (requests.RequestException, zip_range.ZipRangeError) as exc:
            last_error = exc
            logger.warning("list_entries attempt %d/%d failed for %s: %s", attempt, max_retries, url, exc)
    raise zip_range.ZipRangeError(str(last_error))


def _extract_with_retry(
    url: str, entry: zip_range.ZipEntry, session: requests.Session, max_retries: int
) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            return zip_range.extract_entry(url, entry, session)
        except (requests.RequestException, zip_range.ZipRangeError) as exc:
            last_error = exc
            logger.warning(
                "extract_entry attempt %d/%d failed for %s in %s: %s", attempt, max_retries, entry.name, url, exc
            )
    raise zip_range.ZipRangeError(str(last_error))
