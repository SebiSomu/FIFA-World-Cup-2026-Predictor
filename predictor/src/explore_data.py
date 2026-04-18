"""
Data exploration script for FIFA World Cup 2026 Predictor.
Analyzes all data sources and generates summary reports.
"""

import pandas as pd
import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from data_loader import DataLoader
from team_normalizer import TeamNormalizer


def explore_tournaments(results_df: pd.DataFrame):
    """Explore tournament types in the data."""
    print("\n" + "=" * 60)
    print("TOURNAMENT ANALYSIS")
    print("=" * 60)
    
    tournament_counts = results_df['tournament'].value_counts()
    print(f"\n[TOURNAMENTS] Total unique tournaments: {len(tournament_counts)}")
    print("\nTop 10 tournaments by match count:")
    for i, (tournament, count) in enumerate(tournament_counts.head(10).items(), 1):
        print(f"   {i}. {tournament}: {count:,} matches")
    
    # World Cup specific
    wc_matches = results_df[results_df['tournament'] == 'FIFA World Cup']
    print(f"\n[WORLD CUP] FIFA World Cup matches: {len(wc_matches)}")
    if len(wc_matches) > 0:
        wc_years = wc_matches['date'].dt.year.unique()
        print(f"   Years covered: {sorted(wc_years)}")
    
    return tournament_counts


def explore_teams(results_df: pd.DataFrame, normalizer: TeamNormalizer):
    """Explore team statistics."""
    print("\n" + "=" * 60)
    print("TEAM ANALYSIS")
    print("=" * 60)
    
    # Normalize team names
    normalized_df = normalizer.normalize_dataframe(results_df)
    
    all_teams = set(normalized_df['home_team'].unique()) | set(normalized_df['away_team'].unique())
    print(f"\n[TEAMS] Total unique teams (normalized): {len(all_teams)}")
    
    # Most active teams
    home_counts = normalized_df['home_team'].value_counts()
    away_counts = normalized_df['away_team'].value_counts()
    total_matches = home_counts.add(away_counts, fill_value=0).sort_values(ascending=False)
    
    print("\nMost active teams (total matches):")
    for i, (team, count) in enumerate(total_matches.head(10).items(), 1):
        print(f"   {i}. {team}: {int(count)} matches")
    
    return all_teams, total_matches


def explore_match_outcomes(results_df: pd.DataFrame):
    """Analyze match outcomes."""
    print("\n" + "=" * 60)
    print("MATCH OUTCOME ANALYSIS")
    print("=" * 60)
    
    df = results_df.copy()
    
    # Determine outcomes
    df['outcome'] = df.apply(lambda row: 
        'home_win' if row['home_score'] > row['away_score']
        else 'away_win' if row['home_score'] < row['away_score']
        else 'draw', axis=1
    )
    
    outcomes = df['outcome'].value_counts()
    total = len(df)
    
    print(f"\n[OUTCOMES] Match outcomes distribution:")
    for outcome, count in outcomes.items():
        pct = count / total * 100
        label = {'home_win': 'Home win', 'away_win': 'Away win', 'draw': 'Draw'}[outcome]
        print(f"   {label}: {count:,} ({pct:.1f}%)")
    
    # Score distribution
    df['total_goals'] = df['home_score'] + df['away_score']
    print(f"\n[GOALS] Goal statistics:")
    print(f"   Average goals per match: {df['total_goals'].mean():.2f}")
    print(f"   Most common scoreline: {df['home_score']}-{df['away_score']} (mode)")
    print(f"   Highest scoring match: {df['total_goals'].max()} goals")
    
    return df


def check_wc2026_team_coverage(wc2026_df: pd.DataFrame, all_historical_teams: set, 
                                normalizer: TeamNormalizer):
    """Check coverage of WC2026 teams in historical data."""
    print("\n" + "=" * 60)
    print("WORLD CUP 2026 TEAM COVERAGE")
    print("=" * 60)
    
    # Extract team names from WC2026 groups
    wc2026_teams = set()
    
    if 'team' in wc2026_df.columns:
        wc2026_teams = set(wc2026_df['team'].unique())
    else:
        # Parse from columns
        team_cols = ['First match against', 'Second match against', 'Third match against']
        for col in team_cols:
            if col in wc2026_df.columns:
                wc2026_teams.update(wc2026_df[col].dropna().unique())
        if 'team' in wc2026_df.columns:
            wc2026_teams.update(wc2026_df['team'].dropna().unique())
    
    print(f"\n[WORLD CUP] Teams in WC2026 groups: {len(wc2026_teams)}")
    
    # Normalize and check
    normalized_wc2026 = {normalizer.normalize(team) for team in wc2026_teams}
    found = normalized_wc2026 & all_historical_teams
    missing = normalized_wc2026 - all_historical_teams
    
    print(f"[FOUND] Found in historical data: {len(found)}")
    print(f"[MISSING] Missing from historical data: {len(missing)}")
    
    if missing:
        print("\nMissing teams:")
        for team in sorted(missing):
            print(f"   - {team}")
    else:
        print("\n[SUCCESS] All teams found in historical data!")


def main():
    """Run complete data exploration."""
    print("\n" + "=" * 60)
    print("FIFA WORLD CUP 2026 PREDICTOR - DATA EXPLORATION")
    print("=" * 60)
    
    # Initialize
    loader = DataLoader()
    
    # Load all data
    print("\n[LOADING] Loading data...")
    data = loader.load_all()
    
    # Print basic summary
    loader.print_summary()
    
    # Initialize normalizer
    normalizer = TeamNormalizer(data['former_names'])
    
    # Run explorations
    explore_tournaments(data['results'])
    all_teams, team_activity = explore_teams(data['results'], normalizer)
    explore_match_outcomes(data['results'])
    
    # Check WC2026 coverage
    normalized_wc2026, found, missing = check_wc2026_team_coverage(
        data['wc2026_groups'], all_teams, normalizer
    )
    
    print("\n" + "=" * 60)
    print("EXPLORATION COMPLETE")
    print("=" * 60)
    
    return {
        'data': data,
        'all_teams': all_teams,
        'team_activity': team_activity,
        'wc2026_teams': normalized_wc2026,
        'wc2026_found': found,
        'wc2026_missing': missing
    }


if __name__ == '__main__':
    results = main()
