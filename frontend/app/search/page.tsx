import Link from 'next/link'
import SearchClient from './search-client'
import fs from 'fs'
import path from 'path'

type SearchItem = {
  id: string
  route_slug: string
  title: string
  entity_type: 'page' | 'post'
  excerpt_plain?: string
  search_text?: string
  is_index_like?: boolean
}

function getSearchItems(): SearchItem[] {
  const fullPath = path.join(process.cwd(), 'data', 'lcd_bundle', 'search.json')
  return JSON.parse(fs.readFileSync(fullPath, 'utf-8')) as SearchItem[]
}

export default function SearchPage() {
  const items = getSearchItems()

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Search</h1>
        <p className="mt-3 max-w-2xl text-gray-700">
          Search posts and evergreen pages from the LCD bundle.
        </p>
        <p className="mt-2 text-sm text-gray-500">
          {items.length} indexed items.
        </p>
      </header>

      <SearchClient items={items} />

      <div className="mt-10 border-t border-gray-200 pt-6 text-sm text-gray-500">
        <Link href="/posts" className="text-blue-700 hover:underline">
          Browse posts
        </Link>
        <span className="mx-2">·</span>
        <Link href="/pages" className="text-blue-700 hover:underline">
          Browse pages
        </Link>
      </div>
    </main>
  )
}
