from __future__ import annotations

import argparse
import json
from pathlib import Path

from lcd_kb.checks.validation import validate_corpus, write_validation_report
from lcd_kb.consumers.indexer import build_title_slug_index, write_index
from lcd_kb.consumers.reader import get_record_by_slug, search_records, stats
from lcd_kb.normalize.chunking import chunk_jsonl
from lcd_kb.normalize.page_doc import normalize_entity_dir
from lcd_kb.registry.manifest import default_run_id, manifest_for_outputs, utc_now, write_manifest
from lcd_kb.registry.run_lifecycle import (
    STATUS_BUILD_FAILED,
    STATUS_COMPLETED_TRUSTED,
    STATUS_STARTED,
    STATUS_VALIDATION_FAILED,
    build_drift_report,
    ensure_run_layout,
    finalize_run_artifacts,
    load_json,
    promote_trusted_artifacts,
    read_pointer,
    update_pointer,
    write_json,
    write_jsonl,
    write_run_status,
)
from lcd_kb.sources.wordpress_rest import DEFAULT_BASE_URL, FetchResult, fetch_entity_batches


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='lcd-kb', description='LCD knowledgebase pipeline scaffold')
    subparsers = parser.add_subparsers(dest='command', required=True)

    fetch = subparsers.add_parser('fetch', help='Fetch bounded WordPress REST batches')
    fetch.add_argument('--entity', required=True, choices=['page', 'post'], help='Entity type to fetch')
    fetch.add_argument('--base-url', default=DEFAULT_BASE_URL, help='WordPress site base URL')
    fetch.add_argument('--output-dir', help='Directory to write raw JSON batches')
    fetch.add_argument('--per-page', type=int, default=25, help='Items per REST page')
    fetch.add_argument('--max-pages', type=int, default=None, help='Optional page cap for smoke runs')
    fetch.add_argument('--summary-output', help='Optional path to write fetch summary JSON')
    fetch.add_argument('--errors-output', help='Optional path to write fetch errors JSONL')

    normalize = subparsers.add_parser('normalize', help='Normalize raw batches into page_doc.v1 JSONL')
    normalize.add_argument('--entity', required=True, choices=['page', 'post'], help='Entity type to normalize')
    normalize.add_argument('--raw-dir', help='Directory containing raw JSON batches')
    normalize.add_argument('--output', help='Normalized JSONL output path')
    normalize.add_argument('--run-id', help='Run identifier to stamp into normalized records')
    normalize.add_argument('--observed-at', help='Observed timestamp in UTC')

    chunk = subparsers.add_parser('chunk', help='Chunk normalized page_doc.v1 JSONL into chunk_doc.v1 JSONL')
    chunk.add_argument('--entity', required=True, choices=['page', 'post'], help='Entity type to chunk')
    chunk.add_argument('--input', help='Normalized JSONL input path')
    chunk.add_argument('--output', help='Chunk JSONL output path')
    chunk.add_argument('--max-chars', type=int, default=400, help='Maximum characters per chunk')

    index_cmd = subparsers.add_parser('build-index', help='Build a title/slug index from normalized page and post docs')
    index_cmd.add_argument('--page-input', default='data/lcd/normalized/page_doc.v1.jsonl')
    index_cmd.add_argument('--post-input', default='data/lcd/normalized/post_doc.v1.jsonl')
    index_cmd.add_argument('--output', default='data/lcd/indexes/title_slug_index.json')

    build_cmd = subparsers.add_parser('build', help='Run the local raw->normalized->chunked->checked->indexed build pipeline')
    build_cmd.add_argument('--run-id', help='Run identifier to stamp into outputs')
    build_cmd.add_argument('--observed-at', help='Observed timestamp in UTC')
    build_cmd.add_argument('--started-at', help='Run start timestamp')
    build_cmd.add_argument('--completed-at', help='Run completion timestamp')
    build_cmd.add_argument('--run-root', default=str(DEFAULT_RUN_ROOT), help='Directory containing per-run build artifacts')
    build_cmd.add_argument('--latest-success', default=str(DEFAULT_LATEST_SUCCESS_PATH), help='Path to update with the latest successful run pointer')
    build_cmd.add_argument('--page-raw', default='data/lcd/raw/pages')
    build_cmd.add_argument('--post-raw', default='data/lcd/raw/posts')
    build_cmd.add_argument('--page-output', default='data/lcd/normalized/page_doc.v1.jsonl')
    build_cmd.add_argument('--post-output', default='data/lcd/normalized/post_doc.v1.jsonl')
    build_cmd.add_argument('--page-chunks', default='data/lcd/chunks/page_chunk_doc.v1.jsonl')
    build_cmd.add_argument('--post-chunks', default='data/lcd/chunks/post_chunk_doc.v1.jsonl')
    build_cmd.add_argument('--index-output', default='data/lcd/indexes/title_slug_index.json')
    build_cmd.add_argument('--manifest-output', default='data/lcd/manifests/run_manifest.json')
    build_cmd.add_argument('--registry-dir', default='data/lcd/registry')
    build_cmd.add_argument('--runs-dir', default='data/lcd/runs')
    build_cmd.add_argument('--max-chars', type=int, default=400)

    search = subparsers.add_parser('search', help='Search chunk or page records locally')
    search.add_argument('query', help='Search query')
    search.add_argument('--input', default='data/lcd/chunks/page_chunk_doc.v1.jsonl', help='JSONL path to search')
    search.add_argument('--limit', type=int, default=10, help='Maximum matches to return')

    open_cmd = subparsers.add_parser('open', help='Open a page record by slug')
    open_cmd.add_argument('--slug', required=True, help='Slug to locate')
    open_cmd.add_argument('--input', default='data/lcd/normalized/page_doc.v1.jsonl', help='Normalized JSONL path')

    stats_cmd = subparsers.add_parser('stats', help='Show local artifact counts')
    stats_cmd.add_argument('--page-input', default='data/lcd/normalized/page_doc.v1.jsonl')
    stats_cmd.add_argument('--post-input', default='data/lcd/normalized/post_doc.v1.jsonl')
    stats_cmd.add_argument('--page-chunks', default='data/lcd/chunks/page_chunk_doc.v1.jsonl')
    stats_cmd.add_argument('--post-chunks', default='data/lcd/chunks/post_chunk_doc.v1.jsonl')

    latest_cmd = subparsers.add_parser('latest', help='Show the latest successful run pointer')
    latest_cmd.add_argument('--latest-success', default=str(DEFAULT_LATEST_SUCCESS_PATH))

    latest_artifacts = subparsers.add_parser('latest-artifacts', help='List artifacts for the latest successful run')
    latest_artifacts.add_argument('--latest-success', default=str(DEFAULT_LATEST_SUCCESS_PATH))

    inspect_run = subparsers.add_parser('inspect-run', help='Inspect a specific run directory')
    inspect_run.add_argument('--run-id', required=True)
    inspect_run.add_argument('--run-root', default=str(DEFAULT_RUN_ROOT))

    check = subparsers.add_parser('check', help='Run corpus integrity checks')
    check.add_argument('--page-input', default='data/lcd/normalized/page_doc.v1.jsonl')
    check.add_argument('--post-input', default='data/lcd/normalized/post_doc.v1.jsonl')
    check.add_argument('--page-chunks', default='data/lcd/chunks/page_chunk_doc.v1.jsonl')
    check.add_argument('--post-chunks', default='data/lcd/chunks/post_chunk_doc.v1.jsonl')
    check.add_argument('--raw-page-dir', default='data/lcd/raw/pages')
    check.add_argument('--raw-post-dir', default='data/lcd/raw/posts')
    check.add_argument('--report-output', help='Optional path to write machine-readable validation JSON')

    manifest = subparsers.add_parser('manifest', help='Write a run manifest from current artifacts')
    manifest.add_argument('--output', default='data/lcd/manifests/run_manifest.json', help='Path to write manifest JSON')
    manifest.add_argument('--page-normalized', default='data/lcd/normalized/page_doc.v1.jsonl', help='Normalized page JSONL artifact')
    manifest.add_argument('--post-normalized', default='data/lcd/normalized/post_doc.v1.jsonl', help='Normalized post JSONL artifact')
    manifest.add_argument('--page-chunks', default='data/lcd/chunks/page_chunk_doc.v1.jsonl', help='Page chunk JSONL artifact')
    manifest.add_argument('--post-chunks', default='data/lcd/chunks/post_chunk_doc.v1.jsonl', help='Post chunk JSONL artifact')
    manifest.add_argument('--raw-page-dir', default='data/lcd/raw/pages', help='Raw page batches directory')
    manifest.add_argument('--raw-post-dir', default='data/lcd/raw/posts', help='Raw post batches directory')
    manifest.add_argument('--run-id', help='Run identifier to record in the manifest')
    manifest.add_argument('--started-at', help='Run start timestamp')
    manifest.add_argument('--completed-at', help='Run completion timestamp')

    return parser


