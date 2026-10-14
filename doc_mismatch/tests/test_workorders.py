"""Plumbing tests for the work-order screen (Addendum 32). Synthetic text only."""
import hashlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from docmismatch import workorders as W  # noqa: E402

HEADER = ["UniversityID", "PPM/UPM", "SystemCode", "SystemDescription", "SubsystemCode", "SubsystemDescription", "WODescription", "Other"]


def csv_bytes(rows):
    def q(v):
        return '"' + v.replace('"', '""') + '"' if any(c in v for c in ',"\n') else v
    return ("\n".join(",".join(q(v) for v in r) for r in [HEADER] + rows) + "\n").encode()


ROWS = [["U1", "UPM", "D30", "HVAC", "D3040", "Distribution", "AHU-3 fan\nwill not start, \"again\"", "x"],
        ["U1", "PPM", "D30", "HVAC", "D3040", "Distribution", "filters", "x"],
        ["U2", "UPM", "D30", "HVAC", "D3040", "Distribution", "   ", "x"],
        ["U2", "UPM", "D20", "Plumbing", "D2010", "Fixtures", "leak", "x"],
        ["U2", "UPM", "D30", "HVAC", "D3040", "Distribution", "no cooling room 4", "x"]]


def test_hash_and_bytes_match_the_stream():
    data = csv_bytes(ROWS)
    out = W.code_counts(io.BytesIO(data))
    assert out["sha256"] == hashlib.sha256(data).hexdigest() and out["bytes"] == len(data)
    assert out["rows"] == 5 and out["bad_rows"] == 0


def test_counts_handle_quotes_newlines_and_blank_descriptions():
    out = W.code_counts(io.BytesIO(csv_bytes(ROWS)))
    assert out["by_subsystem"][("UPM", "D30", "HVAC", "D3040", "Distribution")] == [3, 2]   # a blank description is an order without text
    assert out["by_subsystem"][("PPM", "D30", "HVAC", "D3040", "Distribution")] == [1, 1]
    assert out["by_university"][("U2", "UPM", "D30", "HVAC")] == [2, 1]
    assert out["by_university"][("U1", "UPM", "D30", "HVAC")] == [1, 1]


def test_short_rows_are_counted_and_skipped():
    data = csv_bytes(ROWS) + b"U9,UPM,D30\n"
    out = W.code_counts(io.BytesIO(data))
    assert out["rows"] == 6 and out["bad_rows"] == 1 and not any(k[0] == "U9" for k in out["by_university"])


def test_no_description_text_is_kept():
    out = W.code_counts(io.BytesIO(csv_bytes(ROWS)))
    blob = repr(out["by_subsystem"]) + repr(out["by_university"])
    assert "AHU-3" not in blob and "no cooling" not in blob and "leak" not in blob


def test_reader_that_returns_short_chunks_still_hashes_everything():
    class Trickle(io.RawIOBase):
        def __init__(self, b):
            self.b, self.i = b, 0

        def read(self, n=-1):
            k = min(3, n if n > 0 else 3)
            out, self.i = self.b[self.i:self.i + k], self.i + k
            return out
    data = csv_bytes(ROWS)
    out = W.code_counts(Trickle(data))
    assert out["sha256"] == hashlib.sha256(data).hexdigest() and out["rows"] == 5


# ---- the frozen sample, keyword search and prompts ----
FULL = list(W.KEEP_COLS) + ["PPM/UPM", "Filler"]


def full_csv(rows):
    out = io.StringIO()
    import csv as _csv
    w = _csv.writer(out)
    w.writerow(FULL)
    for r in rows:
        w.writerow([r.get(c, "") for c in FULL])
    return out.getvalue().encode()


def order(uni, wid, desc="AHU-1 fan noise", sub="D3040", kind="UPM", system="D30"):
    return {"UniversityID": uni, "WOID": wid, "SystemCode": system, "SubsystemCode": sub, "WODescription": desc, "PPM/UPM": kind}


def test_frame_is_by_codes_and_needs_a_description():
    assert W.in_frame("UPM", "D30", "D3040", "x") and W.in_frame("UPM", "D30", "D3060", "x") and W.in_frame("UPM", "D30", "D3050", "x")
    assert not W.in_frame("PPM", "D30", "D3040", "x") and not W.in_frame("UPM", "D20", "D3040", "x")
    assert not W.in_frame("UPM", "D30", "D3020", "x") and not W.in_frame("UPM", "D30", "D3040", "  ")


def test_sample_is_deterministic_uniform_sized_and_in_frame_only():
    rows = [order(str(u), f"{u}-{i}") for u in (1, 2) for i in range(200)] + [order("1", "ppm", kind="PPM"), order("2", "plant", sub="D3020"), order("2", "blank", desc="")]
    data = full_csv(rows)
    a, b = W.reservoir_sample(io.BytesIO(data), 10), W.reservoir_sample(io.BytesIO(data), 10)
    assert a["sample"] == b["sample"] and len(a["sample"]) == 20 and a["eligible"] == {"1": 200, "2": 200}
    assert all(r["WOID"] not in ("ppm", "plant", "blank") for r in a["sample"])
    assert [r["sid"] for r in a["sample"]] == [f"S{i:03d}" for i in range(1, 21)]
    assert sum(r["UniversityID"] == "1" for r in a["sample"]) == 10
    assert a["sha256"] == hashlib.sha256(data).hexdigest() and a["rows"] == 403
    other = W.reservoir_sample(io.BytesIO(data), 10, seed=99)
    assert [r["WOID"] for r in other["sample"]] != [r["WOID"] for r in a["sample"]]


def test_sample_draws_from_the_whole_stream_not_just_the_start():
    data = full_csv([order("1", f"w{i}") for i in range(1000)])
    ids = {int(r["WOID"][1:]) for r in W.reservoir_sample(io.BytesIO(data), 20)["sample"]}
    assert max(ids) > 500 and len(ids) == 20


def test_sample_keeps_only_the_named_columns():
    r = W.reservoir_sample(io.BytesIO(full_csv([order("1", "a")] * 3)), 2)["sample"][0]
    assert set(r) == set(W.KEEP_COLS) | {"sid"} and "Filler" not in r


def test_too_small_a_university_stops_the_run():
    import pytest
    with pytest.raises(ValueError):
        W.reservoir_sample(io.BytesIO(full_csv([order("1", f"a{i}") for i in range(5)])), 10)


def test_keyword_search_finds_obvious_cases_and_not_plain_work():
    assert W.keyword_hits("VAV 2-14 in room 204")["A"] and not W.keyword_hits("replaced belt")["A"]
    assert W.keyword_hits("problem again, same issue as last month")["B"] and not W.keyword_hits("replaced belt")["B"]
    assert W.keyword_hits("box is mislabeled, not on the drawings")["C"] and not W.keyword_hits("box is hot")["C"]
    assert W.keyword_hits("several rooms on 3rd floor hot")["D"] and W.keyword_hits("whole wing no cooling")["D"] and not W.keyword_hits("room 5 hot")["D"]
    assert W.keyword_hits(None) == {k: False for k in W.KINDS}


def test_prompts_name_all_four_kinds_and_the_fingerprint_moves_when_anything_changes(monkeypatch):
    for p in (W.EXTRACT_PROMPT, W.LABEL_PROMPT_1):
        assert all(f"{k}. " in p for k in W.KINDS) and "DATA" in p
    assert "DATA" in W.LABEL_PROMPT_2
    a = W.prompts_sha256()
    monkeypatch.setattr(W, "EXTRACT_PROMPT", W.EXTRACT_PROMPT + " ")
    assert W.prompts_sha256() != a
