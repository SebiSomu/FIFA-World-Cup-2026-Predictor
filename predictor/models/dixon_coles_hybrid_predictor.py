"""
Hybrid Dixon-Coles Predictor for FIFA World Cup 2026

Combines:
1. Dixon-Coles base model for score prediction
2. ELO ratings for current team strength  
3. Historical H2H data
4. Recency weighting
5. Competition importance weighting

This gives more realistic score predictions, especially for draws.
"""

import sys
sys.path.append(str(__file__).rsplit('/', 2)[0])

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from scipy.stats import poisson
import pickle

from features.advanced_features import (
    AdvancedFeatureExtractor,
    COMPETITION_WEIGHTS,
    RECENCY_WEIGHT_BASE,
    RECENCY_WEIGHT_RECENT,
    RECENCY_WINDOW_YEARS,
)
from models.dixon_coles_predictor import DixonColesModel


class DixonColesHybridPredictor:
    """
    Hybrid predictor combining Dixon-Coles with ELO and historical data.
    """

    # All-time training from results.csv; optional cap for experiments (None = no cap).
    FIT_MIN_YEAR = 1872
    FIT_MAX_MATCHES: Optional[int] = None

    def __init__(self):
        # Vectorized likelihood supports full history; L-BFGS-B budget tuned for ~50k rows.
        self.dc_model = DixonColesModel(rho=-0.13, max_iter=220)
        self.extractor = AdvancedFeatureExtractor()
        self.elo_ratings = {}
        self.fitted = False
        self._load_elo()
        
    def _load_elo(self):
        """Load ELO ratings."""
        # Try multiple paths to find the file
        possible_paths = [
            Path('predictor/data/elo_ratings_wc2026_correct.csv'),  # From repo root
            Path('../data/elo_ratings_wc2026_correct.csv'),  # From predictor/ folder
            Path(__file__).resolve().parent.parent / 'data' / 'elo_ratings_wc2026_correct.csv',  # Absolute
        ]
        
        for elo_file in possible_paths:
            if elo_file.exists():
                elo_df = pd.read_csv(elo_file, comment='#')
                self.elo_ratings = dict(zip(elo_df['team'], elo_df['elo_rating']))
                print(f"Loaded {len(self.elo_ratings)} ELO ratings from {elo_file}")
                return
        
        print("WARNING: Could not find ELO ratings file!")
    
    def fit(self, matches_df: pd.DataFrame = None):
        """
        Fit the Dixon-Coles model on historical data.
        
        Args:
            matches_df: Historical matches. If None, loads from default location.
        """
        if matches_df is None:
            # Try multiple paths for results.csv
            possible_paths = [
                Path('predictor/data/results.csv'),
                Path('../data/results.csv'),
                Path(__file__).resolve().parent.parent / 'data' / 'results.csv',
            ]
            
            results_path = None
            for p in possible_paths:
                if p.exists():
                    results_path = p
                    break
            
            if results_path is None:
                print("No historical data found, using default parameters")
                self.fitted = True
                return False
                
            matches_df = pd.read_csv(results_path)
            matches_df['date'] = pd.to_datetime(matches_df['date'])
            matches_df = matches_df[matches_df['date'].dt.year >= self.FIT_MIN_YEAR]

        if "date" in matches_df.columns:
            matches_df = matches_df.copy()
            matches_df["date"] = pd.to_datetime(matches_df["date"])
            matches_df = matches_df[matches_df["date"].dt.year >= self.FIT_MIN_YEAR]

        for col in ("home_score", "away_score"):
            matches_df[col] = pd.to_numeric(matches_df[col], errors="coerce")
        matches_df = matches_df.dropna(subset=["home_score", "away_score"]).copy()
        matches_df["home_score"] = matches_df["home_score"].astype(int)
        matches_df["away_score"] = matches_df["away_score"].astype(int)

        n_before_cap = len(matches_df)
        cap = self.FIT_MAX_MATCHES
        if cap is not None and n_before_cap > cap:
            matches_df = (
                matches_df.sort_values("date")
                .tail(cap)
                .reset_index(drop=True)
            )
            print(
                f"  (Subsample: most recent {cap} of {n_before_cap} matches, "
                f"year >= {self.FIT_MIN_YEAR})"
            )

        print(f"Fitting Dixon-Coles on {len(matches_df)} matches...")
        
        current_year = 2026
        y = matches_df["date"].dt.year
        matches_df["recency_weight"] = np.where(
            y >= current_year - RECENCY_WINDOW_YEARS,
            RECENCY_WEIGHT_RECENT,
            RECENCY_WEIGHT_BASE,
        )

        if "tournament" in matches_df.columns:
            tcol = matches_df["tournament"].fillna("Friendly")
        else:
            tcol = pd.Series("Friendly", index=matches_df.index)
        matches_df["comp_weight"] = tcol.map(
            lambda x: COMPETITION_WEIGHTS.get(str(x), 1.5)
        )
        
        # Combined weights
        matches_df['weight'] = matches_df['recency_weight'] * matches_df['comp_weight']
        
        # Fit Dixon-Coles
        success = self.dc_model.fit(
            matches_df, recency_weights=matches_df["weight"].values
        )
        self.fitted = success
        
        return success
    
    def predict_match(self, home_team: str, away_team: str, neutral: bool = True) -> Dict:
        """
        Predict match score using hybrid approach.
        
        1. Get base prediction from Dixon-Coles
        2. Adjust based on ELO difference
        3. Incorporate H2H history if available
        """
        # Get ELO ratings
        elo_h = self.elo_ratings.get(home_team, 1800)
        elo_a = self.elo_ratings.get(away_team, 1800)
        elo_diff = elo_h - elo_a
        
        # Get base DC prediction
        if self.fitted and home_team in self.dc_model.teams and away_team in self.dc_model.teams:
            dc_result = self.dc_model.predict_score(home_team, away_team, method='expected')
            base_home = dc_result['expected_home']
            base_away = dc_result['expected_away']
        else:
            # Use statistical fallback
            h_stats = self.extractor.get_team_all_time_stats(home_team)
            a_stats = self.extractor.get_team_all_time_stats(away_team)
            
            base_home = h_stats['avg_goals_scored'] if not np.isnan(h_stats['avg_goals_scored']) else 1.3
            base_away = a_stats['avg_goals_scored'] if not np.isnan(a_stats['avg_goals_scored']) else 1.1
        
        # Adjust based on ELO
        elo_factor = elo_diff / 400  # Standard ELO scaling
        if not neutral:
            elo_factor += 0.1  # Home advantage
            
        adjusted_home = base_home * (1 + elo_factor * 0.15)
        adjusted_away = base_away * (1 - elo_factor * 0.15)
        
        # Get H2H adjustment
        h2h = self.extractor.get_h2h_stats(home_team, away_team)
        if h2h['matches'] >= 3:
            # Weight H2H history
            h2h_home_avg = h2h.get('team1_avg_goals', base_home)
            h2h_weight = min(h2h['matches'] / 10, 0.3)  # Max 30% weight
            
            adjusted_home = (1 - h2h_weight) * adjusted_home + h2h_weight * h2h_home_avg
        
        # Ensure minimum expected goals
        adjusted_home = max(0.3, adjusted_home)
        adjusted_away = max(0.3, adjusted_away)
        
        # Calculate score probability matrix with Dixon-Coles adjustment
        # This properly accounts for dependence in low-scoring matches
        max_goals = 10
        prob_matrix = np.zeros((max_goals + 1, max_goals + 1))
        
        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                # Base Poisson probabilities
                p_h = poisson.pmf(h, adjusted_home)
                p_a = poisson.pmf(a, adjusted_away)
                # Dixon-Coles tau adjustment
                tau = self.dc_model._tau(h, a)
                prob_matrix[h, a] = p_h * p_a * tau
        
        # Normalize to get proper probability distribution
        prob_matrix = prob_matrix / prob_matrix.sum()
        
        # Calculate outcome probabilities
        prob_home = np.sum(np.tril(prob_matrix, -1))
        prob_draw = np.sum(np.diag(prob_matrix))
        prob_away = np.sum(np.triu(prob_matrix, 1))
        
        # Sample predicted score from probability matrix
        flat_probs = prob_matrix.flatten()
        flat_idx = np.random.choice(len(flat_probs), p=flat_probs)
        pred_home, pred_away = np.unravel_index(flat_idx, prob_matrix.shape)
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'predicted_home': max(0, pred_home),
            'predicted_away': max(0, pred_away),
            'expected_home': adjusted_home,
            'expected_away': adjusted_away,
            'prob_home_win': prob_home,
            'prob_draw': prob_draw,
            'prob_away_win': prob_away,
            'elo_home': elo_h,
            'elo_away': elo_a,
            'elo_diff': elo_diff,
            'h2h_matches': h2h.get('matches', 0),
            'rho': self.dc_model.rho if self.fitted else -0.13
        }
    
    def simulate_knockout(self, home_team: str, away_team: str, neutral: bool = True) -> Dict:
        """
        Simulate knockout match with ET and penalties if needed.
        """
        result = self.predict_match(home_team, away_team, neutral)
        
        h90 = result['predicted_home']
        a90 = result['predicted_away']
        
        et_home = et_away = 0
        went_to_et = went_to_pens = False
        penalties_home = penalties_away = None
        
        # If draw after 90 min
        if h90 == a90:
            went_to_et = True
            
            # Extra time - reduce expected goals
            lambda_h = result['expected_home'] * 0.25
            lambda_a = result['expected_away'] * 0.25
            
            et_home = np.random.poisson(max(0.2, lambda_h))
            et_away = np.random.poisson(max(0.2, lambda_a))
        
        total_h = h90 + et_home
        total_a = a90 + et_away
        
        # Determine winner
        if total_h > total_a:
            winner = home_team
        elif total_a > total_h:
            winner = away_team
        else:
            # Penalties
            went_to_pens = True
            
            # Slight advantage to higher ELO team
            elo_diff = result['elo_diff']
            p_home_wins = 0.5 + (elo_diff / 4000)
            p_home_wins = np.clip(p_home_wins, 0.35, 0.65)
            
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
            'elo_home': result['elo_home'],
            'elo_away': result['elo_away'],
            'rho': result['rho']
        }
    
    def save(self, filepath: str):
        """Save fitted model."""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'dc_model': self.dc_model,
                'fitted': self.fitted,
                'elo_ratings': self.elo_ratings
            }, f)
    
    def load(self, filepath: str):
        """Load fitted model."""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.dc_model = data['dc_model']
            self.fitted = data['fitted']
            self.elo_ratings = data.get('elo_ratings', {})


