import { ContentDetail } from '@/components/ContentDetail'
import { getPost, getPosts } from '@/lib/lcdBundle'

export function generateStaticParams() {
  return getPosts().map((post) => ({
    route_slug: post.route_slug,
  }))
}

export default async function PostDetailPage({
  params,
}: {
  params: Promise<{ route_slug: string }>
}) {
  const { route_slug } = await params
  const item = getPost(route_slug)

  return (
    <ContentDetail
      item={item}
      backHref="/posts"
      backLabel="Back to posts"
    />
  )
}
