"""
Dixon-Coles Model for Football Score Prediction

The Dixon-Coles model is an improvement on the basic Poisson model that accounts for
the observed under-inflation of low-scoring matches (0-0, 1-0, 0-1, 1-1) in football.

Formula: P(X=x, Y=y) = Poisson(x; λ₁) * Poisson(y; λ₂) * τ(x,y)

Where:
- λ₁, λ₂ = expected goals for home and away teams
- τ(x,y) = Dixon-Coles adjustment factor for dependence
- ρ (rho) = dependence parameter (typically -0.1 to -0.2)

The adjustment τ(x,y) is:
- 1 for most scores
- Reduced for low-score draws (0-0, 1-1)
- Adjusted for low-score wins (1-0, 0-1)
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson
import warnings
warnings.filterwarnings('ignore')

# Import hybrid formula parameters from advanced_features
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from features.advanced_features import (
    COMPETITION_WEIGHT_RATIO,
    RECENCY_WEIGHT_RATIO,
    COMPETITION_WEIGHTS,
    MAX_TOTAL_WEIGHT,
    calculate_age_penalty
)


class DixonColesModel:
    """
    Dixon-Coles model for predicting football match scores.
    
    Features:
    - Home advantage factor
    - Team-specific attack/defense strengths  
    - Dixon-Coles dependence parameter (rho)
    - Recency weighting
    - Competition weighting
    """
    
    def __init__(self, rho=-0.13, max_iter=250):
        """
        Args:
            rho: Dependence parameter (default -0.13, typical range -0.1 to -0.2)
                 Negative = low scores more likely than independent Poisson
            max_iter: L-BFGS-B max iterations (default 250; full-history fits use subsampling).
        """
        self.rho = rho
        self.max_iter = max_iter
        self.teams = []
        self.team_attack = {}
        self.team_defense = {}
        self.home_advantage = 1.0
        self.avg_goals_home = 1.5
        self.avg_goals_away = 1.1
        self.fitted = False
        
    def _tau(self, x, y, rho=None):
        """
        Dixon-Coles adjustment function for dependence.
        
        With negative rho (typical for football, around -0.13):
        - Increases probability of draws (0-0, 1-1)
        - Decreases probability of narrow wins (1-0, 0-1)
        
        Args:
            x: Home goals
            y: Away goals  
            rho: Dependence parameter (typically negative, e.g., -0.13)
            
        Returns:
            Adjustment factor
        """
        if rho is None:
            rho = self.rho
            
        # Note: With negative rho, we want to INCREASE draw probability
        # So we subtract rho (making it > 1) for draws
        # And add rho (making it < 1) for narrow wins
        if x == 0 and y == 0:
            return 1 - rho  # Draw: increases prob when rho < 0
        elif x == 0 and y == 1:
            return 1 + rho  # Narrow win: decreases prob when rho < 0
        elif x == 1 and y == 0:
            return 1 + rho  # Narrow win: decreases prob when rho < 0
        elif x == 1 and y == 1:
            return 1 - rho  # Draw: increases prob when rho < 0
        else:
            return 1.0
    
    def _dc_log_likelihood(
        self,
        params,
        hi: np.ndarray,
        ai: np.ndarray,
        gh: np.ndarray,
        ga: np.ndarray,
        weights: np.ndarray,
    ):
        """
        Vectorized Dixon–Coles log-likelihood (returns NEGATIVE total for minimize).
        """
        n_teams = len(self.teams)

        attack_params = params[:n_teams]
        defense_params = params[n_teams : 2 * n_teams]
        home_adv = params[2 * n_teams]
        rho = np.clip(params[2 * n_teams + 1], -0.3, 0.0)

        lambda_h = np.exp(attack_params[hi] + defense_params[ai] + home_adv)
        lambda_a = np.exp(attack_params[ai] + defense_params[hi])

        ll = poisson.logpmf(gh, lambda_h) + poisson.logpmf(ga, lambda_a)

        tau = np.ones(len(gh), dtype=np.float64)
        m00 = (gh == 0) & (ga == 0)
        m01 = (gh == 0) & (ga == 1)
        m10 = (gh == 1) & (ga == 0)
        m11 = (gh == 1) & (ga == 1)
        tau[m00] = 1.0 - rho
        tau[m01] = 1.0 + rho
        tau[m10] = 1.0 + rho
        tau[m11] = 1.0 - rho
        ll += np.log(np.maximum(tau, 1e-10))

        return -float(np.sum(weights * ll))

    def fit(self, matches_df, recency_weights=None, competition_weights=None):
        """
        Fit the Dixon-Coles model to historical match data.
        
        Args:
            matches_df: DataFrame with columns [home_team, away_team, home_score, away_score]
            recency_weights: Optional weights for recency
            competition_weights: Optional weights for competition importance
        """
        print("Fitting Dixon-Coles model...")
        self.fitted = False

        # Get unique teams
        home_teams = matches_df['home_team'].unique()
        away_teams = matches_df['away_team'].unique()
        self.teams = sorted(list(set(home_teams) | set(away_teams)))
        n_teams = len(self.teams)
        
        print(f"  Teams: {n_teams}")
        print(f"  Matches: {len(matches_df)}")
        
        # Combine weights
        weights = None
        if recency_weights is not None and competition_weights is not None:
            weights = recency_weights * competition_weights
        elif recency_weights is not None:
            weights = recency_weights
        elif competition_weights is not None:
            weights = competition_weights

        w_arr = (
            np.asarray(weights, dtype=np.float64)
            if weights is not None
            else np.ones(len(matches_df), dtype=np.float64)
        )

        team_to_idx = {t: i for i, t in enumerate(self.teams)}
        hi = matches_df["home_team"].map(team_to_idx).astype(np.int32).to_numpy()
        ai = matches_df["away_team"].map(team_to_idx).astype(np.int32).to_numpy()
        gh = matches_df["home_score"].to_numpy(dtype=np.int32, copy=False)
        ga = matches_df["away_score"].to_numpy(dtype=np.int32, copy=False)

        # Initialize parameters
        # attack + defense params (one each per team) + home_adv + rho
        initial_params = np.zeros(2 * n_teams + 2)
        initial_params[:n_teams] = 0.1  # Attack parameters (log scale)
        initial_params[n_teams:2*n_teams] = 0.0  # Defense parameters
        initial_params[2*n_teams] = 0.2  # Home advantage
        initial_params[2*n_teams + 1] = -0.13  # Rho
        
        # Optimize (vectorized likelihood: budget scales with row count)
        n_rows = len(matches_df)
        ftol = 1e-5 if n_rows > 25_000 else 1e-6
        maxfun = max(self.max_iter * 100, 12_000) if n_rows > 25_000 else max(self.max_iter * 50, 5_000)
        print("  Optimizing parameters...")
        result = minimize(
            self._dc_log_likelihood,
            initial_params,
            args=(hi, ai, gh, ga, w_arr),
            method='L-BFGS-B',
            options={
                'maxiter': self.max_iter,
                'maxfun': maxfun,
                'ftol': ftol,
            },
        )

        ok_x = (
            result.x is not None
            and len(result.x) == len(initial_params)
            and np.all(np.isfinite(result.x))
        )
        if result.success:
            print("  Optimization successful!")
        elif ok_x:
            print(f"  Optimization stopped early - using best iterate ({result.message})")

        if result.success or ok_x:
            
            # Extract fitted parameters
            self.team_attack = {team: result.x[i] for i, team in enumerate(self.teams)}
            self.team_defense = {team: result.x[n_teams + i] for i, team in enumerate(self.teams)}
            self.home_advantage = result.x[2 * n_teams]
            self.rho = np.clip(result.x[2 * n_teams + 1], -0.3, 0.0)
            
            # Calculate average goals
            exp_attacks = [np.exp(a) for a in self.team_attack.values()]
            exp_defenses = [np.exp(d) for d in self.team_defense.values()]
            self.avg_goals_home = np.mean(exp_attacks) * np.mean(exp_defenses) * np.exp(self.home_advantage)
            self.avg_goals_away = np.mean(exp_attacks) * np.mean(exp_defenses)
            
            self.fitted = True
            
            print(f"  Home advantage: {self.home_advantage:.3f}")
            print(f"  Rho (dependence): {self.rho:.3f}")
            print(f"  Avg home goals: {self.avg_goals_home:.2f}")
            print(f"  Avg away goals: {self.avg_goals_away:.2f}")
        else:
            print(f"  Optimization failed: {result.message}")

        return self.fitted
    
    def predict_score_probabilities(self, home_team, away_team, max_goals=10):
        """
        Predict full score probability matrix for a match.
        
        Returns:
            2D array where [i,j] = probability of score i-j
        """
        if not self.fitted:
            raise ValueError("Model must be fitted before prediction")
            
        if home_team not in self.teams or away_team not in self.teams:
            # Use average for unknown teams
            lambda_h = self.avg_goals_home
            lambda_a = self.avg_goals_away
        else:
            lambda_h = np.exp(self.team_attack[home_team] + 
                            self.team_defense[away_team] + 
                            self.home_advantage)
            lambda_a = np.exp(self.team_attack[away_team] + 
                            self.team_defense[home_team])
        
        # Calculate probability matrix
        probs = np.zeros((max_goals + 1, max_goals + 1))
        
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                p_h = poisson.pmf(i, lambda_h)
                p_a = poisson.pmf(j, lambda_a)
                tau = self._tau(i, j)
                probs[i, j] = p_h * p_a * tau
        
        # Normalize
        probs = probs / probs.sum()
        
        return probs, lambda_h, lambda_a
    
    def predict_score(self, home_team, away_team, method='expected'):
        """
        Predict most likely score.
        
        Args:
            method: 'expected' (round expected goals) or 'max_prob' (most likely exact score)
        """
        probs, lambda_h, lambda_a = self.predict_score_probabilities(home_team, away_team)
        
        if method == 'expected':
            # Calculate expected goals from probability matrix
            expected_h = sum(i * probs[i, :].sum() for i in range(probs.shape[0]))
            expected_a = sum(j * probs[:, j].sum() for j in range(probs.shape[1]))
            
            pred_h = int(round(expected_h))
            pred_a = int(round(expected_a))
            
        elif method == 'max_prob':
            # Find most likely exact score
            max_idx = np.unravel_index(np.argmax(probs), probs.shape)
            pred_h, pred_a = max_idx
            
        elif method == 'random_sample':
            # Sample from distribution
            flat_probs = probs.flatten()
            idx = np.random.choice(len(flat_probs), p=flat_probs)
            max_idx = np.unravel_index(idx, probs.shape)
            pred_h, pred_a = max_idx
        
        # Calculate outcome probabilities
        home_win_prob = np.tril(probs, -1).sum()
        draw_prob = np.diag(probs).sum()
        away_win_prob = np.triu(probs, 1).sum()
        
        return {
            'predicted_home': pred_h,
            'predicted_away': pred_a,
            'expected_home': lambda_h,
            'expected_away': lambda_a,
            'prob_home_win': home_win_prob,
            'prob_draw': draw_prob,
            'prob_away_win': away_win_prob,
            'rho': self.rho
        }
    
    def simulate_knockout(self, home_team, away_team):
        """Simulate knockout match with ET and penalties if needed."""
        result = self.predict_score(home_team, away_team, method='random_sample')
        
        h90 = result['predicted_home']
        a90 = result['predicted_away']
        
        et_home = et_away = 0
        went_to_et = went_to_pens = False
        penalties_home = penalties_away = None
        
        # If draw after 90 min
        if h90 == a90:
            went_to_et = True
            
            # Extra time - reduce expected goals by 30%
            probs, lambda_h, lambda_a = self.predict_score_probabilities(home_team, away_team)
            lambda_h_et = lambda_h * 0.3
            lambda_a_et = lambda_a * 0.3
            
            et_home = np.random.poisson(lambda_h_et)
            et_away = np.random.poisson(lambda_a_et)
        
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
            
            # Penalty shootout - slight advantage to better team
            if home_team in self.team_attack and away_team in self.team_attack:
                elo_h = np.exp(self.team_attack[home_team])
                elo_a = np.exp(self.team_attack[away_team])
                p_home_wins = 0.5 + (elo_h - elo_a) / 1000
                p_home_wins = np.clip(p_home_wins, 0.35, 0.65)
            else:
                p_home_wins = 0.5
                
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
            'rho': result['rho']
        }


# Training wrapper
def train_dixon_coles_from_historical(matches_df, recency_years=4):
    """
    Train Dixon-Coles model from historical match data.
    
    Args:
        matches_df: DataFrame with historical matches
        recency_years: How many recent years to weight more heavily
    """
    from datetime import datetime
    
    # Calculate recency weights
    current_year = 2026
    matches_df['year'] = pd.to_datetime(matches_df['date']).dt.year
    matches_df['recency_weight'] = matches_df['year'].apply(
        lambda y: 2.0 if y >= current_year - recency_years else 1.0
    )
    
    # Competition weights (WC > EURO > etc.)
    # Use competition weights from advanced_features
    matches_df['comp_weight'] = matches_df['tournament'].map(COMPETITION_WEIGHTS).fillna(1.5)
    
    # Hybrid formula: balance competition importance vs recency
    matches_df['weight'] = (matches_df['comp_weight'] * COMPETITION_WEIGHT_RATIO) + (matches_df['recency_weight'] * RECENCY_WEIGHT_RATIO)
    
    # Apply age penalty to allow weights below competition floor
    matches_df['age_penalty'] = matches_df['date'].apply(lambda d: calculate_age_penalty(pd.to_datetime(d)))
    matches_df['weight'] = matches_df['weight'] * matches_df['age_penalty']
    
    # Fit model
    model = DixonColesModel(rho=-0.13)
    model.fit(matches_df, weights=matches_df['weight'].values)
    
    return model


if __name__ == '__main__':
    # Test with simple example
    print("=" * 60)
    print("DIXON-COLES MODEL TEST")
    print("=" * 60)
    
    # Create dummy data
    test_data = pd.DataFrame([
        {'home_team': 'Spain', 'away_team': 'Germany', 'home_score': 2, 'away_score': 1, 'date': '2022-11-23', 'tournament': 'FIFA World Cup'},
        {'home_team': 'Spain', 'away_team': 'Costa Rica', 'home_score': 7, 'away_score': 0, 'date': '2022-11-23', 'tournament': 'FIFA World Cup'},
        {'home_team': 'Germany', 'away_team': 'Spain', 'home_score': 1, 'away_score': 1, 'date': '2022-11-27', 'tournament': 'FIFA World Cup'},
        {'home_team': 'Germany', 'away_team': 'Costa Rica', 'home_score': 4, 'away_score': 2, 'date': '2022-12-01', 'tournament': 'FIFA World Cup'},
        {'home_team': 'Spain', 'away_team': 'Morocco', 'home_score': 0, 'away_score': 0, 'date': '2022-12-06', 'tournament': 'FIFA World Cup'},
        {'home_team': 'Brazil', 'away_team': 'Serbia', 'home_score': 2, 'away_score': 0, 'date': '2022-11-24', 'tournament': 'FIFA World Cup'},
        {'home_team': 'Brazil', 'away_team': 'Switzerland', 'home_score': 1, 'away_score': 0, 'date': '2022-11-28', 'tournament': 'FIFA World Cup'},
        {'home_team': 'Brazil', 'away_team': 'Korea Republic', 'home_score': 4, 'away_score': 1, 'date': '2022-12-05', 'tournament': 'FIFA World Cup'},
        {'home_team': 'Argentina', 'away_team': 'Saudi Arabia', 'home_score': 1, 'away_score': 2, 'date': '2022-11-22', 'tournament': 'FIFA World Cup'},
        {'home_team': 'Argentina', 'away_team': 'Mexico', 'home_score': 2, 'away_score': 0, 'date': '2022-11-26', 'tournament': 'FIFA World Cup'},
        {'home_team': 'Argentina', 'away_team': 'Australia', 'home_score': 2, 'away_score': 1, 'date': '2022-12-03', 'tournament': 'FIFA World Cup'},
        {'home_team': 'Argentina', 'away_team': 'Netherlands', 'home_score': 2, 'away_score': 2, 'date': '2022-12-09', 'tournament': 'FIFA World Cup'},
        {'home_team': 'Argentina', 'away_team': 'Croatia', 'home_score': 3, 'away_score': 0, 'date': '2022-12-13', 'tournament': 'FIFA World Cup'},
        {'home_team': 'Argentina', 'away_team': 'France', 'home_score': 3, 'away_score': 3, 'date': '2022-12-18', 'tournament': 'FIFA World Cup'},
    ])
    
    # Fit model
    model = DixonColesModel(rho=-0.13)
    
    # Add dummy recency weights
    test_data['year'] = pd.to_datetime(test_data['date']).dt.year
    test_data['weight'] = test_data['year'].apply(lambda y: 2.0 if y >= 2022 else 1.0)
    
    success = model.fit(test_data, weights=test_data['weight'].values)
    
    if success:
        print("\n" + "=" * 60)
        print("PREDICTIONS")
        print("=" * 60)
        
        # Test predictions
        test_matches = [
            ('Spain', 'Argentina'),
            ('Brazil', 'Germany'),
            ('Spain', 'Brazil'),
        ]
        
        for home, away in test_matches:
            result = model.predict_score(home, away)
            print(f"\n{home} vs {away}:")
            print(f"  Predicted: {result['predicted_home']}-{result['predicted_away']}")
            print(f"  Expected: {result['expected_home']:.2f}-{result['expected_away']:.2f}")
            print(f"  Probs: H {result['prob_home_win']:.1%} | D {result['prob_draw']:.1%} | A {result['prob_away_win']:.1%}")
            print(f"  Rho: {result['rho']:.3f}")
