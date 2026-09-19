"""Selective ZIP extraction over HTTP range requests.

The source archives (LBNL FDD data sets on Figshare) are hundreds of
megabytes to several gigabytes each, dominated by time-series CSVs we do
not need. Each archive contains exactly one or two small Brick TTL files.
Rather than downloading whole archives, we:

1. Fetch the last 64 KiB to locate the End Of Central Directory (EOCD)
   record (adequate as long as the archive comment is short, which holds
   for every file inspected in this collection; we fall back to a larger
   tail fetch if the signature is not found).
2. Fetch just the central directory to enumerate every entry name, size,
   and CRC32 without touching file data.
3. For entries we want, fetch only their local-header + compressed bytes
   and inflate them in memory.

Every extracted file's CRC32 is verified against the value recorded in
the central directory so a truncated or corrupted range read is caught
rather than silently accepted.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass

import requests

EOCD_SIG = b"PK\x05\x06"
CENTRAL_DIR_SIG = b"PK\x01\x02"
LOCAL_HEADER_SIG = b"PK\x03\x04"

_TAIL_SIZES = (65536, 1 << 20, 8 << 20)


class ZipRangeError(RuntimeError):
    pass


@dataclass(frozen=True)
class ZipEntry:
    name: str
    method: int
    compressed_size: int
    uncompressed_size: int
    crc32: int
    local_header_offset: int


def _http_range(session: requests.Session, url: str, start: int | None, end: int | None) -> bytes:
    if start is not None and start < 0:
        range_header = f"bytes={start}"
    else:
        range_header = f"bytes={start}-{end}"
    resp = session.get(url, headers={"Range": range_header}, timeout=60)
    if resp.status_code not in (200, 206):
        raise ZipRangeError(f"range request failed ({resp.status_code}) for {url}")
    return resp.content


def _find_eocd(session: requests.Session, url: str) -> bytes:
    for size in _TAIL_SIZES:
        tail = _http_range(session, url, -size, None)
        idx = tail.rfind(EOCD_SIG)
        if idx != -1:
            return tail[idx:]
    raise ZipRangeError(f"could not locate EOCD record in {url}")


def list_entries(url: str, session: requests.Session | None = None) -> list[ZipEntry]:
    """Enumerate a remote ZIP's contents without downloading file data."""
    owns_session = session is None
    session = session or requests.Session()
    try:
        eocd = _find_eocd(session, url)
        if len(eocd) < 22:
            raise ZipRangeError("truncated EOCD record")
        (_, _disk_no, _cd_disk, _disk_entries, total_entries, cd_size, cd_offset, _comment_len) = (
            struct.unpack("<4sHHHHIIH", eocd[:22])
        )
        if cd_offset == 0xFFFFFFFF or cd_size == 0xFFFFFFFF:
            raise ZipRangeError("ZIP64 central directory not supported")

        cd_bytes = _http_range(session, url, cd_offset, cd_offset + cd_size - 1)
        entries: list[ZipEntry] = []
        off = 0
        while off < len(cd_bytes):
            if cd_bytes[off : off + 4] != CENTRAL_DIR_SIG:
                break
            hdr = cd_bytes[off : off + 46]
            (
                _sig,
                _vmade,
                _vneed,
                _flags,
                method,
                _mtime,
                _mdate,
                crc,
                csize,
                usize,
                nlen,
                elen,
                clen,
                _disk,
                _iattr,
                _eattr,
                lho,
            ) = struct.unpack("<4s6H3I5H2I", hdr)
            name = cd_bytes[off + 46 : off + 46 + nlen].decode("utf-8", "replace")
            entries.append(ZipEntry(name, method, csize, usize, crc, lho))
            off += 46 + nlen + elen + clen

        if len(entries) != total_entries:
            raise ZipRangeError(
                f"central directory entry count mismatch: expected {total_entries}, parsed {len(entries)}"
            )
        return entries
    finally:
        if owns_session:
            session.close()


def extract_entry(url: str, entry: ZipEntry, session: requests.Session | None = None) -> bytes:
    """Fetch and inflate a single ZIP entry's bytes, verifying its CRC32."""
    owns_session = session is None
    session = session or requests.Session()
    try:
        # Local header is 30 bytes plus name/extra fields of unknown-but-bounded
        # length; over-fetch a fixed margin and re-fetch further if needed.
        margin = 512
        start = entry.local_header_offset
        end = start + 30 + margin + entry.compressed_size
        chunk = _http_range(session, url, start, end)

        if chunk[:4] != LOCAL_HEADER_SIG:
            raise ZipRangeError(f"bad local file header for {entry.name}")
        (_sig, _ver, _flags, method, _mtime, _mdate, _crc, _csize, _usize, nlen, elen) = struct.unpack(
            "<4s5H3I2H", chunk[:30]
        )
        body_start = 30 + nlen + elen
        needed = body_start + entry.compressed_size
        if len(chunk) < needed:
            chunk += _http_range(session, url, start + len(chunk), start + needed - 1)
        compressed = chunk[body_start : body_start + entry.compressed_size]

        if method == 0:
            data = compressed
        elif method == 8:
            data = zlib.decompressobj(-15).decompress(compressed)
        else:
            raise ZipRangeError(f"unsupported compression method {method} for {entry.name}")

        actual_crc = zlib.crc32(data) & 0xFFFFFFFF
        if actual_crc != entry.crc32:
            raise ZipRangeError(
                f"CRC mismatch for {entry.name}: expected {entry.crc32:#x}, got {actual_crc:#x}"
            )
        return data
    finally:
        if owns_session:
            session.close()
