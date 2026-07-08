import Link from 'next/link'

export function Header() {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-lg font-semibold tracking-tight">
          LCD Knowledge
        </Link>

        <nav className="flex gap-5 text-sm text-gray-700">
          <Link href="/posts" className="hover:text-black">
            Posts
          </Link>
          <Link href="/pages" className="hover:text-black">
            Pages
          </Link>
          <Link href="/search" className="hover:text-black">
            Search
          </Link>
        </nav>
      </div>
    </header>
  )
}
