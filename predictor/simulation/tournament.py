"""
Tournament simulation for FIFA World Cup 2026.
Runs the full 104-match tournament: 72 group stage + 32 knockout.
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))

from simulation.wc2026_groups import (
    GROUPS, get_all_group_matches, init_group_records,
    rank_group, determine_qualifiers, TeamRecord,
)
from simulation.wc2026_knockout_bracket import (
    FINAL_MATCH,
    THIRD_PLACE_MATCH,
    build_final_fixture,
    build_quarter_final_fixtures,
    build_round_of_16_fixtures,
    build_round_of_32_fixtures,
    build_semi_final_fixtures,
    build_third_place_fixture,
)
from models.dixon_coles_hybrid_predictor import DixonColesHybridPredictor
from features.elo_ratings import EloSystem

# Initialize ELO system for tournament ELO updates
TOURNAMENT_ELO = EloSystem()

_SIM_DIR = Path(__file__).resolve().parent
_PREDICTOR_ROOT = _SIM_DIR.parent


def _resolve_results_csv() -> Optional[Path]:
    """Locate results.csv when cwd is repo root, predictor/, or elsewhere."""
    candidates = [
        _PREDICTOR_ROOT / "data" / "results.csv",
        Path("predictor/data/results.csv"),
        Path("data/results.csv"),
    ]
    for p in candidates:
        if p.exists():
            return p.resolve()
    return None


def load_external_elo_ratings() -> Dict[str, float]:
    """Load current ELO ratings from eloratings.net CSV file for WC2026 teams."""
    # Get the directory of this file
    current_dir = Path(__file__).resolve().parent
    # Go up one level to predictor/, then to data/
    elo_file = current_dir.parent / 'data' / 'elo_ratings_wc2026_correct.csv'
    if elo_file.exists():
        # Read CSV, skipping comment lines
        df = pd.read_csv(elo_file, comment='#')
        return dict(zip(df['team'], df['elo_rating']))
    return {}


def get_wc2026_teams() -> List[str]:
    """Get all 48 teams participating in WC2026."""
    teams = set()
    for group_teams in GROUPS.values():
        teams.update(group_teams)
    return list(teams)


def build_base_elo() -> Dict[str, float]:
    """Build base ELO dict for all WC2026 teams using external ratings."""
    external = load_external_elo_ratings()
    wc2026_teams = get_wc2026_teams()
    
    base_elo = {}
    for team in wc2026_teams:
        if team in external:
            base_elo[team] = external[team]
        else:
            # Default ELO for missing teams (1500 is average)
            base_elo[team] = 1500.0
            print(f"Warning: No external ELO for {team}, using default 1500")
    
    return base_elo


# ── ELO & Form State ─────────────────────────────────────────────────────────

class TeamState:
    """Live ELO ratings and form during the tournament with proper ELO updates."""

    def __init__(self, base_elo: Dict[str, float] = None):
        if base_elo is None:
            base_elo = build_base_elo()
        self.elo = dict(base_elo)
        self.form: Dict[str, List[float]] = {team: [0.5] for team in self.elo}
        # Initialize ELO system with current ratings
        for team, rating in self.elo.items():
            TOURNAMENT_ELO.ratings[team] = rating

    def get_elo(self, team: str) -> float:
        return self.elo.get(team, 1500.0)

    def get_form(self, team: str) -> float:
        history = self.form.get(team, [0.5])
        return sum(history) / len(history)

    def update(self, home_team: str, away_team: str, home_goals: int, away_goals: int):
        """Update ELO and form after a match using proper ELO formula."""
        # Update form for both teams
        for team, goals_scored, goals_conceded in [(home_team, home_goals, away_goals), 
                                                    (away_team, away_goals, home_goals)]:
            result = 1.0 if goals_scored > goals_conceded else (0.5 if goals_scored == goals_conceded else 0.0)
            history = self.form.setdefault(team, [0.5])
            history.append(result)
            if len(history) > 5:
                history.pop(0)
        
        # Update ELO ratings using the proper ELO system
        TOURNAMENT_ELO.update_ratings(home_team, away_team, home_goals, away_goals, 
                                       'FIFA World Cup', is_neutral=True)
        
        # Sync with our internal elo dict
        self.elo[home_team] = TOURNAMENT_ELO.get_rating(home_team)
        self.elo[away_team] = TOURNAMENT_ELO.get_rating(away_team)


# ── Group Stage ───────────────────────────────────────────────────────────────

def simulate_group_stage(
    predictor: DixonColesHybridPredictor,
    state: TeamState,
) -> Tuple[Dict, List[Dict]]:
    """
    Simulate all 72 group stage matches.
    Returns (group_standings dict, match_results list).
    """
    records = init_group_records()
    match_results = []
    match_id = 1

    for group, teams in GROUPS.items():
        pairs = [(teams[i], teams[j]) for i in range(4) for j in range(i+1, 4)]

        for home, away in pairs:
            # Use historical predictor (includes ELO automatically)
            result = predictor.predict_match(
                home, away,
                neutral=True,
            )

            h_goals = result['predicted_home']
            a_goals = result['predicted_away']

            # Update records
            records[group][home].update(h_goals, a_goals)
            records[group][away].update(a_goals, h_goals)

            # Update live state (ELO + form)
            state.update(home, away, h_goals, a_goals)

            match_results.append({
                'match_id': f'GS{match_id:03d}',
                'stage': 'Group Stage',
                'group': group,
                'home_team': home,
                'away_team': away,
                'predicted_home_score': h_goals,
                'predicted_away_score': a_goals,
                'prob_home_win': round(result['prob_home_win'], 3),
                'prob_draw': round(result['prob_draw'], 3),
                'prob_away_win': round(result['prob_away_win'], 3),
                'winner': None,  # No winner in group stage (can draw)
            })
            match_id += 1

    # Rank each group
    group_standings = {g: rank_group(records[g]) for g in GROUPS}
    return group_standings, match_results


# ── Knockout Simulation (FIFA bracket match numbers M073 … M104) ─────────────

def simulate_knockout_fixtures(
    predictor: DixonColesHybridPredictor,
    state: TeamState,
    fixtures: List[Tuple[str, str, int]],
    stage_name: str,
) -> Tuple[Dict[int, str], List[Dict]]:
    """
    Simulate knockout ties with official FIFA match numbers on the bracket path.
    Returns (winners keyed by fifa_match_number, list of result dicts).
    """
    winners: Dict[int, str] = {}
    results: List[Dict] = []

    for home, away, mnum in fixtures:
        result = predictor.simulate_knockout(
            home, away,
            neutral=True,
        )

        winner = result['winner']
        winners[mnum] = winner
        state.update(home, away, result['final_score'][0], result['final_score'][1])

        h90, a90 = result['score_90']
        score_str = f"{h90}-{a90}"
        if result['score_et']:
            et_h, et_a = result['score_et']
            score_str += f" (ET: +{et_h}-{et_a})"
        if result['penalties']:
            p_h, p_a = result['penalties']
            score_str += f" [PKs: {p_h}-{p_a}]"

        results.append({
            'match_id': f'M{mnum:03d}',
            'fifa_match_number': mnum,
            'stage': stage_name,
            'group': '',
            'home_team': home,
            'away_team': away,
            'predicted_home_score': result['final_score'][0],
            'predicted_away_score': result['final_score'][1],
            'score_detail': score_str,
            'prob_home_win': round(result['prob_home_win'], 3),
            'prob_draw': round(result['prob_draw'], 3),
            'prob_away_win': round(result['prob_away_win'], 3),
            'winner': winner,
        })

    return winners, results


# ── Full Tournament ───────────────────────────────────────────────────────────

def run_tournament(base_elo: Dict[str, float] = None) -> Dict:
    """
    Run the complete WC2026 simulation.
    Returns dict with all match results and standings.
    """
    np.random.seed(42)  # reproducibility

    predictor = DixonColesHybridPredictor()  # Dixon-Coles hybrid predictor
    results_path = _resolve_results_csv()
    if results_path is not None:
        matches_df = pd.read_csv(results_path)
        matches_df["date"] = pd.to_datetime(matches_df["date"])
        # Same year window as hybrid fit (all-time when FIT_MIN_YEAR is early)
        matches_df = matches_df[
            matches_df["date"].dt.year >= DixonColesHybridPredictor.FIT_MIN_YEAR
        ]
        predictor.fit(matches_df)
    
    state = TeamState(base_elo)  # Uses external eloratings.net by default

    all_results: List[Dict] = []

    # ── Group Stage ──
    print("Simulating Group Stage (72 matches)...")
    group_standings, gs_results = simulate_group_stage(predictor, state)
    all_results.extend(gs_results)

    # ── Determine qualifiers ──
    qualified_by_group, best_thirds = determine_qualifiers(group_standings)
    print(f"  -> 24 group winners/runners-up + 8 best 3rd-place teams qualify")

    # ── Round of 32 (FIFA matches 73–88) ──
    r32_fixtures = build_round_of_32_fixtures(qualified_by_group, best_thirds)
    print(f"\nSimulating Round of 32 ({len(r32_fixtures)} matches, FIFA M073–M088)...")
    r32_winners, r32_results = simulate_knockout_fixtures(
        predictor, state, r32_fixtures, 'Round of 32')
    all_results.extend(r32_results)

    # ── Round of 16 (89–96) ──
    r16_fixtures = build_round_of_16_fixtures(r32_winners)
    print(f"Simulating Round of 16 ({len(r16_fixtures)} matches, FIFA M089–M096)...")
    r16_winners, r16_results = simulate_knockout_fixtures(
        predictor, state, r16_fixtures, 'Round of 16')
    all_results.extend(r16_results)

    # ── Quarter-finals (97–100) ──
    qf_fixtures = build_quarter_final_fixtures(r16_winners)
    print(f"Simulating Quarter-Finals ({len(qf_fixtures)} matches, FIFA M097–M100)...")
    qf_winners, qf_results = simulate_knockout_fixtures(
        predictor, state, qf_fixtures, 'Quarter-Final')
    all_results.extend(qf_results)

    # ── Semi-finals (101–102) ──
    sf_fixtures = build_semi_final_fixtures(qf_winners)
    print(f"Simulating Semi-Finals ({len(sf_fixtures)} matches, FIFA M101–M102)...")
    sf_winners, sf_results = simulate_knockout_fixtures(
        predictor, state, sf_fixtures, 'Semi-Final')
    all_results.extend(sf_results)
    sf_by_num = {r['fifa_match_number']: r for r in sf_results}

    # ── Third place (103) ──
    print("Simulating Third Place Playoff (FIFA M103)...")
    tp_fixtures = build_third_place_fixture(sf_by_num)
    tp_winners, tp_results = simulate_knockout_fixtures(
        predictor, state, tp_fixtures, 'Third Place')
    all_results.extend(tp_results)
    third_place = tp_winners[THIRD_PLACE_MATCH]

    # ── Final (104) ──
    print("Simulating Final (FIFA M104)...")
    final_fixtures = build_final_fixture(sf_by_num)
    final_winners, final_results = simulate_knockout_fixtures(
        predictor, state, final_fixtures, 'Final')
    all_results.extend(final_results)
    champion = final_winners[FINAL_MATCH]
    fr = final_results[0]
    runner_up = fr['away_team'] if fr['winner'] == fr['home_team'] else fr['home_team']

    return {
        'all_results': all_results,
        'group_standings': group_standings,
        'qualified_by_group': qualified_by_group,
        'best_thirds': best_thirds,
        'champion': champion,
        'runner_up': runner_up,
        'third_place': third_place,
    }


if __name__ == '__main__':
    # Run with external eloratings.net ratings
    results = run_tournament()
    print(f"\nCHAMPION: {results['champion']}")
    print(f"RUNNER-UP: {results['runner_up']}")
    print(f"THIRD PLACE: {results['third_place']}")
