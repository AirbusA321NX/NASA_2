'use client'

import React, { useState } from 'react'
import { Dashboard } from '@/components/dashboard'
import { Search } from '@/components/search'
import { Analytics } from '@/components/analytics'
import { KnowledgeGraph } from '@/components/knowledge-graph'
import { OSDRFiles } from '@/components/osdr-files'
import { Header } from '@/components/header'
import { Footer } from '@/components/footer'

type CurrentPage = 'dashboard' | 'search' | 'knowledge-graph' | 'analytics' | 'osdr-files'

export default function HomePage() {
  const [currentPage, setCurrentPage] = useState<CurrentPage>('dashboard')

  const handleNavigate = (page: CurrentPage) => {
    console.log('Navigation to:', page)
    setCurrentPage(page)
  }

  const renderCurrentPage = () => {
    console.log('Rendering page:', currentPage)
    switch (currentPage) {
      case 'search':
        return <Search onBack={() => handleNavigate('dashboard')} />
      case 'knowledge-graph':
        return <KnowledgeGraph onBack={() => handleNavigate('dashboard')} width={1000} height={700} />
      case 'analytics':
        return <Analytics onBack={() => handleNavigate('dashboard')} />
      case 'osdr-files':
        return <OSDRFiles onBack={() => handleNavigate('dashboard')} />
      default:
        return <Dashboard onNavigate={handleNavigate} />
    }
  }

  return (
    <main className="min-h-screen flex flex-col">
      <Header currentPage={currentPage} onNavigate={handleNavigate} />
      <div className="flex-1">
        {renderCurrentPage()}
      </div>
      <Footer />
    </main>
  )
}