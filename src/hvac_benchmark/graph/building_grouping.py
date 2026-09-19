"""File-to-building grouping for the LBNL FDD Brick corpus.

Brick files are merged into one RDF graph *before* relationship extraction
only when source documentation supports treating them as the same physical
building or plant. For this corpus, every one of the nine Brick files is
its own distinct, documented testbed/configuration:

- Eight Figshare articles, each with its own DOI, cover a different named
  HVAC testbed (SDAHU, DDAHU, RTU, FCU, PFPU, SFPU, Chiller Plant, Boiler
  Plant) per the collection's own titles and descriptions.
- The RTU article uniquely contains two Brick files, `..._RTU_Exp.ttl` and
  `..._RTU_Sim.ttl` (experimental vs. simulated model of the same testbed).
  Per the plan, these are *distinct documented configurations* and must be
  kept separate rather than merged just because they share a facility.

No file in this corpus needs cross-file merging, so every group below has
exactly one member. The general N-files-to-one-building merge machinery
(`merge_group`) is still implemented and exercised by the split-file test
fixtures, since a future corpus (or the Brick-example fallback) may need it.

If evidence for a grouping is ever ambiguous, the group is marked
`status="ambiguous"` and its members are excluded from the merged corpus,
not guessed into a group.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import rdflib

from ..data import mortar
from ..data.ontology import BrickOntology
from .rdf_parse import ParseReport, normalize_graph, parse_brick_bytes


@dataclass(frozen=True)
class BuildingGroup:
    building_id: str
    member_logical_names: tuple[str, ...]
    config_type: str  # "experimental" | "simulated" | "unknown"
    evidence: str
    status: str = "confirmed"  # "confirmed" | "ambiguous"


# Evidence-backed grouping for the real LBNL FDD corpus. `member_logical_names`
# match the `{figshare_article_id}__{zip_entry_name}` scheme used by
# `data.fetch.fetch_all_brick_models`.
REAL_CORPUS_GROUPS: tuple[BuildingGroup, ...] = (
    BuildingGroup(
        "sdahu",
        ("22338283__LBNL_FDD_Data_Sets_SDAHU_ttl.ttl",),
        "experimental",
        "Figshare article 22338283 'LBNL FDD Dataset SDAHU' (DOI 10.6084/m9.figshare.22338283.v1): "
        "single Brick file, single-duct AHU testbed. Only the RTU article splits Exp/Sim by filename; "
        "no such split is present here, so treated as the (real, experimental) testbed model.",
    ),
    BuildingGroup(
        "ddahu",
        ("22338250__LBNL_FDD_Data_Sets_DDAHU_ttl.ttl",),
        "experimental",
        "Figshare article 22338250 'LBNL FDD Data Sets DDAHU' (DOI 10.6084/m9.figshare.22338250.v1): "
        "single Brick file, dual-duct AHU testbed.",
    ),
    BuildingGroup(
        "rtu_exp",
        ("22338265__LBNL_FDD_Data_Sets_RTU_Exp.ttl",),
        "experimental",
        "Figshare article 22338265 'LBNL FDD Data Sets RTU' (DOI 10.6084/m9.figshare.22338265.v1), "
        "file 'LBNL_FDD_Data_Sets_RTU_Exp.ttl': filename marks this the experimental RTU model. "
        "Kept separate from RTU_Sim per plan instruction to preserve distinct documented configurations.",
    ),
    BuildingGroup(
        "rtu_sim",
        ("22338265__LBNL_FDD_Data_Sets_RTU_Sim.ttl",),
        "simulated",
        "Figshare article 22338265 'LBNL FDD Data Sets RTU' (DOI 10.6084/m9.figshare.22338265.v1), "
        "file 'LBNL_FDD_Data_Sets_RTU_Sim.ttl': filename marks this the simulated RTU model. "
        "Kept separate from RTU_Exp per plan instruction to preserve distinct documented configurations.",
    ),
    BuildingGroup(
        "fcu",
        ("22338256__LBNL_FDD_Data_Sets_FCU_ttl.ttl",),
        "experimental",
        "Figshare article 22338256 'LBNL FDD Data Sets FCU' (DOI 10.6084/m9.figshare.22338256.v1): "
        "single Brick file, fan coil unit testbed.",
    ),
    BuildingGroup(
        "chiller_plant",
        ("22338244__LBNL_FDD_Data_Sets_Chiller_Plant.ttl",),
        "experimental",
        "Figshare article 22338244 'LBNL FDD Data Sets Chiller Plant' (DOI 10.6084/m9.figshare.22338244.v1): "
        "single Brick file, chiller plant testbed. Contains no `feeds` triples; usable only for "
        "hasPoint/hasPart evaluation (documented in results.md as feeds-unavailable).",
    ),
    BuildingGroup(
        "boiler_plant",
        ("22338238__LBNL_FDD_Data_Sets_Boiler_Plant_ttl.ttl",),
        "experimental",
        "Figshare article 22338238 'LBNL FDD Data Sets Boiler Plant' (DOI 10.6084/m9.figshare.22338238.v1): "
        "single Brick file, boiler plant testbed. Contains no `feeds` triples; usable only for "
        "hasPoint/hasPart evaluation (documented in results.md as feeds-unavailable).",
    ),
    BuildingGroup(
        "pfpu",
        ("22344280__LBNL_FDD_Data_Sets_PFPU_ttl.ttl",),
        "experimental",
        "Figshare article 22344280 'LBNL FDD PFPU Data Sets' (DOI 10.6084/m9.figshare.22344280.v1): "
        "single Brick file, parallel fan-powered terminal unit testbed.",
    ),
    BuildingGroup(
        "sfpu",
        ("22344283__LBNL_FDD_Data_Sets_SFPU_ttl.ttl",),
        "experimental",
        "Figshare article 22344283 'LBNL FDD SFPU Data Sets' (DOI 10.6084/m9.figshare.22344283.v1): "
        "single Brick file, series fan-powered terminal unit testbed.",
    ),
)


# MORTAR corpus: 44 independent anonymized real buildings plus one additional
# building (`smc`), each its own file with its own building-scoped URI
# namespace already (see data/mortar.py) -- no cross-file merging question
# arises here the way it did for the LBNL RTU Exp/Sim split, since every
# MORTAR file is already a single documented, independent building.
MORTAR_CORPUS_GROUPS: tuple[BuildingGroup, ...] = tuple(
    BuildingGroup(
        f"mortar_{filename[:-len('.ttl')]}",
        (f"mortar__{filename}",),
        "experimental",
        f"Hugging Face dataset gtfierro/mortargraphs (pinned revision "
        f"{mortar.HF_REVISION}), file '{filename}': one anonymized real building "
        f"from the MORTAR testbed (Fierro et al., BuildSys 2018), documented as its "
        f"own independent building. License status unconfirmed -- see data/mortar.py.",
    )
    for filename in mortar.MORTAR_FILENAMES
)


@dataclass
class MergedTopology:
    building_id: str
    graph: rdflib.Graph
    config_type: str
    member_logical_names: tuple[str, ...]
    parse_reports: dict[str, ParseReport]


def merge_group(
    group: BuildingGroup,
    files_by_logical_name: dict[str, bytes],
    ontology: BrickOntology,
) -> MergedTopology:
    """Parse every member of a confirmed group under one shared base URI and
    union the results into a single normalized graph."""
    if group.status != "confirmed":
        raise ValueError(f"refusing to merge non-confirmed group {group.building_id!r}")
    base_uri = f"https://hvac-benchmark.invalid/building/{group.building_id}/"
    merged = rdflib.Graph()
    reports: dict[str, ParseReport] = {}
    for logical_name in group.member_logical_names:
        raw = files_by_logical_name[logical_name]
        parsed = parse_brick_bytes(raw, base_uri=base_uri)
        normalized, report = normalize_graph(parsed, ontology)
        for triple in normalized:
            merged.add(triple)
        reports[logical_name] = report
    return MergedTopology(
        building_id=group.building_id,
        graph=merged,
        config_type=group.config_type,
        member_logical_names=group.member_logical_names,
        parse_reports=reports,
    )


def merge_all(
    groups: tuple[BuildingGroup, ...],
    files_by_logical_name: dict[str, bytes],
    ontology: BrickOntology,
) -> tuple[list[MergedTopology], list[BuildingGroup]]:
    """Merge every confirmed group; return (merged topologies, excluded/ambiguous groups)."""
    merged: list[MergedTopology] = []
    excluded: list[BuildingGroup] = []
    for group in groups:
        if group.status != "confirmed":
            excluded.append(group)
            continue
        if not all(name in files_by_logical_name for name in group.member_logical_names):
            excluded.append(group)
            continue
        merged.append(merge_group(group, files_by_logical_name, ontology))
    return merged, excluded
