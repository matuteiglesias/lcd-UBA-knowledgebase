## lcd_kb_pipeline + lcd_page_surface
- Status: moved from support / decision into **working frontend proof achieved**
- Carry: **Watch**
- Horizon: **This week**
- Needs: **Light follow-up / polish only**
- Principal: Recommended

### What changed
The LCD ingestion-to-frontend path is now real.

We now have:
- canonical data root discipline: `data/lcd`, not `src/data/lcd`
- Makefile operational surface
- passing tests: `32 passed`
- successful trusted smoke build
- richer latest pointer contract
- frontend bundle export with:
  - `listing.json`
  - `posts.json`
  - `pages.json`
  - `search.json`
  - `items/*.json`
- minimal Next.js frontend
- `/posts` chronological archive with pagination
- `/pages` evergreen page directory
- `/search` client-side search over `search.json`
- improved homepage structure
- source-first behavior: cards and lists can act as directory entries to original LCD content

### Evidence
- `make test` passed
- `make build RUN_ID=local_contract_check_...` passed
- `make front-bundle` passed
- `make front-bundle-check` passed
- live preview rendered:
  - homepage
  - posts
  - pages
  - search
  - post/page previews

### Important caveat
The real live run produced useful data:
- 19 pages
- 200 posts
- 219 indexed items

but strict validation blocked promotion because of:
- duplicate source URL: `horarios-de-consulta`
- 3 video-only posts with HTML but empty extracted text

Interpretation: this is source/content noise, not frontend failure. For the directory-style site, these should likely become warnings or “soft validation” cases, not hard blockers.

### Next touch exacto
Decide whether to introduce a **frontend-preview / soft-trusted run mode**:
- strict trusted KB corpus remains strict
- frontend directory bundle can be exported from staging or warning-level runs
- duplicate page/post URLs and video-only posts should not block directory publishing

### Recommended next small block
1. Add `front-bundle-url-check` as a script-based Make target.
2. Decide validation severity levels:
   - hard failure: missing parents, empty chunks, count mismatch, bad source URLs
   - warning: duplicate source URL across page/post, iframe-only posts with no text
3. Re-run live fetch/build and promote if warnings are accepted.
4. Deploy frontend to Vercel.

### Parking
- page hierarchy
- curated display titles
- richer UI
- Pagefind/FlexSearch
- real semantic grouping of evergreen pages