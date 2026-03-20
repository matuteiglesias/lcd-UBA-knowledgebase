from __future__ import annotations

import json
import shutil
from pathlib import Path

from lcd_kb.checks.validation import load_jsonl

STATUS_STARTED = "started"
STATUS_FETCH_FAILED = "fetch_failed"
STATUS_BUILD_FAILED = "build_failed"
STATUS_VALIDATION_FAILED = "validation_failed"
STATUS_COMPLETED_UNTRUSTED = "completed_untrusted"
STATUS_COMPLETED_TRUSTED = "completed_trusted"


def ensure_run_layout(run_root: Path) -> dict[str, Path]:
    paths = {
        "run_root": run_root,
        "staging": run_root / "staging",
        "normalized": run_root / "normalized",
        "chunks": run_root / "chunks",
        "indexes": run_root / "indexes",
        "reports": run_root / "reports",
        "registry": run_root / "registry",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_run_status(path: Path, payload: dict) -> None:
    write_json(path, payload)


def copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def finalize_run_artifacts(*, staging_paths: dict[str, Path], final_paths: dict[str, Path]) -> None:
    for key, src in staging_paths.items():
        copy_file(src, final_paths[key])


def promote_trusted_artifacts(*, trusted_paths: dict[str, Path], canonical_paths: dict[str, Path]) -> None:
    for key, src in trusted_paths.items():
        copy_file(src, canonical_paths[key])


def load_json(path: Path | None) -> dict | None:
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_pointer(path: Path) -> dict | None:
    return load_json(path)


def artifact_path_for_kind(manifest: dict, kind: str) -> Path | None:
    for artifact in manifest.get("artifacts", []):
        if artifact.get("kind") == kind:
            return Path(artifact["path"])
    return None


def _record_index(records: list[dict]) -> dict[str, dict]:
    index = {}
    for record in records:
        source_url = record.get("source_url")
        if source_url:
            index[source_url] = record
    return index


def build_drift_report(
    *,
    current_run_id: str,
    current_page_path: Path,
    current_post_path: Path,
    previous_trusted_manifest: dict | None,
) -> dict:
    current_records = load_jsonl(current_page_path) + load_jsonl(current_post_path)
    current_index = _record_index(current_records)

    previous_run_id = None
    previous_records: list[dict] = []
    if previous_trusted_manifest is not None:
        previous_run_id = previous_trusted_manifest.get("run_id")
        prev_page = artifact_path_for_kind(previous_trusted_manifest, "normalized_page_jsonl")
        prev_post = artifact_path_for_kind(previous_trusted_manifest, "normalized_post_jsonl")
        if prev_page is not None:
            previous_records.extend(load_jsonl(prev_page))
        if prev_post is not None:
            previous_records.extend(load_jsonl(prev_post))
    previous_index = _record_index(previous_records)

    current_urls = set(current_index)
    previous_urls = set(previous_index)
    changed_hash_urls = sorted(
        source_url
        for source_url in current_urls & previous_urls
        if current_index[source_url].get("content_hash") != previous_index[source_url].get("content_hash")
    )

    current_slugs = {record.get("slug") for record in current_records if record.get("slug")}
    previous_slugs = {record.get("slug") for record in previous_records if record.get("slug")}
    added_urls = sorted(current_urls - previous_urls)
    removed_urls = sorted(previous_urls - current_urls)

    suspicious = []
    if removed_urls:
        suspicious.append("removed_urls_detected")
    if len(changed_hash_urls) > max(5, len(current_urls) // 2):
        suspicious.append("high_content_hash_churn")
    if len(current_slugs ^ previous_slugs) > max(10, len(current_slugs) // 2):
        suspicious.append("high_slug_churn")

    return {
        "contract": "drift_report.v1",
        "previous_trusted_run_id": previous_run_id,
        "current_run_id": current_run_id,
        "page_count_delta": sum(1 for record in current_records if record.get("entity_type") == "page")
        - sum(1 for record in previous_records if record.get("entity_type") == "page"),
        "post_count_delta": sum(1 for record in current_records if record.get("entity_type") == "post")
        - sum(1 for record in previous_records if record.get("entity_type") == "post"),
        "added_urls": added_urls,
        "removed_urls": removed_urls,
        "changed_content_hash_count": len(changed_hash_urls),
        "changed_content_hash_urls": changed_hash_urls,
        "slug_churn_count": len(current_slugs ^ previous_slugs),
        "suspicious_thresholds_triggered": suspicious,
    }


def update_pointer(path: Path, payload: dict) -> None:
    write_json(path, payload)
