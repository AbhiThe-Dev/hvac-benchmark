"""The v1 documentation is generated from the code (`--tables`, `--demo`) and must not drift from it."""
import contextlib
import io
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docmismatch.troubleshoot.v1 import catalogue as K, causes as C, cli, tables  # noqa: E402

DOC = (ROOT / "TROUBLESHOOT_V1.md").read_text()


def block(name: str) -> str:
    m = re.search(rf"<!-- BEGIN:{name} -->\n(.*?)\n<!-- END:{name} -->", DOC, re.S)
    assert m, f"no {name} block in TROUBLESHOOT_V1.md"
    return m.group(1)


def demo(*argv) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cli.main(list(argv))
    return buf.getvalue().rstrip("\n")


@pytest.mark.parametrize("name", ["tiers", "causes", "catalogue", "readings"])
def test_the_generated_tables_in_the_document_are_the_ones_the_code_produces(name):
    assert block(name) == tables.all_tables()[name]


@pytest.mark.parametrize("name,tier", [("example_t1", "T1"), ("example_t3", "T3")])
def test_the_worked_examples_are_the_current_output_of_the_demo(name, tier):
    assert block(name) == "```text\n" + demo("--demo", "--tier", tier, "--truth", "low_static", "--member", "Room-204") + "\n```"


def test_the_document_covers_every_check_and_cause_and_states_what_it_must():
    assert "@@" not in DOC
    for c in K.CATALOGUE:
        assert f"`{c.name}`" in DOC, c.name
    for c in C.CAUSES:
        assert f"`{c.id}`" in DOC, c.id
    for must in ("Nothing here has been validated", "PLACEHOLDER", "Addendum 27", "Addendum 28", "run once, in simulation", "did not fall with more data", "controlshub.tech/en/blog/66-vav-box-airflow-problems", "pnnl.gov/projects/om-best-practices/variable-air-volume-systems",
                 "vendor blog", "T0", "T1", "T2", "T3", "T4", "next_step()", "documented_owner_wrong", "undocumented_equipment", "documented_attribute_mismatch", "assumptions"):
        assert must in DOC, must
    assert "The number that matters most: how reliable the checks are" in DOC


def test_the_v0_document_points_to_v1_and_nothing_else_about_v0_changed_in_meaning():
    v0 = (ROOT / "TROUBLESHOOT.md").read_text()
    assert "TROUBLESHOOT_V1.md" in v0 and "does not change it" in v0
