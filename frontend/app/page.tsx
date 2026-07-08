import Link from 'next/link'
import { getManifest, getPages, getPosts } from '@/lib/lcdBundle'

function formatDate(value?: string) {
  if (!value) return 'No date'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat('es-AR', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  }).format(date)
}

export default function HomePage() {
  const manifest = getManifest()
  const posts = getPosts().slice(0, 6)
  const pages = getPages().slice(0, 8)

  const runId = manifest?.generated_from?.run_id || 'unknown'
  const sourceCounts = manifest?.source_counts || {}
  const exportCounts = manifest?.export_counts || {}

  return (
    <main>
      <section className="border-b border-gray-200 bg-gradient-to-b from-white to-gray-50">
        <div className="mx-auto max-w-5xl px-6 py-16">
          <p className="text-sm font-medium uppercase tracking-wide text-gray-500">
            LCD Knowledge Surface
          </p>

          <div className="mt-4 grid gap-10 lg:grid-cols-[1.3fr_0.7fr] lg:items-end">
            <div>
              <h1 className="max-w-3xl text-5xl font-semibold tracking-tight text-gray-950">
                A cleaner way to browse LCD updates and institutional pages.
              </h1>

              <p className="mt-5 max-w-2xl text-lg leading-8 text-gray-700">
                This site turns the LCD WordPress content into a static,
                searchable reading surface with separate paths for rolling posts
                and evergreen pages.
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                <Link
                  href="/posts"
                  className="rounded-lg bg-gray-950 px-5 py-3 text-sm font-medium text-white hover:bg-gray-800"
                >
                  Browse latest posts
                </Link>
                <Link
                  href="/pages"
                  className="rounded-lg border border-gray-300 bg-white px-5 py-3 text-sm font-medium text-gray-900 hover:bg-gray-100"
                >
                  Explore pages
                </Link>
                <Link
                  href="/search"
                  className="rounded-lg border border-gray-300 bg-white px-5 py-3 text-sm font-medium text-gray-900 hover:bg-gray-100"
                >
                  Search corpus
                </Link>
              </div>
            </div>

            <aside className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="text-sm font-semibold text-gray-900">
                Current bundle
              </h2>

              <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <dt className="text-gray-500">Posts</dt>
                  <dd className="mt-1 text-2xl font-semibold">
                    {exportCounts.posts ?? sourceCounts.post ?? '–'}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">Pages</dt>
                  <dd className="mt-1 text-2xl font-semibold">
                    {exportCounts.pages ?? sourceCounts.page ?? '–'}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">Items</dt>
                  <dd className="mt-1 text-2xl font-semibold">
                    {exportCounts.items_total ?? '–'}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">Source</dt>
                  <dd className="mt-1 text-sm font-medium">WordPress REST</dd>
                </div>
              </dl>

              <p className="mt-5 break-all border-t border-gray-100 pt-4 text-xs leading-5 text-gray-500">
                Run: {runId}
              </p>
            </aside>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-5xl gap-5 px-6 py-10 md:grid-cols-3">
        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Posts</h2>
          <p className="mt-2 text-sm leading-6 text-gray-700">
            A chronological archive of announcements, events, deadlines, and
            time-sensitive updates.
          </p>
          <Link
            href="/posts"
            className="mt-5 inline-block text-sm font-medium text-blue-700 hover:underline"
          >
            Open posts →
          </Link>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Pages</h2>
          <p className="mt-2 text-sm leading-6 text-gray-700">
            Stable institutional pages such as plans, offices, access, thesis
            information, and recurring references.
          </p>
          <Link
            href="/pages"
            className="mt-5 inline-block text-sm font-medium text-blue-700 hover:underline"
          >
            Open pages →
          </Link>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Search</h2>
          <p className="mt-2 text-sm leading-6 text-gray-700">
            Search across titles, excerpts, and extracted text from the generated
            frontend bundle.
          </p>
          <Link
            href="/search"
            className="mt-5 inline-block text-sm font-medium text-blue-700 hover:underline"
          >
            Search now →
          </Link>
        </div>
      </section>

      <section className="mx-auto grid max-w-5xl gap-10 px-6 pb-16 lg:grid-cols-[1.2fr_0.8fr]">
        <div>
          <div className="mb-5 flex items-end justify-between">
            <div>
              <h2 className="text-2xl font-semibold">Latest posts</h2>
              <p className="mt-1 text-sm text-gray-500">
                Most recent updates first.
              </p>
            </div>
            <Link href="/posts" className="text-sm text-blue-700 hover:underline">
              View archive
            </Link>
          </div>

          <div className="divide-y divide-gray-200 rounded-2xl border border-gray-200 bg-white shadow-sm">
            {posts.map((post) => (
              <article key={post.id} className="px-5 py-4">
                <div className="text-xs uppercase tracking-wide text-gray-500">
                  {formatDate(post.sort_date || post.modified_at || post.created_at)}
                </div>
                <h3 className="mt-1 text-base font-semibold leading-snug">
                  <a
                    href={post.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="hover:underline"
                  >
                    {post.title}
                  </a>
                </h3>
                {post.excerpt_plain && (
                  <p className="mt-2 line-clamp-2 text-sm leading-6 text-gray-700">
                    {post.excerpt_plain}
                  </p>
                )}
              </article>
            ))}
          </div>
        </div>

        <div>
          <div className="mb-5 flex items-end justify-between">
            <div>
              <h2 className="text-2xl font-semibold">Key pages</h2>
              <p className="mt-1 text-sm text-gray-500">
                Evergreen references.
              </p>
            </div>
            <Link href="/pages" className="text-sm text-blue-700 hover:underline">
              View all
            </Link>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-2 shadow-sm">
            {pages.map((page) => (
              <a
                key={page.id}
                href={page.source_url}
                target="_blank"
                rel="noreferrer"
                className="block rounded-xl px-4 py-3 hover:bg-gray-50"
              >
                <div className="text-sm font-medium leading-snug text-gray-950">
                  {page.title}
                </div>
                {page.excerpt_plain && (
                  <div className="mt-1 line-clamp-2 text-xs leading-5 text-gray-600">
                    {page.excerpt_plain}
                  </div>
                )}
              </a>
            ))}
          </div>
        </div>
      </section>
    </main>
  )
}
