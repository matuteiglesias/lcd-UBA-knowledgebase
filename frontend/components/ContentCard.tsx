import Link from 'next/link'
import type { ListingItem } from '@/lib/lcdBundle'

type Props = {
  item: ListingItem
  href: string
}

export function ContentCard({ item, href }: Props) {
  return (
    <article className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-gray-500">
        <span>{item.entity_type}</span>
        {item.has_attachments && <span>• Attachments</span>}
      </div>

      <h2 className="mt-2 text-xl font-semibold leading-snug">
        <Link href={href} className="hover:underline">
          {item.title}
        </Link>
      </h2>

      {item.excerpt_plain && (
        <p className="mt-3 line-clamp-3 text-sm leading-6 text-gray-700">
          {item.excerpt_plain}
        </p>
      )}

      <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
        <span>{item.sort_date || item.modified_at || item.created_at || 'No date'}</span>
        <Link href={href} className="font-medium text-gray-700 hover:text-black">
          Open
        </Link>
      </div>
    </article>
  )
}
