import Link from 'next/link'
import { getPosts } from '@/lib/lcdBundle'

const PAGE_SIZE = 20

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

export default async function PostsPage({
  searchParams,
}: {
  searchParams?: Promise<{ page?: string }>
}) {
  const params = searchParams ? await searchParams : {}
  const currentPage = Math.max(1, Number(params.page || '1') || 1)

  const posts = getPosts().sort((a, b) => {
    const aTime = new Date(a.sort_date || a.modified_at || a.created_at || 0).getTime()
    const bTime = new Date(b.sort_date || b.modified_at || b.created_at || 0).getTime()
    return bTime - aTime
  })

  const totalPages = Math.max(1, Math.ceil(posts.length / PAGE_SIZE))
  const safePage = Math.min(currentPage, totalPages)
  const start = (safePage - 1) * PAGE_SIZE
  const visiblePosts = posts.slice(start, start + PAGE_SIZE)

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Posts</h1>
        <p className="mt-3 max-w-2xl text-gray-700">
          Rolling updates and time-sensitive content from the LCD site.
        </p>
        <p className="mt-2 text-sm text-gray-500">
          Showing {visiblePosts.length} of {posts.length} posts · Page {safePage} of {totalPages}
        </p>
      </header>

      <section className="mt-8 divide-y divide-gray-200 rounded-xl border border-gray-200 bg-white">
        {visiblePosts.map((post) => (
          <article key={post.id} className="px-5 py-5">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div className="min-w-0 flex-1">
                <div className="text-xs uppercase tracking-wide text-gray-500">
                  {formatDate(post.sort_date || post.modified_at || post.created_at)}
                  {post.has_attachments && <span> · Attachments</span>}
                </div>

                <h2 className="mt-1 text-lg font-semibold leading-snug">
                  <a
                    href={post.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="hover:underline"
                  >
                    {post.title}
                  </a>
                </h2>

                {post.excerpt_plain && (
                  <p className="mt-2 line-clamp-2 text-sm leading-6 text-gray-700">
                    {post.excerpt_plain}
                  </p>
                )}

                <div className="mt-2 break-all text-xs text-gray-400">
                  {post.source_url}
                </div>
              </div>

              <div className="flex shrink-0 gap-3 text-sm">
                <a
                  href={post.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="font-medium text-blue-700 hover:underline"
                >
                  Original
                </a>
                <Link
                  href={`/posts/${post.route_slug}`}
                  className="font-medium text-gray-600 hover:text-black"
                >
                  Preview
                </Link>
              </div>
            </div>
          </article>
        ))}
      </section>

      <nav className="mt-8 flex items-center justify-between border-t border-gray-200 pt-6 text-sm">
        <div>
          {safePage > 1 ? (
            <Link
              href={`/posts?page=${safePage - 1}`}
              className="rounded-lg border border-gray-300 px-3 py-2 hover:bg-gray-100"
            >
              ← Previous
            </Link>
          ) : (
            <span className="rounded-lg border border-gray-200 px-3 py-2 text-gray-400">
              ← Previous
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {Array.from({ length: totalPages }, (_, index) => index + 1).map((page) => {
            const isCurrent = page === safePage

            if (
              totalPages > 9 &&
              page !== 1 &&
              page !== totalPages &&
              Math.abs(page - safePage) > 2
            ) {
              if (page === 2 && safePage > 4) {
                return <span key={page} className="px-1 text-gray-400">…</span>
              }
              if (page === totalPages - 1 && safePage < totalPages - 3) {
                return <span key={page} className="px-1 text-gray-400">…</span>
              }
              return null
            }

            return (
              <Link
                key={page}
                href={`/posts?page=${page}`}
                className={
                  isCurrent
                    ? 'rounded-lg bg-gray-900 px-3 py-2 font-medium text-white'
                    : 'rounded-lg border border-gray-300 px-3 py-2 hover:bg-gray-100'
                }
              >
                {page}
              </Link>
            )
          })}
        </div>

        <div>
          {safePage < totalPages ? (
            <Link
              href={`/posts?page=${safePage + 1}`}
              className="rounded-lg border border-gray-300 px-3 py-2 hover:bg-gray-100"
            >
              Next →
            </Link>
          ) : (
            <span className="rounded-lg border border-gray-200 px-3 py-2 text-gray-400">
              Next →
            </span>
          )}
        </div>
      </nav>
    </main>
  )
}
