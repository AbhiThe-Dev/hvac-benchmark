"""HTTP-range ZIP extraction: correctness of central-directory parsing and
CRC verification, without hitting the network -- a tiny in-memory ZIP is
served through a monkeypatched range-request function."""

from __future__ import annotations

import io
import zipfile

import pytest

from hvac_benchmark.data import zip_range


def make_tiny_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("model.ttl", b"@prefix brick: <https://brickschema.org/schema/Brick#> .\n")
        zf.writestr("readme.txt", b"not a brick file")
    return buf.getvalue()


class FakeSession:
    def __init__(self, data: bytes):
        self.data = data

    def get(self, url, headers, timeout):
        range_header = headers["Range"]
        assert range_header.startswith("bytes=")
        spec = range_header[len("bytes="):]
        if spec.startswith("-"):
            n = int(spec[1:])
            body = self.data[-n:]
        else:
            start_s, end_s = spec.split("-")
            start, end = int(start_s), int(end_s)
            body = self.data[start : end + 1]
        return FakeResponse(body)


class FakeResponse:
    def __init__(self, content: bytes):
        self.status_code = 206
        self.content = content


def test_list_entries_finds_all_files_without_full_download():
    data = make_tiny_zip()
    session = FakeSession(data)
    entries = zip_range.list_entries("http://fake/archive.zip", session=session)
    names = {e.name for e in entries}
    assert names == {"model.ttl", "readme.txt"}


def test_extract_entry_returns_correct_bytes_and_validates_crc():
    data = make_tiny_zip()
    session = FakeSession(data)
    entries = zip_range.list_entries("http://fake/archive.zip", session=session)
    entry = next(e for e in entries if e.name == "model.ttl")
    extracted = zip_range.extract_entry("http://fake/archive.zip", entry, session=session)
    assert extracted == b"@prefix brick: <https://brickschema.org/schema/Brick#> .\n"


def test_extract_entry_rejects_crc_mismatch():
    data = make_tiny_zip()
    session = FakeSession(data)
    entries = zip_range.list_entries("http://fake/archive.zip", session=session)
    entry = next(e for e in entries if e.name == "model.ttl")
    corrupted = zip_range.ZipEntry(
        name=entry.name,
        method=entry.method,
        compressed_size=entry.compressed_size,
        uncompressed_size=entry.uncompressed_size,
        crc32=entry.crc32 ^ 0xFFFFFFFF,
        local_header_offset=entry.local_header_offset,
    )
    with pytest.raises(zip_range.ZipRangeError, match="CRC mismatch"):
        zip_range.extract_entry("http://fake/archive.zip", corrupted, session=session)
