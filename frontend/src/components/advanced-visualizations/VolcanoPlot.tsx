'use client'

import { useState, useEffect } from 'react'
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card'

interface VolcanoDataPoint {
    name: string
    foldChange: number
    pValue: number
    significant: boolean
}

interface VolcanoPlotProps {
    data: any
    onBack: () => void
}

export function VolcanoPlot({ data, onBack }: VolcanoPlotProps) {
    const [volcanoData, setVolcanoData] = useState<VolcanoDataPoint[]>([])

    useEffect(() => {
        if (data && data.research_areas?.top_10 && data.temporal_trends?.research_area_trends) {
            // Process data for volcano plot visualization using real temporal trends
            const points: VolcanoDataPoint[] = []

            // Get research area trends data
            const areaTrends = data.temporal_trends.research_area_trends

            // Calculate early vs late period for differential analysis
            const years = Object.keys(data.temporal_trends.yearly_publications)
                .map(Number)
                .sort((a, b) => a - b)

            const midpoint = Math.floor(years.length / 2)
            const earlyYears = years.slice(0, midpoint)
            const lateYears = years.slice(midpoint)

            // Calculate average publications for each research area in early and late periods
            data.research_areas.top_10.slice(0, 20).forEach((area: any, index: number) => {
                const areaName = area.area
                const areaTrendData = areaTrends[areaName]

                if (!areaTrendData) {
                    // If no trend data, use a default non-significant point
                    points.push({
                        name: areaName,
                        foldChange: 0,
                        pValue: 1.0,
                        significant: false
                    })
                    return
                }

                // Calculate average publications in early and late periods
                let earlyTotal = 0
                let lateTotal = 0
                let earlyCount = 0
                let lateCount = 0

                earlyYears.forEach(year => {
                    const count = areaTrendData[year] || 0
                    earlyTotal += count
                    if (count > 0) earlyCount++
                })

                lateYears.forEach(year => {
                    const count = areaTrendData[year] || 0
                    lateTotal += count
                    if (count > 0) lateCount++
                })

                // Calculate averages (avoid division by zero)
                const earlyAvg = earlyCount > 0 ? earlyTotal / earlyCount : 0
                const lateAvg = lateCount > 0 ? lateTotal / lateCount : 0

                // Calculate fold change (log2 scale)
                // Add small epsilon to avoid log(0)
                const epsilon = 0.1
                const foldChange = Math.log2((lateAvg + epsilon) / (earlyAvg + epsilon))

                // Calculate p-value using a simple statistical approach
                // This is a simplified calculation for visualization purposes
                const totalCount = earlyTotal + lateTotal
                const earlyProportion = totalCount > 0 ? earlyTotal / totalCount : 0
                const lateProportion = totalCount > 0 ? lateTotal / totalCount : 0

                // Simple p-value approximation (for visualization only)
                // In a real implementation, this would use statistical tests
                let pValue = 1.0
                if (totalCount > 0) {
                    // Use a simplified calculation based on the difference in proportions
                    const proportionDiff = Math.abs(lateProportion - earlyProportion)
                    // Convert to p-value-like scale (0 to 1)
                    pValue = Math.max(0.001, 1 - proportionDiff * 10)
                }

                // Determine significance
                const significant = Math.abs(foldChange) > 0.5 && pValue < 0.05

                points.push({
                    name: areaName,
                    foldChange: parseFloat(foldChange.toFixed(3)),
                    pValue: parseFloat(pValue.toFixed(3)),
                    significant
                })
            })

            setVolcanoData(points)
        }
    }, [data])

    // Custom tooltip for volcano plot
    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload
            return (
                <div className="bg-gray-800 border border-gray-700 p-3 rounded-lg shadow-lg">
                    <p className="text-white font-semibold">{data.name}</p>
                    <p className="text-blue-400">Fold Change: {data.foldChange.toFixed(3)}</p>
                    <p className="text-green-400">P-value: {data.pValue.toFixed(3)}</p>
                    <p className={`font-semibold ${data.significant ? 'text-red-400' : 'text-gray-400'}`}>
                        {data.significant ? 'Significant' : 'Not Significant'}
                    </p>
                </div>
            )
        }
        return null
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Research Area Volcano Plot</h1>
                    <p className="text-gray-300">Differential analysis of research areas</p>
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
                    <CardTitle className="text-white">Research Area Differential Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                    {volcanoData.length > 0 ? (
                        <div className="h-96">
                            <ResponsiveContainer width="100%" height="100%">
                                <ScatterChart
                                    margin={{
                                        top: 20,
                                        right: 20,
                                        bottom: 20,
                                        left: 20,
                                    }}
                                >
                                    <XAxis
                                        type="number"
                                        dataKey="foldChange"
                                        name="Fold Change"
                                        domain={[-2, 2]}
                                        label={{
                                            value: 'Log2 Fold Change',
                                            position: 'bottom',
                                            fill: '#9CA3AF',
                                            fontSize: 14
                                        }}
                                    />
                                    <YAxis
                                        type="number"
                                        dataKey="pValue"
                                        name="P-value"
                                        domain={[0, 0.1]}
                                        reversed={true}
                                        label={{
                                            value: '-Log10 P-value',
                                            angle: -90,
                                            position: 'insideLeft',
                                            fill: '#9CA3AF',
                                            fontSize: 14
                                        }}
                                    />
                                    <ZAxis type="number" range={[100]} />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Legend />
                                    <Scatter
                                        name="Significant"
                                        data={volcanoData.filter(d => d.significant)}
                                        fill="#ef4444"
                                        stroke="#7f1d1d"
                                        strokeWidth={1}
                                    />
                                    <Scatter
                                        name="Not Significant"
                                        data={volcanoData.filter(d => !d.significant)}
                                        fill="#6b7280"
                                        stroke="#1f2937"
                                        strokeWidth={1}
                                    />
                                    {/* Threshold lines */}
                                    <line
                                        x1={-2}
                                        y1={0.05}
                                        x2={2}
                                        y2={0.05}
                                        stroke="#9CA3AF"
                                        strokeDasharray="3 3"
                                        strokeWidth={1}
                                    />
                                    <line
                                        x1={0.5}
                                        y1={0}
                                        x2={0.5}
                                        y2={0.1}
                                        stroke="#9CA3AF"
                                        strokeDasharray="3 3"
                                        strokeWidth={1}
                                    />
                                    <line
                                        x1={-0.5}
                                        y1={0}
                                        x2={-0.5}
                                        y2={0.1}
                                        stroke="#9CA3AF"
                                        strokeDasharray="3 3"
                                        strokeWidth={1}
                                    />
                                </ScatterChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-400">
                            No differential analysis data available
                        </div>
                    )}
                </CardContent>
            </Card>

            <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="bg-gray-800/50 border-gray-700">
                    <CardHeader>
                        <CardTitle className="text-white text-lg">Significant Findings</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {volcanoData.filter(d => d.significant).slice(0, 5).map((point, index) => (
                                <div key={index} className="flex items-center justify-between">
                                    <span className="text-gray-300">{point.name}</span>
                                    <span className="text-red-400">
                                        FC: {point.foldChange.toFixed(2)}, P: {point.pValue.toFixed(3)}
                                    </span>
                                </div>
                            ))}
                            {volcanoData.filter(d => d.significant).length === 0 && (
                                <div className="text-gray-400 text-center py-4">
                                    No significant findings identified
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-gray-800/50 border-gray-700">
                    <CardHeader>
                        <CardTitle className="text-white text-lg">Analysis Parameters</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            <div className="flex justify-between">
                                <span className="text-gray-300">Significance Threshold</span>
                                <span className="text-blue-400">P &lt; 0.05</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-300">Fold Change Threshold</span>
                                <span className="text-blue-400">|FC| &gt; 0.5</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-300">Total Research Areas</span>
                                <span className="text-green-400">{volcanoData.length}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-300">Significant Areas</span>
                                <span className="text-red-400">{volcanoData.filter(d => d.significant).length}</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}