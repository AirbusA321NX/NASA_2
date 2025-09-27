'use client'

import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'

interface GraphNode extends d3.SimulationNodeDatum {
  id: string
  type: string
  label: string
  properties?: any
  group?: string
  level?: number
}

interface GraphEdge extends d3.SimulationLinkDatum<GraphNode> {
  id: string
  source: string | GraphNode
  target: string | GraphNode
  type: string
  weight?: number
}

interface KnowledgeGraphProps {
  data?: {
    nodes: GraphNode[]
    edges: GraphEdge[]
  }
  width?: number
  height?: number
  onBack?: () => void
}

export function KnowledgeGraph({ data, width, height, onBack }: KnowledgeGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [graphData, setGraphData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [expandedStudies, setExpandedStudies] = useState<Set<string>>(new Set())

  // Fetch real knowledge graph data from backend
  useEffect(() => {
    const testConnection = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4004'}/health`, {
          method: 'GET',
          mode: 'cors',
          cache: 'no-cache'
        });
        return response.ok;
      } catch (error) {
        console.warn('Backend health check failed:', error);
        return false;
      }
    };

    const fetchKnowledgeGraphData = async () => {
      try {
        setLoading(true)
        setAnalyzing(true)

        // First test connection
        const isConnected = await testConnection();
        if (!isConnected) {
          console.warn('Backend service appears to be unavailable. Please ensure the backend is running on port 4001.');
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4004'}/api/knowledge-graph?limit=50&depth=3`, {
          method: 'GET',
          mode: 'cors',
          cache: 'no-cache'
        })

        if (response.ok) {
          const result = await response.json()
          if (result.success && result.data && result.data.graph) {
            setGraphData(result.data.graph)
          } else {
            console.warn('No knowledge graph data available, using minimal structure')
            setGraphData(getMinimalGraphStructure())
          }
        } else {
          console.warn('Knowledge graph API not available')
          setGraphData(getMinimalGraphStructure())
        }
      } catch (error) {
        console.warn('Failed to fetch knowledge graph data:', error)
        // Log more detailed error information
        if (error instanceof TypeError) {
          console.warn('This is likely a network connectivity issue. Please check if the backend service is running on port 4001.')
        }
        setGraphData(getMinimalGraphStructure())
      } finally {
        setLoading(false)
        // Simulate analysis time for better UX
        setTimeout(() => {
          setAnalyzing(false)
        }, 1000)
      }
    }

    if (data) {
      setGraphData(data)
      setLoading(false)
    } else {
      fetchKnowledgeGraphData()
    }
  }, [data])

  // Minimal graph structure for when no real data is available
  const getMinimalGraphStructure = () => {
    return {
      nodes: [
        { id: 'nasa-osdr', type: 'database', label: 'NASA OSDR', x: 0, y: 0, level: 0 } as GraphNode,
        { id: 'space-biology', type: 'research_area', label: 'Space Biology', x: 0, y: 0, level: 1 } as GraphNode,
        { id: 'data-loading', type: 'status', label: 'Loading Real Data...', x: 0, y: 0, level: 1 } as GraphNode
      ],
      edges: [
        { id: 'e1', source: 'nasa-osdr', target: 'space-biology', type: 'contains' },
        { id: 'e2', source: 'space-biology', target: 'data-loading', type: 'processing' }
      ]
    }
  }

  // Toggle study expansion
  const toggleStudyExpansion = (studyId: string) => {
    setExpandedStudies(prev => {
      const newSet = new Set(prev)
      if (newSet.has(studyId)) {
        newSet.delete(studyId)
      } else {
        newSet.add(studyId)
      }
      return newSet
    })
  }

  useEffect(() => {
    if (!graphData || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    // Get the actual dimensions of the SVG container
    const containerWidth = svgRef.current.clientWidth || width || 1200
    const containerHeight = svgRef.current.clientHeight || height || 800

    // Create color scale for different node types
    const colorScale = d3.scaleOrdinal()
      .domain(['publication', 'research_area', 'organism', 'author', 'keyword', 'database', 'study', 'file', 'metadata'])
      .range(['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#F97316', '#EC4899', '#64748B'])

    // Create size scale based on connections and level
    const nodeConnections = new Map()
    graphData.edges.forEach((edge: any) => {
      nodeConnections.set(edge.source, (nodeConnections.get(edge.source) || 0) + 1)
      nodeConnections.set(edge.target, (nodeConnections.get(edge.target) || 0) + 1)
    })

    const sizeScale = d3.scaleLinear()
      .domain([1, d3.max(Array.from(nodeConnections.values())) || 1])
      .range([8, 25])

    // Filter nodes to limit the number of file nodes for better performance
    const maxFileNodes = 100;
    let fileNodeCount = 0;
    const filteredNodes = graphData.nodes.filter((node: GraphNode) => {
      if (node.type === 'file') {
        if (fileNodeCount < maxFileNodes) {
          fileNodeCount++;
          return true;
        }
        return false;
      }
      return true;
    });

    // Filter edges to only include those connected to filtered nodes
    const filteredNodeIds = new Set(filteredNodes.map((node: GraphNode) => node.id));
    const filteredEdges = graphData.edges.filter((edge: GraphEdge) => {
      const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
      const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
      return filteredNodeIds.has(sourceId) && filteredNodeIds.has(targetId);
    });

    // Create force simulation with improved parameters for better spacing
    const simulation = d3.forceSimulation<GraphNode>(filteredNodes)
      .force('link', d3.forceLink<GraphNode, GraphEdge>(filteredEdges)
        .id((d) => d.id)
        .distance((d) => {
          // Increase distance based on node levels and types
          const sourceNode = d.source as GraphNode;
          const targetNode = d.target as GraphNode;
          const levelFactor = (sourceNode.level || 0) + (targetNode.level || 0) + 1;

          // Different distances for different relationship types
          switch ((d as GraphEdge).type) {
            case 'contains': return 150 + (levelFactor * 50);
            case 'references': return 200;
            case 'similar_to': return 250;
            default: return 100 + (levelFactor * 30);
          }
        })
        .strength(0.7)
      )
      .force('charge', d3.forceManyBody().strength((d) => {
        // Stronger repulsion for better spacing
        const level = (d as GraphNode).level || 0;
        return -400 - (level * 150);
      }))
      .force('center', d3.forceCenter(containerWidth / 2, containerHeight / 2))
      .force('collision', d3.forceCollide<GraphNode>()
        .radius((d) => sizeScale(nodeConnections.get(d.id) || 1) + 20)
        .strength(0.9)
      )
      .force('x', d3.forceX(containerWidth / 2).strength(0.1))
      .force('y', d3.forceY(containerHeight / 2).strength(0.1))

    // Create zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform)
      })

    svg.call(zoom as any)

    // Create container for zoomable content
    const container = svg.append('g')

    // Create links with different styles based on type
    const links = container.append('g')
      .selectAll('line')
      .data(filteredEdges)
      .enter()
      .append('line')
      .attr('stroke', (d) => {
        // Different colors for different edge types
        switch ((d as GraphEdge).type) {
          case 'contains': return '#60A5FA';
          case 'references': return '#34D399';
          case 'author_of': return '#FBBF24';
          case 'keyword_of': return '#A78BFA';
          case 'belongs_to': return '#F87171';
          case 'studies': return '#34D399';
          case 'authored': return '#FBBF24';
          case 'tagged_with': return '#A78BFA';
          case 'similar_to': return '#C084FC';
          default: return '#6B7280';
        }
      })
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', (d) => Math.sqrt((d as GraphEdge).weight || 1) * 2)
      .attr('stroke-dasharray', (d) => {
        // Dashed lines for certain relationships
        switch ((d as GraphEdge).type) {
          case 'references': return '5,5';
          case 'similar_to': return '3,3';
          default: return null;
        }
      })

    // Create nodes
    const nodes = container.append('g')
      .selectAll('circle')
      .data(filteredNodes)
      .enter()
      .append('circle')
      .attr('r', (d) => {
        // Special size for study nodes that can be expanded
        if ((d as GraphNode).type === 'study') {
          return sizeScale(nodeConnections.get((d as GraphNode).id) || 1) * 1.2;
        }
        return sizeScale(nodeConnections.get((d as GraphNode).id) || 1);
      })
      .attr('fill', (d) => {
        // Special color for expanded study nodes
        if ((d as GraphNode).type === 'study' && expandedStudies.has((d as GraphNode).id)) {
          return '#F97316'; // Brighter orange for expanded studies
        }
        return colorScale((d as GraphNode).type) as string;
      })
      .attr('stroke', (d) => {
        // Special stroke for study nodes
        if ((d as GraphNode).type === 'study') {
          return expandedStudies.has((d as GraphNode).id) ? '#FFFFFF' : '#F59E0B';
        }
        return '#374151';
      })
      .attr('stroke-width', (d) => {
        // Thicker stroke for higher level nodes and study nodes
        const level = (d as GraphNode).level || 0;
        if ((d as GraphNode).type === 'study') {
          return expandedStudies.has((d as GraphNode).id) ? 4 : 3;
        }
        return 1 + level;
      })
      .style('cursor', 'pointer')
      .call(d3.drag<SVGCircleElement, GraphNode, GraphNode>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended) as any)

    // Add labels with better positioning
    const labels = container.append('g')
      .selectAll('text')
      .data(filteredNodes)
      .enter()
      .append('text')
      .text((d) => (d as GraphNode).label.length > 25 ? (d as GraphNode).label.substring(0, 25) + '...' : (d as GraphNode).label)
      .attr('font-size', (d) => {
        // Larger font for higher level nodes and study nodes
        const level = (d as GraphNode).level || 0;
        if ((d as GraphNode).type === 'study') {
          return 12 + (level * 2);
        }
        return 10 + (level * 2);
      })
      .attr('font-weight', (d) => {
        // Bold for higher level nodes and study nodes
        const level = (d as GraphNode).level || 0;
        if ((d as GraphNode).type === 'study') {
          return 'bold';
        }
        return level > 0 ? 'bold' : 'normal';
      })
      .attr('fill', '#E5E7EB')
      .attr('text-anchor', 'middle')
      .attr('dy', (d) => {
        // Position label based on node size
        const size = sizeScale(nodeConnections.get((d as GraphNode).id) || 1);
        return size + 15;
      })
      .style('pointer-events', 'none')
      .style('text-shadow', '1px 1px 2px black')

    // Add hover effects
    nodes
      .on('mouseover', function (event, d) {
        const node = d as GraphNode;
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', sizeScale(nodeConnections.get(node.id) || 1) * 1.5)
          .attr('stroke-width', 3)

        // Highlight connected nodes and edges
        highlightConnected(node.id, filteredEdges);

        // Show tooltip
        showTooltip(event, node)
      })
      .on('mouseout', function (event, d) {
        const node = d as GraphNode;
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', (d) => {
            // Special size for study nodes that can be expanded
            if ((d as GraphNode).type === 'study') {
              return sizeScale(nodeConnections.get((d as GraphNode).id) || 1) * 1.2;
            }
            return sizeScale(nodeConnections.get((d as GraphNode).id) || 1);
          })
          .attr('stroke-width', (d) => {
            const level = (d as GraphNode).level || 0;
            if ((d as GraphNode).type === 'study') {
              return expandedStudies.has((d as GraphNode).id) ? 4 : 3;
            }
            return 1 + level;
          })

        // Remove highlight
        removeHighlight();

        hideTooltip()
      })
      .on('click', function (event, d) {
        const node = d as GraphNode;
        // Toggle expansion for study nodes
        if (node.type === 'study') {
          toggleStudyExpansion(node.id);
        }
      })

    // Update positions on simulation tick
    simulation.on('tick', () => {
      links
        .attr('x1', (d) => ((d as GraphEdge).source as GraphNode).x || 0)
        .attr('y1', (d) => ((d as GraphEdge).source as GraphNode).y || 0)
        .attr('x2', (d) => ((d as GraphEdge).target as GraphNode).x || 0)
        .attr('y2', (d) => ((d as GraphEdge).target as GraphNode).y || 0)

      nodes
        .attr('cx', (d) => (d as GraphNode).x || 0)
        .attr('cy', (d) => (d as GraphNode).y || 0)

      labels
        .attr('x', (d) => (d as GraphNode).x || 0)
        .attr('y', (d) => {
          const node = d as GraphNode;
          const size = sizeScale(nodeConnections.get(node.id) || 1);
          return (node.y || 0) + size + 15;
        })
    })

    // Drag functions
    function dragstarted(event: d3.D3DragEvent<SVGCircleElement, GraphNode, GraphNode>) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      event.subject.fx = event.subject.x
      event.subject.fy = event.subject.y
    }

    function dragged(event: d3.D3DragEvent<SVGCircleElement, GraphNode, GraphNode>) {
      event.subject.fx = event.x
      event.subject.fy = event.y
    }

    function dragended(event: d3.D3DragEvent<SVGCircleElement, GraphNode, GraphNode>) {
      if (!event.active) simulation.alphaTarget(0)
      event.subject.fx = null
      event.subject.fy = null
    }

    // Highlight connected nodes and edges
    function highlightConnected(nodeId: string, edges: GraphEdge[]) {
      // Highlight connected edges
      links
        .filter((d) => (d as GraphEdge).source === nodeId || (d as GraphEdge).target === nodeId)
        .attr('stroke-opacity', 1)
        .attr('stroke-width', (d) => (Math.sqrt((d as GraphEdge).weight || 1) * 2) + 2)

      // Highlight connected nodes
      nodes
        .filter((d) => {
          const node = d as GraphNode;
          return node.id === nodeId ||
            edges.some((e: GraphEdge) =>
              (e.source === nodeId && e.target === node.id) ||
              (e.target === nodeId && e.source === node.id)
            );
        })
        .attr('stroke', '#FFFFFF')
        .attr('stroke-width', 3)
    }

    // Remove highlight
    function removeHighlight() {
      links
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', (d) => Math.sqrt((d as GraphEdge).weight || 1) * 2)

      nodes
        .attr('stroke', (d) => {
          // Special stroke for study nodes
          if ((d as GraphNode).type === 'study') {
            return expandedStudies.has((d as GraphNode).id) ? '#FFFFFF' : '#F59E0B';
          }
          return '#374151';
        })
        .attr('stroke-width', (d) => {
          const level = (d as GraphNode).level || 0;
          if ((d as GraphNode).type === 'study') {
            return expandedStudies.has((d as GraphNode).id) ? 4 : 3;
          }
          return 1 + level;
        })
    }

    // Tooltip functions
    function showTooltip(event: MouseEvent, d: GraphNode) {
      // Remove any existing tooltips
      d3.selectAll('.graph-tooltip').remove();

      const tooltip = d3.select('body')
        .append('div')
        .attr('class', 'graph-tooltip')
        .style('position', 'absolute')
        .style('background', 'rgba(0, 0, 0, 0.9)')
        .style('color', 'white')
        .style('padding', '10px')
        .style('border-radius', '6px')
        .style('pointer-events', 'none')
        .style('opacity', 0)
        .style('border', '1px solid #4B5563')
        .style('box-shadow', '0 4px 6px rgba(0, 0, 0, 0.3)')
        .style('max-width', '300px')
        .style('font-size', '12px')
        .style('z-index', '1000')

      tooltip.transition()
        .duration(200)
        .style('opacity', 1)

      // Format properties for display
      let propertiesHtml = '';
      if (d.properties) {
        propertiesHtml = '<div class="mt-2">';
        Object.entries(d.properties).forEach(([key, value]) => {
          if (typeof value === 'string' && value.length > 50) {
            propertiesHtml += `<div class="mb-1"><strong>${key}:</strong> ${value.substring(0, 50)}...</div>`;
          } else {
            propertiesHtml += `<div class="mb-1"><strong>${key}:</strong> ${value}</div>`;
          }
        });
        propertiesHtml += '</div>';
      }

      // Add expansion indicator for study nodes
      let expansionHtml = '';
      if (d.type === 'study') {
        expansionHtml = `<div class="mt-2 text-yellow-300">${expandedStudies.has(d.id) ? '▼ Click to collapse files' : '▶ Click to expand files'}</div>`;
      }

      tooltip.html(`
        <div class="font-bold text-blue-300">${d.label}</div>
        <div class="text-gray-300 mt-1">Type: ${d.type}</div>
        <div class="text-gray-300">Connections: ${nodeConnections.get(d.id) || 0}</div>
        ${d.level !== undefined ? `<div class="text-gray-300">Level: ${d.level}</div>` : ''}
        ${propertiesHtml}
        ${expansionHtml}
      `)
        .style('left', (event.pageX + 15) + 'px')
        .style('top', (event.pageY - 15) + 'px')
    }

    function hideTooltip() {
      d3.selectAll('.graph-tooltip').transition()
        .duration(200)
        .style('opacity', 0)
        .remove()
    }

    // Cleanup
    return () => {
      simulation.stop()
      d3.selectAll('.graph-tooltip').remove()
    }

  }, [graphData, width, height, expandedStudies])

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
        <div className="text-center py-24">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
          <p className="text-gray-300 text-lg">{analyzing ? 'Analyzing knowledge graph data...' : 'Loading knowledge graph from NASA OSDR data...'}</p>
          {analyzing && (
            <div className="mt-4">
              <div className="w-64 h-2 bg-gray-700 rounded-full mx-auto overflow-hidden">
                <div className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full animate-pulse-custom"></div>
              </div>
              <p className="text-gray-400 text-sm mt-2">Mapping relationships between studies, organisms, and research areas</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-24">
          <div className="text-6xl mb-4">🕸️</div>
          <p className="text-gray-400 text-lg">No knowledge graph data available</p>
          <p className="text-gray-500 text-sm mt-2">Knowledge graph will be populated from real NASA OSDR analysis</p>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full bg-gray-900 flex flex-col h-[calc(100vh-150px)]">
      {/* Header */}
      <div className="bg-gray-800/90 backdrop-blur-sm border-b border-gray-700 p-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white font-orbitron">Knowledge Graph Explorer</h1>
          <p className="text-gray-300 text-sm">Interactive visualization of NASA space biology research connections</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-300">
            {graphData && (
              <span>
                {graphData.nodes.length} nodes, {graphData.edges.length} connections
              </span>
            )}
          </div>
          {onBack && (
            <button
              onClick={onBack}
              className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors font-orbitron"
            >
              ← Back to Dashboard
            </button>
          )}
        </div>
      </div>

      {/* Loading Overlay */}
      {analyzing && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full mx-4 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
            <h3 className="text-xl font-semibold text-white mb-2">Analyzing Knowledge Graph</h3>
            <p className="text-gray-300 mb-4">Mapping relationships between NASA OSDR studies and research entities</p>
            <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
              <div className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full animate-pulse-custom"></div>
            </div>
          </div>
        </div>
      )}

      <div className="knowledge-graph relative bg-gray-800/30 rounded-lg p-4 flex-1 overflow-hidden">
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          className="border border-gray-600 rounded-lg bg-gray-900 w-full h-full"
        >
        </svg>
        {/* Legend */}
        <div className="absolute top-4 right-4 bg-gray-800/90 p-4 rounded-lg text-sm max-w-xs">
          <h4 className="font-semibold mb-3 text-white">Node Types</h4>
          <div className="grid grid-cols-2 gap-2">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span className="text-gray-300">Publications</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-gray-300">Research Areas</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <span className="text-gray-300">Organisms</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <span className="text-gray-300">Authors</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
              <span className="text-gray-300">Keywords</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-cyan-500 rounded-full"></div>
              <span className="text-gray-300">Database</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
              <span className="text-gray-300">Studies</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-pink-500 rounded-full"></div>
              <span className="text-gray-300">Files</span>
            </div>
          </div>

          <h4 className="font-semibold mb-2 mt-3 text-white">Relationship Types</h4>
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-0.5 bg-blue-400"></div>
              <span className="text-gray-300">Contains</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-0.5 bg-green-400" style={{ strokeDasharray: '5,5' }}></div>
              <span className="text-gray-300">References</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-0.5 bg-purple-400" style={{ strokeDasharray: '3,3' }}></div>
              <span className="text-gray-300">Similar</span>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="absolute bottom-4 left-4 bg-gray-800/90 p-4 rounded-lg text-sm">
          <div className="space-y-2 text-gray-300">
            <div>🖱️ Drag nodes to reposition</div>
            <div>🔍 Scroll to zoom</div>
            <div>📄 Click nodes for details</div>
            <div>📁 Click study nodes to expand/collapse files</div>
          </div>
        </div>
      </div>

      {/* Info Panel */}
      <div className="mt-6 bg-gray-800/50 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-white mb-2">About this Visualization</h3>
        <p className="text-gray-300 text-sm">
          This knowledge graph shows relationships between NASA OSDR studies, their associated files, and related research.
          Studies are connected to their files, and publications are linked to research areas, organisms, and keywords.
          Drag nodes to reposition them, scroll to zoom, and click on nodes for more details. Click on study nodes to expand and see their associated files.
        </p>
      </div>
    </div>
  )
}

export default KnowledgeGraph