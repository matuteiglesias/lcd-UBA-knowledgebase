import { ContentDetail } from '@/components/ContentDetail'
import { getPage, getPages } from '@/lib/lcdBundle'

export function generateStaticParams() {
  return getPages().map((page) => ({
    route_slug: page.route_slug,
  }))
}

export default async function EvergreenPageDetail({
  params,
}: {
  params: Promise<{ route_slug: string }>
}) {
  const { route_slug } = await params
  const item = getPage(route_slug)

  return (
    <ContentDetail
      item={item}
      backHref="/pages"
      backLabel="Back to pages"
    />
  )
}
