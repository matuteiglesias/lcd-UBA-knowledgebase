import fs from 'fs'
import path from 'path'

const bundleDir = path.join(process.cwd(), 'data', 'lcd_bundle')

export type ListingItem = {
  id: string
  entity_type: 'page' | 'post'
  source_id: number
  slug: string
  route_slug: string
  title: string
  source_url: string
  created_at?: string
  modified_at?: string
  sort_date?: string
  excerpt_plain?: string
  has_attachments?: boolean
  attachment_count?: number
  is_index_like?: boolean
  index_like_reason?: string | null
  render_mode?: string
}

export type DetailItem = ListingItem & {
  text?: string
  html_clean?: string
  attachments?: Array<{
    url: string
    label: string
    kind: string
    is_download_like?: boolean
  }>
  outlinks?: Array<{
    url: string
    kind: string
  }>
  content_hash?: string
  search_text?: string
}

function readJson<T>(relativePath: string): T {
  const fullPath = path.join(bundleDir, relativePath)
  return JSON.parse(fs.readFileSync(fullPath, 'utf-8')) as T
}

export function getManifest() {
  return readJson<any>('manifest.json')
}

export function getListing(): ListingItem[] {
  return readJson<{ items: ListingItem[] }>('listing.json').items
}

export function getPosts(): ListingItem[] {
  return readJson<{ items: ListingItem[] }>('posts.json').items
}

export function getPages(): ListingItem[] {
  return readJson<{ items: ListingItem[] }>('pages.json').items
}

export function getItem(routeSlug: string): DetailItem {
  return readJson<DetailItem>(path.join('items', `${routeSlug}.json`))
}

export function getPost(routeSlug: string): DetailItem {
  const item = getItem(routeSlug)
  if (item.entity_type !== 'post') {
    throw new Error(`Expected post, got ${item.entity_type}: ${routeSlug}`)
  }
  return item
}

export function getPage(routeSlug: string): DetailItem {
  const item = getItem(routeSlug)
  if (item.entity_type !== 'page') {
    throw new Error(`Expected page, got ${item.entity_type}: ${routeSlug}`)
  }
  return item
}