def default_raw_dir(entity: str) -> Path:
    return Path(f'data/lcd/raw/{entity}s')


def default_output_path(entity: str) -> Path:
    return Path(f'data/lcd/normalized/{entity}_doc.v1.jsonl')


def default_chunk_path(entity: str) -> Path:
    return Path(f'data/lcd/chunks/{entity}_chunk_doc.v1.jsonl')


def resolve_run_artifact_paths(run_root: Path, run_id: str) -> dict[str, Path]:
    run_dir = run_root / run_id
    return {
        'run_dir': run_dir,
        'page_output': run_dir / 'normalized' / 'page_doc.v1.jsonl',
        'post_output': run_dir / 'normalized' / 'post_doc.v1.jsonl',
        'page_chunks': run_dir / 'chunks' / 'page_chunk_doc.v1.jsonl',
        'post_chunks': run_dir / 'chunks' / 'post_chunk_doc.v1.jsonl',
        'index_output': run_dir / 'indexes' / 'title_slug_index.json',
        'manifest_output': run_dir / 'manifests' / 'run_manifest.json',
        'validation_report': run_dir / 'reports' / 'validation_report.json',
        'inventory_output': run_dir / 'registry' / 'artifact_inventory.json',
    }


def cmd_fetch(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir) if args.output_dir else default_raw_dir(args.entity)
    summary_output, errors_output = default_fetch_report_paths(output_dir, args.entity)
    if args.summary_output:
        summary_output = Path(args.summary_output)
    if args.errors_output:
        errors_output = Path(args.errors_output)

    result: FetchResult = fetch_entity_batches(
        base_url=args.base_url,
        entity=args.entity,
        output_dir=output_dir,
        per_page=args.per_page,
        max_pages=args.max_pages,
    )
    write_fetch_summary(summary_output, result.summary)
    write_fetch_errors(errors_output, result.errors)
    print(json.dumps({'result': 'pass' if not result.errors else 'fail', 'entity': result.entity, 'pages_fetched': result.pages_fetched, 'records_fetched': result.records_fetched, 'raw_files': result.raw_files, 'summary_output': str(summary_output), 'errors_output': str(errors_output), 'error_count': len(result.errors)}, indent=2))
    return 0 if not result.errors else 1


