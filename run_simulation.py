import sys
from pathlib import Path

# Anchor imports to this repo (works regardless of cwd)
_REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_REPO_ROOT / "predictor"))

import pandas as pd

from simulation.output_writer import default_predictions_dir, save_tournament_outputs
from simulation.tournament import run_tournament

print("WC 2026 SIMULATION")
print("=" * 60)

results = run_tournament()

save_tournament_outputs(results, verbose=True)
out_dir = default_predictions_dir()
print(f"\nOutput saved in: {out_dir}")

print("\n" + "=" * 60)
print("SIMULATION COMPLETE!")
print(f"\nChampion: {results['champion']}")
print(f"Runner-up: {results['runner_up']}")
print(f"Third place: {results['third_place']}")