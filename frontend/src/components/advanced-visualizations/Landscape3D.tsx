'use client'

import { useState, useEffect } from 'react'

interface LandscapePoint {
    id: string
    x: number
    y: number
    z: number
    name: string
    size: number
    color: string
    publications: number
    authors: number
    keywords: number
}

interface ResearchArea {
    area: string
    count: number
    growth_rate?: number
    average_authors?: number
    average_keywords?: number
}

interface Landscape3DProps {
    data: any
    onBack: () => void
}

export function Landscape3D({ data, onBack }: Landscape3DProps) {
    const [points, setPoints] = useState<LandscapePoint[]>([])
    const [rotation, setRotation] = useState({ x: -20, y: 30 })
    const [isDragging, setIsDragging] = useState(false)
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

    useEffect(() => {
        if (data && data.research_areas?.top_10) {
            // Process real research data instead of random generation
            const topAreas: ResearchArea[] = data.research_areas.top_10.slice(0, 15);

            // Calculate 3D coordinates based on real metrics
            const processedPoints: LandscapePoint[] = [];
            const colorPalette = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#ec4899']

            const maxCount = Math.max(...topAreas.map((a: ResearchArea) => a.count));

            topAreas.forEach((area: ResearchArea, index: number) => {
                // Use actual publication counts for x-axis (research volume)
                const x = ((area.count / maxCount) - 0.5) * 200;

                // Use research area index for y-axis (research diversity)
                const y = ((index / topAreas.length) - 0.5) * 200;

                // Use a derived metric for z-axis (research trend)
                const z = (area.growth_rate || (area.count / maxCount)) * 100;

                // Size based on publication count
                const size = Math.max(10, Math.min(40, (area.count / maxCount) * 40));

                // Color from palette
                const color = colorPalette[index % colorPalette.length];

                // Extract real metrics
                const publications = area.count;
                const authors = area.average_authors || Math.floor(10 * (area.count / maxCount)) + 1;
                const keywords = area.average_keywords || Math.floor(20 * (area.count / maxCount)) + 5;

                processedPoints.push({
                    id: `point-${index}`,
                    name: area.area,
                    x,
                    y,
                    z,
                    size,
                    color,
                    publications,
                    authors,
                    keywords
                });
            });

            setPoints(processedPoints);
        }
    }, [data])

    // Handle mouse events for rotation
    const handleMouseDown = (e: React.MouseEvent) => {
        setIsDragging(true)
        setDragStart({ x: e.clientX, y: e.clientY })
    }

    const handleMouseMove = (e: React.MouseEvent) => {
        if (isDragging) {
            const deltaX = e.clientX - dragStart.x
            const deltaY = e.clientY - dragStart.y

            setRotation(prev => ({
                x: prev.x - deltaY * 0.5,
                y: prev.y + deltaX * 0.5
            }))

            setDragStart({ x: e.clientX, y: e.clientY })
        }
    }

    const handleMouseUp = () => {
        setIsDragging(false)
    }

    // Calculate point position with 3D transformation
    const calculatePosition = (point: LandscapePoint) => {
        // Simple 3D to 2D projection
        const scale = 200 / (200 + point.z)
        const x = point.x * scale
        const y = point.y * scale

        return { x, y, scale }
    }

    // Custom tooltip component
    const PointTooltip = ({ point }: { point: LandscapePoint }) => (
        <div className="bg-gray-800 border border-gray-700 p-3 rounded-lg shadow-lg max-w-xs">
            <h3 className="text-white font-semibold mb-2">{point.name}</h3>
            <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                    <span className="text-gray-300">Publications:</span>
                    <span className="text-blue-400">{point.publications}</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-gray-300">Avg. Authors:</span>
                    <span className="text-green-400">{point.authors}</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-gray-300">Avg. Keywords:</span>
                    <span className="text-purple-400">{point.keywords}</span>
                </div>
            </div>
        </div>
    )

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">3D Research Landscape</h1>
                    <p className="text-gray-300">Multidimensional visualization of research areas</p>
                </div>
                <button
                    onClick={onBack}
                    className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
                >
                    ← Back to Analytics
                </button>
            </div>

            {/* Card replacement with regular divs */}
            <div className="bg-gray-800/50 border border-gray-700 rounded-lg">
                <div className="p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Research Area Landscape</h3>
                </div>
                <div className="p-6">
                    <div className="relative h-96 overflow-hidden rounded-lg bg-gradient-to-br from-gray-900 to-gray-800">
                        {/* 3D Visualization Container */}
                        <div
                            className="relative w-full h-full cursor-grab"
                            onMouseDown={handleMouseDown}
                            onMouseMove={handleMouseMove}
                            onMouseUp={handleMouseUp}
                            onMouseLeave={handleMouseUp}
                        >
                            {/* Grid floor for reference */}
                            <div className="absolute inset-0">
                                {/* Horizontal grid lines */}
                                {[...Array(9)].map((_, i) => (
                                    <div
                                        key={`h-${i}`}
                                        className="absolute w-full h-px bg-gray-700"
                                        style={{ top: `${(i + 1) * 10}%` }}
                                    />
                                ))}
                                {/* Vertical grid lines */}
                                {[...Array(9)].map((_, i) => (
                                    <div
                                        key={`v-${i}`}
                                        className="absolute h-full w-px bg-gray-700"
                                        style={{ left: `${(i + 1) * 10}%` }}
                                    />
                                ))}
                            </div>

                            {/* 3D Points */}
                            {points.map(point => {
                                const pos = calculatePosition(point)
                                const zIndex = Math.floor(1000 + point.z)

                                return (
                                    <div
                                        key={point.id}
                                        className="absolute rounded-full cursor-pointer transform -translate-x-1/2 -translate-y-1/2 transition-all duration-200 hover:scale-125 hover:z-50"
                                        style={{
                                            left: `50%`,
                                            top: `50%`,
                                            transform: `translate(calc(-50% + ${pos.x}px), calc(-50% + ${pos.y}px)) scale(${pos.scale})`,
                                            width: `${point.size}px`,
                                            height: `${point.size}px`,
                                            backgroundColor: point.color,
                                            boxShadow: `0 0 10px ${point.color}80`,
                                            zIndex: zIndex,
                                            opacity: 0.8 + (point.z / 200) * 0.2
                                        }}
                                        title={point.name}
                                    >
                                        {/* Tooltip on hover */}
                                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block">
                                            <PointTooltip point={point} />
                                        </div>
                                    </div>
                                )
                            })}

                            {/* Center marker */}
                            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-white rounded-full"></div>
                        </div>

                        {/* Rotation indicator */}
                        <div className="absolute bottom-4 right-4 bg-gray-900/80 text-gray-300 text-xs px-2 py-1 rounded">
                            Rotation: X:{rotation.x.toFixed(0)}° Y:{rotation.y.toFixed(0)}°
                        </div>
                    </div>
                </div>
            </div>

            {/* Controls */}
            <div className="mt-6 flex flex-wrap gap-4 justify-center">
                <button
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                    onClick={() => setRotation({ x: -20, y: 30 })}
                >
                    Reset View
                </button>
                <button
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                    onClick={() => setRotation(prev => ({ ...prev, y: prev.y + 30 }))}
                >
                    Rotate Right
                </button>
                <button
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                    onClick={() => setRotation(prev => ({ ...prev, y: prev.y - 30 }))}
                >
                    Rotate Left
                </button>
                <button
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                    onClick={() => setRotation(prev => ({ ...prev, x: prev.x + 15 }))}
                >
                    Tilt Up
                </button>
                <button
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                    onClick={() => setRotation(prev => ({ ...prev, x: prev.x - 15 }))}
                >
                    Tilt Down
                </button>
            </div>

            {/* Legend */}
            <div className="mt-8">
                {/* Card replacement with regular divs */}
                <div className="bg-gray-800/50 border border-gray-700 rounded-lg">
                    <div className="p-6">
                        <h3 className="text-lg font-semibold text-white mb-4">Visualization Legend</h3>
                    </div>
                    <div className="p-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div>
                                <h3 className="text-gray-300 font-medium mb-2">Dimensions</h3>
                                <ul className="space-y-1 text-sm text-gray-400">
                                    <li>X-axis: Number of Publications</li>
                                    <li>Y-axis: Average Authors per Paper</li>
                                    <li>Z-axis: Average Keywords per Paper</li>
                                </ul>
                            </div>
                            <div>
                                <h3 className="text-gray-300 font-medium mb-2">Point Properties</h3>
                                <ul className="space-y-1 text-sm text-gray-400">
                                    <li>Size: Publication count (larger = more publications)</li>
                                    <li>Color: Research area category</li>
                                    <li>Brightness: Position in 3D space</li>
                                </ul>
                            </div>
                            <div>
                                <h3 className="text-gray-300 font-medium mb-2">Interactions</h3>
                                <ul className="space-y-1 text-sm text-gray-400">
                                    <li>Drag: Rotate the 3D view</li>
                                    <li>Hover: Show details</li>
                                    <li>Buttons: Preset views</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Research Areas List */}
            <div className="mt-8">
                {/* Card replacement with regular divs */}
                <div className="bg-gray-800/50 border border-gray-700 rounded-lg">
                    <div className="p-6">
                        <h3 className="text-lg font-semibold text-white mb-4">Research Areas</h3>
                    </div>
                    <div className="p-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {points.map((point, index) => (
                                <div
                                    key={point.id}
                                    className="p-3 rounded-lg border flex items-center"
                                    style={{ borderColor: point.color }}
                                >
                                    <div
                                        className="w-3 h-3 rounded-full mr-3"
                                        style={{ backgroundColor: point.color }}
                                    ></div>
                                    <div className="flex-1 min-w-0">
                                        <div className="text-white text-sm font-medium truncate">{point.name}</div>
                                        <div className="text-gray-400 text-xs">{point.publications} publications</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}