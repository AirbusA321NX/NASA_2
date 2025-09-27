import './globals.css'
import type { Metadata, Viewport } from 'next'
import { Inter, Roboto_Mono, Orbitron } from 'next/font/google'
import { Providers } from '@/components/providers'
import { Toaster } from 'react-hot-toast'

// Primary font for body text - Inter is clean and modern
const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter'
})

// Monospace font for technical content
const robotoMono = Roboto_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-roboto-mono'
})

// Futuristic font for headings and NASA-themed elements
const orbitron = Orbitron({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-orbitron'
})

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#0B3D91',
}

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'),
  title: 'NASA Space Biology Knowledge Engine',
  description: 'Dynamic dashboard for exploring NASA bioscience publications and space biology research',
  keywords: [
    'NASA',
    'space biology',
    'bioscience',
    'research',
    'knowledge engine',
    'artificial intelligence',
    'space exploration'
  ],
  authors: [{ name: 'NASA Space Apps Challenge Team' }],
  openGraph: {
    title: 'NASA Space Biology Knowledge Engine',
    description: 'Explore decades of NASA space biology research with AI-powered insights',
    type: 'website',
    images: ['/og-image.jpg'],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'NASA Space Biology Knowledge Engine',
    description: 'Explore decades of NASA space biology research with AI-powered insights',
    images: ['/og-image.jpg'],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${robotoMono.variable} ${orbitron.variable} font-sans bg-gray-900 text-white antialiased`}>
        <Providers>
          <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-blue-900">
            {children}
          </div>
          <Toaster
            position="top-right"
            toastOptions={{
              className: 'bg-gray-800 border-gray-600 text-white',
              duration: 4000,
            }}
          />
        </Providers>
      </body>
    </html>
  )
}