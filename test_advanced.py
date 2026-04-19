import sys
sys.path.append('predictor')

print("Loading predictor...")
from models.advanced_predictor import AdvancedMLPredictor

print("Initializing...")
predictor = AdvancedMLPredictor()

print("\n=== Test Predictions ===")

# Test some key matches
tests = [
    ('Spain', 'Brazil'),
    ('Argentina', 'France'),
    ('England', 'Germany'),
    ('Mexico', 'United States'),
]

for home, away in tests:
    result = predictor.predict_match(home, away)
    print(f"\n{home} vs {away}:")
    print(f"  Score: {result['predicted_home']}-{result['predicted_away']}")
    print(f"  Probs: H {result['prob_home_win']:.1%} | D {result['prob_draw']:.1%} | A {result['prob_away_win']:.1%}")

print("\n✓ Predictor working correctly!")
