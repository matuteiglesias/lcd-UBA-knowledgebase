from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_run_id(timestamp: str | None = None) -> str:
    value = timestamp or utc_now()
    return f"lcd_ingest_{value.replace(':', '').replace('-', '')}"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def count_jsonl_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def build_manifest(
    *,
    run_id: str,
    started_at: str,
    completed_at: str,
    entity_counts: dict[str, int],
    artifacts: list[dict],
    result: str = "success",
    run_status: str = "completed_trusted",
    trust_level: str = "trusted",
    notes: list[str] | None = None,
) -> dict:
    return {
        "contract": "run_manifest.v1",
        "run_id": run_id,
        "site_id": "lcd.exactas.uba.ar",
        "started_at": started_at,
        "completed_at": completed_at,
        "result": result,
        "run_status": run_status,
        "trust_level": trust_level,
        "entity_counts": entity_counts,
        "artifacts": artifacts,
        "notes": notes or [],
    }


def manifest_for_outputs(
    *,
    run_id: str,
    started_at: str,
    completed_at: str,
    normalized_paths: dict[str, Path],
    chunk_paths: dict[str, Path],
    raw_dirs: dict[str, Path],
) -> dict:
    entity_counts = {entity: count_jsonl_rows(path) for entity, path in normalized_paths.items()}
    artifacts = []
    for entity, normalized_path in normalized_paths.items():
        if normalized_path.exists():
            artifacts.append(
                {
                    "path": str(normalized_path),
                    "kind": f"normalized_{entity}_jsonl",
                    "sha256": file_sha256(normalized_path),
                    "rows": count_jsonl_rows(normalized_path),
                }
            )
    for entity, chunk_path in chunk_paths.items():
        if chunk_path.exists():
            artifacts.append(
                {
                    "path": str(chunk_path),
                    "kind": f"chunks_{entity}_jsonl",
                    "sha256": file_sha256(chunk_path),
                    "rows": count_jsonl_rows(chunk_path),
                }
            )
    for entity, directory in raw_dirs.items():
        raw_files = sorted(directory.glob("*.json")) if directory.exists() else []
        artifacts.append(
            {
                "path": str(directory),
                "kind": f"raw_{entity}",
                "files": len(raw_files),
            }
        )
    return build_manifest(
        run_id=run_id,
        started_at=started_at,
        completed_at=completed_at,
        entity_counts=entity_counts,
        artifacts=artifacts,
        run_status="completed_untrusted",
        trust_level="untrusted",
        notes=["Manifest generated from current raw and normalized outputs."],
    )


def write_manifest(path: Path, manifest: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
