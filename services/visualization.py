import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
import base64

class TreeVisualizer:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        sns.set_style("whitegrid")
        
    def create_species_pie_chart(self) -> str:
        """Create species distribution pie chart"""
        distribution = self.analyzer.get_species_distribution()
        
        fig = go.Figure(data=[go.Pie(
            labels=list(distribution.keys()),
            values=list(distribution.values()),
            hole=0.3
        )])
        
        fig.update_layout(
            title="Species Distribution",
            font=dict(size=14)
        )
        
        return fig.to_html()
    
    def create_carbon_bar_chart(self) -> str:
        """Create carbon sequestration bar chart"""
        carbon_data = self.analyzer.get_carbon_by_species()
        
        # Sort by value
        sorted_data = dict(sorted(carbon_data.items(), key=lambda x: x[1], reverse=True)[:10])
        
        fig = go.Figure([go.Bar(
            x=list(sorted_data.keys()),
            y=list(sorted_data.values()),
            marker_color='#27ae60'
        )])
        
        fig.update_layout(
            title="Carbon Sequestration by Species (Top 10)",
            xaxis_title="Species",
            yaxis_title="Carbon Sequestration (kg CO₂/year)",
            font=dict(size=12)
        )
        
        return fig.to_html()
    
    def create_height_distribution(self) -> str:
        """Create height distribution histogram"""
        df = self.analyzer.df
        
        fig = px.histogram(
            df,
            x='height',
            nbins=20,
            title="Tree Height Distribution",
            labels={'height': 'Height (m)', 'count': 'Frequency'}
        )
        
        fig.update_traces(marker_color='#3498db')
        
        return fig.to_html()
    
    def create_location_comparison(self) -> str:
        """Create location comparison chart"""
        location_stats = self.analyzer.get_location_stats()
        
        locations = list(location_stats.keys())
        tree_counts = [stats['tree_count'] for stats in location_stats.values()]
        carbon_totals = [stats['total_carbon'] for stats in location_stats.values()]
        
        fig = go.Figure(data=[
            go.Bar(name='Tree Count', x=locations, y=tree_counts),
            go.Bar(name='Total Carbon (kg)', x=locations, y=carbon_totals)
        ])
        
        fig.update_layout(
            title="Comparison by Location",
            barmode='group',
            font=dict(size=12)
        )
        
        return fig.to_html()
    
    def create_heatmap(self) -> str:
        """Create geographical heatmap"""
        df = self.analyzer.df
        
        fig = px.density_mapbox(
            df,
            lat='latitude',
            lon='longitude',
            z='carbon_seq',
            radius=10,
            center=dict(lat=df['latitude'].mean(), lon=df['longitude'].mean()),
            zoom=12,
            mapbox_style="open-street-map",
            title="Carbon Sequestration Heatmap"
        )
        
        return fig.to_html()