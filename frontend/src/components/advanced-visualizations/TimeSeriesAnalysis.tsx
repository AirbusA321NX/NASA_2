'use client'

import { useState, useEffect } from 'react'
import {
    LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, AreaChart, Area
} from 'recharts'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card'

interface TimeSeriesDataPoint {
    year: number
    publications: number
    growthRate?: number
}

interface TimeSeriesAnalysisProps {
    data: any
    onBack: () => void
}

export function TimeSeriesAnalysis({ data, onBack }: TimeSeriesAnalysisProps) {
    const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesDataPoint[]>([])
    const [viewMode, setViewMode] = useState<'line' | 'bar' | 'area'>('line')

    useEffect(() => {
        if (data && data.temporal_trends?.publications_by_year) {
            // Process data for time series visualization
            const rawData = data.temporal_trends.publications_by_year
            const years = Object.keys(rawData).map(Number).sort((a, b) => a - b)

            const points: TimeSeriesDataPoint[] = years.map((year, index) => {
                const publications = rawData[year]

                // Calculate growth rate compared to previous year
                let growthRate = 0
                if (index > 0) {
                    const previousYear = years[index - 1]
                    const previousPublications = rawData[previousYear]
                    if (previousPublications > 0) {
                        growthRate = ((publications - previousPublications) / previousPublications) * 100
                    }
                }

                return {
                    year,
                    publications,
                    growthRate: parseFloat(growthRate.toFixed(2))
                }
            })

            setTimeSeriesData(points)
        }
    }, [data])

    // Custom tooltip for time series
    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-gray-800 border border-gray-700 p-3 rounded-lg shadow-lg">
                    <p className="text-white font-semibold">{`Year: ${label}`}</p>
                    {payload.map((entry: any, index: number) => (
                        <p key={index} className={entry.dataKey === 'publications' ? 'text-blue-400' : 'text-green-400'}>
                            {`${entry.name}: ${entry.value}${entry.dataKey === 'growthRate' ? '%' : ''}`}
                        </p>
                    ))}
                </div>
            )
        }
        return null
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Publication Trends Analysis</h1>
                    <p className="text-gray-300">Temporal analysis of NASA space biology research</p>
                </div>
                <button
                    onClick={onBack}
                    className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
                >
                    ← Back to Analytics
                </button>
            </div>

            {/* View Mode Selector */}
            <div className="mb-6 flex justify-center">
                <div className="inline-flex rounded-md shadow-sm" role="group">
                    <button
                        type="button"
                        className={`px-4 py-2 text-sm font-medium rounded-l-lg ${viewMode === 'line'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                            }`}
                        onClick={() => setViewMode('line')}
                    >
                        Line Chart
                    </button>
                    <button
                        type="button"
                        className={`px-4 py-2 text-sm font-medium ${viewMode === 'bar'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                            }`}
                        onClick={() => setViewMode('bar')}
                    >
                        Bar Chart
                    </button>
                    <button
                        type="button"
                        className={`px-4 py-2 text-sm font-medium rounded-r-lg ${viewMode === 'area'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                            }`}
                        onClick={() => setViewMode('area')}
                    >
                        Area Chart
                    </button>
                </div>
            </div>

            <Card className="bg-gray-800/50 border-gray-700">
                <CardHeader>
                    <CardTitle className="text-white">Publication Trends Over Time</CardTitle>
                </CardHeader>
                <CardContent>
                    {timeSeriesData.length > 0 ? (
                        <div className="h-96">
                            <ResponsiveContainer width="100%" height="100%">
                                {viewMode === 'line' ? (
                                    <LineChart
                                        data={timeSeriesData}
                                        margin={{
                                            top: 5,
                                            right: 30,
                                            left: 20,
                                            bottom: 5,
                                        }}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                        <XAxis
                                            dataKey="year"
                                            stroke="#9CA3AF"
                                            tick={{ fill: '#9CA3AF' }}
                                        />
                                        <YAxis
                                            stroke="#9CA3AF"
                                            tick={{ fill: '#9CA3AF' }}
                                        />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Legend />
                                        <Line
                                            type="monotone"
                                            dataKey="publications"
                                            name="Publications"
                                            stroke="#3b82f6"
                                            strokeWidth={2}
                                            dot={{ r: 4 }}
                                            activeDot={{ r: 6 }}
                                        />
                                    </LineChart>
                                ) : viewMode === 'bar' ? (
                                    <BarChart
                                        data={timeSeriesData}
                                        margin={{
                                            top: 5,
                                            right: 30,
                                            left: 20,
                                            bottom: 5,
                                        }}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                        <XAxis
                                            dataKey="year"
                                            stroke="#9CA3AF"
                                            tick={{ fill: '#9CA3AF' }}
                                        />
                                        <YAxis
                                            stroke="#9CA3AF"
                                            tick={{ fill: '#9CA3AF' }}
                                        />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Legend />
                                        <Bar
                                            dataKey="publications"
                                            name="Publications"
                                            fill="#3b82f6"
                                        />
                                    </BarChart>
                                ) : (
                                    <AreaChart
                                        data={timeSeriesData}
                                        margin={{
                                            top: 5,
                                            right: 30,
                                            left: 20,
                                            bottom: 5,
                                        }}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                        <XAxis
                                            dataKey="year"
                                            stroke="#9CA3AF"
                                            tick={{ fill: '#9CA3AF' }}
                                        />
                                        <YAxis
                                            stroke="#9CA3AF"
                                            tick={{ fill: '#9CA3AF' }}
                                        />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Legend />
                                        <Area
                                            type="monotone"
                                            dataKey="publications"
                                            name="Publications"
                                            stroke="#3b82f6"
                                            fill="#3b82f6"
                                            fillOpacity={0.2}
                                        />
                                    </AreaChart>
                                )}
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-400">
                            No temporal data available
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Growth Rate Chart */}
            <Card className="bg-gray-800/50 border-gray-700 mt-8">
                <CardHeader>
                    <CardTitle className="text-white">Year-over-Year Growth Rate</CardTitle>
                </CardHeader>
                <CardContent>
                    {timeSeriesData.length > 0 ? (
                        <div className="h-80">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart
                                    data={timeSeriesData.filter(d => d.growthRate !== undefined)}
                                    margin={{
                                        top: 5,
                                        right: 30,
                                        left: 20,
                                        bottom: 5,
                                    }}
                                >
                                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                    <XAxis
                                        dataKey="year"
                                        stroke="#9CA3AF"
                                        tick={{ fill: '#9CA3AF' }}
                                    />
                                    <YAxis
                                        stroke="#9CA3AF"
                                        tick={{ fill: '#9CA3AF' }}
                                        tickFormatter={(value) => `${value}%`}
                                    />
                                    <Tooltip
                                        content={({ active, payload, label }) => {
                                            if (active && payload && payload.length) {
                                                return (
                                                    <div className="bg-gray-800 border border-gray-700 p-3 rounded-lg shadow-lg">
                                                        <p className="text-white font-semibold">{`Year: ${label}`}</p>
                                                        <p className="text-green-400">{`Growth Rate: ${payload[0].value}%`}</p>
                                                    </div>
                                                )
                                            }
                                            return null
                                        }}
                                    />
                                    <Legend />
                                    <Bar
                                        dataKey="growthRate"
                                        name="Growth Rate"
                                        fill={timeSeriesData.filter(d => d.growthRate !== undefined).some(d => (d.growthRate || 0) > 0) ? "#10b981" : "#ef4444"}
                                    >
                                        {timeSeriesData.filter(d => d.growthRate !== undefined).map((entry, index) => (
                                            <rect
                                                key={`bar-${index}`}
                                                fill={(entry.growthRate || 0) >= 0 ? "#10b981" : "#ef4444"}
                                            />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-400">
                            No growth rate data available
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Year-Specific Insights */}
            <Card className="bg-gray-800/50 border-gray-700 mt-8">
                <CardHeader>
                    <CardTitle className="text-white">Year-by-Year Research Insights</CardTitle>
                </CardHeader>
                <CardContent>
                    {timeSeriesData.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
                            {timeSeriesData.map((point, index) => (
                                <div key={point.year} className="bg-gray-700/50 p-4 rounded-lg border border-gray-600">
                                    <div className="text-lg font-semibold text-blue-400 mb-2">{point.year}</div>
                                    <div className="text-white mb-1">{point.publications} publications</div>
                                    {point.growthRate !== undefined && point.growthRate !== 0 && (
                                        <div className={`text-sm ${point.growthRate > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                            {point.growthRate > 0 ? '↗' : '↘'} {Math.abs(point.growthRate)}% from previous year
                                        </div>
                                    )}
                                    <div className="mt-2 text-xs text-gray-300">
                                        <div>Year-specific insights:</div>
                                        <ul className="list-disc pl-4 mt-1 space-y-1">
                                            <li>Publication count: {point.publications}</li>
                                            <li>{point.growthRate !== undefined && point.growthRate !== 0 ?
                                                `${point.growthRate > 0 ? 'Increased' : 'Decreased'} by ${Math.abs(point.growthRate)}%` :
                                                'Stable publication rate'}</li>
                                            <li>Research focus for {point.year}</li>
                                        </ul>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-400">
                            No year-specific insights available
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Summary Statistics */}
            <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-6">
                <Card className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4 text-center">
                        <div className="text-2xl font-bold text-blue-400">
                            {timeSeriesData.length > 0 ? Math.max(...timeSeriesData.map(d => d.year)) - Math.min(...timeSeriesData.map(d => d.year)) + 1 : '0'}
                        </div>
                        <div className="text-gray-300 text-sm">Years of Data</div>
                    </CardContent>
                </Card>

                <Card className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4 text-center">
                        <div className="text-2xl font-bold text-green-400">
                            {timeSeriesData.length > 0 ? timeSeriesData.reduce((sum, d) => sum + d.publications, 0) : '0'}
                        </div>
                        <div className="text-gray-300 text-sm">Total Publications</div>
                    </CardContent>
                </Card>

                <Card className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4 text-center">
                        <div className="text-2xl font-bold text-purple-400">
                            {timeSeriesData.length > 0 ? Math.max(...timeSeriesData.map(d => d.publications)) : '0'}
                        </div>
                        <div className="text-gray-300 text-sm">Peak Year Publications</div>
                    </CardContent>
                </Card>

                <Card className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4 text-center">
                        <div className="text-2xl font-bold text-yellow-400">
                            {timeSeriesData.length > 0 ?
                                `${(timeSeriesData.reduce((sum, d) => sum + (d.growthRate || 0), 0) / timeSeriesData.filter(d => d.growthRate !== undefined).length).toFixed(1)}%` :
                                '0%'}
                        </div>
                        <div className="text-gray-300 text-sm">Average Growth Rate</div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}