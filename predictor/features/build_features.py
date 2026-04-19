import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import sys

# Add the project root to sys.path to allow imports from src
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.data_loader import DataLoader
from src.team_normalizer import TeamNormalizer
from features.elo_ratings import EloSystem

def build_features():
    print("Starting Feature Engineering Pipeline...")
    
    # 0. Load external scaled ELO ratings for WC2026 teams
    external_elo_file = Path('predictor/data/elo_ratings_wc2026_scaled.csv')
    external_elo = {}
    if external_elo_file.exists():
        elo_df = pd.read_csv(external_elo_file)
        external_elo = dict(zip(elo_df['team'], elo_df['elo_rating']))
        print(f"Loaded {len(external_elo)} external ELO ratings")
    
    # 1. Load data
    loader = DataLoader()
    results = loader.load_results()
    former_names = loader.load_former_names()
    
    # 2. Normalize teams
    print("Standardizing team names...")
    normalizer = TeamNormalizer(former_names)
    results = normalizer.normalize_dataframe(results)
    
    # 3. Sort by date to process matches chronologically
    results = results.sort_values('date').reset_index(drop=True)
    
    # 4. Initialize ELO System with external ratings
    elo = EloSystem()
    # Pre-populate with external ELO ratings for WC2026 teams
    for team, rating in external_elo.items():
        elo.ratings[team] = rating
    print(f"Pre-populated ELO system with {len(external_elo)} external ratings")
    
    # 5. Prepare tracking for features
    elo_h = []
    elo_a = []
    form_h = []
    form_a = []
    
    # Head-to-head history: {(team1, team2): {'wins': 0, 'draws': 0, 'losses': 0, 'goals_for': 0, 'goals_against': 0}}
    h2h_history = {}
    
    # Dictionary to track last 5 match results for each team (1 for win, 0.5 draw, 0 loss)
    team_history = {} # {team: [results]}
    
    def get_form(team):
        if team not in team_history or not team_history[team]:
            return 0.5 # Average form for new teams
        return sum(team_history[team]) / len(team_history[team])
    
    def update_history(team, result):
        if team not in team_history:
            team_history[team] = []
        team_history[team].append(result)
        if len(team_history[team]) > 5:
            team_history[team].pop(0)
    
    def get_h2h_key(team1, team2):
        """Get canonical key for head-to-head (alphabetical order)."""
        return (min(team1, team2), max(team1, team2))
    
    def get_h2h_stats(team1, team2):
        """Get head-to-head stats for team1 vs team2. Returns dict with win rate, avg goals."""
        key = get_h2h_key(team1, team2)
        if key not in h2h_history:
            return {'h2h_matches': 0, 'h2h_win_rate': 0.5, 'h2h_avg_goals': 0}
        
        stats = h2h_history[key]
        total = stats['wins'] + stats['draws'] + stats['losses']
        if total == 0:
            return {'h2h_matches': 0, 'h2h_win_rate': 0.5, 'h2h_avg_goals': 0}
        
        # Calculate win rate from team1 perspective
        # Note: if key is (team2, team1), we need to flip the perspective
        if key[0] == team1:
            wins = stats['wins']
        else:
            wins = stats['losses']
        
        return {
            'h2h_matches': total,
            'h2h_win_rate': wins / total,
            'h2h_avg_goals': stats['goals_for'] / total if total > 0 else 0
        }
    
    def update_h2h(team1, team2, team1_goals, team2_goals):
        """Update head-to-head history after a match."""
        key = get_h2h_key(team1, team2)
        if key not in h2h_history:
            h2h_history[key] = {'wins': 0, 'draws': 0, 'losses': 0, 'goals_for': 0, 'goals_against': 0}
        
        if team1_goals > team2_goals:
            if key[0] == team1:
                h2h_history[key]['wins'] += 1
            else:
                h2h_history[key]['losses'] += 1
        elif team1_goals < team2_goals:
            if key[0] == team1:
                h2h_history[key]['losses'] += 1
            else:
                h2h_history[key]['wins'] += 1
        else:
            h2h_history[key]['draws'] += 1
        
        # Track goals
        if key[0] == team1:
            h2h_history[key]['goals_for'] += team1_goals
            h2h_history[key]['goals_against'] += team2_goals
        else:
            h2h_history[key]['goals_for'] += team2_goals
            h2h_history[key]['goals_against'] += team1_goals

    # 6. Process matches
    print(f"Processing {len(results):,} matches...")
    
    # Lists for head-to-head features
    h2h_matches_h = []
    h2h_matches_a = []
    h2h_win_rate_h = []
    h2h_win_rate_a = []
    
    for idx, row in tqdm(results.iterrows(), total=len(results)):
        h, a = row['home_team'], row['away_team']
        hs, ascore = row['home_score'], row['away_score']
        tournament = row['tournament']
        neutral = row['neutral']
        
        # Get ELO before match
        r_h = elo.get_rating(h)
        r_a = elo.get_rating(a)
        
        # Get head-to-head stats BEFORE this match (historical only)
        h2h_h = get_h2h_stats(h, a)
        h2h_a = get_h2h_stats(a, h)
        
        # Record features BEFORE update
        elo_h.append(r_h)
        elo_a.append(r_a)
        form_h.append(get_form(h))
        form_a.append(get_form(a))
        h2h_matches_h.append(h2h_h['h2h_matches'])
        h2h_matches_a.append(h2h_a['h2h_matches'])
        h2h_win_rate_h.append(h2h_h['h2h_win_rate'])
        h2h_win_rate_a.append(h2h_a['h2h_win_rate'])
        
        # Update ELO
        elo.update_ratings(h, a, hs, ascore, tournament, neutral)
        
        # Update Form History
        if hs > ascore:
            update_history(h, 1.0)
            update_history(a, 0.0)
        elif hs < ascore:
            update_history(h, 0.0)
            update_history(a, 1.0)
        else:
            update_history(h, 0.5)
            update_history(a, 0.5)
        
        # Update head-to-head history AFTER recording features
        update_h2h(h, a, hs, ascore)
            
    # 7. Add columns to dataframe
    results['elo_home'] = elo_h
    results['elo_away'] = elo_a
    results['elo_diff'] = results['elo_home'] - results['elo_away']
    results['form_home'] = form_h
    results['form_away'] = form_a
    results['h2h_matches'] = h2h_matches_h  # number of previous meetings
    results['h2h_win_rate_home'] = h2h_win_rate_h  # home team win rate in h2h
    results['h2h_win_rate_away'] = h2h_win_rate_a  # away team win rate in h2h
    
    # 8. Save processed data
    output_dir = Path('predictor/data/processed')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / 'training_data.csv'
    results.to_csv(output_file, index=False)
    
    print(f"\n✅ Feature engineering complete! Saved to {output_file}")
    
    # Print top 10 teams by current ELO for verification
    print("\nTop 10 Teams by current ELO:")
    sorted_ratings = sorted(elo.ratings.items(), key=lambda x: x[1], reverse=True)
    for i, (team, rating) in enumerate(sorted_ratings[:10]):
        print(f"{i+1}. {team}: {rating:.1f}")

if __name__ == '__main__':
    build_features()
