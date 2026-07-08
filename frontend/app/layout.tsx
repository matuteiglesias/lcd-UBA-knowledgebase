import type { Metadata } from 'next'
import { Header } from '@/components/Header'
import './globals.css'

export const metadata: Metadata = {
  title: 'LCD Knowledge',
  description: 'Static LCD posts and evergreen pages from an ingested corpus.',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-gray-50 text-gray-950 antialiased">
        <Header />
        {children}
      </body>
    </html>
  )
}
