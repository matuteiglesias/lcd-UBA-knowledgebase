import Link from 'next/link'
import type { DetailItem } from '@/lib/lcdBundle'

type Props = {
  item: DetailItem
  backHref: string
  backLabel: string
}

export function ContentDetail({ item, backHref, backLabel }: Props) {
  const shouldRenderHtml = item.render_mode === 'html_clean' && item.html_clean

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <Link href={backHref} className="text-sm text-gray-600 hover:text-black">
        ← {backLabel}
      </Link>

      <header className="mt-8">
        <div className="text-xs uppercase tracking-wide text-gray-500">
          {item.entity_type}
        </div>

        <h1 className="mt-2 text-3xl font-semibold tracking-tight">
          {item.title}
        </h1>

        {(item.modified_at || item.created_at) && (
          <p className="mt-3 text-sm text-gray-500">
            Updated: {item.modified_at || item.created_at}
          </p>
        )}
      </header>

      <section className="mt-8">
        {shouldRenderHtml ? (
          <article
            className="prose prose-gray max-w-none"
            dangerouslySetInnerHTML={{ __html: item.html_clean || '' }}
          />
        ) : (
          <article className="prose prose-gray max-w-none whitespace-pre-wrap">
            {item.text || item.excerpt_plain || 'No text available.'}
          </article>
        )}
      </section>

      {item.attachments && item.attachments.length > 0 && (
        <section className="mt-10 border-t border-gray-200 pt-6">
          <h2 className="text-lg font-semibold">Attachments</h2>
          <ul className="mt-3 list-disc space-y-2 pl-6 text-sm">
            {item.attachments.map((attachment) => (
              <li key={attachment.url}>
                <a
                  href={attachment.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-700 hover:underline"
                >
                  {attachment.label || attachment.url}
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}

      <footer className="mt-10 border-t border-gray-200 pt-6 text-sm text-gray-500">
        <a
          href={item.source_url}
          target="_blank"
          rel="noreferrer"
          className="text-blue-700 hover:underline"
        >
          Original source
        </a>

        {item.content_hash && (
          <p className="mt-3 break-all font-mono text-xs">
            {item.content_hash}
          </p>
        )}
      </footer>
    </main>
  )
}
