'use client'

import React, { useState, useEffect } from 'react'
import { PDFViewer } from '@/components/pdf-viewer'

interface OSDRFile {
  id: string
  name: string
  type: string
  experiment_type: string
  size: string
  date: string
  description: string
  url: string
  study_id: string
  species: string
  mission: string
}

interface OSDRFilesProps {
  onBack: () => void
}

export function OSDRFiles({ onBack }: OSDRFilesProps) {
  const [files, setFiles] = useState<OSDRFile[]>([])
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<OSDRFile | null>(null)
  const [viewingPdf, setViewingPdf] = useState<OSDRFile | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalFiles, setTotalFiles] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const filesPerPage = 50

  useEffect(() => {
    const fetchFiles = async () => {
      try {
        setLoading(true)
        setAnalyzing(true)
        setError(null)
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4004'}/api/osdr/files`)
        const data = await response.json()

        if (data.success) {
          setFiles(data.data || [])
          setTotalFiles(data.total || data.data?.length || 0)
          setHasMore(data.total > (data.data?.length || 0))
        } else {
          setError(data.error || 'Failed to fetch OSDR files')
        }
      } catch (err) {
        console.error('Error fetching OSDR files:', err)
        setError('Failed to connect to NASA OSDR API')
      } finally {
        setLoading(false)
        // Simulate analysis time for better UX
        setTimeout(() => {
          setAnalyzing(false)
        }, 800)
      }
    }

    fetchFiles()
  }, [])

  const handleDownload = (file: OSDRFile) => {
    if (file.url) {
      window.open(file.url, '_blank')
    }
  }

  const handleViewPDF = (file: OSDRFile) => {
    if (file.type.toLowerCase() === 'document' || file.name.toLowerCase().endsWith('.pdf')) {
      setViewingPdf(file)
    } else {
      // For non-PDF files, just download
      handleDownload(file)
    }
  }

  const getFileIcon = (fileType: string) => {
    switch (fileType.toLowerCase()) {
      case 'image':
        return '🖼️'
      case 'document':
        return '📄'
      case 'archive':
        return '📦'
      case 'metadata':
        return '📋'
      case 'tabular':
        return '📊'
      case 'omics':
        return '🧬'
      default:
        return '📁'
    }
  }

  if (loading || analyzing) {
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
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={onBack}
            className="flex items-center text-blue-400 hover:text-blue-300 transition-colors"
          >
            ← Back to Dashboard
          </button>
          <h2 className="text-3xl font-bold text-white">NASA OSDR Files</h2>
        </div>

        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-300">{analyzing ? 'Analyzing NASA OSDR files...' : 'Loading real NASA OSDR files from S3 repository...'}</p>
          {analyzing && (
            <div className="mt-6 max-w-md mx-auto">
              <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full animate-pulse-custom"></div>
              </div>
              <p className="text-gray-400 text-sm mt-2">Processing metadata and research context</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={onBack}
            className="flex items-center text-blue-400 hover:text-blue-300 transition-colors"
          >
            ← Back to Dashboard
          </button>
          <h2 className="text-3xl font-bold text-white">NASA OSDR Files</h2>
        </div>

        <div className="bg-red-900/30 border border-red-700 rounded-lg p-6 text-center">
          <div className="text-red-400 text-2xl mb-2">⚠️</div>
          <h3 className="text-xl font-semibold text-red-300 mb-2">Error Loading Files</h3>
          <p className="text-red-200 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-red-700 hover:bg-red-600 rounded-md transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
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

      {/* Loading Overlay */}
      {analyzing && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full mx-4 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
            <h3 className="text-xl font-semibold text-white mb-2">Analyzing OSDR Files</h3>
            <p className="text-gray-300 mb-4">Processing NASA research files and metadata</p>
            <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
              <div className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full animate-pulse-custom"></div>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between mb-8">
        <button
          onClick={onBack}
          className="flex items-center text-blue-400 hover:text-blue-300 transition-colors"
        >
          ← Back to Dashboard
        </button>
        <h2 className="text-3xl font-bold text-white">NASA OSDR Files</h2>
      </div>

      {selectedFile ? (
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 mb-8">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-2xl font-semibold text-white flex items-center">
              <span className="text-3xl mr-3">{getFileIcon(selectedFile.type)}</span>
              {selectedFile.name}
            </h3>
            <button
              onClick={() => setSelectedFile(null)}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-lg font-medium text-blue-400 mb-3">File Information</h4>
              <div className="space-y-3">
                <div>
                  <span className="text-gray-400">Type:</span>
                  <span className="ml-2 text-white">{selectedFile.type}</span>
                </div>
                <div>
                  <span className="text-gray-400">Experiment:</span>
                  <span className="ml-2 text-white">{selectedFile.experiment_type}</span>
                </div>
                <div>
                  <span className="text-gray-400">Study ID:</span>
                  <span className="ml-2 text-white font-mono">{selectedFile.study_id}</span>
                </div>
                <div>
                  <span className="text-gray-400">Date:</span>
                  <span className="ml-2 text-white">{selectedFile.date}</span>
                </div>
                <div>
                  <span className="text-gray-400">Size:</span>
                  <span className="ml-2 text-white">{selectedFile.size}</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-medium text-blue-400 mb-3">Research Context</h4>
              <div className="space-y-3">
                <div>
                  <span className="text-gray-400">Species:</span>
                  <span className="ml-2 text-white">{selectedFile.species}</span>
                </div>
                <div>
                  <span className="text-gray-400">Mission:</span>
                  <span className="ml-2 text-white">{selectedFile.mission}</span>
                </div>
                <div>
                  <span className="text-gray-400">Description:</span>
                  <p className="mt-1 text-white">{selectedFile.description}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 flex space-x-4">
            <button
              onClick={() => handleViewPDF(selectedFile)}
              className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
            >
              👁️ View File
            </button>
            <button
              onClick={() => handleDownload(selectedFile)}
              className="flex items-center px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-md transition-colors"
            >
              📥 Download File
            </button>
            <button
              onClick={() => navigator.clipboard.writeText(selectedFile.url)}
              className="flex items-center px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-md transition-colors"
            >
              ℹ️ Copy URL
            </button>
          </div>

          <div className="mt-6 bg-gray-900/50 border border-gray-700 rounded-lg p-4">
            <h4 className="text-lg font-medium text-blue-400 mb-3">Provenance Information</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-gray-400 mb-1">Repository Source</div>
                <div className="text-white">NASA Open Science Data Repository (OSDR)</div>
              </div>
              <div>
                <div className="text-gray-400 mb-1">Access Method</div>
                <div className="text-white">Direct S3 Access</div>
              </div>
              <div>
                <div className="text-gray-400 mb-1">Original URL</div>
                <div className="text-blue-300 font-mono text-xs truncate">{selectedFile.url}</div>
              </div>
              <div>
                <div className="text-gray-400 mb-1">File Identifier</div>
                <div className="text-white font-mono">{selectedFile.id}</div>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      <div className="mb-6 flex justify-between items-center">
        <p className="text-gray-300">
          Showing {files.length} of {totalFiles} files from NASA OSDR S3 repository
        </p>
        <div className="text-sm text-gray-400">
          Last updated: {new Date().toLocaleString()}
        </div>
      </div>

      {files.length === 0 ? (
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-12 text-center">
          <div className="text-4xl mb-4">📭</div>
          <h3 className="text-xl font-semibold text-white mb-2">No Files Found</h3>
          <p className="text-gray-300">
            No OSDR files are currently available. Please check back later or ensure the data pipeline is running.
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {files.map((file) => (
              <div
                key={file.id}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 hover:border-blue-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/20"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="text-3xl">
                    {getFileIcon(file.type)}
                  </div>
                  <span className="text-xs bg-blue-900/50 text-blue-300 px-2 py-1 rounded">
                    {file.type}
                  </span>
                </div>

                <h3 className="font-semibold text-white mb-2 truncate" title={file.name}>
                  {file.name}
                </h3>

                <p className="text-sm text-gray-300 mb-4 line-clamp-2">
                  {file.description}
                </p>

                <div className="space-y-2 text-xs text-gray-400 mb-4">
                  <div className="flex justify-between">
                    <span>Study:</span>
                    <span className="text-gray-200 font-mono">{file.study_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Species:</span>
                    <span className="text-gray-200">{file.species}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Mission:</span>
                    <span className="text-gray-200">{file.mission}</span>
                  </div>
                </div>

                <div className="flex space-x-2">
                  <button
                    onClick={() => setSelectedFile(file)}
                    className="flex-1 flex items-center justify-center px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-md transition-colors text-sm"
                  >
                    ℹ️ Details
                  </button>
                  <button
                    onClick={() => handleViewPDF(file)}
                    className="flex items-center px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-md transition-colors text-sm"
                  >
                    👁️
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination Controls */}
          <div className="mt-8 flex justify-center items-center space-x-4">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-500 rounded-md transition-colors"
            >
              Previous
            </button>

            <span className="text-gray-300">
              Page {currentPage} of {Math.ceil(totalFiles / filesPerPage)}
            </span>

            <button
              onClick={() => setCurrentPage(prev => prev + 1)}
              disabled={!hasMore}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-500 rounded-md transition-colors"
            >
              Next
            </button>
          </div>
        </>
      )}

      {viewingPdf && (
        <PDFViewer
          fileUrl={viewingPdf.url}
          fileName={viewingPdf.name}
          studyId={viewingPdf.study_id}
          onClose={() => setViewingPdf(null)}
        />
      )}
    </div>
  )
}

export default OSDRFiles