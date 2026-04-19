"""
Historical-based predictor for FIFA World Cup 2026.
Uses actual FIFA match history as primary factor, with ELO as adjustment.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, List
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))


class HistoricalPredictor:
    """
    Predicts match outcomes based on:
    1. Historical head-to-head results (primary)
    2. ELO ratings for current strength adjustment (secondary)
    """
    
    def __init__(self):
        self.matches_df = None
        self.elo_ratings = {}
        self._load_data()
    
    def _load_data(self):
        """Load historical matches and ELO ratings."""
        # Load historical matches
        results_path = Path('predictor/data/raw/results.csv')
        if results_path.exists():
            self.matches_df = pd.read_csv(results_path)
            self.matches_df['date'] = pd.to_datetime(self.matches_df['date'])
            # Keep only matches from 1990 onwards for relevance
            self.matches_df = self.matches_df[self.matches_df['date'].dt.year >= 1990]
            print(f"Loaded {len(self.matches_df)} historical matches (1990+)")
        
        # Load external ELO ratings (real values from eloratings.net)
        elo_path = Path('predictor/data/elo_ratings_wc2026_correct.csv')
        if elo_path.exists():
            elo_df = pd.read_csv(elo_path, comment='#')
            self.elo_ratings = dict(zip(elo_df['team'], elo_df['elo_rating']))
            print(f"Loaded {len(self.elo_ratings)} ELO ratings (real values)")
    
    def get_historical_matches(self, team1: str, team2: str) -> pd.DataFrame:
        """Get all historical matches between two teams."""
        if self.matches_df is None:
            return pd.DataFrame()
        
        # Find matches where team1 is home and team2 is away, or vice versa
        mask1 = (self.matches_df['home_team'] == team1) & (self.matches_df['away_team'] == team2)
        mask2 = (self.matches_df['home_team'] == team2) & (self.matches_df['away_team'] == team1)
        
        matches = self.matches_df[mask1 | mask2].copy()
        
        # Standardize perspective: team1 is always "home" in our view
        def standardize_row(row):
            if row['home_team'] == team2:
                # Swap
                return pd.Series({
                    'date': row['date'],
                    'tournament': row['tournament'],
                    'team1_goals': row['away_score'],
                    'team2_goals': row['home_score'],
                    'neutral': row['neutral']
                })
            else:
                return pd.Series({
                    'date': row['date'],
                    'tournament': row['tournament'],
                    'team1_goals': row['home_score'],
                    'team2_goals': row['away_score'],
                    'neutral': row['neutral']
                })
        
        if len(matches) > 0:
            matches[['date', 'tournament', 'team1_goals', 'team2_goals', 'neutral']] = matches.apply(standardize_row, axis=1)
        
        return matches
    
    def calculate_historical_stats(self, team1: str, team2: str) -> Dict:
        """Calculate historical statistics between two teams."""
        matches = self.get_historical_matches(team1, team2)
        
        if len(matches) == 0:
            return {
                'matches_played': 0,
                'team1_wins': 0,
                'draws': 0,
                'team2_wins': 0,
                'team1_avg_goals': 0,
                'team2_avg_goals': 0,
                'recent_form_team1': 0.5,  # Neutral if no history
                'recent_form_team2': 0.5
            }
        
        # Calculate basic stats
        team1_goals = matches['team1_goals'].sum()
        team2_goals = matches['team2_goals'].sum()
        
        team1_wins = (matches['team1_goals'] > matches['team2_goals']).sum()
        draws = (matches['team1_goals'] == matches['team2_goals']).sum()
        team2_wins = (matches['team1_goals'] < matches['team2_goals']).sum()
        
        # Recent form (last 5 matches, weighted by recency)
        recent_matches = matches.tail(5)
        if len(recent_matches) > 0:
            weights = np.linspace(0.5, 1.0, len(recent_matches))  # More recent = higher weight
            recent_results_t1 = []
            recent_results_t2 = []
            
            for _, row in recent_matches.iterrows():
                if row['team1_goals'] > row['team2_goals']:
                    recent_results_t1.append(1.0)
                    recent_results_t2.append(0.0)
                elif row['team1_goals'] < row['team2_goals']:
                    recent_results_t1.append(0.0)
                    recent_results_t2.append(1.0)
                else:
                    recent_results_t1.append(0.5)
                    recent_results_t2.append(0.5)
            
            recent_form_t1 = np.average(recent_results_t1, weights=weights)
            recent_form_t2 = np.average(recent_results_t2, weights=weights)
        else:
            recent_form_t1 = 0.5
            recent_form_t2 = 0.5
        
        return {
            'matches_played': len(matches),
            'team1_wins': team1_wins,
            'draws': draws,
            'team2_wins': team2_wins,
            'team1_avg_goals': team1_goals / len(matches),
            'team2_avg_goals': team2_goals / len(matches),
            'recent_form_team1': recent_form_t1,
            'recent_form_team2': recent_form_t2
        }
    
    def predict_match(
        self,
        home_team: str,
        away_team: str,
        neutral: bool = True
    ) -> Dict:
        """
        Predict match outcome based on historical results + ELO.
        
        Formula:
        1. Get historical stats between teams
        2. Get ELO ratings
        3. Combine: Predicted_score = Historical_avg + ELO_adjustment
        """
        # Get historical stats
        hist = self.calculate_historical_stats(home_team, away_team)
        
        # Get ELO ratings
        elo_home = self.elo_ratings.get(home_team, 1500)
        elo_away = self.elo_ratings.get(away_team, 1500)
        elo_diff = elo_home - elo_away
        
        # Calculate base prediction from history
        if hist['matches_played'] >= 3:
            # Use historical averages as base
            base_home = hist['team1_avg_goals']
            base_away = hist['team2_avg_goals']
            
            # Adjust by recent form
            form_factor_home = (hist['recent_form_team1'] - 0.5) * 0.5
            form_factor_away = (hist['recent_form_team2'] - 0.5) * 0.5
            
            base_home += form_factor_home
            base_away += form_factor_away
            
        elif hist['matches_played'] > 0:
            # Some history, but not much - blend with ELO-based estimate
            hist_weight = hist['matches_played'] / 3.0  # 0.33 to 1.0
            
            historical_base_home = hist['team1_avg_goals'] if hist['team1_avg_goals'] > 0 else 1.0
            historical_base_away = hist['team2_avg_goals'] if hist['team2_avg_goals'] > 0 else 1.0
            
            # ELO-based estimate: each 100 ELO points = ~0.3 goals advantage
            elo_based_home = 1.5 + (elo_diff / 100) * 0.3
            elo_based_away = 1.5 - (elo_diff / 100) * 0.3
            
            base_home = hist_weight * historical_base_home + (1 - hist_weight) * elo_based_home
            base_away = hist_weight * historical_base_away + (1 - hist_weight) * elo_based_away
        else:
            # No history - use ELO-based prediction
            # Each 100 ELO points = ~0.3 goals advantage
            base_home = 1.5 + (elo_diff / 100) * 0.3
            base_away = 1.5 - (elo_diff / 100) * 0.3
        
        # Final ELO adjustment (even when we have history, ELO helps for current strength)
        elo_adjustment = (elo_diff / 100) * 0.15  # Smaller adjustment if we have history
        
        raw_home = max(0.1, base_home + elo_adjustment)
        raw_away = max(0.1, base_away - elo_adjustment)
        
        # Round to get predicted scores
        pred_home = int(round(raw_home))
        pred_away = int(round(raw_away))
        
        # Calculate probabilities using Poisson
        n_sim = 1000
        sim_h = np.random.poisson(raw_home, n_sim)
        sim_a = np.random.poisson(raw_away, n_sim)
        
        prob_home = float((sim_h > sim_a).mean())
        prob_draw = float((sim_h == sim_a).mean())
        prob_away = float((sim_h < sim_a).mean())
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'historical_matches': hist['matches_played'],
            'elo_home': elo_home,
            'elo_away': elo_away,
            'elo_diff': elo_diff,
            'raw_home': raw_home,
            'raw_away': raw_away,
            'predicted_home': pred_home,
            'predicted_away': pred_away,
            'prob_home_win': prob_home,
            'prob_draw': prob_draw,
            'prob_away_win': prob_away,
            'method': 'historical' if hist['matches_played'] >= 3 else ('blend' if hist['matches_played'] > 0 else 'elo_only')
        }
    
    def simulate_knockout(
        self,
        home_team: str,
        away_team: str,
        neutral: bool = True
    ) -> Dict:
        """Simulate a knockout match with extra time and penalties if needed."""
        result = self.predict_match(home_team, away_team, neutral)
        
        h90 = result['predicted_home']
        a90 = result['predicted_away']
        
        et_home = et_away = 0
        went_to_et = went_to_pens = False
        penalties_home = penalties_away = None
        
        # If draw after 90 min, go to extra time
        if h90 == a90:
            went_to_et = True
            # Extra time: use ~25% of 90min rate
            et_raw_h = max(0, result['raw_home'] * 0.25)
            et_raw_a = max(0, result['raw_away'] * 0.25)
            et_home = int(np.random.poisson(et_raw_h))
            et_away = int(np.random.poisson(et_raw_a))
        
        total_h = h90 + et_home
        total_a = a90 + et_away
        
        # If still draw, go to penalties
        winner = home_team if total_h > total_a else away_team if total_a > total_h else None
        
        if total_h == total_a:
            went_to_pens = True
            # Penalty shootout: slight randomness, but favor team with higher ELO slightly
            elo_diff = result['elo_diff']
            p_home_wins = 0.5 + (elo_diff / 4000)  # Small ELO advantage
            p_home_wins = max(0.35, min(0.65, p_home_wins))  # Cap between 35-65%
            
            if np.random.random() < p_home_wins:
                penalties_home, penalties_away = 1, 0
                winner = home_team
            else:
                penalties_home, penalties_away = 0, 1
                winner = away_team
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'score_90': (h90, a90),
            'score_et': (et_home, et_away) if went_to_et else None,
            'penalties': (penalties_home, penalties_away) if went_to_pens else None,
            'final_score': (total_h, total_a),
            'winner': winner,
            'prob_home_win': result['prob_home_win'],
            'prob_draw': result['prob_draw'],
            'prob_away_win': result['prob_away_win'],
            'method': result['method']
        }


if __name__ == '__main__':
    # Test
    pred = HistoricalPredictor()
    
    print("=== Test Predictions ===\n")
    
    # Test with history (Brazil vs Argentina)
    result = pred.predict_match('Brazil', 'Argentina')
    print(f"Brazil vs Argentina:")
    print(f"  Historical matches: {result['historical_matches']}")
    print(f"  ELO diff: {result['elo_diff']:.0f}")
    print(f"  Predicted: {result['predicted_home']}-{result['predicted_away']}")
    print(f"  Method: {result['method']}")
    print()
    
    # Test with less history (Mexico vs random)
    result = pred.predict_match('Mexico', 'Iraq')
    print(f"Mexico vs Iraq:")
    print(f"  Historical matches: {result['historical_matches']}")
    print(f"  ELO diff: {result['elo_diff']:.0f}")
    print(f"  Predicted: {result['predicted_home']}-{result['predicted_away']}")
    print(f"  Method: {result['method']}")
