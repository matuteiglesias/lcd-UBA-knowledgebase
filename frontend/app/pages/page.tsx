import { ContentCard } from '@/components/ContentCard'
import { getPages } from '@/lib/lcdBundle'

export default function PagesPage() {
  const pages = getPages()

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">
          Evergreen pages
        </h1>
        <p className="mt-3 max-w-2xl text-gray-700">
          Stable institutional pages from the LCD corpus.
        </p>
      </header>

      <section className="mt-8 grid gap-5 md:grid-cols-2">
        {pages.map((page) => (
          <ContentCard
            key={page.id}
            item={page}
            href={`/pages/${page.route_slug}`}
          />
        ))}
      </section>
    </main>
  )
}
