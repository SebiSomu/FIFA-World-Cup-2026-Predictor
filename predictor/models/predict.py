"""
Prediction module for FIFA World Cup 2026 Predictor.
Loads trained models and exposes a clean predict_match() interface.
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Tuple, Dict
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.confederation_weights import calculate_confederation_adjusted_elo

MODELS_DIR = Path('predictor/models/saved')

NUMERIC_FEATURES = [
    'elo_home', 'elo_away', 'elo_diff', 
    'form_home', 'form_away',
    'h2h_matches', 'h2h_win_rate_home', 'h2h_win_rate_away'
]
CATEGORICAL_FEATURES = ['tournament_category']

TOURNAMENT_MAP = {
    'FIFA World Cup': 'world_cup',
    'UEFA Euro': 'major_continental',
    'Copa América': 'major_continental',
    'African Cup of Nations': 'major_continental',
    'AFC Asian Cup': 'major_continental',
    'Confederations Cup': 'major_continental',
    'CONCACAF Championship': 'major_continental',
    'Oceania Nations Cup': 'major_continental',
    'FIFA World Cup qualification': 'wc_qualification',
    'UEFA Euro qualification': 'euro_qualification',
    'Friendly': 'friendly',
}


def categorize_tournament(tournament: str) -> str:
    for key, val in TOURNAMENT_MAP.items():
        if key in tournament:
            return val
    return 'other_competitive'


class Predictor:
    """Loads models and provides match predictions."""

    def __init__(self, use_ensemble: bool = True):
        self.use_ensemble = use_ensemble
        self._load_models()
        # Head-to-head history during tournament
        self.h2h_history: Dict[Tuple[str, str], Dict] = {}

    def _load_models(self):
        self.gb_home = joblib.load(MODELS_DIR / 'gb_home.joblib')
        self.gb_away = joblib.load(MODELS_DIR / 'gb_away.joblib')
        if self.use_ensemble:
            self.rf_home = joblib.load(MODELS_DIR / 'rf_home.joblib')
            self.rf_away = joblib.load(MODELS_DIR / 'rf_away.joblib')

    def _get_h2h_key(self, team1: str, team2: str) -> Tuple[str, str]:
        """Get canonical key for head-to-head."""
        return (min(team1, team2), max(team1, team2))

    def _get_h2h_stats(self, team1: str, team2: str) -> Tuple[int, float]:
        """Get head-to-head matches and win rate for team1."""
        key = self._get_h2h_key(team1, team2)
        if key not in self.h2h_history:
            return 0, 0.5
        stats = self.h2h_history[key]
        total = stats['wins'] + stats['draws'] + stats['losses']
        if total == 0:
            return 0, 0.5
        # Calculate win rate from team1 perspective
        wins = stats['wins'] if key[0] == team1 else stats['losses']
        return total, wins / total

    def _update_h2h(self, team1: str, team2: str, t1_goals: int, t2_goals: int):
        """Update head-to-head history after a match."""
        key = self._get_h2h_key(team1, team2)
        if key not in self.h2h_history:
            self.h2h_history[key] = {'wins': 0, 'draws': 0, 'losses': 0}
        if t1_goals > t2_goals:
            if key[0] == team1:
                self.h2h_history[key]['wins'] += 1
            else:
                self.h2h_history[key]['losses'] += 1
        elif t1_goals < t2_goals:
            if key[0] == team1:
                self.h2h_history[key]['losses'] += 1
            else:
                self.h2h_history[key]['wins'] += 1
        else:
            self.h2h_history[key]['draws'] += 1

    def _build_row(
        self,
        home_team: str,
        away_team: str,
        elo_home: float,
        elo_away: float,
        form_home: float,
        form_away: float,
        tournament: str,
    ) -> pd.DataFrame:
        # Get head-to-head stats
        h2h_matches, h2h_win_home = self._get_h2h_stats(home_team, away_team)
        _, h2h_win_away = self._get_h2h_stats(away_team, home_team)
        
        return pd.DataFrame([{
            'elo_home': elo_home,
            'elo_away': elo_away,
            'elo_diff': elo_home - elo_away,
            'form_home': form_home,
            'form_away': form_away,
            'h2h_matches': h2h_matches,
            'h2h_win_rate_home': h2h_win_home,
            'h2h_win_rate_away': h2h_win_away,
            'tournament_category': categorize_tournament(tournament),
        }])

    def predict_match(
        self,
        home_team: str,
        away_team: str,
        elo_home: float,
        elo_away: float,
        form_home: float = 0.5,
        form_away: float = 0.5,
        tournament: str = 'FIFA World Cup',
        neutral: bool = True,
        home_advantage: float = 50.0,
        n_simulations: int = 1000,
        use_confederation_weights: bool = True,
    ) -> Dict:
        """
        Predict match outcome.

        Returns dict with:
          predicted_home, predicted_away  — rounded expected goals
          raw_home, raw_away              — continuous model output
          prob_home_win, prob_draw, prob_away_win
          simulated_scores                — list[(h,a)] from Monte Carlo
        """
        # Apply confederation weighting to adjust ELO ratings
        if use_confederation_weights:
            adj_elo_home, adj_elo_away = calculate_confederation_adjusted_elo(
                home_team, away_team, elo_home, elo_away
            )
        else:
            adj_elo_home, adj_elo_away = elo_home, elo_away
        
        # Apply home advantage to ELO for non-neutral venues
        if not neutral:
            adj_elo_home += home_advantage

        row = self._build_row(
            home_team, away_team,
            adj_elo_home, adj_elo_away,
            form_home, form_away,
            tournament,
        )

        # Raw predictions (continuous)
        raw_h = float(self.gb_home.predict(row)[0])
        raw_a = float(self.gb_away.predict(row)[0])

        if self.use_ensemble:
            raw_h = 0.6 * raw_h + 0.4 * float(self.rf_home.predict(row)[0])
            raw_a = 0.6 * raw_a + 0.4 * float(self.rf_away.predict(row)[0])

        # Clip to non-negative
        raw_h = max(0.0, raw_h)
        raw_a = max(0.0, raw_a)

        # Monte Carlo simulation using Poisson distribution
        sim_h = np.random.poisson(raw_h, n_simulations)
        sim_a = np.random.poisson(raw_a, n_simulations)

        prob_home = float((sim_h > sim_a).mean())
        prob_draw = float((sim_h == sim_a).mean())
        prob_away = float((sim_h < sim_a).mean())

        return {
            'home_team': home_team,
            'away_team': away_team,
            'raw_home': raw_h,
            'raw_away': raw_a,
            'predicted_home': int(round(raw_h)),
            'predicted_away': int(round(raw_a)),
            'prob_home_win': prob_home,
            'prob_draw': prob_draw,
            'prob_away_win': prob_away,
            'simulated_scores': list(zip(sim_h.tolist(), sim_a.tolist())),
        }

    def simulate_knockout(
        self,
        home_team: str,
        away_team: str,
        elo_home: float,
        elo_away: float,
        form_home: float = 0.5,
        form_away: float = 0.5,
        tournament: str = 'FIFA World Cup',
    ) -> Dict:
        """
        Simulate a knockout match (90min → ET → penalties if needed).
        Returns winner and full score detail.
        """
        result = self.predict_match(
            home_team, away_team,
            elo_home, elo_away,
            form_home, form_away,
            tournament, neutral=True,
        )

        h90 = result['predicted_home']
        a90 = result['predicted_away']

        et_home = et_away = 0
        penalties_home = penalties_away = None
        went_to_et = went_to_pens = False

        if h90 == a90:
            went_to_et = True
            # Extra time: lower-scoring, use ~30% of 90min rate
            et_raw_h = max(0, result['raw_home'] * 0.30)
            et_raw_a = max(0, result['raw_away'] * 0.30)
            et_home = int(np.random.poisson(et_raw_h))
            et_away = int(np.random.poisson(et_raw_a))

        total_h = h90 + et_home
        total_a = a90 + et_away

        if total_h == total_a:
            went_to_pens = True
            # Penalty shootout: slight advantage to better form team
            form_advantage = (form_home - form_away) * 0.1  # small edge
            p_home_wins_pens = 0.5 + form_advantage
            p_home_wins_pens = max(0.3, min(0.7, p_home_wins_pens))

            if np.random.random() < p_home_wins_pens:
                penalties_home, penalties_away = 1, 0
                winner = home_team
            else:
                penalties_home, penalties_away = 0, 1
                winner = away_team
        else:
            winner = home_team if total_h > total_a else away_team

        return {
            'home_team': home_team,
            'away_team': away_team,
            'winner': winner,
            'score_90': (h90, a90),
            'score_et': (et_home, et_away) if went_to_et else None,
            'penalties': (penalties_home, penalties_away) if went_to_pens else None,
            'final_score': (total_h, total_a),
            'prob_home_win': result['prob_home_win'],
            'prob_draw': result['prob_draw'],
            'prob_away_win': result['prob_away_win'],
        }


# Singleton accessor
_predictor: Predictor = None


def get_predictor(use_ensemble: bool = True) -> Predictor:
    global _predictor
    if _predictor is None:
        _predictor = Predictor(use_ensemble)
    return _predictor


if __name__ == '__main__':
    pred = get_predictor()
    result = pred.predict_match(
        'Brazil', 'Argentina',
        elo_home=2050, elo_away=2100,
        form_home=0.8, form_away=0.9,
    )
    print(f"Brazil vs Argentina: {result['predicted_home']}-{result['predicted_away']}")
    print(f"  Home win: {result['prob_home_win']:.1%}  Draw: {result['prob_draw']:.1%}  Away win: {result['prob_away_win']:.1%}")
