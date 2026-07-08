'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'

type SearchItem = {
  id: string
  route_slug: string
  title: string
  entity_type: 'page' | 'post'
  excerpt_plain?: string
  search_text?: string
  is_index_like?: boolean
}

type Props = {
  items: SearchItem[]
}

function normalize(value: string) {
  return value
    .toLowerCase()
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
}

function itemHref(item: SearchItem) {
  return item.entity_type === 'post'
    ? `/posts/${item.route_slug}`
    : `/pages/${item.route_slug}`
}

export default function SearchClient({ items }: Props) {
  const [query, setQuery] = useState('')
  const [kind, setKind] = useState<'all' | 'post' | 'page'>('all')

  const results = useMemo(() => {
    const q = normalize(query.trim())

    if (!q) {
      return items.slice(0, 30)
    }

    const tokens = q.split(/\s+/).filter(Boolean)

    return items
      .filter((item) => {
        if (kind !== 'all' && item.entity_type !== kind) return false

        const haystack = normalize(
          [
            item.title,
            item.excerpt_plain,
            item.search_text,
            item.entity_type,
          ]
            .filter(Boolean)
            .join(' ')
        )

        return tokens.every((token) => haystack.includes(token))
      })
      .slice(0, 50)
  }, [items, query, kind])

  return (
    <section className="mt-8">
      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <label htmlFor="search" className="text-sm font-medium text-gray-700">
          Query
        </label>

        <input
          id="search"
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Try: tesis, materias, inscripción, horarios..."
          className="mt-2 w-full rounded-lg border border-gray-300 px-4 py-3 text-sm outline-none focus:border-gray-900"
        />

        <div className="mt-4 flex flex-wrap gap-2 text-sm">
          {(['all', 'post', 'page'] as const).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setKind(value)}
              className={
                kind === value
                  ? 'rounded-full bg-gray-900 px-3 py-1 text-white'
                  : 'rounded-full border border-gray-300 px-3 py-1 text-gray-700 hover:bg-gray-100'
              }
            >
              {value === 'all' ? 'All' : value === 'post' ? 'Posts' : 'Pages'}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 text-sm text-gray-500">
        Showing {results.length} result{results.length === 1 ? '' : 's'}.
      </div>

      <div className="mt-4 divide-y divide-gray-200 rounded-xl border border-gray-200 bg-white">
        {results.map((item) => (
          <article key={item.id} className="px-5 py-4">
            <div className="text-xs uppercase tracking-wide text-gray-500">
              {item.entity_type}
            </div>

            <h2 className="mt-1 text-lg font-semibold">
              <Link href={itemHref(item)} className="hover:underline">
                {item.title}
              </Link>
            </h2>

            {item.excerpt_plain && (
              <p className="mt-2 line-clamp-2 text-sm leading-6 text-gray-700">
                {item.excerpt_plain}
              </p>
            )}

            <Link
              href={itemHref(item)}
              className="mt-3 inline-block text-sm font-medium text-blue-700 hover:underline"
            >
              Open preview
            </Link>
          </article>
        ))}

        {results.length === 0 && (
          <div className="px-5 py-8 text-sm text-gray-500">
            No results found.
          </div>
        )}
      </div>
    </section>
  )
}
