"""Guards for the hvac_benchmark Brick-graph bridge (PREREGISTRATION_DR.md Addendum 5).

Anchored mostly to the REAL, already-cached corpus (offline, deterministic) rather than synthetic fixtures,
because the whole point of this module is to answer a building-specific question correctly -- including the
non-canonical-class edge case (`Electrical_Power_Sensor`) that was only discovered by querying real data.
"""
import sys
from pathlib import Path

import networkx as nx
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.active import brick_bridge as B  # noqa: E402

pytestmark = pytest.mark.skipif(not B.DEFAULT_CACHE_DIR.exists(), reason="data_cache/ not present")


@pytest.fixture(scope="module")
def real_corpus():
    return B.load_real_topologies()


@pytest.fixture(scope="module")
def ornl(real_corpus):
    topos, ontology = real_corpus
    return topos["rtu_exp"], ontology


def test_load_real_topologies_has_ornl_and_the_full_mortar_set(real_corpus):
    topos, _ = real_corpus
    assert "rtu_exp" in topos
    assert len(topos) >= 45   # 44 MORTAR buildings + smc + rtu_exp


def test_ornl_has_ten_vav_boxes(ornl):
    tg, ontology = ornl
    vavs = B.class_nodes(tg, ontology, "VAV")
    assert len(vavs) == 10


def test_ornl_vav_boxes_confidently_lack_flow_documentation(ornl):
    """Ground truth independently established this session (Addendum 1/4, purely statistical): the ORNL RTU-VAV
    boxes have no per-box airflow sensor. This reproduces that from the Brick documentation alone."""
    tg, ontology = ornl
    vavs = B.class_nodes(tg, ontology, "VAV")
    assert vavs
    for v in vavs:
        assert B.equipment_has_signal(tg, ontology, v, "flow") is False


def test_ornl_vav_boxes_have_discharge_temperature_documentation(ornl):
    tg, ontology = ornl
    vavs = B.class_nodes(tg, ontology, "VAV")
    assert all(B.equipment_has_signal(tg, ontology, v, "t_dis") is True for v in vavs)


def test_nonstandard_class_name_is_undetermined_not_false(ornl):
    """The real rtu_exp file tags VAV reheat power points `Electrical_Power_Sensor` -- not Brick 1.3.0's own
    `Electric_Power_Sensor` -- so the reference ontology cannot place it in the Power_Sensor subclass chain.
    That must come back None (undetermined), never a confident False -- `ontology.py` never guesses equivalences."""
    tg, ontology = ornl
    vavs = B.class_nodes(tg, ontology, "VAV")
    types = {tg.node_type(o) for v in vavs for (s, o) in tg.edges_by_relation["hasPoint"] if s == v}
    assert "Electrical_Power_Sensor" in types
    assert "Electrical_Power_Sensor" not in ontology.known_classes()
    v = vavs[0]
    assert B.equipment_has_signal(tg, ontology, v, "kw") is None


def test_structural_requirement_met_vav_zone_channel_0_is_false_on_ornl(ornl):
    """channel 0 needs owner flow + member temp; flow is confidently absent -> False overall regardless of
    the member (Zone) side, which is never even looked up since temp has no distinct sensor-class requirement."""
    tg, ontology = ornl
    v = B.class_nodes(tg, ontology, "VAV")[0]
    assert B.structural_requirement_met(tg, ontology, v, None, "vav_zone", 0) is False


def test_structural_requirement_met_vav_zone_channel_1_is_true_on_ornl():
    """channel 1 (BAS-only: owner discharge temp + member temp) needs no extra instrument and IS documented."""
    topos, ontology = B.load_real_topologies()
    tg = topos["rtu_exp"]
    v = B.class_nodes(tg, ontology, "VAV")[0]
    assert B.structural_requirement_met(tg, ontology, v, None, "vav_zone", 1) is True


def test_structural_requirement_met_none_for_uncatalogued_channel(ornl):
    tg, ontology = ornl
    v = B.class_nodes(tg, ontology, "VAV")[0]
    assert B.structural_requirement_met(tg, ontology, v, None, "not_a_real_slot", 0) is None


# ---------------------------------------------------------------------------------------------- synthetic positive path
def _fake_topology(equip_type, point_type):
    g = nx.MultiDiGraph()
    g.add_node("equip", brick_type=equip_type, brick_types=[equip_type])
    g.add_node("pt", brick_type=point_type, brick_types=[point_type])
    g.add_edge("equip", "pt", relation="hasPoint")
    from hvac_benchmark.graph.networkx_build import TopologyGraph
    return TopologyGraph(building_id="fake", config_type="experimental", nx_graph=g, edges_by_relation={"hasPoint": {("equip", "pt")}})


def test_equipment_has_signal_true_for_a_direct_flow_sensor(real_corpus):
    _, ontology = real_corpus
    tg = _fake_topology("VAV", "Discharge_Air_Flow_Sensor")
    assert B.equipment_has_signal(tg, ontology, "equip", "flow") is True


def test_equipment_has_signal_false_when_point_class_known_but_wrong(real_corpus):
    _, ontology = real_corpus
    tg = _fake_topology("VAV", "Zone_Air_Temperature_Sensor")
    assert B.equipment_has_signal(tg, ontology, "equip", "flow") is False


def test_equipment_has_signal_true_for_signal_with_no_distinct_class(real_corpus):
    _, ontology = real_corpus
    tg = _fake_topology("VAV", "Zone_Air_Temperature_Sensor")
    assert B.equipment_has_signal(tg, ontology, "equip", "value") is True
