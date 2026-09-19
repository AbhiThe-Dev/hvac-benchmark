"""Figshare API client for resolving the LBNL FDD collection to its articles,
and each article to the archive containing a Brick model.

Only metadata endpoints and small ranged reads are used; the multi-hundred
megabyte to multi-gigabyte time-series archives are never fully downloaded
(see `zip_range.py`).
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

API_BASE = "https://api.figshare.com/v2"
COLLECTION_DOI = "10.6084/m9.figshare.c.6486349.v1"


class FigshareError(RuntimeError):
    pass


@dataclass(frozen=True)
class FigshareFile:
    id: int
    name: str
    size: int
    download_url: str


@dataclass(frozen=True)
class FigshareArticle:
    id: int
    title: str
    doi: str
    url_public_html: str
    files: tuple[FigshareFile, ...]
    license: str | None
    citation: str | None


def resolve_collection_id(doi: str = COLLECTION_DOI, session: requests.Session | None = None) -> int:
    owns = session is None
    session = session or requests.Session()
    try:
        resp = session.get(f"{API_BASE}/collections", params={"doi": doi}, timeout=30)
        resp.raise_for_status()
        matches = resp.json()
        if not matches:
            raise FigshareError(f"no collection found for DOI {doi}")
        return matches[0]["id"]
    finally:
        if owns:
            session.close()


def list_collection_articles(
    collection_id: int, session: requests.Session | None = None, page_size: int = 100
) -> list[dict]:
    owns = session is None
    session = session or requests.Session()
    try:
        resp = session.get(
            f"{API_BASE}/collections/{collection_id}/articles",
            params={"page_size": page_size},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    finally:
        if owns:
            session.close()


def get_article(article_id: int, session: requests.Session | None = None) -> FigshareArticle:
    owns = session is None
    session = session or requests.Session()
    try:
        resp = session.get(f"{API_BASE}/articles/{article_id}", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        files = tuple(
            FigshareFile(id=f["id"], name=f["name"], size=f["size"], download_url=f["download_url"])
            for f in data.get("files", [])
        )
        license_name = None
        lic = data.get("license")
        if isinstance(lic, dict):
            license_name = lic.get("name")
        citation = data.get("citation")
        return FigshareArticle(
            id=data["id"],
            title=data["title"],
            doi=data.get("doi", ""),
            url_public_html=data.get("url_public_html", ""),
            files=files,
            license=license_name,
            citation=citation,
        )
    finally:
        if owns:
            session.close()


def list_collection_source_articles(
    doi: str = COLLECTION_DOI, session: requests.Session | None = None
) -> list[FigshareArticle]:
    """Full resolution: collection DOI -> member articles -> file listings."""
    owns = session is None
    session = session or requests.Session()
    try:
        collection_id = resolve_collection_id(doi, session)
        summaries = list_collection_articles(collection_id, session)
        return [get_article(s["id"], session) for s in summaries]
    finally:
        if owns:
            session.close()
