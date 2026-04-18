"""
Data loader module for FIFA World Cup 2026 Predictor.
Handles loading and basic inspection of all data sources.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional

class DataLoader:
    """Load and provide access to all FIFA match data sources."""
    
    def __init__(self, data_dir: str = None):
        """
        Initialize DataLoader with path to data directory.
        
        Args:
            data_dir: Path to data directory. If None, uses default relative path.
        """
        if data_dir is None:
            # Default path relative to this file
            current_file = Path(__file__).resolve()
            self.data_dir = current_file.parent.parent / 'data'
        else:
            self.data_dir = Path(data_dir)
        
        self._results: Optional[pd.DataFrame] = None
        self._goalscorers: Optional[pd.DataFrame] = None
        self._shootouts: Optional[pd.DataFrame] = None
        self._former_names: Optional[pd.DataFrame] = None
        self._wc2026_groups: Optional[pd.DataFrame] = None
    
    def load_all(self) -> Dict[str, pd.DataFrame]:
        """Load all data files and return as dictionary."""
        return {
            'results': self.load_results(),
            'goalscorers': self.load_goalscorers(),
            'shootouts': self.load_shootouts(),
            'former_names': self.load_former_names(),
            'wc2026_groups': self.load_wc2026_groups()
        }
    
    def load_results(self) -> pd.DataFrame:
        """Load match results data."""
        if self._results is None:
            filepath = self.data_dir / 'results.csv'
            self._results = pd.read_csv(filepath)
            self._results['date'] = pd.to_datetime(self._results['date'])
        return self._results
    
    def load_goalscorers(self) -> pd.DataFrame:
        """Load goalscorers data."""
        if self._goalscorers is None:
            filepath = self.data_dir / 'goalscorers.csv'
            self._goalscorers = pd.read_csv(filepath)
            self._goalscorers['date'] = pd.to_datetime(self._goalscorers['date'])
        return self._goalscorers
    
    def load_shootouts(self) -> pd.DataFrame:
        """Load penalty shootout data."""
        if self._shootouts is None:
            filepath = self.data_dir / 'shootouts.csv'
            self._shootouts = pd.read_csv(filepath)
            self._shootouts['date'] = pd.to_datetime(self._shootouts['date'])
        return self._shootouts
    
    def load_former_names(self) -> pd.DataFrame:
        """Load team name mappings (former to current)."""
        if self._former_names is None:
            filepath = self.data_dir / 'former_names.csv'
            self._former_names = pd.read_csv(filepath)
            self._former_names['start_date'] = pd.to_datetime(self._former_names['start_date'])
            self._former_names['end_date'] = pd.to_datetime(self._former_names['end_date'])
        return self._former_names
    
    def load_wc2026_groups(self) -> pd.DataFrame:
        """Load World Cup 2026 groups data."""
        if self._wc2026_groups is None:
            filepath = self.data_dir / 'wc2026_groups.csv'
            self._wc2026_groups = pd.read_csv(filepath)
        return self._wc2026_groups
    
    def get_data_summary(self) -> Dict:
        """Get summary statistics for all loaded data."""
        results = self.load_results()
        goalscorers = self.load_goalscorers()
        shootouts = self.load_shootouts()
        former_names = self.load_former_names()
        wc2026 = self.load_wc2026_groups()
        
        return {
            'results': {
                'total_matches': len(results),
                'date_range': (results['date'].min(), results['date'].max()),
                'unique_teams': len(set(results['home_team']) | set(results['away_team'])),
                'tournaments': results['tournament'].nunique()
            },
            'goalscorers': {
                'total_goals': len(goalscorers),
                'date_range': (goalscorers['date'].min(), goalscorers['date'].max())
            },
            'shootouts': {
                'total_shootouts': len(shootouts)
            },
            'former_names': {
                'total_mappings': len(former_names),
                'unique_current_names': former_names['current'].nunique()
            },
            'wc2026_groups': {
                'total_teams': len(wc2026),
                'groups': wc2026['groups'].nunique() if 'groups' in wc2026.columns else None
            }
        }
    
    def print_summary(self):
        """Print formatted summary of all data."""
        summary = self.get_data_summary()
        
        print("=" * 60)
        print("FIFA DATA SUMMARY")
        print("=" * 60)
        
        print(f"\n[RESULTS] MATCH RESULTS:")
        print(f"   Total matches: {summary['results']['total_matches']:,}")
        print(f"   Date range: {summary['results']['date_range'][0].date()} to {summary['results']['date_range'][1].date()}")
        print(f"   Unique teams: {summary['results']['unique_teams']}")
        print(f"   Tournaments: {summary['results']['tournaments']}")
        
        print(f"\n[GOALS] GOALSCORERS:")
        print(f"   Total goals recorded: {summary['goalscorers']['total_goals']:,}")
        print(f"   Date range: {summary['goalscorers']['date_range'][0].date()} to {summary['goalscorers']['date_range'][1].date()}")
        
        print(f"\n[SHOOTOUTS] PENALTY SHOOTOUTS:")
        print(f"   Total shootouts: {summary['shootouts']['total_shootouts']}")
        
        print(f"\n[MAPPINGS] TEAM NAME MAPPINGS:")
        print(f"   Total mappings: {summary['former_names']['total_mappings']}")
        print(f"   Unique current names: {summary['former_names']['unique_current_names']}")
        
        print(f"\n[WORLD CUP] WORLD CUP 2026:")
        print(f"   Teams qualified: {summary['wc2026_groups']['total_teams']}")
        if summary['wc2026_groups']['groups']:
            print(f"   Groups: {summary['wc2026_groups']['groups']}")
        
        print("=" * 60)


if __name__ == '__main__':
    # Test the data loader
    loader = DataLoader()
    loader.print_summary()
