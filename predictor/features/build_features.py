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
    
    # 4. Initialize ELO System
    elo = EloSystem()
    
    # 5. Prepare tracking for features
    elo_h = []
    elo_a = []
    form_h = []
    form_a = []
    
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

    # 6. Process matches
    print(f"Processing {len(results):,} matches...")
    
    for idx, row in tqdm(results.iterrows(), total=len(results)):
        h, a = row['home_team'], row['away_team']
        hs, ascore = row['home_score'], row['away_score']
        tournament = row['tournament']
        neutral = row['neutral']
        
        # Get ELO before match
        r_h = elo.get_rating(h)
        r_a = elo.get_rating(a)
        
        # Record features BEFORE update
        elo_h.append(r_h)
        elo_a.append(r_a)
        form_h.append(get_form(h))
        form_a.append(get_form(a))
        
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
            
    # 7. Add columns to dataframe
    results['elo_home'] = elo_h
    results['elo_away'] = elo_a
    results['elo_diff'] = results['elo_home'] - results['elo_away']
    results['form_home'] = form_h
    results['form_away'] = form_a
    
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
