"""Test draw generation with the updated predictor"""
import sys
sys.path.append('predictor')

import numpy as np
from models.advanced_predictor import AdvancedMLPredictor

# Set seed for reproducibility
np.random.seed(42)

predictor = AdvancedMLPredictor()

print("=" * 60)
print("TEST Egaluri cu Predictor Avansat")
print("=" * 60)

# Test matches that should produce draws (close teams)
test_matches = [
    ('Netherlands', 'Japan'),      # Close match - should draw often
    ('Portugal', 'Colombia'),       # Close match  
    ('Morocco', 'Scotland'),        # Medium difference
    ('Croatia', 'Panama'),          # Medium difference
    ('England', 'Croatia'),         # Close match
    ('Senegal', 'Australia'),      # Close match
    ('Belgium', 'Iran'),          # Medium difference
    ('Spain', 'Uruguay'),         # Top teams close
]

print("\nMeciuri test (10 rulari fiecare):")
print("-" * 60)

draw_count = 0
total = 0

for home, away in test_matches:
    draws_in_10 = 0
    results = []
    
    for i in range(10):  # Run 10 times
        np.random.seed(42 + i)  # Different seed each time
        result = predictor.predict_match(home, away)
        score = f"{result['predicted_home']}-{result['predicted_away']}"
        results.append(score)
        if result['predicted_home'] == result['predicted_away']:
            draws_in_10 += 1
            draw_count += 1
        total += 1
    
    unique_results = list(set(results))
    print(f"\n{home} vs {away}:")
    print(f"  Rezultate: {', '.join(unique_results)}")
    print(f"  Egaluri: {draws_in_10}/10")

print("\n" + "=" * 60)
print(f"TOTAL EGALURI: {draw_count}/{total} ({draw_count/total*100:.1f}%)")
print("=" * 60)
print("\nTarget realist: ~20-25% egaluri")
