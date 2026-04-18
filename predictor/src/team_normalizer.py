"""
Team name normalizer for FIFA World Cup 2026 Predictor.
Standardizes historical team names to current names using former_names.csv mapping.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Set, Optional, List
from datetime import datetime


class TeamNormalizer:
    """
    Normalizes team names from historical data to current standard names.
    Uses former_names.csv to map old team names to current ones.
    """
    
    def __init__(self, former_names_df: Optional[pd.DataFrame] = None):
        """
        Initialize TeamNormalizer.
        
        Args:
            former_names_df: DataFrame with former names mapping. If None, will be loaded.
        """
        if former_names_df is None:
            from .data_loader import DataLoader
            loader = DataLoader()
            former_names_df = loader.load_former_names()
        
        self.former_names = former_names_df
        self._build_mapping()
    
    def _build_mapping(self):
        """Build mapping dictionary from former names to current names."""
        self.name_mapping: Dict[str, str] = {}
        
        # Group timed mappings: {former_name: [(start, end, current), ...]}
        self.timed_mappings: Dict[str, List[Tuple[pd.Timestamp, pd.Timestamp, str]]] = {}
        
        for _, row in self.former_names.iterrows():
            former = row['former']
            current = row['current']
            
            # If no dates, add to static mapping
            if pd.isna(row['start_date']) or pd.isna(row['end_date']):
                self.name_mapping[former] = current
            else:
                if former not in self.timed_mappings:
                    self.timed_mappings[former] = []
                self.timed_mappings[former].append((row['start_date'], row['end_date'], current))
        
        # Add common manual mappings for edge cases
        self._add_manual_mappings()
        
        # Add reverse mappings (WC2026 name -> historical name)
        self._add_reverse_mappings()
    
    def _add_manual_mappings(self):
        """Add manual mappings for common variations not in former_names.csv."""
        manual_mappings = {
            # Common abbreviations and variations
            'USA': 'United States',
            'Korea Republic': 'South Korea',
            'Korea DPR': 'North Korea',
            'Trinidad and Tobago': 'Trinidad & Tobago',
            'Czechia': 'Czech Republic',
            'Türkiye': 'Turkey',
            'DR Congo': 'DR Congo',  # Keep as is
        }
        
        # Only add if not already mapped
        for old, new in manual_mappings.items():
            if old not in self.name_mapping:
                self.name_mapping[old] = new
    
    def _add_reverse_mappings(self):
        """Add reverse mappings for WC2026 team names to historical names."""
        reverse_mappings = {
            'Cabo Verde': 'Cape Verde',      # WC2026 name -> historical name
            'Congo DR': 'DR Congo',          # WC2026 name -> historical name
            "Côte d'Ivoire": 'Ivory Coast',  # WC2026 name -> historical name
        }
        
        for wc_name, hist_name in reverse_mappings.items():
            self.name_mapping[wc_name] = hist_name
    
    def normalize(self, team_name: str, match_date: Optional[pd.Timestamp] = None) -> str:
        """
        Normalize a team name to its current standard name.
        """
        if pd.isna(team_name):
            return team_name
        
        team_name = str(team_name).strip()
        
        # Check timed mappings first if date is provided
        if match_date is not None and team_name in self.timed_mappings:
            for start, end, current in self.timed_mappings[team_name]:
                if start <= match_date <= end:
                    return current
        
        # Check direct mapping
        if team_name in self.name_mapping:
            return self.name_mapping[team_name]
        
        # Return original if no mapping found
        return team_name
    
    def normalize_dataframe(self, df: pd.DataFrame, home_col: str = 'home_team', 
                           away_col: str = 'away_team', date_col: str = 'date') -> pd.DataFrame:
        """
        Normalize team names in a DataFrame.
        
        Args:
            df: DataFrame with team names
            home_col: Column name for home team
            away_col: Column name for away team
            date_col: Column name for match date
            
        Returns:
            DataFrame with normalized team names
        """
        df = df.copy()
        
        # Apply normalization
        if date_col in df.columns:
            df[home_col] = df.apply(
                lambda row: self.normalize(row[home_col], row[date_col]), axis=1
            )
            df[away_col] = df.apply(
                lambda row: self.normalize(row[away_col], row[date_col]), axis=1
            )
        else:
            df[home_col] = df[home_col].apply(self.normalize)
            df[away_col] = df[away_col].apply(self.normalize)
        
        return df
    
    def get_all_unique_teams(self, results_df: pd.DataFrame) -> Set[str]:
        """Get all unique team names from results data (normalized)."""
        normalized_df = self.normalize_dataframe(results_df)
        home_teams = set(normalized_df['home_team'].unique())
        away_teams = set(normalized_df['away_team'].unique())
        return home_teams | away_teams
    
    def validate_wc2026_teams(self, wc2026_df: pd.DataFrame, 
                              all_teams: Set[str]) -> Dict:
        """
        Validate that all WC2026 teams exist in historical data.
        
        Args:
            wc2026_df: DataFrame with WC2026 teams
            all_teams: Set of all teams from historical data
            
        Returns:
            Dictionary with validation results
        """
        # Extract team names from wc2026 dataframe
        wc2026_teams = set()
        
        # Check different possible column names
        if 'team' in wc2026_df.columns:
            wc2026_teams = set(wc2026_df['team'].unique())
        elif 'First match against' in wc2026_df.columns:
            # Parse from match schedule format
            for col in ['First match against', 'Second match against', 'Third match against']:
                if col in wc2026_df.columns:
                    wc2026_teams.update(wc2026_df[col].dropna().unique())
            if 'team' in wc2026_df.columns:
                wc2026_teams.update(wc2026_df['team'].dropna().unique())
        
        # Normalize WC2026 team names
        normalized_wc2026_teams = {self.normalize(team) for team in wc2026_teams}
        
        # Find missing teams
        missing_teams = normalized_wc2026_teams - all_teams
        found_teams = normalized_wc2026_teams & all_teams
        
        return {
            'wc2026_teams': sorted(normalized_wc2026_teams),
            'found_teams': sorted(found_teams),
            'missing_teams': sorted(missing_teams),
            'total_qualified': len(normalized_wc2026_teams),
            'total_found': len(found_teams),
            'total_missing': len(missing_teams),
            'coverage_pct': len(found_teams) / len(normalized_wc2026_teams) * 100 if normalized_wc2026_teams else 0
        }
    
    def print_validation_report(self, validation_results: Dict):
        """Print formatted validation report."""
        print("\n" + "=" * 60)
        print("WORLD CUP 2026 TEAM VALIDATION REPORT")
        print("=" * 60)
        
        print(f"\n✅ TEAMS FOUND: {validation_results['total_found']}/{validation_results['total_qualified']} "
              f"({validation_results['coverage_pct']:.1f}%)")
        
        if validation_results['missing_teams']:
            print(f"\n❌ MISSING TEAMS ({validation_results['total_missing']}):")
            for team in validation_results['missing_teams']:
                print(f"   - {team}")
        else:
            print("\n✨ All teams found in historical data!")
        
        print("=" * 60)


if __name__ == '__main__':
    # Test the team normalizer
    try:
        from .data_loader import DataLoader
    except ImportError:
        from data_loader import DataLoader
    
    loader = DataLoader()
    results = loader.load_results()
    wc2026 = loader.load_wc2026_groups()
    
    normalizer = TeamNormalizer(loader.load_former_names())
    
    # Get all unique teams
    all_teams = normalizer.get_all_unique_teams(results)
    print(f"\nTotal unique teams in historical data: {len(all_teams)}")
    
    # Validate WC2026 teams
    validation = normalizer.validate_wc2026_teams(wc2026, all_teams)
    normalizer.print_validation_report(validation)
