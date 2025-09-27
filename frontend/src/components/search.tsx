'use client'

import { useState, useEffect } from 'react'
import { MagnifyingGlassIcon, DocumentTextIcon, CalendarIcon, UserIcon } from '@heroicons/react/24/outline'

interface Publication {
  id: string
  title: string
  abstract: string
  authors: string[]
  date: string
  source: string
  tags: string[]
  relevanceScore?: number
}

interface SearchProps {
  onBack: () => void
}

export function Search({ onBack }: SearchProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Publication[]>([])
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [searchType, setSearchType] = useState<'semantic' | 'keyword'>('semantic')

  // Real local AI-powered search function
  const performSearch = async (searchQuery: string) => {
    setLoading(true)
    setAnalyzing(true)

    try {
      // Use the local AI-powered search endpoint
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4004'}/api/search/ai`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          search_type: searchType === 'semantic' ? 'semantic' : 'keyword',
          limit: 10
        })
      })

      if (!response.ok) {
        throw new Error(`Backend API error: ${response.status}`)
      }

      const data = await response.json()

      if (!data.success) {
        throw new Error(data.error || 'Search failed')
      }

      // Transform backend data to our format
      const publications: Publication[] = data.data.results?.map((result: any) => ({
        id: result.osdr_id || result.id,
        title: result.title || 'Untitled Study',
        abstract: result.ai_summary || result.abstract || result.description || '',
        authors: Array.isArray(result.authors) ? result.authors :
          result.principal_investigator ? [result.principal_investigator] : [],
        date: result.publication_date || result.submission_date || new Date().toISOString(),
        source: 'NASA OSDR',
        tags: [
          ...(result.ai_keywords || result.keywords || []),
          result.research_area || result.study_type || 'Space Biology',
          ...(result.organisms?.map((org: any) =>
            typeof org === 'string' ? org : org.scientificName
          ).filter(Boolean) || [])
        ].slice(0, 8),
        relevanceScore: result.semantic_score || result.relevance_score || 0.8
      })) || []

      setResults(publications)

      // Show AI enhancement status
      if (data.data.ai_enhanced) {
        console.log(` AI Enhanced Search - Model: ${data.data.model_used}`);
      } else {
        console.log('⚠️ Fallback keyword search used');
      }

    } catch (error) {
      console.error('AI search error:', error)
      // Show error to user
      setResults([])
      alert(`Error with AI search: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`)
    } finally {
      setLoading(false)
      // Simulate analysis time for better UX
      setTimeout(() => {
        setAnalyzing(false)
      }, 800)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      performSearch(query)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <style jsx>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
        .animate-pulse-custom {
          animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
      `}</style>

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 font-orbitron">AI-Powered Smart Search</h1>
          <p className="text-gray-300">Search through NASA space biology publications using semantic AI</p>
        </div>
        <button
          onClick={onBack}
          className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors font-orbitron"
        >
          ← Back to Dashboard
        </button>
      </div>

      {/* Loading Overlay */}
      {analyzing && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full mx-4 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
            <h3 className="text-xl font-semibold text-white mb-2 font-orbitron">
              {searchType === 'semantic' ? 'AI Analysis in Progress' : 'Searching Publications'}
            </h3>
            <p className="text-gray-300 mb-4">
              {searchType === 'semantic'
                ? 'Analyzing publications with semantic AI...'
                : 'Scanning through NASA OSDR database...'}
            </p>
            <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
              <div className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full animate-pulse-custom"></div>
            </div>
          </div>
        </div>
      )}

      {/* Search Form */}
      <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 mb-8">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search for topics, organisms, research areas, or specific findings..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600 rounded-lg 
                          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                          text-white placeholder-gray-400 font-sans"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-6 py-3 rounded-lg transition-colors font-medium font-orbitron"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>

          {/* Search Type Toggle */}
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-300 font-orbitron">Search Type:</span>
            <button
              type="button"
              onClick={() => setSearchType('semantic')}
              className={`px-3 py-1 rounded text-sm transition-colors font-orbitron ${searchType === 'semantic'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
            >
              Semantic AI
            </button>
            <button
              type="button"
              onClick={() => setSearchType('keyword')}
              className={`px-3 py-1 rounded text-sm transition-colors font-orbitron ${searchType === 'keyword'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
            >
              Keyword Search
            </button>
          </div>
        </form>
      </div>

      {/* Search Results */}
      {(loading || analyzing) && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="text-gray-300 mt-4">{analyzing ? 'AI is analyzing publications...' : 'Searching...'}</p>
          {analyzing && (
            <div className="mt-4 max-w-md mx-auto">
              <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full animate-pulse-custom"></div>
              </div>
              <p className="text-gray-400 text-sm mt-2">
                {searchType === 'semantic'
                  ? 'Processing with semantic AI analysis...'
                  : 'Scanning through NASA OSDR database...'}
              </p>
            </div>
          )}
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-white">Search Results ({results.length})</h2>
            <div className="text-sm text-gray-400">Sorted by relevance</div>
          </div>

          {results.map((publication) => (
            <div key={publication.id} className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 hover:bg-gray-800/70 transition-all duration-300">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-white mb-2 hover:text-blue-400 cursor-pointer transition-colors">
                    {publication.title}
                  </h3>
                  <div className="flex items-center space-x-4 text-sm text-gray-400 mb-3">
                    <div className="flex items-center space-x-1">
                      <CalendarIcon className="h-4 w-4" />
                      <span>{new Date(publication.date).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <UserIcon className="h-4 w-4" />
                      <span>{publication.authors[0]} {publication.authors.length > 1 && `+${publication.authors.length - 1} others`}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <DocumentTextIcon className="h-4 w-4" />
                      <span>{publication.source}</span>
                    </div>
                  </div>
                </div>
                {publication.relevanceScore && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-400">Relevance:</span>
                    <div className="bg-blue-600 text-white px-2 py-1 rounded text-sm">
                      {Math.round(publication.relevanceScore * 100)}%
                    </div>
                  </div>
                )}
              </div>

              <p className="text-gray-300 mb-4 leading-relaxed">
                {publication.abstract}
              </p>

              <div className="flex items-center justify-between">
                <div className="flex flex-wrap gap-2">
                  {publication.tags.map((tag, index) => (
                    <span key={index} className="bg-gray-700 text-gray-300 px-2 py-1 rounded text-xs">
                      {tag}
                    </span>
                  ))}
                </div>
                <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm transition-colors">
                  View Full Paper
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {results.length === 0 && !loading && query && (
        <div className="text-center py-12">
          <p className="text-gray-400">No results found for "{query}". Try different keywords or use semantic search.</p>
        </div>
      )}

      {results.length === 0 && !loading && !query && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🔍</div>
          <p className="text-gray-400 text-lg">Enter a search query to find relevant space biology research</p>
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mx-auto">
            <div className="bg-gray-800/30 p-4 rounded-lg">
              <h4 className="text-white font-medium mb-2">Example Searches</h4>
              <div className="space-y-1 text-sm text-gray-400">
                <div>• "plant growth in microgravity"</div>
                <div>• "radiation effects on DNA"</div>
                <div>• "muscle atrophy countermeasures"</div>
              </div>
            </div>
            <div className="bg-gray-800/30 p-4 rounded-lg">
              <h4 className="text-white font-medium mb-2">Semantic AI</h4>
              <p className="text-sm text-gray-400">Understands context and meaning, not just keywords</p>
            </div>
            <div className="bg-gray-800/30 p-4 rounded-lg">
              <h4 className="text-white font-medium mb-2">Smart Results</h4>
              <p className="text-sm text-gray-400">Ranked by relevance and semantic similarity</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Search