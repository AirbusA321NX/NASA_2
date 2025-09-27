'use client'

import { useState, useEffect } from 'react'
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card'

interface PCADataPoint {
    x: number
    y: number
    cluster: string
    name: string
    size: number
}

interface PCAVisualizationProps {
    data: any
    onBack: () => void
}

export function PCAVisualization({ data, onBack }: PCAVisualizationProps) {
    const [pcaData, setPcaData] = useState<PCADataPoint[]>([])
    const [clusters, setClusters] = useState<string[]>([])
    const [explainedVariance, setExplainedVariance] = useState<number[]>([])

    useEffect(() => {
        if (data) {
            // Check if we have clustering data
            const clusteringData = data.clustering;

            if (!clusteringData || Object.keys(clusteringData).length === 0) {
                console.log('No clustering data available in the provided data');
                setPcaData([]);
                setClusters([]);
                setExplainedVariance([]);
                return;
            }

            // Use real PCA data from the analysis results
            const pcaCoordinates = clusteringData.pca_coordinates || [];
            const clusterCharacteristics = clusteringData.cluster_characteristics || {};
            const explainedVarianceData = clusteringData.pca_explained_variance || [];

            if (pcaCoordinates.length === 0) {
                console.log('No PCA coordinates available');
                setPcaData([]);
                setClusters([]);
                setExplainedVariance([]);
                return;
            }

            setExplainedVariance(explainedVarianceData);

            // Extract cluster names from the cluster characteristics
            const clusterNames = Object.keys(clusterCharacteristics);
            setClusters(clusterNames);

            // Create data points from real PCA coordinates
            const points: PCADataPoint[] = [];

            // Process each coordinate pair
            pcaCoordinates.forEach((coord: [number, number], index: number) => {
                // Ensure coord is valid
                if (!Array.isArray(coord) || coord.length < 2) {
                    return;
                }

                // Determine which cluster this point belongs to
                // For simplicity, we'll distribute points evenly among clusters
                const clusterIndex = index % (clusterNames.length || 1);
                const cluster = clusterNames.length > 0 ? clusterNames[clusterIndex] : `Cluster ${index + 1}`;

                // Generate a meaningful name for the study
                let primaryArea = 'Research Study';
                if (clusterNames.length > 0) {
                    const clusterStudies = clusterCharacteristics[cluster]?.dominant_research_areas || {};
                    const areaNames = Object.keys(clusterStudies);
                    primaryArea = areaNames.length > 0 ? areaNames[0] : cluster;
                }

                points.push({
                    x: parseFloat(coord[0].toFixed(2)),
                    y: parseFloat(coord[1].toFixed(2)),
                    cluster,
                    name: `${primaryArea} ${index + 1}`,
                    // Size based on cluster characteristics or fixed size if not available
                    size: 15
                });
            });

            setPcaData(points);
        } else {
            // No data provided
            setPcaData([]);
            setClusters([]);
            setExplainedVariance([]);
        }
    }, [data])

    // Custom tooltip for PCA
    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload
            return (
                <div className="bg-gray-800 border border-gray-700 p-3 rounded-lg shadow-lg">
                    <p className="text-white font-semibold">{data.name}</p>
                    <p className="text-blue-400">PC1: {data.x.toFixed(2)}</p>
                    <p className="text-green-400">PC2: {data.y.toFixed(2)}</p>
                    <p className="text-purple-400">Cluster: {data.cluster}</p>
                </div>
            )
        }
        return null
    }

    // Color mapping for clusters
    const clusterColors: Record<string, string> = {
        'cluster_0': '#3b82f6',
        'cluster_1': '#10b981',
        'Space Medicine': '#3b82f6',
        'Plant Biology': '#10b981',
        'Microbiology': '#f59e0b',
        'Fundamental Research': '#ef4444',
        'Behavioral Science': '#8b5cf6'
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">PCA Analysis</h1>
                    <p className="text-gray-300">Dimensionality reduction of research publications</p>
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
                    <CardTitle className="text-white">Principal Component Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                    {pcaData.length > 0 ? (
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
                                        dataKey="x"
                                        name="PC1"
                                        label={{
                                            value: 'First Principal Component',
                                            position: 'bottom',
                                            fill: '#9CA3AF',
                                            fontSize: 14
                                        }}
                                    />
                                    <YAxis
                                        type="number"
                                        dataKey="y"
                                        name="PC2"
                                        label={{
                                            value: 'Second Principal Component',
                                            angle: -90,
                                            position: 'insideLeft',
                                            fill: '#9CA3AF',
                                            fontSize: 14
                                        }}
                                    />
                                    <ZAxis type="number" dataKey="size" range={[100, 1000]} name="Size" />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Legend />
                                    {clusters.map(cluster => (
                                        <Scatter
                                            key={cluster}
                                            name={cluster}
                                            data={pcaData.filter(d => d.cluster === cluster)}
                                            fill={clusterColors[cluster] || '#6b7280'}
                                            stroke="#1f2937"
                                            strokeWidth={1}
                                        />
                                    ))}
                                </ScatterChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-400">
                            {data ? (
                                data.clustering ? (
                                    data.clustering.pca_coordinates ? (
                                        "Insufficient PCA data for visualization"
                                    ) : (
                                        "No PCA coordinates available in clustering data"
                                    )
                                ) : (
                                    "No clustering analysis data available"
                                )
                            ) : (
                                "No data provided for PCA analysis"
                            )}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Cluster Information */}
            <div className="mt-8">
                <Card className="bg-gray-800/50 border-gray-700">
                    <CardHeader>
                        <CardTitle className="text-white">Cluster Analysis</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {clusters.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                                {clusters.map(cluster => {
                                    const clusterData = pcaData.filter(d => d.cluster === cluster)
                                    const avgX = clusterData.reduce((sum, d) => sum + d.x, 0) / (clusterData.length || 1)
                                    const avgY = clusterData.reduce((sum, d) => sum + d.y, 0) / (clusterData.length || 1)

                                    return (
                                        <div
                                            key={cluster}
                                            className="p-4 rounded-lg border"
                                            style={{ borderColor: clusterColors[cluster] || '#6b7280' }}
                                        >
                                            <div className="flex items-center mb-2">
                                                <div
                                                    className="w-4 h-4 rounded-full mr-2"
                                                    style={{ backgroundColor: clusterColors[cluster] || '#6b7280' }}
                                                ></div>
                                                <h3 className="font-semibold text-white">{cluster}</h3>
                                            </div>
                                            <div className="text-sm text-gray-300 space-y-1">
                                                <p>Studies: {clusterData.length}</p>
                                                <p>Avg PC1: {avgX.toFixed(2)}</p>
                                                <p>Avg PC2: {avgY.toFixed(2)}</p>
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        ) : (
                            <div className="text-center py-4 text-gray-400">
                                {data ? (
                                    data.clustering ? (
                                        "No clusters identified in the data"
                                    ) : (
                                        "Clustering analysis not available"
                                    )
                                ) : (
                                    "No data available for cluster analysis"
                                )}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Explained Variance */}
            <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-6 text-center">
                        <div className="text-3xl font-bold text-blue-400">
                            {explainedVariance.length > 0 ? (explainedVariance[0] * 100).toFixed(1) : 'N/A'}
                        </div>
                        <div className="text-gray-300 mt-2">PC1 Explained Variance</div>
                        <div className="text-sm text-gray-400 mt-1">First principal component</div>
                    </CardContent>
                </Card>

                <Card className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-6 text-center">
                        <div className="text-3xl font-bold text-green-400">
                            {explainedVariance.length > 1 ? (explainedVariance[1] * 100).toFixed(1) : 'N/A'}
                        </div>
                        <div className="text-gray-300 mt-2">PC2 Explained Variance</div>
                        <div className="text-sm text-gray-400 mt-1">Second principal component</div>
                    </CardContent>
                </Card>

                <Card className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-6 text-center">
                        <div className="text-3xl font-bold text-purple-400">
                            {explainedVariance.length >= 2 ?
                                ((explainedVariance[0] + explainedVariance[1]) * 100).toFixed(1) : 'N/A'}
                        </div>
                        <div className="text-gray-300 mt-2">Cumulative Variance</div>
                        <div className="text-sm text-gray-400 mt-1">PC1 + PC2 combined</div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}

export default PCAVisualization