'use client'

import { useState } from 'react'
import { MagnifyingGlassIcon, BarsArrowUpIcon, FolderIcon } from '@heroicons/react/24/outline'

interface HeaderProps {
  currentPage?: string
  onNavigate?: (page: 'dashboard' | 'search' | 'knowledge-graph' | 'analytics' | 'osdr-files') => void
}

export function Header({ currentPage, onNavigate }: HeaderProps = {}) {
  const [searchQuery, setSearchQuery] = useState('')

  return (
    <header className="sticky top-0 z-50 bg-gray-900/95 backdrop-blur-sm border-b border-gray-700 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Title */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center">
                <img
                  src="/nasa_logo.png"
                  alt="NASA Logo"
                  width={60}
                  height={60}
                  className="bg-transparent"
                />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 via-purple-500 to-cyan-400 bg-clip-text text-transparent font-orbitron">
                  Space Biology Knowledge Engine
                </h1>
                <p className="text-xs text-gray-400">2025 Space Apps Challenge</p>
              </div>
            </div>
          </div>

          {/* Search Bar */}
          <div className="flex-1 max-w-lg mx-8">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search publications, topics, or research areas..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded-lg 
                          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                          text-white placeholder-gray-400 text-sm transition-all duration-200 font-sans"
              />
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex items-center space-x-6">
            <button
              onClick={() => onNavigate?.('dashboard')}
              className={`transition-colors duration-200 text-sm font-medium font-orbitron ${currentPage === 'dashboard' ? 'text-white' : 'text-gray-300 hover:text-white'
                }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => onNavigate?.('search')}
              className={`transition-colors duration-200 text-sm font-medium font-orbitron ${currentPage === 'search' ? 'text-white' : 'text-gray-300 hover:text-white'
                }`}
            >
              Search
            </button>
            <button
              onClick={() => onNavigate?.('knowledge-graph')}
              className={`transition-colors duration-200 text-sm font-medium font-orbitron ${currentPage === 'knowledge-graph' ? 'text-white' : 'text-gray-300 hover:text-white'
                }`}
            >
              Knowledge Graph
            </button>
            <button
              onClick={() => onNavigate?.('analytics')}
              className={`transition-colors duration-200 text-sm font-medium font-orbitron ${currentPage === 'analytics' ? 'text-white' : 'text-gray-300 hover:text-white'
                }`}
            >
              Analytics
            </button>
            <button
              onClick={() => onNavigate?.('osdr-files')}
              className={`transition-colors duration-200 text-sm font-medium flex items-center font-orbitron ${currentPage === 'osdr-files' ? 'text-white' : 'text-gray-300 hover:text-white'
                }`}
            >
              <FolderIcon className="h-4 w-4 mr-1" />
              Files
            </button>
            <button className="p-2 text-gray-300 hover:text-white transition-colors duration-200 hover:bg-gray-800 rounded">
              <BarsArrowUpIcon className="h-5 w-5" />
            </button>
          </nav>
        </div>
      </div>
    </header>
  )
}