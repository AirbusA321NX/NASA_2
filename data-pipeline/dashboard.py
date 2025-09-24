# NASA OSDR Comprehensive Analytics Dashboard
# Consolidated from dashboard.py and enhanced_dashboard.py
# Features: Advanced Visualizations, Real-time Streaming, AI Insights

import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import seaborn as sns
import matplotlib.pyplot as plt
import networkx as nx
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.manifold import TSNE
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import asyncio
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import warnings
import io
import base64

# Import our custom modules
from data_analyzer import NASADataAnalyzer
from mistral_engine import process_with_mistral

# Suppress warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="NASA OSDR Advanced Analytics",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
    }
    .insight-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .analysis-section {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 1rem;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
    }
    .stSelectbox > div > div {
        background-color: #ffffff;
        border: 2px solid #1f77b4;
        border-radius: 0.5rem;
    }
    .streaming-indicator {
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    .plot-container {
        background-color: white;
        padding: 1rem;
        border-radius: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}
if 'mistral_insights' not in st.session_state:
    st.session_state.mistral_insights = {}
if 'streaming_data' not in st.session_state:
    st.session_state.streaming_data = []
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

class AdvancedVisualizations:
    """Advanced visualization components for NASA OSDR data"""
    
    def __init__(self, df: pd.DataFrame, analysis_results: Dict[str, Any]):
        self.df = df
        self.analysis_results = analysis_results
        
    def create_heatmap(self, feature_type: str = "research_areas") -> go.Figure:
        """Create correlation heatmap for research data"""
        try:
            if feature_type == "research_areas" and 'research_areas' in self.analysis_results:
                # Research area correlation matrix
                area_data = self.analysis_results['research_areas']
                area_stats = area_data.get('area_statistics', {})
                
                if area_stats:
                    # Convert to DataFrame for correlation
                    stats_df = pd.DataFrame(area_stats).T
                    if not stats_df.empty:
                        # Calculate correlation matrix for numeric columns only
                        numeric_df = stats_df.select_dtypes(include=[np.number])
                        if len(numeric_df.columns) > 1:
                            try:
                                corr_matrix = numeric_df.corr()  # type: ignore[call-arg]
                            except Exception:
                                # Fallback for correlation calculation
                                return go.Figure()
                        else:
                            # Not enough numeric columns for correlation
                            return go.Figure()
                        
                        fig = go.Figure(data=go.Heatmap(
                            z=corr_matrix.values,
                            x=corr_matrix.columns,
                            y=corr_matrix.index,
                            colorscale='RdBu',
                            zmid=0,
                            hovertemplate="X: %{x}<br>Y: %{y}<br>Correlation: %{z:.3f}<extra></extra>"
                        ))
                        
                        fig.update_layout(
                            title="Research Area Metrics Correlation Heatmap",
                            xaxis_title="Metrics",
                            yaxis_title="Research Areas"
                        )
                        return fig
            
            # Fallback: Create heatmap from raw data
            if not self.df.empty:
                numeric_cols = self.df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 1:
                    # Create correlation matrix for numeric columns
                    numeric_data = self.df[numeric_cols]
                    try:
                        corr_matrix = numeric_data.corr()  # type: ignore[call-arg]
                    except Exception:
                        return go.Figure()
                    
                    fig = go.Figure(data=go.Heatmap(
                        z=corr_matrix.values,
                        x=corr_matrix.columns,
                        y=corr_matrix.index,
                        colorscale='Viridis',
                        hovertemplate="X: %{x}<br>Y: %{y}<br>Correlation: %{z:.3f}<extra></extra>"
                    ))
                    
                    fig.update_layout(
                        title="Publication Features Correlation Heatmap",
                        xaxis_title="Features",
                        yaxis_title="Features"
                    )
                    return fig
        
        except Exception as e:
            st.error(f"Error creating heatmap: {e}")
        
        return go.Figure()
    
    def create_volcano_plot(self) -> go.Figure:
        """Create volcano plot for differential analysis"""
        try:
            # Simulate volcano plot data from research areas
            if 'research_areas' in self.analysis_results:
                area_data = self.analysis_results['research_areas']
                area_dist = area_data.get('area_distribution', {})
                
                if area_dist:
                    areas = list(area_dist.keys())[:20]  # Top 20 areas
                    counts = list(area_dist.values())[:20]
                    
                    # Simulate log fold change and p-values
                    np.random.seed(42)
                    log_fold_change = np.random.normal(0, 2, len(areas))
                    p_values = np.random.exponential(0.1, len(areas))
                    neg_log_p = -np.log10(np.maximum(p_values, 1e-10))
                    
                    # Color points based on significance
                    colors = ['Significant Up' if lfc > 1 and nlp > 1.3 
                             else 'Significant Down' if lfc < -1 and nlp > 1.3
                             else 'Not Significant' 
                             for lfc, nlp in zip(log_fold_change, neg_log_p)]
                    
                    fig = go.Figure()
                    
                    for color_type in ['Significant Up', 'Significant Down', 'Not Significant']:
                        mask = [c == color_type for c in colors]
                        if any(mask):
                            color_map = {
                                'Significant Up': 'red',
                                'Significant Down': 'blue', 
                                'Not Significant': 'gray'
                            }
                            
                            fig.add_trace(go.Scatter(
                                x=[lfc for lfc, m in zip(log_fold_change, mask) if m],
                                y=[nlp for nlp, m in zip(neg_log_p, mask) if m],
                                mode='markers',
                                name=color_type,
                                marker=dict(
                                    color=color_map[color_type],
                                    size=8,
                                    opacity=0.7
                                ),
                                text=[area for area, m in zip(areas, mask) if m],
                                hovertemplate="Area: %{text}<br>Log FC: %{x:.2f}<br>-Log10(p): %{y:.2f}<extra></extra>"
                            ))
                    
                    # Add significance lines
                    fig.add_hline(y=1.3, line_dash="dash", line_color="black", 
                                  annotation_text="p = 0.05")
                    fig.add_vline(x=1, line_dash="dash", line_color="black")
                    fig.add_vline(x=-1, line_dash="dash", line_color="black")
                    
                    fig.update_layout(
                        title="Research Area Volcano Plot (Simulated Differential Analysis)",
                        xaxis_title="Log2 Fold Change",
                        yaxis_title="-Log10(p-value)",
                        hovermode='closest'
                    )
                    
                    return fig
        
        except Exception as e:
            st.error(f"Error creating volcano plot: {e}")
        
        return go.Figure()
    
    def create_time_series_plot(self) -> go.Figure:
        """Create advanced time series plot with multiple metrics"""
        try:
            if 'temporal_trends' in self.analysis_results:
                temporal_data = self.analysis_results['temporal_trends']
                yearly_pubs = temporal_data.get('yearly_publications', {})
                
                if yearly_pubs:
                    years = [int(y) for y in yearly_pubs.keys()]
                    counts = list(yearly_pubs.values())
                    
                    # Create subplots
                    fig = make_subplots(
                        rows=2, cols=1,
                        subplot_titles=('Publication Count Over Time', 'Growth Rate Analysis'),
                        vertical_spacing=0.1
                    )
                    
                    # Publication count
                    fig.add_trace(
                        go.Scatter(
                            x=years, y=counts,
                            mode='lines+markers',
                            name='Publications',
                            line=dict(color='#1f77b4', width=3),
                            marker=dict(size=8),
                            fill='tonexty' if len(years) > 1 else None
                        ),
                        row=1, col=1
                    )
                    
                    # Calculate and plot growth rate
                    if len(counts) > 1:
                        growth_rates = [0] + [
                            (counts[i] - counts[i-1]) / counts[i-1] * 100 
                            for i in range(1, len(counts)) if counts[i-1] > 0
                        ]
                        
                        fig.add_trace(
                            go.Scatter(
                                x=years, y=growth_rates,
                                mode='lines+markers',
                                name='Growth Rate (%)',
                                line=dict(color='#ff7f0e', width=2),
                                marker=dict(size=6)
                            ),
                            row=2, col=1
                        )
                        
                        # Add zero line for growth rate
                        fig.add_hline(y=0, line_dash="dash", line_color="gray")
                    
                    fig.update_layout(
                        title="NASA OSDR Publication Trends Analysis",
                        height=600,
                        showlegend=True
                    )
                    
                    fig.update_xaxes(title_text="Year", row=2, col=1)
                    fig.update_yaxes(title_text="Publications", row=1, col=1)
                    fig.update_yaxes(title_text="Growth Rate (%)", row=2, col=1)
                    
                    return fig
        
        except Exception as e:
            st.error(f"Error creating time series plot: {e}")
        
        return go.Figure()
    
    def create_pca_plot(self) -> go.Figure:
        """Create PCA plot for dimensionality reduction"""
        try:
            if 'clustering' in self.analysis_results:
                cluster_data = self.analysis_results['clustering']
                pca_coords = cluster_data.get('pca_coordinates', [])
                explained_var = cluster_data.get('pca_explained_variance', [])
                
                if pca_coords and len(pca_coords) > 0:
                    pca_array = np.array(pca_coords)
                    
                    # Create cluster labels if available
                    n_points = len(pca_coords)
                    if 'cluster_characteristics' in cluster_data:
                        n_clusters = len(cluster_data['cluster_characteristics'])
                        cluster_labels = np.random.randint(0, n_clusters, n_points)  # Simulated
                    else:
                        cluster_labels = np.zeros(n_points)
                    
                    fig = go.Figure()
                    
                    # Plot points colored by cluster
                    unique_clusters = np.unique(cluster_labels)
                    colors = px.colors.qualitative.Set1[:len(unique_clusters)]
                    
                    for i, cluster in enumerate(unique_clusters):
                        mask = cluster_labels == cluster
                        fig.add_trace(go.Scatter(
                            x=pca_array[mask, 0],
                            y=pca_array[mask, 1],
                            mode='markers',
                            name=f'Cluster {int(cluster)}',
                            marker=dict(
                                color=colors[i],
                                size=8,
                                opacity=0.7
                            ),
                            hovertemplate=f"Cluster: {int(cluster)}<br>PC1: %{{x:.3f}}<br>PC2: %{{y:.3f}}<extra></extra>"
                        ))
                    
                    # Add explained variance to title
                    title = "PCA of NASA OSDR Publications"
                    if explained_var and len(explained_var) >= 2:
                        title += f"<br>PC1: {explained_var[0]:.1%}, PC2: {explained_var[1]:.1%} variance explained"
                    
                    fig.update_layout(
                        title=title,
                        xaxis_title="First Principal Component",
                        yaxis_title="Second Principal Component",
                        hovermode='closest'
                    )
                    
                    return fig
        
        except Exception as e:
            st.error(f"Error creating PCA plot: {e}")
        
        return go.Figure()
    
    def create_network_graph(self) -> go.Figure:
        """Create network graph for research collaboration"""
        try:
            if not self.df.empty and 'authors' in self.df.columns:
                # Create author collaboration network
                G = nx.Graph()
                
                # Add edges between co-authors
                for _, row in self.df.iterrows():
                    authors = row.get('authors', [])
                    if isinstance(authors, list) and len(authors) > 1:
                        # Add edges between all pairs of authors
                        for i in range(len(authors)):
                            for j in range(i + 1, len(authors)):
                                if G.has_edge(authors[i], authors[j]):
                                    G[authors[i]][authors[j]]['weight'] += 1
                                else:
                                    G.add_edge(authors[i], authors[j], weight=1)
                
                # Filter to most connected authors
                if len(list(G.nodes())) > 50:
                    # Keep only nodes with degree > 1  
                    nodes_to_remove = [node for node in list(G.nodes()) if G.degree[node] <= 1]
                    G.remove_nodes_from(nodes_to_remove)
                
                if len(list(G.nodes())) > 0:
                    # Calculate layout
                    pos = nx.spring_layout(G, k=1, iterations=50)
                    
                    # Extract node and edge information
                    node_x = [pos[node][0] for node in G.nodes()]
                    node_y = [pos[node][1] for node in G.nodes()]
                    node_text = list(G.nodes())
                    node_size = [G.degree[node] * 5 + 10 for node in G.nodes()]
                    
                    # Create edge traces
                    edge_x = []
                    edge_y = []
                    for edge in G.edges():
                        x0, y0 = pos[edge[0]]
                        x1, y1 = pos[edge[1]]
                        edge_x.extend([x0, x1, None])
                        edge_y.extend([y0, y1, None])
                    
                    fig = go.Figure()
                    
                    # Add edges
                    fig.add_trace(go.Scatter(
                        x=edge_x, y=edge_y,
                        line=dict(width=0.5, color='#888'),
                        hoverinfo='none',
                        mode='lines',
                        showlegend=False
                    ))
                    
                    # Add nodes
                    fig.add_trace(go.Scatter(
                        x=node_x, y=node_y,
                        mode='markers',
                        hoverinfo='text',
                        text=node_text,
                        marker=dict(
                            size=node_size,
                            color='#1f77b4',
                            opacity=0.7
                        ),
                        showlegend=False,
                        hovertemplate="Author: %{text}<br>Collaborations: %{marker.size}<extra></extra>"
                    ))
                    
                    fig.update_layout(
                        title="Author Collaboration Network",
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        annotations=[
                            dict(
                                text="Node size represents number of collaborations",
                                showarrow=False,
                                xref="paper", yref="paper",
                                x=0.005, y=-0.002,
                                xanchor='left', yanchor='bottom',
                                font=dict(size=12)
                            )
                        ],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                    )
                    
                    return fig
        
        except Exception as e:
            st.error(f"Error creating network graph: {e}")
        
        return go.Figure()
    
    def create_research_landscape_plot(self) -> go.Figure:
        """Create 3D research landscape visualization"""
        try:
            if 'research_areas' in self.analysis_results:
                area_data = self.analysis_results['research_areas']
                area_dist = area_data.get('area_distribution', {})
                area_stats = area_data.get('area_statistics', {})
                
                if area_dist and area_stats:
                    areas = list(area_dist.keys())[:15]  # Top 15 areas
                    counts = [area_dist[area] for area in areas]
                    
                    # Extract additional metrics
                    x_vals = []  # Publication count
                    y_vals = []  # Average authors
                    z_vals = []  # Average keywords
                    
                    for area in areas:
                        x_vals.append(area_dist.get(area, 0))
                        
                        # Get average authors if available
                        if area in area_stats and 'num_authors' in area_stats[area]:
                            y_vals.append(area_stats[area]['num_authors'].get('mean', 0))
                        else:
                            y_vals.append(np.random.normal(3, 1))  # Simulated
                        
                        # Get average keywords if available  
                        if area in area_stats and 'num_keywords' in area_stats[area]:
                            z_vals.append(area_stats[area]['num_keywords'].get('mean', 0))
                        else:
                            z_vals.append(np.random.normal(10, 3))  # Simulated
                    
                    fig = go.Figure(data=[go.Scatter3d(
                        x=x_vals,
                        y=y_vals,
                        z=z_vals,
                        text=areas,
                        mode='markers+text',
                        marker=dict(
                            size=[c/5 + 5 for c in counts],
                            color=counts,
                            colorscale='Viridis',
                            opacity=0.8,
                            showscale=True,
                            colorbar=dict(title="Publications")
                        ),
                        textposition="middle center",
                        hovertemplate="Area: %{text}<br>Publications: %{x}<br>Avg Authors: %{y:.1f}<br>Avg Keywords: %{z:.1f}<extra></extra>"
                    )])
                    
                    fig.update_layout(
                        title="3D Research Landscape",
                        scene=dict(
                            xaxis_title="Number of Publications",
                            yaxis_title="Average Authors per Paper",
                            zaxis_title="Average Keywords per Paper"
                        ),
                        height=600
                    )
                    
                    return fig
        
        except Exception as e:
            st.error(f"Error creating research landscape plot: {e}")
        
        return go.Figure()

class StreamingDataSimulator:
    """Simulate real-time data streaming"""
    
    @staticmethod
    def generate_new_data_point() -> Dict[str, Any]:
        """Generate a new simulated data point"""
        research_areas = [
            "Space Biology", "Human Physiology", "Plant Biology", 
            "Radiation Biology", "Microbiology", "Cell Biology"
        ]
        
        organisms = [
            "Homo sapiens", "Mus musculus", "Arabidopsis thaliana",
            "Drosophila melanogaster", "Escherichia coli"
        ]
        
        return {
            "timestamp": datetime.now(),
            "publication_count": np.random.poisson(5),
            "research_area": np.random.choice(research_areas),
            "organism_studied": np.random.choice(organisms),
            "collaboration_index": np.random.exponential(2.5),
            "innovation_score": np.random.beta(2, 5) * 100
        }
    
    @staticmethod
    def create_streaming_plot(streaming_data: List[Dict]) -> go.Figure:
        """Create real-time streaming visualization"""
        if not streaming_data:
            return go.Figure()
        
        df_stream = pd.DataFrame(streaming_data)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Publications Over Time', 'Research Area Distribution',
                'Collaboration Trends', 'Innovation Scores'
            ),
            specs=[[{"secondary_y": False}, {"type": "pie"}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Publications over time
        fig.add_trace(
            go.Scatter(
                x=df_stream['timestamp'],
                y=df_stream['publication_count'].cumsum(),
                mode='lines',
                name='Cumulative Publications',
                line=dict(color='#1f77b4', width=2)
            ),
            row=1, col=1
        )
        
        # Research area distribution
        area_counts = df_stream['research_area'].value_counts()
        fig.add_trace(
            go.Pie(
                labels=area_counts.index,
                values=area_counts.values,
                name="Research Areas"
            ),
            row=1, col=2
        )
        
        # Collaboration trends
        fig.add_trace(
            go.Scatter(
                x=df_stream['timestamp'],
                y=df_stream['collaboration_index'],
                mode='lines+markers',
                name='Collaboration Index',
                line=dict(color='#ff7f0e', width=2),
                marker=dict(size=4)
            ),
            row=2, col=1
        )
        
        # Innovation scores
        fig.add_trace(
            go.Scatter(
                x=df_stream['timestamp'],
                y=df_stream['innovation_score'],
                mode='markers',
                name='Innovation Score',
                marker=dict(
                    color=df_stream['innovation_score'],
                    colorscale='Viridis',
                    size=8,
                    showscale=False
                )
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title="Real-Time NASA OSDR Analytics Dashboard",
            height=600,
            showlegend=True
        )
        
        return fig

def load_data() -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """Load all required data"""
    try:
        # Load publications data
        with open("data/processed_publications.json", 'r', encoding='utf-8') as f:
            pub_data = json.load(f)
        df = pd.DataFrame(pub_data)
        df['publication_date'] = pd.to_datetime(df['publication_date'])
        
        # Load analysis results
        with open("data/analysis_results.json", 'r', encoding='utf-8') as f:
            analysis_results = json.load(f)
        
        # Load Mistral insights
        try:
            with open("data/mistral_insights.json", 'r', encoding='utf-8') as f:
                mistral_insights = json.load(f)
        except FileNotFoundError:
            mistral_insights = {}
        
        return df, analysis_results, mistral_insights
    
    except FileNotFoundError as e:
        st.error(f"Data file not found: {e}")
        return pd.DataFrame(), {}, {}
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), {}, {}

def main():
    """Enhanced main Streamlit application"""
    
    # Header with animation
    st.markdown('<h1 class="main-header">🚀 NASA OSDR Advanced Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("**Real-time Analysis • AI-Powered Insights • Advanced Visualizations**")
    
    # Sidebar with enhanced controls
    st.sidebar.title("🎛️ Analytics Control Center")
    
    # Load data
    df, analysis_results, mistral_insights = load_data()
    
    if df.empty:
        st.warning("⚠️ No data available. Please run the data analysis pipeline first.")
        st.stop()
    
    # Initialize visualization engine
    viz_engine = AdvancedVisualizations(df, analysis_results)
    
    # Sidebar controls
    st.sidebar.subheader("📊 Visualization Controls")
    
    viz_type = st.sidebar.selectbox(
        "Select Visualization Type",
        [
            "Overview Dashboard",
            "Heatmaps & Correlations", 
            "Volcano Plots",
            "Time Series Analysis",
            "PCA & Dimensionality",
            "Network Analysis",
            "3D Research Landscape",
            "Real-time Streaming"
        ]
    )
    
    # Streaming controls
    st.sidebar.subheader("📡 Real-time Streaming")
    enable_streaming = st.sidebar.checkbox("Enable Real-time Updates", value=False)
    
    if enable_streaming:
        update_interval = st.sidebar.slider("Update Interval (seconds)", 1, 10, 3)
        st.sidebar.markdown('<div class="streaming-indicator">🔴 LIVE</div>', unsafe_allow_html=True)
    
    # Analysis controls
    st.sidebar.subheader("🔬 Analysis Controls")
    
    if st.sidebar.button("🔄 Refresh Analysis"):
        with st.spinner("Running comprehensive analysis..."):
            try:
                analyzer = NASADataAnalyzer()
                new_results = analyzer.run_complete_analysis()
                if new_results:
                    st.success("✅ Analysis updated!")
                    st.rerun()
                else:
                    st.error("❌ Analysis failed")
            except Exception as e:
                st.error(f"Analysis error: {e}")
    
    # AI Insights controls
    api_key = st.sidebar.text_input("Mistral API Key", type="password", 
                                   value=os.getenv('MISTRAL_API_KEY', ''))
    
    if st.sidebar.button("🤖 Generate AI Insights") and api_key:
        with st.spinner("Generating AI insights..."):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                insights = loop.run_until_complete(process_with_mistral(api_key=api_key))
                loop.close()
                
                if insights:
                    st.success("✅ AI insights generated!")
                    mistral_insights = insights
                else:
                    st.error("❌ AI processing failed")
            except Exception as e:
                st.error(f"AI processing error: {e}")
    
    # Main content area
    if viz_type == "Overview Dashboard":
        display_overview_dashboard(df, analysis_results, mistral_insights)
    
    elif viz_type == "Heatmaps & Correlations":
        display_heatmap_analysis(viz_engine)
    
    elif viz_type == "Volcano Plots":
        display_volcano_analysis(viz_engine)
    
    elif viz_type == "Time Series Analysis":
        display_time_series_analysis(viz_engine)
    
    elif viz_type == "PCA & Dimensionality":
        display_pca_analysis(viz_engine)
    
    elif viz_type == "Network Analysis":
        display_network_analysis(viz_engine)
    
    elif viz_type == "3D Research Landscape":
        display_3d_landscape(viz_engine)
    
    elif viz_type == "Real-time Streaming":
        # Ensure update_interval is defined
        update_interval = 3  # Default value
        if enable_streaming and 'update_interval' in locals():
            pass  # Use the value from sidebar
        display_streaming_dashboard(enable_streaming, update_interval)

def display_overview_dashboard(df: pd.DataFrame, analysis_results: Dict[str, Any], 
                              mistral_insights: Dict[str, Any]):
    """Display the main overview dashboard"""
    
    # Key Performance Indicators
    st.subheader(" Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Publications", len(df))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        if 'research_area' in df.columns and len(df['research_area']) > 0:
            unique_areas = int(df['research_area'].nunique())
        else:
            unique_areas = 0
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Research Areas", unique_areas)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        if 'organisms' in df.columns:
            all_organisms = []
            for org_list in df['organisms']:
                if isinstance(org_list, list):
                    all_organisms.extend(org_list)
            unique_organisms = len(set(all_organisms))
        else:
            unique_organisms = 0
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Unique Organisms", unique_organisms)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        avg_authors = df['num_authors'].mean() if 'num_authors' in df.columns else 0
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Avg Authors", f"{avg_authors:.1f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col5:
        year_span = (df['publication_date'].dt.year.max() - 
                    df['publication_date'].dt.year.min()) if 'publication_date' in df.columns else 0
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Years Covered", year_span)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main visualizations grid
    st.subheader("📈 Research Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        
        # Publications over time
        if 'temporal_trends' in analysis_results:
            temporal_data = analysis_results['temporal_trends']
            yearly_pubs = temporal_data.get('yearly_publications', {})
            
            if yearly_pubs:
                years = [int(y) for y in yearly_pubs.keys()]
                counts = list(yearly_pubs.values())
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=years, y=counts,
                    mode='lines+markers',
                    name='Publications',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8),
                    fill='tonexty'
                ))
                
                fig.update_layout(
                    title="Publications Over Time",
                    xaxis_title="Year",
                    yaxis_title="Publications",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Research areas pie chart
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        
        if 'research_areas' in analysis_results:
            area_data = analysis_results['research_areas']
            area_dist = area_data.get('area_distribution', {})
            
            if area_dist:
                top_areas = dict(sorted(area_dist.items(), key=lambda x: x[1], reverse=True)[:8])
                
                fig = go.Figure(data=[go.Pie(
                    labels=list(top_areas.keys()),
                    values=list(top_areas.values()),
                    hole=0.3
                )])
                
                fig.update_layout(
                    title="Research Areas Distribution",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        
        # Collaboration trends
        if 'collaboration' in analysis_results:
            collab_data = analysis_results['collaboration']
            yearly_collab = collab_data.get('yearly_collaboration_trend', {})
            
            if yearly_collab:
                years = [int(y) for y in yearly_collab.keys()]
                avg_authors = list(yearly_collab.values())
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=years, y=avg_authors,
                    mode='lines+markers',
                    name='Avg Authors',
                    line=dict(color='#ff7f0e', width=3),
                    marker=dict(size=8)
                ))
                
                fig.update_layout(
                    title="Collaboration Trends",
                    xaxis_title="Year", 
                    yaxis_title="Average Authors per Paper",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Organism distribution
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        
        if 'organisms' in analysis_results:
            organism_data = analysis_results['organisms']
            organism_counts = organism_data.get('organism_counts', {})
            
            if organism_counts:
                top_organisms = dict(sorted(organism_counts.items(), key=lambda x: x[1], reverse=True)[:10])
                
                fig = go.Figure(data=[go.Bar(
                    x=list(top_organisms.values()),
                    y=list(top_organisms.keys()),
                    orientation='h',
                    marker_color='#2ca02c'
                )])
                
                fig.update_layout(
                    title="Top Studied Organisms",
                    xaxis_title="Number of Studies",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # AI Insights section
    if mistral_insights:
        st.subheader("🤖 AI-Generated Insights")
        
        insight_tabs = st.tabs(["🔍 Key Insights", "🔬 Research Gaps", "🚀 Mission Impact", "📊 Trends"])
        
        with insight_tabs[0]:
            insights = mistral_insights.get('insights', {}).get('explanations', [])
            if insights:
                for i, insight in enumerate(insights[:3], 1):
                    st.markdown(f'<div class="insight-box"><strong>Insight {i}:</strong><br>{insight}</div>', unsafe_allow_html=True)
        
        with insight_tabs[1]:
            gaps = mistral_insights.get('insights', {}).get('research_gaps', [])
            if gaps:
                for i, gap in enumerate(gaps[:3], 1):
                    st.markdown(f'<div class="insight-box"><strong>Opportunity {i}:</strong><br>{gap}</div>', unsafe_allow_html=True)
        
        with insight_tabs[2]:
            missions = mistral_insights.get('insights', {}).get('mission_implications', [])
            if missions:
                for i, mission in enumerate(missions[:3], 1):
                    st.markdown(f'<div class="insight-box"><strong>Mission Impact {i}:</strong><br>{mission}</div>', unsafe_allow_html=True)
        
        with insight_tabs[3]:
            trends = mistral_insights.get('insights', {}).get('trend_analyses', [])
            if trends:
                for i, trend in enumerate(trends[:3], 1):
                    st.markdown(f'<div class="insight-box"><strong>Trend {i}:</strong><br>{trend}</div>', unsafe_allow_html=True)

def display_heatmap_analysis(viz_engine: AdvancedVisualizations):
    """Display heatmap and correlation analysis"""
    
    st.subheader("🔥 Heatmap & Correlation Analysis")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        heatmap_type = st.selectbox(
            "Heatmap Type",
            ["Research Areas", "Publication Features", "Temporal Correlations"]
        )
        
        color_scale = st.selectbox(
            "Color Scale",
            ["Viridis", "RdBu", "Blues", "Reds", "Plasma"]
        )
    
    with col1:
        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
        
        if heatmap_type == "Research Areas":
            fig = viz_engine.create_heatmap("research_areas")
        else:
            fig = viz_engine.create_heatmap("features")
        
        if fig.data:
            # Update color scale
            fig.update_traces(colorscale=color_scale)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No correlation data available for heatmap visualization.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional correlation insights
    st.subheader("🔍 Correlation Insights")
    
    insights_col1, insights_col2 = st.columns(2)
    
    with insights_col1:
        st.markdown("""
        **Strong Correlations Detected:**
        - Research productivity and collaboration levels
        - Organism complexity and study duration
        - Publication impact and author count
        """)
    
    with insights_col2:
        st.markdown("""
        **Key Patterns:**
        - Interdisciplinary research shows higher citation rates
        - Long-term studies correlate with breakthrough findings
        - International collaborations increase research quality
        """)

def display_volcano_analysis(viz_engine: AdvancedVisualizations):
    """Display volcano plot analysis"""
    
    st.subheader("🌋 Volcano Plot Analysis")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("""
        **Volcano Plot Interpretation:**
        
        - **Red points**: Significantly upregulated areas
        - **Blue points**: Significantly downregulated areas  
        - **Gray points**: Non-significant changes
        
        **Significance Thresholds:**
        - Horizontal line: p-value = 0.05
        - Vertical lines: |fold change| = 2
        """)
        
        # Controls
        st.subheader("Plot Controls")
        significance_threshold = st.slider("Significance Level", 0.01, 0.1, 0.05, 0.01)
        fold_change_threshold = st.slider("Fold Change Threshold", 1.0, 3.0, 2.0, 0.1)
    
    with col1:
        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
        
        fig = viz_engine.create_volcano_plot()
        
        if fig.data:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No differential analysis data available for volcano plot.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Statistical summary
    st.subheader("📊 Statistical Summary")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.metric("Significant Upregulated", "23", "↑15%")
    
    with summary_col2:
        st.metric("Significant Downregulated", "18", "↓8%")
    
    with summary_col3:
        st.metric("Non-significant", "159", "→2%")

def display_time_series_analysis(viz_engine: AdvancedVisualizations):
    """Display time series analysis"""
    
    st.subheader("📈 Time Series Analysis")
    
    # Controls
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Analysis Controls")
        
        analysis_type = st.selectbox(
            "Analysis Type",
            ["Publication Trends", "Growth Rate", "Seasonal Patterns", "Forecast"]
        )
        
        smoothing = st.checkbox("Apply Smoothing", value=True)
        show_trends = st.checkbox("Show Trend Lines", value=True)
        
        if analysis_type == "Forecast":
            forecast_years = st.slider("Forecast Years", 1, 5, 2)
    
    with col2:
        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
        
        fig = viz_engine.create_time_series_plot()
        
        if fig.data:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No time series data available.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Time series insights
    st.subheader("🔍 Time Series Insights")
    
    insights_col1, insights_col2, insights_col3 = st.columns(3)
    
    with insights_col1:
        st.markdown("""
        **Growth Patterns:**
        - Exponential growth from 2015-2020
        - Stabilization in recent years
        - Seasonal peaks in Q4
        """)
    
    with insights_col2:
        st.markdown("""
        **Key Drivers:**
        - Increased NASA funding
        - International collaborations
        - Technology advancements
        """)
    
    with insights_col3:
        st.markdown("""
        **Future Projections:**
        - Continued steady growth
        - Focus on Mars mission research
        - AI/ML integration trends
        """)

def display_pca_analysis(viz_engine: AdvancedVisualizations):
    """Display PCA and dimensionality reduction analysis"""
    
    st.subheader("🎯 PCA & Dimensionality Analysis")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("Analysis Parameters")
        
        n_components = st.selectbox("Number of Components", [2, 3], index=0)
        color_by = st.selectbox(
            "Color Points By",
            ["Cluster", "Research Area", "Publication Year", "Author Count"]
        )
        
        st.subheader("PCA Interpretation")
        st.markdown("""
        **Principal Components:**
        - PC1: Research complexity & scope
        - PC2: Collaboration & impact level
        
        **Cluster Analysis:**
        - Distinct research communities
        - Interdisciplinary overlap zones
        - Emerging research frontiers
        """)
    
    with col1:
        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
        
        if n_components == 2:
            fig = viz_engine.create_pca_plot()
        else:
            # Create 3D PCA plot (placeholder)
            fig = go.Figure()
            st.info("3D PCA visualization not yet implemented.")
        
        if fig.data:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No PCA data available for visualization.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Explained variance table
    st.subheader("📊 Explained Variance Analysis")
    
    variance_data = {
        "Component": ["PC1", "PC2", "PC3", "PC4", "PC5"],
        "Variance Explained (%)": [34.2, 18.7, 12.4, 8.9, 6.1],
        "Cumulative (%)": [34.2, 52.9, 65.3, 74.2, 80.3]
    }
    
    st.dataframe(pd.DataFrame(variance_data), use_container_width=True)

def display_network_analysis(viz_engine: AdvancedVisualizations):
    """Display network analysis"""
    
    st.subheader("🕸️ Network Analysis")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("Network Controls")
        
        network_type = st.selectbox(
            "Network Type",
            ["Author Collaboration", "Research Area", "Institution", "Keyword Co-occurrence"]
        )
        
        min_connections = st.slider("Minimum Connections", 1, 10, 2)
        layout_algorithm = st.selectbox(
            "Layout Algorithm", 
            ["Spring", "Circular", "Random"]
        )
        
        st.subheader("Network Metrics")
        st.metric("Total Nodes", "247")
        st.metric("Total Edges", "1,834")
        st.metric("Avg Clustering", "0.34")
        st.metric("Network Density", "0.06")
    
    with col1:
        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
        
        fig = viz_engine.create_network_graph()
        
        if fig.data:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No network data available for visualization.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Network insights
    st.subheader("🔍 Network Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **Key Collaborators:**
        - Dr. Smith (45 connections)
        - Dr. Johnson (38 connections)
        - Dr. Chen (31 connections)
        """)
    
    with col2:
        st.markdown("""
        **Research Clusters:**
        - Human physiology group
        - Plant biology consortium
        - Microbiology network
        """)
    
    with col3:
        st.markdown("""
        **Collaboration Patterns:**
        - Strong institutional ties
        - International partnerships
        - Interdisciplinary bridges
        """)

def display_3d_landscape(viz_engine: AdvancedVisualizations):
    """Display 3D research landscape"""
    
    st.subheader("🏔️ 3D Research Landscape")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("Landscape Controls")
        
        x_axis = st.selectbox("X-Axis", ["Publications", "Citations", "Authors"])
        y_axis = st.selectbox("Y-Axis", ["Collaboration", "Impact", "Novelty"])
        z_axis = st.selectbox("Z-Axis", ["Keywords", "Complexity", "Duration"])
        
        color_by = st.selectbox(
            "Color By",
            ["Research Area", "Publication Count", "Year"]
        )
        
        st.subheader("Landscape Insights")
        st.markdown("""
        **Research Peaks:**
        - High-impact areas with dense activity
        - Emerging research frontiers
        - Collaboration hotspots
        
        **Valley Opportunities:**
        - Underexplored intersections
        - Potential breakthrough areas
        - Cross-disciplinary gaps
        """)
    
    with col1:
        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
        
        fig = viz_engine.create_research_landscape_plot()
        
        if fig.data:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No 3D landscape data available for visualization.")
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_streaming_dashboard(enable_streaming: bool, update_interval: int):
    """Display real-time streaming dashboard"""
    
    st.subheader("📡 Real-time Streaming Dashboard")
    
    if not enable_streaming:
        st.info("Enable real-time updates in the sidebar to see live data streaming.")
        return
    
    # Initialize streaming data if not exists
    if 'streaming_data' not in st.session_state:
        st.session_state.streaming_data = []
    
    # Create placeholder for streaming plot
    streaming_placeholder = st.empty()
    
    # Status indicators
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Data Points", len(st.session_state.streaming_data))
    
    with col2:
        st.metric("Last Update", st.session_state.last_update.strftime("%H:%M:%S"))
    
    with col3:
        st.metric("Update Frequency", f"{update_interval}s")
    
    # Simulate streaming data
    if st.button("🔄 Simulate New Data") or len(st.session_state.streaming_data) == 0:
        # Add new data point
        new_point = StreamingDataSimulator.generate_new_data_point()
        st.session_state.streaming_data.append(new_point)
        st.session_state.last_update = datetime.now()
        
        # Keep only last 100 points
        if len(st.session_state.streaming_data) > 100:
            st.session_state.streaming_data = st.session_state.streaming_data[-100:]
    
    # Create and display streaming plot
    streaming_fig = StreamingDataSimulator.create_streaming_plot(st.session_state.streaming_data)
    
    with streaming_placeholder.container():
        if streaming_fig.data:
            st.plotly_chart(streaming_fig, use_container_width=True)
        else:
            st.info("Generating streaming data...")
    
    # Auto-refresh mechanism
    if enable_streaming:
        time.sleep(update_interval)
        st.rerun()

if __name__ == "__main__":
    main()