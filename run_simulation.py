import sys
from pathlib import Path

# Anchor imports to this repo (works regardless of cwd)
_REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_REPO_ROOT / "predictor"))

import pandas as pd

from simulation.output_writer import default_predictions_dir, save_tournament_outputs
from simulation.tournament import run_tournament

print("Rulare simulare WC2026 cu predictor avansat (inclusiv egaluri)...")
print("=" * 60)

results = run_tournament()

save_tournament_outputs(results, verbose=True)
out_dir = default_predictions_dir()
print(f"\nOutput salvat in: {out_dir}")

print("\n" + "=" * 60)
print("SIMULARE COMPLETA!")
print(f"\nCampioana: {results['champion']}")
print(f"Finalista: {results['runner_up']}")
print(f"Locul 3: {results['third_place']}")

# Draws from the same run (in-memory; matches freshly written CSV)
df = pd.DataFrame(results["all_results"])
group_matches = df[df["stage"] == "Group Stage"]
draws = group_matches[
    group_matches["predicted_home_score"] == group_matches["predicted_away_score"]
]
n_group = len(group_matches)
n_draws = len(draws)
pct = (n_draws / n_group * 100) if n_group else 0.0
print(f"\nEgaluri in grupe: {n_draws} din {n_group} meciuri ({pct:.1f}%)")
if n_draws > 0:
    print("\nMeciuri la egalitate:")
    for _, row in draws.iterrows():
        print(
            f"  {row['home_team']} {int(row['predicted_home_score'])}-"
            f"{int(row['predicted_away_score'])} {row['away_team']}"
        )
