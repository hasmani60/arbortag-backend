import pandas as pd
import numpy as np
from typing import Dict, List
from collections import Counter

class TreeAnalyzer:
    def __init__(self, trees: List[Dict]):
        self.df = pd.DataFrame(trees)
        
    def get_statistics(self) -> Dict:
        """Calculate comprehensive statistics"""
        stats = {
            'total_trees': len(self.df),
            'total_carbon': self.df['carbon_seq'].sum(),
            'total_oxygen': self.df['oxygen_prod'].sum() if 'oxygen_prod' in self.df else 0,
            'avg_height': self.df['height'].mean(),
            'avg_width': self.df['width'].mean(),
            'total_locations': self.df['location'].nunique(),
            'total_species': self.df['species_id'].nunique(),
            'most_common_species': self.df['common_name'].mode()[0] if len(self.df) > 0 else 'N/A',
        }
        
        # Most carbon efficient species
        species_carbon = self.df.groupby('common_name')['carbon_seq'].mean()
        stats['most_carbon_efficient'] = species_carbon.idxmax() if len(species_carbon) > 0 else 'N/A'
        
        return stats
    
    def get_species_distribution(self) -> Dict:
        """Get species distribution data"""
        distribution = self.df['common_name'].value_counts().to_dict()
        return distribution
    
    def get_carbon_by_species(self) -> Dict:
        """Get carbon sequestration by species"""
        carbon = self.df.groupby('common_name')['carbon_seq'].sum().to_dict()
        return carbon
    
    def get_height_distribution(self) -> Dict:
        """Get height distribution"""
        height_ranges = pd.cut(self.df['height'], bins=[0, 5, 10, 15, 20, 200])
        distribution = height_ranges.value_counts().to_dict()
        return {str(k): v for k, v in distribution.items()}
    
    def get_location_stats(self) -> Dict:
        """Get statistics by location"""
        location_stats = {}
        for location in self.df['location'].unique():
            loc_data = self.df[self.df['location'] == location]
            location_stats[location] = {
                'tree_count': len(loc_data),
                'total_carbon': loc_data['carbon_seq'].sum(),
                'avg_height': loc_data['height'].mean(),
                'species_count': loc_data['species_id'].nunique(),
            }
        return location_stats
    
    def get_temporal_analysis(self) -> Dict:
        """Analyze data over time"""
        self.df['date'] = pd.to_datetime(self.df['date'])
        temporal = self.df.groupby(self.df['date'].dt.to_period('M')).agg({
            'carbon_seq': 'sum',
            'id': 'count'
        }).to_dict()
        return temporal