from __future__ import annotations

import argparse
import json
from pathlib import Path

from lcd_kb.checks.validation import validate_corpus
from lcd_kb.consumers.indexer import build_title_slug_index, write_index
from lcd_kb.consumers.reader import get_record_by_slug, search_records, stats
from lcd_kb.normalize.chunking import chunk_jsonl
from lcd_kb.normalize.page_doc import normalize_entity_dir
from lcd_kb.registry.manifest import default_run_id, manifest_for_outputs, utc_now, write_manifest
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
    build_cmd.add_argument('--page-raw', default='data/lcd/raw/pages')
    build_cmd.add_argument('--post-raw', default='data/lcd/raw/posts')
    build_cmd.add_argument('--page-output', default='data/lcd/normalized/page_doc.v1.jsonl')
    build_cmd.add_argument('--post-output', default='data/lcd/normalized/post_doc.v1.jsonl')
    build_cmd.add_argument('--page-chunks', default='data/lcd/chunks/page_chunk_doc.v1.jsonl')
    build_cmd.add_argument('--post-chunks', default='data/lcd/chunks/post_chunk_doc.v1.jsonl')
    build_cmd.add_argument('--index-output', default='data/lcd/indexes/title_slug_index.json')
    build_cmd.add_argument('--manifest-output', default='data/lcd/manifests/run_manifest.json')
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

    check = subparsers.add_parser('check', help='Run corpus integrity checks')
    check.add_argument('--page-input', default='data/lcd/normalized/page_doc.v1.jsonl')
    check.add_argument('--post-input', default='data/lcd/normalized/post_doc.v1.jsonl')
    check.add_argument('--page-chunks', default='data/lcd/chunks/page_chunk_doc.v1.jsonl')
    check.add_argument('--post-chunks', default='data/lcd/chunks/post_chunk_doc.v1.jsonl')

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


def cmd_fetch(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir) if args.output_dir else default_raw_dir(args.entity)
    result: FetchResult = fetch_entity_batches(
        base_url=args.base_url,
        entity=args.entity,
        output_dir=output_dir,
        per_page=args.per_page,
        max_pages=args.max_pages,
    )
    print(json.dumps({'result': 'pass', 'entity': result.entity, 'pages_fetched': result.pages_fetched, 'records_fetched': result.records_fetched, 'raw_files': result.raw_files}, indent=2))
    return 0


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

    page_count = normalize_entity_dir(Path(args.page_raw), page_output, entity='page', run_id=run_id, observed_at=observed_at)
    post_count = normalize_entity_dir(Path(args.post_raw), post_output, entity='post', run_id=run_id, observed_at=observed_at)
    page_chunk_count = chunk_jsonl(page_output, page_chunks, max_chars=args.max_chars)
    post_chunk_count = chunk_jsonl(post_output, post_chunks, max_chars=args.max_chars)
    index_rows = build_title_slug_index(page_path=page_output, post_path=post_output)
    write_index(index_output, index_rows)

    validation = validate_corpus(page_path=page_output, post_path=post_output, page_chunk_path=page_chunks, post_chunk_path=post_chunks)
    manifest = manifest_for_outputs(
        run_id=run_id,
        started_at=started_at,
        completed_at=completed_at,
        normalized_paths={'page': page_output, 'post': post_output},
        chunk_paths={'page': page_chunks, 'post': post_chunks},
        raw_dirs={'page': Path(args.page_raw), 'post': Path(args.post_raw)},
    )
    manifest['artifacts'].append({'path': str(index_output), 'kind': 'title_slug_index', 'rows': len(index_rows)})
    if not validation['ok']:
        manifest['result'] = 'fail'
        manifest['notes'].append('Validation failed during build.')
    write_manifest(manifest_output, manifest)

    result = {
        'result': 'pass' if validation['ok'] else 'fail',
        'run_id': run_id,
        'normalized': {'page': page_count, 'post': post_count},
        'chunks': {'page': page_chunk_count, 'post': post_chunk_count},
        'index_rows': len(index_rows),
        'validation': validation,
        'manifest_output': str(manifest_output),
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


def cmd_check(args: argparse.Namespace) -> int:
    required_paths = [Path('docs/lcd_ingest_scope_v1.md'), Path('docs/runbook_lcd_ingest.md'), Path('schemas/page_doc_v1.json'), Path('schemas/chunk_doc_v1.json'), Path('schemas/run_manifest_v1.json')]
    missing_required = [str(path) for path in required_paths if not path.exists()]
    validation = validate_corpus(page_path=Path(args.page_input), post_path=Path(args.post_input), page_chunk_path=Path(args.page_chunks), post_chunk_path=Path(args.post_chunks))
    ok = not missing_required and validation['ok']
    print(json.dumps({'result': 'pass' if ok else 'fail', 'missing_required': missing_required, 'validation': validation}, indent=2))
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
    if args.command == 'check':
        return cmd_check(args)
    if args.command == 'manifest':
        return cmd_manifest(args)

    parser.error(f'Unhandled command: {args.command}')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
