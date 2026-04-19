"""
FIFA World Cup 2026 Predictor — Main Entry Point.
Orchestrates the full pipeline: features → training → simulation → output.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

PROCESSED_DATA = ROOT / 'data' / 'processed' / 'training_data.csv'
MODELS_DIR     = ROOT / 'models' / 'saved'
OUTPUT_DIR     = ROOT / 'output' / 'predictions'


def step_features():
    print("\n" + "=" * 60)
    print("STEP 1: FEATURE ENGINEERING")
    print("=" * 60)
    if PROCESSED_DATA.exists():
        print(f"  ✅ training_data.csv already exists — skipping build_features.")
        return
    from features.build_features import build_features
    build_features()


def step_train():
    print("\n" + "=" * 60)
    print("STEP 2: MODEL TRAINING")
    print("=" * 60)
    if (MODELS_DIR / 'gb_home.joblib').exists():
        print("  ✅ Trained models already exist — skipping training.")
        return
    from models.train import train
    train()


def load_final_elo() -> dict:
    """
    Read training_data.csv, replay the last known ELO for every team.
    Uses the most recent match row for each team as their 'current' ELO.
    """
    df = pd.read_csv(PROCESSED_DATA)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    elo_map = {}
    for _, row in df.iterrows():
        elo_map[row['home_team']] = row['elo_home']
        elo_map[row['away_team']] = row['elo_away']

    return elo_map


def step_simulate(elo_map: dict) -> dict:
    print("\n" + "=" * 60)
    print("STEP 3: WORLD CUP 2026 SIMULATION")
    print("=" * 60)
    from simulation.tournament import run_tournament
    return run_tournament(elo_map)


def step_output(tournament_results: dict):
    print("\n" + "=" * 60)
    print("STEP 4: GENERATING OUTPUT")
    print("=" * 60)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── All match predictions CSV ──
    all_results = tournament_results['all_results']
    df_matches = pd.DataFrame(all_results)
    matches_path = OUTPUT_DIR / 'wc2026_predictions.csv'
    df_matches.to_csv(matches_path, index=False)
    print(f"  📄 Match predictions → {matches_path} ({len(df_matches)} matches)")

    # ── Group standings CSV ──
    standings_rows = []
    for group, ranked in tournament_results['group_standings'].items():
        for pos, record in enumerate(ranked, 1):
            row = record.as_dict()
            row['position'] = pos
            standings_rows.append(row)
    df_standings = pd.DataFrame(standings_rows)
    standings_path = OUTPUT_DIR / 'group_standings.csv'
    df_standings.to_csv(standings_path, index=False)
    print(f"  📄 Group standings → {standings_path}")

    # ── Knockout bracket CSV ──
    ko_results = [r for r in all_results if r['stage'] != 'Group Stage']
    df_ko = pd.DataFrame(ko_results)
    ko_path = OUTPUT_DIR / 'knockout_bracket.csv'
    df_ko.to_csv(ko_path, index=False)
    print(f"  📄 Knockout bracket → {ko_path}")

    return df_matches, df_standings


def print_summary(tournament_results: dict, df_standings: pd.DataFrame):
    print("\n" + "=" * 60)
    print("WC 2026 SIMULATION SUMMARY")
    print("=" * 60)

    # Group standings per group
    print("\n── GROUP STANDINGS ──")
    for group in sorted(tournament_results['group_standings'].keys()):
        ranked = tournament_results['group_standings'][group]
        print(f"\n  Group {group}:")
        for pos, r in enumerate(ranked, 1):
            marker = "✅" if pos <= 2 else ("🔶" if pos == 3 else "  ")
            print(f"    {marker} {pos}. {r.team:<22} Pts:{r.points}  GD:{r.goal_diff:+d}  GF:{r.goals_for}")

    best_thirds = tournament_results['best_thirds']
    print(f"\n── BEST 3RD-PLACE TEAMS (8 qualify) ──")
    for i, r in enumerate(best_thirds, 1):
        print(f"  {i}. {r.team} (Group {r.group}) — Pts:{r.points}  GD:{r.goal_diff:+d}")

    # Knockout summary
    ko = [r for r in tournament_results['all_results'] if r['stage'] != 'Group Stage']
    print(f"\n── KNOCKOUT RESULTS ──")
    for stage in ['Round of 32', 'Round of 16', 'Quarter-Final', 'Semi-Final', 'Third Place', 'Final']:
        stage_matches = [r for r in ko if r['stage'] == stage]
        if stage_matches:
            print(f"\n  {stage}:")
            for r in stage_matches:
                detail = r.get('score_detail', f"{r['predicted_home_score']}-{r['predicted_away_score']}")
                winner_mark = f" → {r['winner']}" if r.get('winner') else ""
                print(f"    {r['home_team']} vs {r['away_team']}: {detail}{winner_mark}")

    print("\n" + "=" * 60)
    print(f"  🏆  CHAMPION:     {tournament_results['champion']}")
    print(f"  🥈  RUNNER-UP:    {tournament_results['runner_up']}")
    print(f"  🥉  THIRD PLACE:  {tournament_results['third_place']}")
    print("=" * 60)
    print(f"\n  Output files in: {OUTPUT_DIR}")


def main():
    print("\n" + "=" * 60)
    print("  FIFA WORLD CUP 2026 PREDICTOR")
    print("=" * 60)

    step_features()
    step_train()

    elo_map = load_final_elo()
    print(f"  Loaded ELO ratings for {len(elo_map)} teams.")

    tournament_results = step_simulate(elo_map)
    _, df_standings = step_output(tournament_results)

    print_summary(tournament_results, df_standings)


if __name__ == '__main__':
    main()