if __name__ == '__main__':
    print("=" * 60)
    print("DIXON-COLES HYBRID PREDICTOR TEST")
    print("=" * 60)
    
    predictor = DixonColesHybridPredictor()
    
    # Try to fit on historical data
    results_path = Path('predictor/data/results.csv')
    if results_path.exists():
        print("\nFitting on historical data...")
        matches_df = pd.read_csv(results_path)
        matches_df['date'] = pd.to_datetime(matches_df['date'])
        matches_df = matches_df[matches_df['date'].dt.year >= 2010]  # Last 16 years
        predictor.fit(matches_df)
    
    print("\n" + "=" * 60)
    print("TEST PREDICTIONS")
    print("=" * 60)
    
    test_matches = [
        ('Spain', 'Argentina'),
        ('Brazil', 'France'),
        ('England', 'Germany'),
        ('Netherlands', 'Japan'),
        ('Portugal', 'Colombia'),
    ]
    
    for home, away in test_matches:
        result = predictor.predict_match(home, away)
        print(f"\n{home} vs {away}:")
        print(f"  Score: {result['predicted_home']}-{result['predicted_away']}")
        print(f"  xG: {result['expected_home']:.2f}-{result['expected_away']:.2f}")
        print(f"  Probs: H {result['prob_home_win']:.1%} | D {result['prob_draw']:.1%} | A {result['prob_away_win']:.1%}")
        print(f"  ELO: {result['elo_home']:.0f} vs {result['elo_away']:.0f}")
        print(f"  Rho: {result['rho']:.3f}")
        
        # Show if it's a draw
        if result['predicted_home'] == result['predicted_away']:
            print(f"  *** EGAL ***")