def cmd_normalize(args: argparse.Namespace) -> int:
    run_id = args.run_id or default_run_id()
    observed_at = args.observed_at or utc_now()
    raw_dir = Path(args.raw_dir) if args.raw_dir else default_raw_dir(args.entity)
    output_path = Path(args.output) if args.output else default_output_path(args.entity)
    count = normalize_entity_dir(raw_dir, output_path, entity=args.entity, run_id=run_id, observed_at=observed_at)
    print(json.dumps({'result': 'pass', 'entity': args.entity, 'records_normalized': count, 'output': str(output_path)}, indent=2))
    return 0


def cmd_chunk(args: argparse.Namespace) -> int:
    input_path = Path(args.input) if args.input else default_output_path(args.entity)
    output_path = Path(args.output) if args.output else default_chunk_path(args.entity)
    count = chunk_jsonl(input_path, output_path, max_chars=args.max_chars)
    print(json.dumps({'result': 'pass', 'entity': args.entity, 'chunks_written': count, 'output': str(output_path)}, indent=2))
    return 0


def cmd_build_index(args: argparse.Namespace) -> int:
    rows = build_title_slug_index(page_path=Path(args.page_input), post_path=Path(args.post_input))
    write_index(Path(args.output), rows)
    print(json.dumps({'result': 'pass', 'rows': len(rows), 'output': args.output}, indent=2, ensure_ascii=False))
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    run_id = args.run_id or default_run_id()
    observed_at = args.observed_at or utc_now()
    started_at = args.started_at or utc_now()
    completed_at = args.completed_at or utc_now()

    page_output = Path(args.page_output)
    post_output = Path(args.post_output)
    page_chunks = Path(args.page_chunks)
    post_chunks = Path(args.post_chunks)
    index_output = Path(args.index_output)
    manifest_output = Path(args.manifest_output)
    registry_dir = Path(args.registry_dir)
    run_root = Path(args.runs_dir) / run_id
    run_layout = ensure_run_layout(run_root)

    staging_paths = {
        'page_output': run_layout['staging'] / 'page_doc.v1.jsonl',
        'post_output': run_layout['staging'] / 'post_doc.v1.jsonl',
        'page_chunks': run_layout['staging'] / 'page_chunk_doc.v1.jsonl',
        'post_chunks': run_layout['staging'] / 'post_chunk_doc.v1.jsonl',
        'index_output': run_layout['staging'] / 'title_slug_index.json',
    }
    final_run_paths = {
        'page_output': run_layout['normalized'] / 'page_doc.v1.jsonl',
        'post_output': run_layout['normalized'] / 'post_doc.v1.jsonl',
        'page_chunks': run_layout['chunks'] / 'page_chunk_doc.v1.jsonl',
        'post_chunks': run_layout['chunks'] / 'post_chunk_doc.v1.jsonl',
        'index_output': run_layout['indexes'] / 'title_slug_index.json',
    }
    canonical_paths = {
        'page_output': page_output,
        'post_output': post_output,
        'page_chunks': page_chunks,
        'post_chunks': post_chunks,
        'index_output': index_output,
    }

    latest_trusted_pointer = registry_dir / 'latest_trusted.json'
    latest_success_pointer = registry_dir / 'latest_success.json'
    latest_attempted_pointer = registry_dir / 'latest_attempted.json'
    previous_trusted_pointer = read_pointer(latest_trusted_pointer)
    previous_trusted_manifest = None
    if previous_trusted_pointer and previous_trusted_pointer.get('manifest_path'):
        previous_trusted_manifest = load_json(Path(previous_trusted_pointer['manifest_path']))

    status_path = run_layout['registry'] / 'run_status.json'
    write_run_status(
        status_path,
        {
            'contract': 'run_status.v1',
            'run_id': run_id,
            'status': STATUS_STARTED,
            'result': 'running',
            'started_at': started_at,
            'completed_at': None,
            'promotion_performed': False,
            'trusted': False,
            'notes': ['Build started; artifacts will remain in staging until validation passes.'],
        },
    )

    try:
        page_count = normalize_entity_dir(Path(args.page_raw), staging_paths['page_output'], entity='page', run_id=run_id, observed_at=observed_at)
        post_count = normalize_entity_dir(Path(args.post_raw), staging_paths['post_output'], entity='post', run_id=run_id, observed_at=observed_at)
        page_chunk_count = chunk_jsonl(staging_paths['page_output'], staging_paths['page_chunks'], max_chars=args.max_chars)
        post_chunk_count = chunk_jsonl(staging_paths['post_output'], staging_paths['post_chunks'], max_chars=args.max_chars)
        index_rows = build_title_slug_index(page_path=staging_paths['page_output'], post_path=staging_paths['post_output'])
        write_index(staging_paths['index_output'], index_rows)
    except Exception as exc:
        completed_at = args.completed_at or utc_now()
        write_run_status(
            status_path,
            {
                'contract': 'run_status.v1',
                'run_id': run_id,
                'status': STATUS_BUILD_FAILED,
                'result': 'fail',
                'started_at': started_at,
                'completed_at': completed_at,
                'promotion_performed': False,
                'trusted': False,
                'notes': [f'Build failed before validation: {exc}'],
            },
        )
        update_pointer(
            latest_attempted_pointer,
            {
                'run_id': run_id,
                'status': STATUS_BUILD_FAILED,
                'manifest_path': str(run_root / 'registry' / 'run_manifest.json'),
                'run_status_path': str(status_path),
                'updated_at': completed_at,
            },
        )
        raise

    validation = validate_corpus(
        page_path=staging_paths['page_output'],
        post_path=staging_paths['post_output'],
        page_chunk_path=staging_paths['page_chunks'],
        post_chunk_path=staging_paths['post_chunks'],
    )
    write_json(run_layout['reports'] / 'validation_report.json', validation)
    anomaly_dir = run_layout['reports'] / 'anomalies'
    anomaly_paths = {
        'duplicate_source_urls': anomaly_dir / 'duplicate_source_urls.jsonl',
        'empty_text_docs': anomaly_dir / 'empty_text_docs.jsonl',
        'orphan_chunks': anomaly_dir / 'orphan_chunks.jsonl',
        'empty_chunks': anomaly_dir / 'empty_chunks.jsonl',
        'fetch_failures': anomaly_dir / 'fetch_failures.jsonl',
    }
    for anomaly_name, output_path in anomaly_paths.items():
        write_jsonl(output_path, validation['anomaly_records'][anomaly_name])
    drift_report = build_drift_report(
        current_run_id=run_id,
        current_page_path=staging_paths['page_output'],
        current_post_path=staging_paths['post_output'],
        previous_trusted_manifest=previous_trusted_manifest,
    )
    write_json(run_layout['reports'] / 'drift_report.json', drift_report)

    run_status = STATUS_COMPLETED_TRUSTED if validation['ok'] else STATUS_VALIDATION_FAILED
    manifest = manifest_for_outputs(
        run_id=run_id,
        started_at=started_at,
        completed_at=completed_at,
        normalized_paths={'page': staging_paths['page_output'], 'post': staging_paths['post_output']},
        chunk_paths={'page': staging_paths['page_chunks'], 'post': staging_paths['post_chunks']},
        raw_dirs={'page': Path(args.page_raw), 'post': Path(args.post_raw)},
    )
    manifest['result'] = 'pass' if validation['ok'] else 'fail'
    manifest['run_status'] = run_status
    manifest['trust_level'] = 'trusted' if validation['ok'] else 'untrusted'
    manifest['promotion'] = {
        'latest_attempted': str(latest_attempted_pointer),
        'latest_success': str(latest_success_pointer),
        'latest_trusted': str(latest_trusted_pointer),
        'promoted': validation['ok'],
    }
    manifest['artifacts'].extend([
        {'path': str(staging_paths['index_output']), 'kind': 'staging_title_slug_index', 'rows': len(index_rows)},
        {'path': str(run_layout['reports'] / 'validation_report.json'), 'kind': 'validation_report'},
        {'path': str(run_layout['reports'] / 'drift_report.json'), 'kind': 'drift_report'},
        {'path': str(status_path), 'kind': 'run_status'},
    ])
    manifest['artifacts'].extend(
        {
            'path': str(path),
            'kind': f'anomaly_{name}',
            'rows': len(validation['anomaly_records'][name]),
        }
        for name, path in anomaly_paths.items()
    )
    if validation['ok']:
        finalize_run_artifacts(staging_paths=staging_paths, final_paths=final_run_paths)
        promote_trusted_artifacts(trusted_paths=final_run_paths, canonical_paths=canonical_paths)
        for artifact in manifest['artifacts']:
            if artifact.get('kind') == 'normalized_page_jsonl':
                artifact['path'] = str(final_run_paths['page_output'])
            elif artifact.get('kind') == 'normalized_post_jsonl':
                artifact['path'] = str(final_run_paths['post_output'])
            elif artifact.get('kind') == 'chunks_page_jsonl':
                artifact['path'] = str(final_run_paths['page_chunks'])
            elif artifact.get('kind') == 'chunks_post_jsonl':
                artifact['path'] = str(final_run_paths['post_chunks'])
        manifest['artifacts'].append({'path': str(final_run_paths['index_output']), 'kind': 'title_slug_index', 'rows': len(index_rows)})
        manifest['notes'].append('Validation passed; staged outputs were finalized and promoted as trusted.')
    else:
        manifest['notes'].append('Validation failed; staged outputs were preserved for inspection and not promoted.')

    run_manifest_path = run_layout['registry'] / 'run_manifest.json'
    write_manifest(run_manifest_path, manifest)
    if validation['ok']:
        write_manifest(manifest_output, manifest)

    write_run_status(
        status_path,
        {
            'contract': 'run_status.v1',
            'run_id': run_id,
            'status': run_status,
            'result': manifest['result'],
            'started_at': started_at,
            'completed_at': completed_at,
            'promotion_performed': validation['ok'],
            'trusted': validation['ok'],
            'validation_ok': validation['ok'],
            'validation_report_path': str(run_layout['reports'] / 'validation_report.json'),
            'drift_report_path': str(run_layout['reports'] / 'drift_report.json'),
            'anomaly_directory': str(anomaly_dir),
            'manifest_path': str(run_manifest_path),
            'notes': manifest['notes'],
        },
    )

    latest_attempted_payload = {
        'run_id': run_id,
        'status': run_status,
        'manifest_path': str(run_manifest_path),
        'run_status_path': str(status_path),
        'updated_at': completed_at,
    }
    update_pointer(latest_attempted_pointer, latest_attempted_payload)
    if validation['ok']:
        update_pointer(latest_success_pointer, latest_attempted_payload)
        update_pointer(latest_trusted_pointer, latest_attempted_payload)

    inventory = build_artifact_inventory(
        run_id=run_id,
        run_dir=run_dir,
        manifest_path=manifest_output,
        manifest=manifest,
        index_path=index_output,
        validation_report_path=validation_report_output,
        latest_success_path=latest_success_output,
    )
    write_inventory(inventory_output, inventory)

    latest_success_record = None
    if validation['ok']:
        latest_success_record = build_latest_success_record(
            run_id=run_id,
            completed_at=completed_at,
            run_dir=run_dir,
            manifest_path=manifest_output,
            index_path=index_output,
            validation_report_path=validation_report_output,
            inventory_path=inventory_output,
        )
        write_latest_success(latest_success_output, latest_success_record)

    result = {
        'result': manifest['result'],
        'run_id': run_id,
        'run_status': run_status,
        'normalized': {'page': page_count, 'post': post_count},
        'chunks': {'page': page_chunk_count, 'post': post_chunk_count},
        'index_rows': len(index_rows),
        'validation': validation,
        'drift_report': drift_report,
        'anomaly_dir': str(anomaly_dir),
        'manifest_output': str(run_manifest_path),
        'promoted': validation['ok'],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if validation['ok'] else 1


def cmd_search(args: argparse.Namespace) -> int:
    matches = search_records(Path(args.input), args.query, limit=args.limit)
    print(json.dumps({'result': 'pass', 'matches': matches, 'count': len(matches)}, indent=2, ensure_ascii=False))
    return 0


def cmd_open(args: argparse.Namespace) -> int:
    record = get_record_by_slug(Path(args.input), args.slug)
    if record is None:
        print(json.dumps({'result': 'fail', 'slug': args.slug}, indent=2))
        return 1
    print(json.dumps({'result': 'pass', 'record': record}, indent=2, ensure_ascii=False))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    report = stats({'page_docs': Path(args.page_input), 'post_docs': Path(args.post_input), 'page_chunks': Path(args.page_chunks), 'post_chunks': Path(args.post_chunks)})
    print(json.dumps({'result': 'pass', 'stats': report}, indent=2))
    return 0


def cmd_latest(args: argparse.Namespace) -> int:
    latest_success_path = Path(args.latest_success)
    if not latest_success_path.exists():
        print(json.dumps({'result': 'fail', 'latest_success': str(latest_success_path)}, indent=2))
        return 1
    print(json.dumps({'result': 'pass', 'latest': load_json_file(latest_success_path)}, indent=2, ensure_ascii=False))
    return 0


def cmd_latest_artifacts(args: argparse.Namespace) -> int:
    latest_success_path = Path(args.latest_success)
    if not latest_success_path.exists():
        print(json.dumps({'result': 'fail', 'latest_success': str(latest_success_path)}, indent=2))
        return 1
    latest = load_json_file(latest_success_path)
    inventory_path = Path(latest['inventory_path'])
    inventory = load_json_file(inventory_path)
    print(json.dumps({'result': 'pass', 'run_id': latest['run_id'], 'artifacts': inventory.get('artifacts', [])}, indent=2, ensure_ascii=False))
    return 0


def cmd_inspect_run(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_root) / args.run_id
    inventory_path = run_dir / 'registry' / 'artifact_inventory.json'
    manifest_path = run_dir / 'manifests' / 'run_manifest.json'
    validation_report_path = run_dir / 'reports' / 'validation_report.json'
    missing = [str(path) for path in [inventory_path, manifest_path, validation_report_path] if not path.exists()]
    if missing:
        print(json.dumps({'result': 'fail', 'run_id': args.run_id, 'missing': missing}, indent=2))
        return 1
    inventory = load_json_file(inventory_path)
    manifest = load_json_file(manifest_path)
    validation = load_json_file(validation_report_path)
    summary = {
        'run_id': args.run_id,
        'run_dir': str(run_dir),
        'manifest_result': manifest.get('result'),
        'entity_counts': manifest.get('entity_counts', {}),
        'artifact_count': len(inventory.get('artifacts', [])),
        'validation_ok': validation.get('ok'),
        'checks_with_failures': [name for name, failures in validation.get('checks', {}).items() if failures],
    }
    print(json.dumps({'result': 'pass', 'summary': summary, 'inventory': inventory}, indent=2, ensure_ascii=False))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    required_paths = [Path('docs/lcd_ingest_scope_v1.md'), Path('docs/runbook_lcd_ingest.md'), Path('schemas/page_doc_v1.json'), Path('schemas/chunk_doc_v1.json'), Path('schemas/run_manifest_v1.json')]
    missing_required = [str(path) for path in required_paths if not path.exists()]
    validation = validate_corpus(
        page_path=Path(args.page_input),
        post_path=Path(args.post_input),
        page_chunk_path=Path(args.page_chunks),
        post_chunk_path=Path(args.post_chunks),
        raw_page_dir=Path(args.raw_page_dir),
        raw_post_dir=Path(args.raw_post_dir),
    )
    if args.report_output:
        write_validation_report(Path(args.report_output), validation)
    ok = not missing_required and validation['ok']
    print(json.dumps({'result': 'pass' if ok else 'fail', 'missing_required': missing_required, 'validation': validation, 'report_output': args.report_output}, indent=2))
    return 0 if ok else 1


def cmd_manifest(args: argparse.Namespace) -> int:
    output = Path(args.output)
    started_at = args.started_at or utc_now()
    completed_at = args.completed_at or utc_now()
    run_id = args.run_id or default_run_id(completed_at)
    manifest = manifest_for_outputs(
        run_id=run_id,
        started_at=started_at,
        completed_at=completed_at,
        normalized_paths={'page': Path(args.page_normalized), 'post': Path(args.post_normalized)},
        chunk_paths={'page': Path(args.page_chunks), 'post': Path(args.post_chunks)},
        raw_dirs={'page': Path(args.raw_page_dir), 'post': Path(args.raw_post_dir)},
    )
    write_manifest(output, manifest)
    print(json.dumps({'result': 'pass', 'output': str(output), 'run_id': run_id}, indent=2))
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == 'fetch':
        return cmd_fetch(args)
    if args.command == 'normalize':
        return cmd_normalize(args)
    if args.command == 'chunk':
        return cmd_chunk(args)
    if args.command == 'build-index':
        return cmd_build_index(args)
    if args.command == 'build':
        return cmd_build(args)
    if args.command == 'search':
        return cmd_search(args)
    if args.command == 'open':
        return cmd_open(args)
    if args.command == 'stats':
        return cmd_stats(args)
    if args.command == 'latest':
        return cmd_latest(args)
    if args.command == 'latest-artifacts':
        return cmd_latest_artifacts(args)
    if args.command == 'inspect-run':
        return cmd_inspect_run(args)
    if args.command == 'check':
        return cmd_check(args)
    if args.command == 'manifest':
        return cmd_manifest(args)

    parser.error(f'Unhandled command: {args.command}')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
