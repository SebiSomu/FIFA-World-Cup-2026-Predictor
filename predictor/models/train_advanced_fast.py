"""
Fast training using pre-computed team statistics.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')
import pickle

sys.path.append(str(Path(__file__).resolve().parent.parent))

from features.advanced_features import AdvancedFeatureExtractor


def precompute_team_stats(extractor, teams):
    """Pre-compute all team statistics once."""
    print("Pre-computing team statistics...")
    stats_cache = {}
    for i, team in enumerate(teams):
        if i % 10 == 0:
            print(f"  {i}/{len(teams)} teams...", end='\r')
        stats_cache[team] = extractor.get_team_all_time_stats(team)
    print(f"  ✓ Cached stats for {len(teams)} teams")
    return stats_cache


def train_fast():
    """Train models using pre-computed statistics."""
    print("=== Fast Advanced Model Training ===\n")
    
    # Load results
    results_path = Path('predictor/data/results.csv')
    df = pd.read_csv(results_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df[df['date'].dt.year >= 1990]
    df = df.dropna(subset=['home_score', 'away_score'])
    
    # Get all unique teams
    all_teams = pd.concat([df['home_team'], df['away_team']]).unique()
    print(f"Total unique teams: {len(all_teams)}")
    print(f"Total matches: {len(df)}")
    
    # Initialize extractor and pre-compute stats
    extractor = AdvancedFeatureExtractor()
    stats_cache = precompute_team_stats(extractor, all_teams)
    
    # Sample matches for training (every 10th for speed)
    sample_df = df.iloc[::10].copy()
    print(f"\nTraining sample: {len(sample_df)} matches")
    
    # Build features
    print("Building feature matrix...")
    X_list = []
    y_home = []
    y_away = []
    
    for _, row in sample_df.iterrows():
        home = row['home_team']
        away = row['away_team']
        
        # Get pre-computed stats
        h_stats = stats_cache.get(home, extractor._default_stats())
        a_stats = stats_cache.get(away, extractor._default_stats())
        
        # Approximate ELO from win rate
        elo_h = 1500 + (h_stats['win_rate'] - 0.5) * 1000
        elo_a = 1500 + (a_stats['win_rate'] - 0.5) * 1000
        
        # Get H2H
        h2h = extractor.get_h2h_stats(home, away)
        
        # Build feature vector
        features = [
            h_stats['win_rate'], h_stats['draw_rate'],
            h_stats['avg_goals_scored'] if not np.isnan(h_stats['avg_goals_scored']) else 1.0,
            h_stats['avg_goals_conceded'] if not np.isnan(h_stats['avg_goals_conceded']) else 1.0,
            h_stats['clean_sheet_rate'],
            h_stats['recent_form'],
            h_stats['trend'],
            a_stats['win_rate'], a_stats['draw_rate'],
            a_stats['avg_goals_scored'] if not np.isnan(a_stats['avg_goals_scored']) else 1.0,
            a_stats['avg_goals_conceded'] if not np.isnan(a_stats['avg_goals_conceded']) else 1.0,
            a_stats['clean_sheet_rate'],
            a_stats['recent_form'],
            a_stats['trend'],
            h2h['matches'] / 100.0,
            h2h['team1_win_rate'],
            h2h['avg_goals'] / 5.0,
            elo_h / 2500.0,
            elo_a / 2500.0,
            (elo_h - elo_a) / 500.0,
        ]
        
        X_list.append(features)
        y_home.append(row['home_score'])
        y_away.append(row['away_score'])
    
    X = np.array(X_list)
    y_home = np.array(y_home)
    y_away = np.array(y_away)
    
    print(f"Feature matrix: {X.shape}")
    
    # Split
    X_train, X_test, yh_train, yh_test = train_test_split(X, y_home, test_size=0.2, random_state=42)
    _, _, ya_train, ya_test = train_test_split(X, y_away, test_size=0.2, random_state=42)
    
    # Train
    print("\nTraining Random Forest models...")
    model_home = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    model_away = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    
    model_home.fit(X_train, yh_train)
    model_away.fit(X_train, ya_train)
    
    # Evaluate
    yh_pred = model_home.predict(X_test)
    ya_pred = model_away.predict(X_test)
    
    print(f"\n[Results]")
    print(f"  Home MAE: {mean_absolute_error(yh_test, yh_pred):.3f}")
    print(f"  Home RMSE: {np.sqrt(mean_squared_error(yh_test, yh_pred)):.3f}")
    print(f"  Away MAE: {mean_absolute_error(ya_test, ya_pred):.3f}")
    print(f"  Away RMSE: {np.sqrt(mean_squared_error(ya_test, ya_pred)):.3f}")
    
    # Feature importance
    feature_names = [
        'home_win_rate', 'home_draw_rate', 'home_goals_scored', 'home_goals_conceded',
        'home_clean_sheet', 'home_recent_form', 'home_trend',
        'away_win_rate', 'away_draw_rate', 'away_goals_scored', 'away_goals_conceded',
        'away_clean_sheet', 'away_recent_form', 'away_trend',
        'h2h_matches', 'h2h_home_win_rate', 'h2h_avg_goals',
        'elo_home', 'elo_away', 'elo_diff'
    ]
    
    print("\n[Top 10 Feature Importances]")
    importances = model_home.feature_importances_
    for name, imp in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {name}: {imp:.3f}")
    
    # Save
    save_dir = Path('predictor/models/saved')
    save_dir.mkdir(parents=True, exist_ok=True)
    
    with open(save_dir / 'advanced_home_model.pkl', 'wb') as f:
        pickle.dump(model_home, f)
    with open(save_dir / 'advanced_away_model.pkl', 'wb') as f:
        pickle.dump(model_away, f)
    
    # Save stats cache for prediction
    with open(save_dir / 'team_stats_cache.pkl', 'wb') as f:
        pickle.dump(stats_cache, f)
    
    print(f"\n✓ Models and stats cache saved to {save_dir}")
    
    return model_home, model_away, stats_cache


if __name__ == '__main__':
    train_fast()
