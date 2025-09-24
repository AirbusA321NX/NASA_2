'use client'

import React, { useState, useEffect } from 'react'

interface PDFViewerProps {
  fileUrl: string
  fileName: string
  studyId: string
  onClose: () => void
}

export function PDFViewer({ fileUrl, fileName, studyId, onClose }: PDFViewerProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)

  useEffect(() => {
    // For security reasons, we can't directly embed external PDFs
    // Instead, we'll provide a download link and instructions
    setPdfUrl(fileUrl)
    setLoading(false)
  }, [fileUrl])

  const handleDownload = () => {
    if (pdfUrl) {
      window.open(pdfUrl, '_blank')
    }
  }

  const handleViewInNewTab = () => {
    if (pdfUrl) {
      window.open(pdfUrl, '_blank')
    }
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-8 max-w-2xl w-full mx-4">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white">Loading PDF Viewer</h2>
            <button 
              onClick={onClose}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>
          
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <span className="ml-4 text-gray-300">Preparing PDF viewer...</span>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-8 max-w-2xl w-full mx-4">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white">PDF Viewer Error</h2>
            <button 
              onClick={onClose}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>
          
          <div className="bg-red-900/30 border border-red-700 rounded-lg p-6">
            <div className="text-red-400 text-2xl mb-2">⚠️</div>
            <h3 className="text-xl font-semibold text-red-300 mb-2">Unable to Load PDF</h3>
            <p className="text-red-200 mb-4">{error}</p>
            <div className="flex space-x-4">
              <button 
                onClick={handleDownload}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
              >
                Download PDF
              </button>
              <button 
                onClick={onClose}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-md transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 max-w-4xl w-full h-[90vh] mx-4 flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-xl font-bold text-white truncate max-w-md">{fileName}</h2>
            <p className="text-sm text-gray-400">Study ID: {studyId}</p>
          </div>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl"
          >
            ✕
          </button>
        </div>
        
        <div className="flex-1 flex flex-col bg-gray-900 rounded-lg overflow-hidden">
          <div className="bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-gray-300">📄</span>
              <span className="text-white font-medium">PDF Document</span>
            </div>
            <div className="flex space-x-2">
              <button 
                onClick={handleViewInNewTab}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm text-white transition-colors"
              >
                View in New Tab
              </button>
              <button 
                onClick={handleDownload}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm text-white transition-colors"
              >
                Download
              </button>
            </div>
          </div>
          
          <div className="flex-1 overflow-auto p-4 bg-gray-900">
            <div className="bg-white/5 border border-gray-700 rounded-lg p-8 text-center h-full flex flex-col items-center justify-center">
              <div className="text-6xl mb-4">📄</div>
              <h3 className="text-2xl font-semibold text-white mb-2">PDF Document Viewer</h3>
              <p className="text-gray-300 mb-6 max-w-md">
                For security reasons, PDFs from external sources cannot be embedded directly. 
                You can view or download the document using the buttons above.
              </p>
              
              <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 max-w-md w-full">
                <h4 className="font-medium text-white mb-2">Provenance Information</h4>
                <div className="text-sm text-gray-300 space-y-1">
                  <div className="flex justify-between">
                    <span>Source:</span>
                    <span className="text-blue-300">NASA OSDR</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Study ID:</span>
                    <span className="font-mono">{studyId}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>File Name:</span>
                    <span className="font-mono truncate max-w-[120px]">{fileName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>URL:</span>
                    <span className="font-mono text-xs truncate max-w-[120px]">{fileUrl.split('/').pop()}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}