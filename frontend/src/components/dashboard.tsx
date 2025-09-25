'use client'

import { useState, useEffect } from 'react'

interface DashboardProps {
  onNavigate: (page: 'search' | 'knowledge-graph' | 'analytics' | 'osdr-files') => void
}

interface DashboardStats {
  totalDatasets: number | null
  yearsOfResearch: number | null
  totalRecords: number | null
  dataSource: string
}

// Add new interface for error state
interface DashboardError {
  error: string
  message: string
}

interface Publication {
  osdr_id: string
  title: string
  authors: string[]
  publication_date: string
  abstract: string
  research_area: string
}

interface ResearchArea {
  area: string
  count: number
  percentage: string
}

export function Dashboard({ onNavigate }: DashboardProps) {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [publications, setPublications] = useState<Publication[]>([])
  const [researchAreas, setResearchAreas] = useState<ResearchArea[]>([])
  const [sectionsLoading, setSectionsLoading] = useState(true)
  const [error, setError] = useState<DashboardError | null>(null)

  // Fetch real dashboard statistics from NASA OSDR analytics
  useEffect(() => {
    const fetchDashboardStats = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4004'}/api/analytics?period=all_time`)
        const data = await response.json()
        
        if (data.success && data.data) {
          const analytics = data.data
          console.log('Dashboard analytics data:', analytics);
          
          // Calculate values from real data with proper fallbacks
          const totalDatasets = analytics.overview?.total_publications ?? null
          const yearsOfResearch = analytics.overview?.year_range ? 
            (new Date().getFullYear() - parseInt(analytics.overview.year_range.split(' - ')[0]) + 1) : null
          const totalRecords = analytics.overview?.total_publications ?? null
          
          setStats({
            totalDatasets: totalDatasets,
            yearsOfResearch: yearsOfResearch,
            totalRecords: totalRecords,
            dataSource: 'NASA OSDR'
          })
        } else if (!data.success && data.error) {
          // Handle error response
          setError({
            error: data.error,
            message: data.message || 'Error fetching NASA OSDR data'
          });
          setStats(null);
        } else {
          // If no analytics available, show appropriate error state
          console.warn('No analytics data received for dashboard');
          setError({
            error: 'No data',
            message: 'No analytics data received'
          });
          setStats(null);
        }
      } catch (error: any) {
        console.warn('Failed to fetch dashboard stats:', error)
        // Show error state
        setError({
          error: 'Connection error',
          message: 'Failed to connect to backend services'
        });
        setStats(null);
      } finally {
        setLoading(false)
      }
    }
    
    fetchDashboardStats()
  }, [])

  // Fetch recent publications and research areas
  useEffect(() => {
    const fetchDashboardSections = async () => {
      try {
        setSectionsLoading(true);
        setError(null);
        
        // Fetch recent publications
        const pubResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4004'}/api/publications?limit=5`)
        const pubData = await pubResponse.json()
        
        if (pubData.success && pubData.data && pubData.data.publications) {
          setPublications(pubData.data.publications.slice(0, 3)) // Show only top 3
        }
        
        // Fetch research areas
        const areasResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4004'}/api/analytics`)
        const areasData = await areasResponse.json()
        
        if (areasData.success && areasData.data && areasData.data.research_areas?.top_10) {
          setResearchAreas(areasData.data.research_areas.top_10.slice(0, 5)) // Show only top 5
        } else if (!areasData.success && areasData.error) {
          // Handle error in research areas
          console.warn('Error fetching research areas:', areasData.message);
        }
      } catch (error) {
        console.warn('Failed to fetch dashboard sections:', error)
        setError({
          error: 'Connection error',
          message: 'Failed to connect to backend services'
        });
      } finally {
        setSectionsLoading(false)
      }
    }
    
    fetchDashboardSections()
  }, [])

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Error Message */}
      {error && (
        <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 mb-6">
          <h3 className="text-lg font-semibold text-red-300 mb-2">Error Fetching Data</h3>
          <p className="text-red-200">{error.message}</p>
          <p className="text-red-400 text-sm mt-2">Please ensure all backend services are running and NASA OSDR data is available.</p>
        </div>
      )}

      {/* Hero Section */}
      <div className="text-center mb-12">
        <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-400 via-purple-500 to-cyan-400 bg-clip-text text-transparent">
          Explore 40+ Years of Space Biology Research
        </h2>
        <p className="text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
          Discover insights from NASA's Open Science Data Repository (OSDR) using AI-powered analysis,
          knowledge graphs, and interactive visualizations from real space biology datasets.
        </p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 text-center hover:bg-gray-800/70 transition-all duration-300 shadow-lg hover:shadow-blue-500/20">
          <div className="text-3xl font-bold text-blue-400 mb-2">
            {loading ? '...' : stats?.totalDatasets ? stats.totalDatasets.toLocaleString() : 'N/A'}
          </div>
          <div className="text-gray-300 text-sm font-medium">Real Datasets</div>
        </div>
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 text-center hover:bg-gray-800/70 transition-all duration-300 shadow-lg hover:shadow-cyan-500/20">
          <div className="text-3xl font-bold text-cyan-400 mb-2">
            {loading ? '...' : stats?.yearsOfResearch ? `${stats.yearsOfResearch}+` : 'N/A'}
          </div>
          <div className="text-gray-300 text-sm font-medium">Years of Research</div>
        </div>
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 text-center hover:bg-gray-800/70 transition-all duration-300 shadow-lg hover:shadow-pink-500/20">
          <div className="text-3xl font-bold text-pink-400 mb-2">
            {loading ? '...' : stats?.totalRecords ? `${stats.totalRecords}+` : 'N/A'}
          </div>
          <div className="text-gray-300 text-sm font-medium">Research Records</div>
        </div>
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 text-center hover:bg-gray-800/70 transition-all duration-300 shadow-lg hover:shadow-purple-500/20">
          <div className="text-3xl font-bold text-purple-400 mb-2">
            {loading ? '...' : stats?.dataSource || 'Data Unavailable'}
          </div>
          <div className="text-gray-300 text-sm font-medium">Data Source</div>
        </div>
      </div>

      {/* Feature Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Publications */}
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6">
          <h3 className="text-xl font-semibold mb-6 text-blue-400 flex items-center">
            <span className="mr-2">📚</span>
            Recent Publications
          </h3>
          <div className="space-y-4">
            {sectionsLoading ? (
              <div className="border-l-4 border-blue-500 pl-4 py-2">
                <h4 className="font-medium mb-1 text-white">
                  Loading Recent Publications...
                </h4>
                <p className="text-sm text-gray-300 mb-2">
                  Real publications will be fetched from NASA OSDR analytics API
                </p>
                <div className="text-xs text-gray-400">
                  NASA OSDR S3 • Space Biology • Live Data
                </div>
              </div>
            ) : publications.length > 0 ? (
              publications.map((pub) => (
                <div key={pub.osdr_id} className="border-l-4 border-blue-500 pl-4 py-2 hover:bg-gray-700/30 rounded-r transition-colors">
                  <h4 className="font-medium mb-1 text-white">
                    {pub.title}
                  </h4>
                  <p className="text-sm text-gray-300 mb-2">
                    {pub.abstract?.substring(0, 100)}...
                  </p>
                  <div className="text-xs text-gray-400">
                    {pub.authors?.[0]} • {new Date(pub.publication_date).getFullYear()} • {pub.research_area}
                  </div>
                </div>
              ))
            ) : (
              <div className="border-l-4 border-blue-500 pl-4 py-2">
                <h4 className="font-medium mb-1 text-white">
                  No publications found
                </h4>
                <p className="text-sm text-gray-300 mb-2">
                  Check back later for updated NASA OSDR data
                </p>
                <div className="text-xs text-gray-400">
                  NASA OSDR S3 • Space Biology
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Research Areas */}
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6">
          <h3 className="text-xl font-semibold mb-6 text-cyan-400 flex items-center">
            <span className="mr-2">🔬</span>
            Research Areas
          </h3>
          <div className="space-y-3">
            {sectionsLoading ? (
              <div className="flex items-center space-x-3 p-2 rounded">
                <div className="w-2 h-2 bg-purple-400 rounded-full flex-shrink-0"></div>
                <span className="text-gray-200 text-sm">Research areas will be loaded from real NASA OSDR data analysis</span>
              </div>
            ) : researchAreas.length > 0 ? (
              researchAreas.map((area, index) => (
                <div key={index} className="flex items-center space-x-3 p-2 rounded hover:bg-gray-700/30 transition-colors">
                  <div className="w-2 h-2 bg-purple-400 rounded-full flex-shrink-0"></div>
                  <div className="flex-1">
                    <span className="text-gray-200 text-sm">{area.area}</span>
                  </div>
                  <div className="text-gray-400 text-xs">
                    {area.count} studies ({area.percentage}%)
                  </div>
                </div>
              ))
            ) : (
              <div className="flex items-center space-x-3 p-2 rounded">
                <div className="w-2 h-2 bg-purple-400 rounded-full flex-shrink-0"></div>
                <span className="text-gray-200 text-sm">No research areas data available</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-12">
        <h3 className="text-2xl font-semibold mb-8 text-center text-white">
          Explore the Knowledge Engine
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <button 
            onClick={() => {
              console.log('Smart Search clicked');
              onNavigate('search');
            }}
            className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 text-center hover:bg-gray-800/70 transition-all duration-300 hover:scale-105 hover:border-blue-500/50 group"
          >
            <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">🔍</div>
            <h4 className="font-semibold mb-3 text-white text-lg">Smart Search</h4>
            <p className="text-sm text-gray-300 leading-relaxed">
              Search real NASA OSDR datasets with AI-powered semantic understanding of space biology research
            </p>
          </button>
          
          <button 
            onClick={() => {
              console.log('Knowledge Graph clicked');
              onNavigate('knowledge-graph');
            }}
            className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 text-center hover:bg-gray-800/70 transition-all duration-300 hover:scale-105 hover:border-cyan-500/50 group"
          >
            <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">🕸️</div>
            <h4 className="font-semibold mb-3 text-white text-lg">Knowledge Graph</h4>
            <p className="text-sm text-gray-300 leading-relaxed">
              Explore connections between OSDR datasets, organisms, and research findings
            </p>
          </button>
          
          <button 
            onClick={() => {
              console.log('Analytics clicked');
              onNavigate('analytics');
            }}
            className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 text-center hover:bg-gray-800/70 transition-all duration-300 hover:scale-105 hover:border-pink-500/50 group"
          >
            <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">📊</div>
            <h4 className="font-semibold mb-3 text-white text-lg">Analytics</h4>
            <p className="text-sm text-gray-300 leading-relaxed">
              Analyze trends and patterns from NASA space biology data archives
            </p>
          </button>
          
          <button 
            onClick={() => {
              console.log('OSDR Files clicked');
              onNavigate('osdr-files');
            }}
            className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 text-center hover:bg-gray-800/70 transition-all duration-300 hover:scale-105 hover:border-green-500/50 group"
          >
            <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">📁</div>
            <h4 className="font-semibold mb-3 text-white text-lg">OSDR Files</h4>
            <p className="text-sm text-gray-300 leading-relaxed">
              Browse and access real research files from NASA's Open Science Data Repository
            </p>
          </button>
        </div>
      </div>
    </div>
  )
}