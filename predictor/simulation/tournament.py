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
from models.historical_predictor import HistoricalPredictor
from features.elo_ratings import EloSystem

# Initialize ELO system for tournament ELO updates
TOURNAMENT_ELO = EloSystem()


def load_external_elo_ratings() -> Dict[str, float]:
    """Load current ELO ratings from eloratings.net CSV file for WC2026 teams."""
    elo_file = Path('predictor/data/elo_ratings_wc2026_correct.csv')
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
    predictor: HistoricalPredictor,
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


# ── Bracket Builder (Round of 32) ─────────────────────────────────────────────

def build_r32_bracket(
    qualified_by_group: Dict,
    best_thirds: List[TeamRecord],
) -> List[Tuple[str, str]]:
    """
    Build the Round of 32 bracket.
    WC2026 format: 16 matches between group winners/runners-up/best-thirds.

    Simplified pairing: 1st of group X vs 2nd of group Y (FIFA will announce
    the exact cross-group pairings after the draw; we use a representative schedule).
    Winners + best thirds fill the 32-team bracket.
    """
    # Collect 1st and 2nd place teams
    firsts  = [qualified_by_group[g][0].team for g in sorted(GROUPS)]
    seconds = [qualified_by_group[g][1].team for g in sorted(GROUPS)]
    thirds  = [t.team for t in best_thirds]

    # 32 teams total: 12 firsts + 12 seconds + 8 best thirds
    # Pair: first[i] vs second[11-i] with thirds filling remaining slots
    bracket: List[Tuple[str, str]] = []

    # Pair each 1st-place vs a 2nd-place (avoid same group where possible)
    # Simple sequential pairing as placeholder for official draw
    all_32 = firsts + thirds  # 12 + 8 = 20 "seeded" side
    other_16 = seconds        # 12 seconds

    # Fill to 16 matches
    side_a = firsts[:12] + thirds[:4]   # 16 teams
    side_b = seconds[:12] + thirds[4:8] # 16 teams

    for a, b in zip(side_a, side_b):
        bracket.append((a, b))

    return bracket


# ── Knockout Simulation ───────────────────────────────────────────────────────

def simulate_knockout_round(
    predictor: Predictor,
    state: TeamState,
    matches: List[Tuple[str, str]],
    stage_name: str,
    match_id_start: int,
) -> Tuple[List[str], List[Dict]]:
    """
    Simulate a single knockout round.
    Returns (winners list, match_results list).
    """
    winners = []
    results = []
    mid = match_id_start

    for home, away in matches:
        elo_h = state.get_elo(home)
        elo_a = state.get_elo(away)
        form_h = state.get_form(home)
        form_a = state.get_form(away)

        # Use historical predictor for knockout
        result = predictor.simulate_knockout(
            home, away,
            neutral=True,
        )

        winner = result['winner']
        winners.append(winner)
        # Update state (ELO + form)
        state.update(home, away, result['final_score'][0], result['final_score'][1])

        # Format score string
        h90, a90 = result['score_90']
        score_str = f"{h90}-{a90}"
        if result['score_et']:
            et_h, et_a = result['score_et']
            score_str += f" (ET: +{et_h}-{et_a})"
        if result['penalties']:
            p_h, p_a = result['penalties']
            score_str += f" [PKs: {p_h}-{p_a}]"

        results.append({
            'match_id': f'KO{mid:03d}',
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
        mid += 1

    return winners, results


def pair_for_next_round(winners: List[str]) -> List[Tuple[str, str]]:
    """Pair consecutive winners: [0 vs 1, 2 vs 3, ...]"""
    return [(winners[i], winners[i+1]) for i in range(0, len(winners), 2)]


# ── Full Tournament ───────────────────────────────────────────────────────────

def run_tournament(base_elo: Dict[str, float] = None) -> Dict:
    """
    Run the complete WC2026 simulation.
    Returns dict with all match results and standings.
    """
    np.random.seed(42)  # reproducibility

    predictor = HistoricalPredictor()  # New historical-based predictor
    state = TeamState(base_elo)  # Uses external eloratings.net by default

    all_results: List[Dict] = []

    # ── Group Stage ──
    print("Simulating Group Stage (72 matches)...")
    group_standings, gs_results = simulate_group_stage(predictor, state)
    all_results.extend(gs_results)

    # ── Determine qualifiers ──
    qualified_by_group, best_thirds = determine_qualifiers(group_standings)
    print(f"  -> 24 group winners/runners-up + 8 best 3rd-place teams qualify")

    # ── Round of 32 ──
    r32_bracket = build_r32_bracket(qualified_by_group, best_thirds)
    print(f"\nSimulating Round of 32 ({len(r32_bracket)} matches)...")
    r32_winners, r32_results = simulate_knockout_round(
        predictor, state, r32_bracket, 'Round of 32', 1)
    all_results.extend(r32_results)

    # ── Round of 16 ──
    r16_bracket = pair_for_next_round(r32_winners)
    print(f"Simulating Round of 16 ({len(r16_bracket)} matches)...")
    r16_winners, r16_results = simulate_knockout_round(
        predictor, state, r16_bracket, 'Round of 16', 17)
    all_results.extend(r16_results)

    # ── Quarter-finals ──
    qf_bracket = pair_for_next_round(r16_winners)
    print(f"Simulating Quarter-Finals ({len(qf_bracket)} matches)...")
    qf_winners, qf_results = simulate_knockout_round(
        predictor, state, qf_bracket, 'Quarter-Final', 25)
    all_results.extend(qf_results)

    # ── Semi-finals ──
    sf_bracket = pair_for_next_round(qf_winners)
    print(f"Simulating Semi-Finals ({len(sf_bracket)} matches)...")
    sf_winners, sf_results = simulate_knockout_round(
        predictor, state, sf_bracket, 'Semi-Final', 29)
    sf_losers = [
        sf_results[0]['home_team'] if sf_results[0]['winner'] == sf_results[0]['away_team'] else sf_results[0]['away_team'],
        sf_results[1]['home_team'] if sf_results[1]['winner'] == sf_results[1]['away_team'] else sf_results[1]['away_team'],
    ]
    all_results.extend(sf_results)

    # ── Third place ──
    print("Simulating Third Place Playoff...")
    tp_winners, tp_results = simulate_knockout_round(
        predictor, state, [(sf_losers[0], sf_losers[1])], 'Third Place', 31)
    all_results.extend(tp_results)
    third_place = tp_winners[0]

    # ── Final ──
    print("Simulating Final...")
    final_bracket = [(sf_winners[0], sf_winners[1])]
    final_winners, final_results = simulate_knockout_round(
        predictor, state, final_bracket, 'Final', 32)
    all_results.extend(final_results)
    champion = final_winners[0]
    runner_up = sf_winners[1] if champion == sf_winners[0] else sf_winners[0]

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
