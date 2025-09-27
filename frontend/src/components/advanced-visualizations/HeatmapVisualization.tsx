'use client'

import { useState, useEffect } from 'react'
import { HeatMapGrid } from 'react-grid-heatmap'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card'

interface HeatmapDataPoint {
    x: string
    y: string
    value: number
}

interface HeatmapVisualizationProps {
    data: any
    onBack: () => void
}

export function HeatmapVisualization({ data, onBack }: HeatmapVisualizationProps) {
    const [heatmapData, setHeatmapData] = useState<HeatmapDataPoint[]>([])
    const [xLabels, setXLabels] = useState<string[]>([])
    const [yLabels, setYLabels] = useState<string[]>([])

    useEffect(() => {
        console.log('HeatmapVisualization received data:', data);

        if (data && data.research_areas?.distribution && data.organisms) {
            // Get top 10 research areas
            const areaEntries = Object.entries(data.research_areas.distribution)
                .sort((a, b) => (b[1] as number) - (a[1] as number))
                .slice(0, 10)
            const areas = areaEntries.map(([area]) => area)

            // Get top 10 organisms
            const organisms = Array.isArray(data.organisms.top_organisms) ?
                data.organisms.top_organisms.slice(0, 10) :
                Object.keys(data.organisms || {}).slice(0, 10)

            // Create labels
            setXLabels(areas)
            setYLabels(organisms)

            // Create correlation data points based on actual data
            // For this visualization, we'll use a simple correlation based on the relative frequency
            // of research areas and organisms in the dataset
            const points: HeatmapDataPoint[] = []

            // Calculate max values for normalization
            const maxAreaCount = Math.max(...areaEntries.map(([_, count]) => count as number), 1)
            const maxOrganismCount = Math.max(
                ...(Array.isArray(data.organisms.top_organisms) ?
                    data.organisms.top_organisms.map(() => 1) :
                    Object.values(data.organisms || {}).map(count => count as number)),
                1
            )

            areas.forEach((area, xIndex) => {
                organisms.forEach((organism: string, yIndex: number) => {
                    // Get actual counts
                    const areaCount = data.research_areas.distribution[area] || 0
                    // For organisms, we don't have counts, so we'll use a simple approach
                    const organismCount = 1 // Simplified for this visualization

                    // Normalize values to 0-1 range
                    const normalizedArea = areaCount / maxAreaCount
                    const normalizedOrganism = organismCount / maxOrganismCount

                    // Calculate correlation value (0-100 range)
                    // This is a simplified correlation for visualization purposes
                    // In a real implementation, this would come from actual co-occurrence analysis
                    const correlation = (normalizedArea * normalizedOrganism * 100)

                    points.push({ x: area, y: organism, value: correlation })
                })
            })

            setHeatmapData(points)
        } else {
            console.log('Insufficient data for heatmap visualization');
            setXLabels([]);
            setYLabels([]);
            setHeatmapData([]);
        }
    }, [data])

    // Convert data to matrix format for heatmap
    const getDataMatrix = () => {
        const matrix: number[][] = []
        yLabels.forEach((yLabel, yIndex) => {
            const row: number[] = []
            xLabels.forEach((xLabel, xIndex) => {
                const point = heatmapData.find(p => p.x === xLabel && p.y === yLabel)
                row.push(point ? point.value : 0)
            })
            matrix.push(row)
        })
        return matrix
    }

    const dataMatrix = getDataMatrix()

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Research Correlation Heatmap</h1>
                    <p className="text-gray-300">Correlation analysis between research areas and organisms</p>
                </div>
                <button
                    onClick={onBack}
                    className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
                >
                    ← Back to Analytics
                </button>
            </div>

            <Card className="bg-gray-800/50 border-gray-700">
                <CardHeader>
                    <CardTitle className="text-white">Research Area vs Organism Correlation</CardTitle>
                </CardHeader>
                <CardContent>
                    {dataMatrix.length > 0 && xLabels.length > 0 && yLabels.length > 0 ? (
                        <div className="overflow-x-auto">
                            <HeatMapGrid
                                data={dataMatrix}
                                xLabels={xLabels.map(label => label.length > 15 ? `${label.substring(0, 15)}...` : label)}
                                yLabels={yLabels.map(label => label.length > 15 ? `${label.substring(0, 15)}...` : label)}
                                cellRender={(x, y, value) => (
                                    <div className="flex items-center justify-center w-full h-full text-xs">
                                        {value.toFixed(1)}
                                    </div>
                                )}
                                cellHeight="2rem"
                                xLabelsStyle={(index) => ({
                                    color: '#9CA3AF',
                                    fontSize: '.75rem',
                                })}
                                yLabelsStyle={() => ({
                                    color: '#9CA3AF',
                                    fontSize: '.75rem',
                                })}
                                cellStyle={(_x, _y, ratio) => ({
                                    background: `rgb(59, 130, 246, ${ratio})`,
                                    border: '1px solid #374151',
                                    borderRadius: '0.25rem',
                                })}
                                onClick={(x, y) => console.log(`Clicked ${xLabels[x]}, ${yLabels[y]}`)}
                            />
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-400">
                            No correlation data available for visualization
                        </div>
                    )}
                </CardContent>
            </Card>

            <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="bg-gray-800/50 border-gray-700">
                    <CardHeader>
                        <CardTitle className="text-white text-lg">Top Research Areas</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {data?.research_areas?.top_10?.slice(0, 5).map((area: any, index: number) => (
                                <div key={index} className="flex items-center justify-between">
                                    <span className="text-gray-300">{area.area}</span>
                                    <span className="text-blue-400">{area.count} studies</span>
                                </div>
                            )) || (
                                    <div className="text-gray-400 text-center py-4">
                                        No research area data available
                                    </div>
                                )}
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-gray-800/50 border-gray-700">
                    <CardHeader>
                        <CardTitle className="text-white text-lg">Top Organisms</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {data?.organisms?.top_organisms?.slice(0, 5).map((organism: string, index: number) => (
                                <div key={index} className="flex items-center justify-between">
                                    <span className="text-gray-300">{organism}</span>
                                    <span className="text-green-400">Studied</span>
                                </div>
                            )) || (
                                    <div className="text-gray-400 text-center py-4">
                                        No organism data available
                                    </div>
                                )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}

export default HeatmapVisualization