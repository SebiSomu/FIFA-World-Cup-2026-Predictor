"""
Advanced ML-based predictor using pre-trained models with recency-weighted features.
Combines all-time stats, head-to-head, and ELO for predictions.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict
import pickle
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from features.advanced_features import AdvancedFeatureExtractor


class AdvancedMLPredictor:
    """
    ML-based predictor using:
    1. All-time team stats with recency weighting
    2. Head-to-head statistics
    3. ELO ratings
    """
    
    def __init__(self):
        self.home_model = None
        self.away_model = None
        self.stats_cache = None
        self.extractor = None
        self.elo_ratings = {}
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models and caches."""
        models_dir = Path('predictor/models/saved')
        
        # Load ML models
        try:
            with open(models_dir / 'advanced_home_model.pkl', 'rb') as f:
                self.home_model = pickle.load(f)
            with open(models_dir / 'advanced_away_model.pkl', 'rb') as f:
                self.away_model = pickle.load(f)
            print("Loaded ML models")
        except FileNotFoundError:
            print("ML models not found, falling back to statistical predictor")
        
        # Load team stats cache
        try:
            with open(models_dir / 'team_stats_cache.pkl', 'rb') as f:
                self.stats_cache = pickle.load(f)
            print(f"Loaded stats cache for {len(self.stats_cache)} teams")
        except FileNotFoundError:
            print("Stats cache not found, will compute on demand")
            self.extractor = AdvancedFeatureExtractor()
        
        # Load ELO ratings
        elo_file = Path('predictor/data/elo_ratings_wc2026_correct.csv')
        if elo_file.exists():
            elo_df = pd.read_csv(elo_file, comment='#')
            self.elo_ratings = dict(zip(elo_df['team'], elo_df['elo_rating']))
            print(f"Loaded {len(self.elo_ratings)} ELO ratings")
    
    def get_team_stats(self, team: str) -> Dict:
        """Get team stats from cache or compute on demand."""
        if self.stats_cache and team in self.stats_cache:
            return self.stats_cache[team]
        if self.extractor:
            return self.extractor.get_team_all_time_stats(team)
        return self._default_stats()
    
    def _default_stats(self) -> Dict:
        """Default stats for unknown teams."""
        return {
            'win_rate': 0.5, 'draw_rate': 0.25, 'loss_rate': 0.25,
            'avg_goals_scored': 1.0, 'avg_goals_conceded': 1.0,
            'clean_sheet_rate': 0.2, 'recent_form': 0.5, 'trend': 0.0,
        }
    
    def get_h2h_stats(self, team1: str, team2: str) -> Dict:
        """Get head-to-head stats."""
        if self.extractor:
            return self.extractor.get_h2h_stats(team1, team2)
        return {'matches': 0, 'team1_win_rate': 0.5, 'avg_goals': 1.0}
    
    def _build_features(self, home_team: str, away_team: str) -> np.ndarray:
        """Build feature vector for prediction."""
        # Get stats
        h_stats = self.get_team_stats(home_team)
        a_stats = self.get_team_stats(away_team)
        h2h = self.get_h2h_stats(home_team, away_team)
        
        # Get ELO
        elo_h = self.elo_ratings.get(home_team, 1800)
        elo_a = self.elo_ratings.get(away_team, 1800)
        
        # Build features
        features = [
            h_stats['win_rate'], h_stats['draw_rate'],
            h_stats.get('avg_goals_scored', 1.0) if not np.isnan(h_stats.get('avg_goals_scored', 1.0)) else 1.0,
            h_stats.get('avg_goals_conceded', 1.0) if not np.isnan(h_stats.get('avg_goals_conceded', 1.0)) else 1.0,
            h_stats.get('clean_sheet_rate', 0.2),
            h_stats.get('recent_form', 0.5),
            h_stats.get('trend', 0.0),
            a_stats['win_rate'], a_stats['draw_rate'],
            a_stats.get('avg_goals_scored', 1.0) if not np.isnan(a_stats.get('avg_goals_scored', 1.0)) else 1.0,
            a_stats.get('avg_goals_conceded', 1.0) if not np.isnan(a_stats.get('avg_goals_conceded', 1.0)) else 1.0,
            a_stats.get('clean_sheet_rate', 0.2),
            a_stats.get('recent_form', 0.5),
            a_stats.get('trend', 0.0),
            h2h['matches'] / 100.0,
            h2h['team1_win_rate'],
            h2h['avg_goals'] / 5.0,
            elo_h / 2500.0,
            elo_a / 2500.0,
            (elo_h - elo_a) / 500.0,
        ]
        
        return np.array(features).reshape(1, -1)
    
    def predict_match(self, home_team: str, away_team: str, neutral: bool = True) -> Dict:
        """
        Predict match outcome using ML models.
        """
        # Build features
        features = self._build_features(home_team, away_team)
        
        # Get raw predictions from ML
        if self.home_model and self.away_model:
            raw_home = self.home_model.predict(features)[0]
            raw_away = self.away_model.predict(features)[0]
        else:
            # Fallback to simple statistical method
            h_stats = self.get_team_stats(home_team)
            a_stats = self.get_team_stats(away_team)
            elo_h = self.elo_ratings.get(home_team, 1800)
            elo_a = self.elo_ratings.get(away_team, 1800)
            elo_diff = elo_h - elo_a
            
            raw_home = h_stats['avg_goals_scored'] + (elo_diff / 500) * 0.3
            raw_away = a_stats['avg_goals_scored'] - (elo_diff / 500) * 0.3
        
        # Ensure non-negative
        raw_home = max(0.3, raw_home)
        raw_away = max(0.3, raw_away)
        
        # Calculate probabilities with Poisson first (needed for draw decision)
        n_sim = 1000
        sim_h = np.random.poisson(raw_home, n_sim)
        sim_a = np.random.poisson(raw_away, n_sim)
        
        prob_home = float((sim_h > sim_a).mean())
        prob_draw = float((sim_h == sim_a).mean())
        prob_away = float((sim_h < sim_a).mean())
        
        # Round to integers for predicted score
        # IF probabilities are balanced (draw probability is highest or close), predict a draw
        pred_home = int(round(raw_home))
        pred_away = int(round(raw_away))
        
        # Force draw if:
        # 1. Draw probability is significant (>20%) AND match is close
        # 2. Raw goals are very close AND random chance (50%)
        # 3. Both teams have similar strength (ELO diff < 100) AND random chance
        is_close_match = abs(prob_home - prob_away) < 0.25  # Win probs are close
        has_significant_draw_prob = prob_draw > 0.20  # Draw prob is significant
        very_close_goals = abs(raw_home - raw_away) < 0.5
        similar_elo = abs(elo_home - elo_away) < 100
        
        # Combined conditions for draw
        draw_condition = (
            (has_significant_draw_prob and is_close_match) or  # Probabilistic draw
            (very_close_goals and np.random.random() < 0.50) or  # Close match draw
            (similar_elo and prob_draw > 0.18 and np.random.random() < 0.40)  # Similar teams draw
        )
        
        if draw_condition:
            # Make it a draw - set equal scores
            avg_goals = (pred_home + pred_away) / 2
            pred_home = pred_away = max(1, int(round(avg_goals)))
        
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'predicted_home': pred_home,
            'predicted_away': pred_away,
            'raw_home': raw_home,
            'raw_away': raw_away,
            'prob_home_win': prob_home,
            'prob_draw': prob_draw,
            'prob_away_win': prob_away,
        }
    
    def simulate_knockout(self, home_team: str, away_team: str, neutral: bool = True) -> Dict:
        """Simulate knockout match with ET and penalties if needed."""
        result = self.predict_match(home_team, away_team, neutral)
        
        h90 = result['predicted_home']
        a90 = result['predicted_away']
        
        et_home = et_away = 0
        went_to_et = went_to_pens = False
        penalties_home = penalties_away = None
        
        # If draw after 90 min, go to extra time
        if h90 == a90:
            went_to_et = True
            et_raw_h = max(0, result['raw_home'] * 0.25)
            et_raw_a = max(0, result['raw_away'] * 0.25)
            et_home = int(np.random.poisson(et_raw_h))
            et_away = int(np.random.poisson(et_raw_a))
        
        total_h = h90 + et_home
        total_a = a90 + et_away
        
        # Determine winner or go to penalties
        winner = home_team if total_h > total_a else away_team if total_a > total_h else None
        
        if total_h == total_a:
            went_to_pens = True
            elo_h = self.elo_ratings.get(home_team, 1800)
            elo_a = self.elo_ratings.get(away_team, 1800)
            elo_diff = elo_h - elo_a
            
            # Slight advantage to higher ELO team in penalties
            p_home_wins = 0.5 + (elo_diff / 4000)
            p_home_wins = max(0.35, min(0.65, p_home_wins))
            
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
        }


if __name__ == '__main__':
    # Test
    predictor = AdvancedMLPredictor()
    
    print("\n=== Test Predictions ===")
    
    # Test Brazil vs Argentina
    result = predictor.predict_match('Brazil', 'Argentina')
    print(f"\nBrazil vs Argentina:")
    print(f"  Predicted: {result['predicted_home']}-{result['predicted_away']}")
    print(f"  Probs: H {result['prob_home_win']:.2%} | D {result['prob_draw']:.2%} | A {result['prob_away_win']:.2%}")
    
    # Test Spain vs Mexico
    result = predictor.predict_match('Spain', 'Mexico')
    print(f"\nSpain vs Mexico:")
    print(f"  Predicted: {result['predicted_home']}-{result['predicted_away']}")
    print(f"  Probs: H {result['prob_home_win']:.2%} | D {result['prob_draw']:.2%} | A {result['prob_away_win']:.2%}")
