"""
Model training for FIFA World Cup 2026 Predictor.
Trains two regression models: one for home_score, one for away_score.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error

PROCESSED_DATA = Path('predictor/data/processed/training_data.csv')
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


def load_and_prepare(min_year: int = 1994) -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DATA)
    df['date'] = pd.to_datetime(df['date'])
    df = df[df['date'].dt.year >= min_year].copy()
    df['tournament_category'] = df['tournament'].apply(categorize_tournament)
    # Remove rows with missing target values
    df = df.dropna(subset=['home_score', 'away_score'])
    return df


def build_preprocessor():
    numeric_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
    ])
    return ColumnTransformer(transformers=[
        ('num', numeric_pipeline, NUMERIC_FEATURES),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL_FEATURES),
    ])


def evaluate(name: str, y_true, y_pred_home, y_pred_away):
    mae_h = mean_absolute_error(y_true['home_score'], y_pred_home)
    mae_a = mean_absolute_error(y_true['away_score'], y_pred_away)
    rmse_h = mean_squared_error(y_true['home_score'], y_pred_home) ** 0.5
    rmse_a = mean_squared_error(y_true['away_score'], y_pred_away) ** 0.5

    # Outcome accuracy
    pred_outcome = np.sign(y_pred_home - y_pred_away)
    true_outcome = np.sign(y_true['home_score'].values - y_true['away_score'].values)
    accuracy = (pred_outcome == true_outcome).mean()

    print(f"\n[{name}]")
    print(f"  Home  MAE={mae_h:.3f}  RMSE={rmse_h:.3f}")
    print(f"  Away  MAE={mae_a:.3f}  RMSE={rmse_a:.3f}")
    print(f"  Outcome accuracy: {accuracy:.3f}")


def train():
    print("Loading training data...")
    df = load_and_prepare()
    print(f"  Matches loaded: {len(df):,} (from {df['date'].dt.year.min()})")

    # Temporal split
    train_df = df[df['date'].dt.year <= 2018]
    val_df   = df[(df['date'].dt.year > 2018) & (df['date'].dt.year <= 2022)]
    test_df  = df[df['date'].dt.year > 2022]

    print(f"  Train: {len(train_df):,} | Val: {len(val_df):,} | Test: {len(test_df):,}")

    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    X_train = train_df[features]
    X_val   = val_df[features]
    X_test  = test_df[features]

    y_train = train_df[['home_score', 'away_score']]
    y_val   = val_df[['home_score', 'away_score']]
    y_test  = test_df[['home_score', 'away_score']]

    preprocessor = build_preprocessor()

    # --- Gradient Boosting (primary model) ---
    print("\nTraining Gradient Boosting models...")
    gb_home = Pipeline([
        ('pre', preprocessor),
        ('model', GradientBoostingRegressor(
            n_estimators=300, learning_rate=0.05, max_depth=4,
            subsample=0.8, random_state=42
        ))
    ])
    gb_away = Pipeline([
        ('pre', build_preprocessor()),
        ('model', GradientBoostingRegressor(
            n_estimators=300, learning_rate=0.05, max_depth=4,
            subsample=0.8, random_state=42
        ))
    ])
    gb_home.fit(X_train, y_train['home_score'])
    gb_away.fit(X_train, y_train['away_score'])

    evaluate('GB - Validation', y_val,
             gb_home.predict(X_val), gb_away.predict(X_val))
    evaluate('GB - Test', y_test,
             gb_home.predict(X_test), gb_away.predict(X_test))

    # --- Random Forest (backup / ensemble member) ---
    print("\nTraining Random Forest models...")
    rf_home = Pipeline([
        ('pre', build_preprocessor()),
        ('model', RandomForestRegressor(
            n_estimators=300, max_depth=8, min_samples_leaf=10,
            random_state=42, n_jobs=-1
        ))
    ])
    rf_away = Pipeline([
        ('pre', build_preprocessor()),
        ('model', RandomForestRegressor(
            n_estimators=300, max_depth=8, min_samples_leaf=10,
            random_state=42, n_jobs=-1
        ))
    ])
    rf_home.fit(X_train, y_train['home_score'])
    rf_away.fit(X_train, y_train['away_score'])

    evaluate('RF - Validation', y_val,
             rf_home.predict(X_val), rf_away.predict(X_val))
    evaluate('RF - Test', y_test,
             rf_home.predict(X_test), rf_away.predict(X_test))

    # Save all models
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(gb_home, MODELS_DIR / 'gb_home.joblib')
    joblib.dump(gb_away, MODELS_DIR / 'gb_away.joblib')
    joblib.dump(rf_home, MODELS_DIR / 'rf_home.joblib')
    joblib.dump(rf_away, MODELS_DIR / 'rf_away.joblib')

    # Save tournament map for use in predict.py
    joblib.dump(TOURNAMENT_MAP, MODELS_DIR / 'tournament_map.joblib')

    print(f"\n✅ Models saved to {MODELS_DIR}")


if __name__ == '__main__':
    train()
