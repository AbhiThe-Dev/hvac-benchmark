"""Guards for the instrumentation census (Brick metadata only)."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch import census as C  # noqa: E402

TTL = """@prefix brick: <https://brickschema.org/schema/Brick#> .
@prefix ref: <https://brickschema.org/schema/Brick/ref#> .
@prefix ns: <urn:t/c#> .
ns:AHU01 a brick:Air_Handler_Unit ; brick:feeds ns:V1, ns:V2, ns:R1 ; brick:hasPoint ns:sat, ns:mat .
ns:V1 a brick:VAV ; brick:feeds ns:Z1 ; brick:hasPoint ns:f1, ns:d1, ns:t1 .
ns:V2 a brick:VAV ; brick:feeds ns:Z2 ; brick:hasPoint ns:f2, ns:d2, ns:t2 .
ns:R1 a brick:RVAV ; brick:feeds ns:Z3 ; brick:hasPoint ns:f3, ns:d3, ns:t3 ; brick:hasPart ns:C1 .
ns:C1 a brick:Heating_Coil .
ns:Z1 a brick:HVACZone . ns:Z2 a brick:HVACZone . ns:Z3 a brick:HVACZone .
ns:sat a brick:Supply_Air_Temperature_Sensor ; ref:hasExternalReference [ ref:hasTimeseriesId "u-sat" ] .
ns:mat a brick:Mixed_Air_Temperature_Sensor .
ns:f1 a brick:Supply_Air_Flow_Sensor ; ref:hasExternalReference [ ref:hasTimeseriesId "u-f1" ] .
ns:d1 a brick:Discharge_Air_Temperature_Sensor ; ref:hasExternalReference [ ref:hasTimeseriesId "u-d1" ] .
ns:t1 a brick:Zone_Air_Temperature_Sensor ; ref:hasExternalReference [ ref:hasTimeseriesId "u-t1" ] .
ns:f2 a brick:Supply_Air_Flow_Sensor .
ns:d2 a brick:Supply_Air_Temperature_Sensor ; ref:hasExternalReference [ ref:hasTimeseriesId "u-d2" ] .
ns:t2 a brick:Zone_Air_Temperature_Sensor ; ref:hasExternalReference [ ref:hasTimeseriesId "u-t2" ] .
ns:f3 a brick:Air_Flow_Sensor ; ref:hasExternalReference [ ref:hasTimeseriesId "u-f3" ] .
ns:d3 a brick:Discharge_Air_Temperature_Sensor ; ref:hasExternalReference [ ref:hasTimeseriesId "u-d3" ] .
ns:t3 a brick:Zone_Air_Temperature_Sensor ; ref:hasExternalReference [ ref:hasTimeseriesId "u-t3" ] .
"""


@pytest.fixture()
def bc(tmp_path):
    (tmp_path / "mortar__x.ttl").write_text(TTL)
    return C.parse_census(tmp_path / "mortar__x.ttl")


def test_parse_finds_kinds_pairs_and_counts_reheat_vavs_as_vavs(bc):
    assert sorted(k for k, v in bc.kinds.items() if v == "VAV") == ["R1", "V1", "V2"]              # RVAV is a VAV
    assert bc.pairs["ahu_vav"] == [("AHU01", "R1"), ("AHU01", "V1"), ("AHU01", "V2")]
    assert bc.pairs["vav_zone"] == [("R1", "Z3"), ("V1", "Z1"), ("V2", "Z2")] and bc.pairs["coil_vav"] == [("R1", "C1")]


def test_a_documented_point_without_a_timeseries_counts_only_when_documentation_is_enough(bc):
    rec, doc = C.channel_shares(bc, "vav_zone", recorded=True), C.channel_shares(bc, "vav_zone", recorded=False)
    assert rec["channels"] == pytest.approx({0: 2 / 3, 1: 1.0, 2: 2 / 3}) and doc["channels"] == pytest.approx({0: 1.0, 1: 1.0, 2: 1.0})     # V2's flow is documented, not recorded
    assert C.supports(rec, 1) and not C.supports(rec, 0) and C.supports(doc, 0)


def test_roles_nobody_records_block_the_channels_that_read_them(bc):
    av = C.channel_shares(bc, "ahu_vav")
    assert av["n_pairs"] == 3 and av["channels"] == {0: 0.0, 1: 0.0, 2: 0.0}                        # no VAV inlet temperature, no AHU airflow anywhere
    assert C.channel_shares(bc, "coil_vav")["channels"] == {0: 0.0, 1: 0.0, 2: 0.0}                 # no coil power
    assert C.channel_shares(bc, "coil_vav", recorded=False)["channels"][0] == 0.0
    assert not C.has_role(bc, "AHU01", "AHU", "mat", recorded=True) and C.has_role(bc, "AHU01", "AHU", "mat", recorded=False)     # documented, never trended


def test_zone_temperature_may_sit_on_the_vav_that_feeds_the_zone(bc):
    assert C.has_role(bc, "Z1", "Zone", "temp", recorded=True)


def test_duplicate_buildings_are_detected_by_their_timeseries_ids(bc, tmp_path):
    (tmp_path / "mortar__y.ttl").write_text(TTL)
    other = C.parse_census(tmp_path / "mortar__y.ttl", "y")
    kept, dup = C.distinct([bc, other])
    assert [c.building for c in kept] == ["x"] and dup == [("y", "x")]
