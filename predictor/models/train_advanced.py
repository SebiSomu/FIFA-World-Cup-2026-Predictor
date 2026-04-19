"""
Train ML models on advanced features with recency weighting.
Uses XGBoost to predict home and away scores.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

sys.path.append(str(Path(__file__).resolve().parent.parent))

from features.advanced_features import AdvancedFeatureExtractor


def load_and_prepare_training_data():
    """
    Load historical matches and build training dataset with advanced features.
    """
    print("Loading training data...")
    
    # Load results
    results_path = Path('predictor/data/results.csv')
    df = pd.read_csv(results_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter to recent matches (1990+) for training
    df = df[df['date'].dt.year >= 1990]
    
    # Remove rows with missing scores
    df = df.dropna(subset=['home_score', 'away_score'])
    
    print(f"  Total matches: {len(df)}")
    
    # Initialize feature extractor
    extractor = AdvancedFeatureExtractor()
    
    # Build feature matrix
    X_list = []
    y_home = []
    y_away = []
    
    # Sample for training (use every 5th match to speed up)
    sample_df = df.iloc[::5].copy()
    print(f"  Training sample: {len(sample_df)} matches")
    
    for idx, row in sample_df.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']
        
        # Get ELO ratings (use approximate based on historical performance)
        # For training, we use a simplified ELO calculation
        home_stats = extractor.get_team_all_time_stats(home_team)
        away_stats = extractor.get_team_all_time_stats(away_team)
        
        # Approximate ELO from win rate (scaled to 1500-2500 range)
        elo_home = 1500 + (home_stats['win_rate'] - 0.5) * 1000
        elo_away = 1500 + (away_stats['win_rate'] - 0.5) * 1000
        
        # Build features
        features = extractor.build_match_features(home_team, away_team, elo_home, elo_away)
        
        X_list.append(features)
        y_home.append(row['home_score'])
        y_away.append(row['away_score'])
    
    X = np.array(X_list)
    y_home = np.array(y_home)
    y_away = np.array(y_away)
    
    # Handle NaN values
    X = np.nan_to_num(X, nan=0.0)
    
    print(f"  Feature matrix shape: {X.shape}")
    print(f"  Home scores range: {y_home.min():.0f} - {y_home.max():.0f}")
    print(f"  Away scores range: {y_away.min():.0f} - {y_away.max():.0f}")
    
    return X, y_home, y_away


def train_models(X, y_home, y_away):
    """Train XGBoost models for home and away scores."""
    print("\nTraining XGBoost models...")
    
    try:
        import xgboost as xgb
    except ImportError:
        print("XGBoost not available, using Random Forest instead...")
        from sklearn.ensemble import RandomForestRegressor
        
        # Split data
        X_train, X_test, yh_train, yh_test = train_test_split(X, y_home, test_size=0.2, random_state=42)
        _, _, ya_train, ya_test = train_test_split(X, y_away, test_size=0.2, random_state=42)
        
        # Train Random Forest models
        model_home = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        model_away = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        
        model_home.fit(X_train, yh_train)
        model_away.fit(X_train, ya_train)
        
        # Evaluate
        yh_pred = model_home.predict(X_test)
        ya_pred = model_away.predict(X_test)
        
        print(f"\n[RF - Test Results]")
        print(f"  Home MAE: {mean_absolute_error(yh_test, yh_pred):.3f}")
        print(f"  Away MAE: {mean_absolute_error(ya_test, ya_pred):.3f}")
        
        return model_home, model_away
    
    # Split data
    X_train, X_test, yh_train, yh_test = train_test_split(X, y_home, test_size=0.2, random_state=42)
    _, _, ya_train, ya_test = train_test_split(X, y_away, test_size=0.2, random_state=42)
    
    # Train XGBoost models
    print("  Training home score model...")
    model_home = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )
    model_home.fit(X_train, yh_train, eval_set=[(X_test, yh_test)], verbose=False)
    
    print("  Training away score model...")
    model_away = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )
    model_away.fit(X_train, ya_train, eval_set=[(X_test, ya_test)], verbose=False)
    
    # Evaluate
    yh_pred = model_home.predict(X_test)
    ya_pred = model_away.predict(X_test)
    
    print(f"\n[XGBoost - Test Results]")
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
    
    print("\n[Feature Importance - Home Model]")
    importances = model_home.feature_importances_
    for name, imp in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {name}: {imp:.3f}")
    
    return model_home, model_away


def save_models(model_home, model_away):
    """Save trained models."""
    import pickle
    
    save_dir = Path('predictor/models/saved')
    save_dir.mkdir(parents=True, exist_ok=True)
    
    with open(save_dir / 'advanced_home_model.pkl', 'wb') as f:
        pickle.dump(model_home, f)
    
    with open(save_dir / 'advanced_away_model.pkl', 'wb') as f:
        pickle.dump(model_away, f)
    
    print(f"\n✓ Models saved to {save_dir}")


if __name__ == '__main__':
    # Load data
    X, y_home, y_away = load_and_prepare_training_data()
    
    # Train models
    model_home, model_away = train_models(X, y_home, y_away)
    
    # Save models
    save_models(model_home, model_away)
    
    print("\n=== Training Complete ===")
