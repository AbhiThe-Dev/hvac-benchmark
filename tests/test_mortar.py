"""MORTAR source: ontology equivalence handling, cached/provenance-tracked
fetching (network mocked), grouping, the candidate-universe feasibility cap,
and explicit exclusion of unusable topologies."""

from __future__ import annotations

import pytest

from hvac_benchmark.data import mortar
from hvac_benchmark.data.cache import FileCache
from hvac_benchmark.graph.building_grouping import MORTAR_CORPUS_GROUPS, BuildingGroup, merge_all
from hvac_benchmark.graph.networkx_build import build_topology_graph
from hvac_benchmark.pipeline import compute_availability


def test_equivalent_classes_share_ancestors(ontology):
    # Brick 1.3.0 declares AHU / Air_Handler_Unit owl:equivalentClass, not subClassOf.
    assert ontology.is_a("Air_Handler_Unit", "AHU")
    assert ontology.is_a("AHU", "Air_Handler_Unit")
    # equivalence must not leak unrelated ancestry
    assert not ontology.is_a("Air_Handler_Unit", "Terminal_Unit")


def test_no_invented_rec_brick_bridge(ontology):
    # REC classes are not in the reference ontology; nothing may be guessed.
    assert "HVACZone" not in ontology.known_classes()
    assert "Room" in ontology.known_classes()


def test_mortar_file_list_is_44_buildings_plus_smc():
    assert len(mortar.MORTAR_FILENAMES) == 45
    assert mortar.MORTAR_FILENAMES[0] == "bldg1.ttl"
    assert mortar.MORTAR_FILENAMES[43] == "bldg44.ttl"
    assert mortar.MORTAR_FILENAMES[-1] == "smc.ttl"
    assert len(MORTAR_CORPUS_GROUPS) == 45
    assert len({g.building_id for g in MORTAR_CORPUS_GROUPS}) == 45


class _Resp:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        pass


class _Session:
    def __init__(self):
        self.urls: list[str] = []

    def get(self, url, timeout):
        self.urls.append(url)
        return _Resp(b"@prefix brick: <https://brickschema.org/schema/Brick#> .\n")

    def close(self):
        pass


def test_fetch_caches_with_unconfirmed_license_and_pinned_revision(tmp_path, monkeypatch):
    session = _Session()
    monkeypatch.setattr(mortar.requests, "Session", lambda: session)
    cache = FileCache(tmp_path)

    models = mortar.fetch_all_mortar_graphs(cache)
    assert len(models) == 45
    assert len(session.urls) == 45
    assert all(mortar.HF_REVISION in u for u in session.urls)

    prov = models[0].provenance
    assert prov.source == "mortar_huggingface"
    assert prov.license is None  # unconfirmed, never asserted
    assert "UNCONFIRMED" in prov.citation
    assert prov.source_revision == mortar.HF_REVISION
    assert len(prov.sha256) == 64

    # second call is served from cache: no further requests
    mortar.fetch_all_mortar_graphs(cache)
    assert len(session.urls) == 45


def test_fetch_failure_raises_after_retries(tmp_path, monkeypatch):
    class Failing:
        def get(self, url, timeout):
            raise mortar.requests.ConnectionError("down")

        def close(self):
            pass

    monkeypatch.setattr(mortar.requests, "Session", lambda: Failing())
    with pytest.raises(RuntimeError):
        mortar.fetch_all_mortar_graphs(FileCache(tmp_path), max_retries=2)


def test_missing_mortar_file_excludes_group(ontology):
    merged, excluded = merge_all(MORTAR_CORPUS_GROUPS[:2], {}, ontology)
    assert merged == []
    assert len(excluded) == 2


MINI = b"""
@prefix brick: <https://brickschema.org/schema/Brick#> .
@prefix b: <http://example.org/b#> .
b:ahu a brick:Air_Handler_Unit ; brick:feeds b:vav .
b:vav a brick:VAV .
"""


def _tg(ontology):
    g = BuildingGroup("mini", ("m.ttl",), "experimental", "test")
    merged, _ = merge_all((g,), {"m.ttl": MINI}, ontology)
    return build_topology_graph("mini", "experimental", merged[0].graph)


def test_air_handler_unit_alias_now_generates_feeds_candidates(ontology):
    tg = _tg(ontology)
    avail = compute_availability(tg, "feeds", ontology)
    assert avail.available and avail.n_candidates >= 1 and avail.n_missed == 0


def test_feasibility_cap_marks_relation_unavailable_with_reason(ontology):
    tg = _tg(ontology)
    avail = compute_availability(tg, "feeds", ontology, max_universe=0)
    assert not avail.available
    assert "feasibility cap" in avail.reason
    assert avail.n_candidates >= 1
