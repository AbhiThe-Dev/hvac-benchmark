from pathlib import Path

from symptom_pipeline.ingestion import (
    hash_source_files,
    load_documented_graph_from_table,
    validate_documented_graph,
)


def _rows():
    equipment_rows = [
        {"equipment_id": "AHU_1", "brick_type": "AHU", "display_name": "AHU 1"},
        {"equipment_id": "VAV_1", "brick_type": "VAV", "display_name": "VAV 1", "room_label": "R101"},
        {"equipment_id": "Zone_1", "brick_type": "HVAC_Zone", "display_name": "Zone 1", "room_label": "R101"},
    ]
    connection_rows = [
        {"source_id": "AHU_1", "target_id": "VAV_1", "relation": "feeds"},
        {"source_id": "VAV_1", "target_id": "Zone_1", "relation": "feeds"},
    ]
    return equipment_rows, connection_rows


def test_load_from_table_round_trips_into_topology_graph():
    equipment_rows, connection_rows = _rows()
    dg, tg = load_documented_graph_from_table("bldg1", equipment_rows, connection_rows, source_paths=[])

    assert dg.building_id == "bldg1"
    assert dg.claimed_pairs("feeds") == frozenset({("AHU_1", "VAV_1"), ("VAV_1", "Zone_1")})
    assert set(tg.nodes()) == {"AHU_1", "VAV_1", "Zone_1"}
    assert tg.node_type("AHU_1") == "AHU"
    assert tg.node_location("VAV_1") == "R101"
    assert tg.edges_by_relation["feeds"] == {("AHU_1", "VAV_1"), ("VAV_1", "Zone_1")}


def test_validate_documented_graph_flags_dangling_connection():
    equipment_rows, connection_rows = _rows()
    connection_rows.append({"source_id": "VAV_1", "target_id": "Ghost_Zone", "relation": "feeds"})
    dg, _ = load_documented_graph_from_table("bldg1", equipment_rows, connection_rows, source_paths=[])
    issues = validate_documented_graph(dg)
    assert any(i.equipment_id == "Ghost_Zone" for i in issues)


def test_validate_documented_graph_flags_duplicate_id():
    equipment_rows, connection_rows = _rows()
    equipment_rows.append({"equipment_id": "AHU_1", "brick_type": "AHU", "display_name": "dup"})
    dg, _ = load_documented_graph_from_table("bldg1", equipment_rows, connection_rows, source_paths=[])
    issues = validate_documented_graph(dg)
    assert any(i.issue == "duplicate equipment_id" for i in issues)


def test_validate_documented_graph_flags_unrecognized_relation():
    equipment_rows, connection_rows = _rows()
    connection_rows.append({"source_id": "AHU_1", "target_id": "Zone_1", "relation": "controls"})
    dg, _ = load_documented_graph_from_table("bldg1", equipment_rows, connection_rows, source_paths=[])
    issues = validate_documented_graph(dg)
    assert any("unrecognized relation" in i.issue for i in issues)


def test_hash_source_files_is_deterministic_and_order_independent(tmp_path: Path):
    f1 = tmp_path / "a.ttl"
    f2 = tmp_path / "b.ttl"
    f1.write_text("a")
    f2.write_text("b")
    before = hash_source_files([f1, f2])
    assert before == hash_source_files([f2, f1])

    f2.write_text("changed")
    after = hash_source_files([f1, f2])
    assert after != before
    assert after == hash_source_files([f2, f1])
