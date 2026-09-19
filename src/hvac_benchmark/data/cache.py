"""Disk cache for extracted Brick files with checksum + provenance tracking.

Every cached file is written alongside a `.provenance.json` sidecar
recording where it came from, when, its checksums, and licensing/citation
metadata, so `results/provenance.json` can be assembled without re-hitting
the network.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProvenanceRecord:
    logical_name: str
    source: str
    archive_url: str
    archive_entry_name: str
    archive_entry_crc32: str
    sha256: str
    size_bytes: int
    retrieved_at: str
    license: str | None
    citation: str | None
    source_revision: str | None = None
    fallback_reason: str | None = None


class FileCache:
    def __init__(self, cache_dir: str | Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _paths(self, logical_name: str) -> tuple[Path, Path]:
        safe = logical_name.replace("/", "__")
        return (self.cache_dir / safe, self.cache_dir / f"{safe}.provenance.json")

    def has(self, logical_name: str) -> bool:
        data_path, prov_path = self._paths(logical_name)
        return data_path.exists() and prov_path.exists()

    def get_bytes(self, logical_name: str) -> bytes:
        data_path, _ = self._paths(logical_name)
        return data_path.read_bytes()

    def get_provenance(self, logical_name: str) -> ProvenanceRecord:
        _, prov_path = self._paths(logical_name)
        return ProvenanceRecord(**json.loads(prov_path.read_text()))

    def put(
        self,
        logical_name: str,
        data: bytes,
        *,
        source: str,
        archive_url: str,
        archive_entry_name: str,
        archive_entry_crc32: int,
        license: str | None,
        citation: str | None,
        source_revision: str | None = None,
        fallback_reason: str | None = None,
    ) -> ProvenanceRecord:
        data_path, prov_path = self._paths(logical_name)
        data_path.write_bytes(data)
        record = ProvenanceRecord(
            logical_name=logical_name,
            source=source,
            archive_url=archive_url,
            archive_entry_name=archive_entry_name,
            archive_entry_crc32=f"{archive_entry_crc32:#010x}",
            sha256=hashlib.sha256(data).hexdigest(),
            size_bytes=len(data),
            retrieved_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            license=license,
            citation=citation,
            source_revision=source_revision,
            fallback_reason=fallback_reason,
        )
        prov_path.write_text(json.dumps(asdict(record), indent=2))
        return record

    def all_provenance(self) -> list[ProvenanceRecord]:
        records = []
        for prov_path in sorted(self.cache_dir.glob("*.provenance.json")):
            records.append(ProvenanceRecord(**json.loads(prov_path.read_text())))
        return records
