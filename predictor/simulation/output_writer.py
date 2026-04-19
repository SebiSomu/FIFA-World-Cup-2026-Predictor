"""Persist tournament simulation results under predictor/output/predictions/."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

# predictor/simulation/ -> predictor/
PREDICTOR_ROOT = Path(__file__).resolve().parent.parent


def default_predictions_dir() -> Path:
    return PREDICTOR_ROOT / "output" / "predictions"


def save_tournament_outputs(
    tournament_results: Dict[str, Any],
    output_dir: Optional[Path] = None,
    verbose: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Write wc2026_predictions.csv, group_standings.csv, knockout_bracket.csv.
    Paths are anchored to the predictor package unless output_dir is given.
    """
    out = output_dir if output_dir is not None else default_predictions_dir()
    out.mkdir(parents=True, exist_ok=True)

    all_results = tournament_results["all_results"]
    df_matches = pd.DataFrame(all_results)
    matches_path = out / "wc2026_predictions.csv"
    df_matches.to_csv(matches_path, index=False)
    if verbose:
        print(f"  Match predictions -> {matches_path} ({len(df_matches)} matches)")

    standings_rows = []
    for group, ranked in tournament_results["group_standings"].items():
        for pos, record in enumerate(ranked, 1):
            row = record.as_dict()
            row["position"] = pos
            standings_rows.append(row)
    df_standings = pd.DataFrame(standings_rows)
    standings_path = out / "group_standings.csv"
    df_standings.to_csv(standings_path, index=False)
    if verbose:
        print(f"  Group standings -> {standings_path}")

    ko_results = [r for r in all_results if r["stage"] != "Group Stage"]
    df_ko = pd.DataFrame(ko_results)
    ko_path = out / "knockout_bracket.csv"
    df_ko.to_csv(ko_path, index=False)
    if verbose:
        print(f"  Knockout bracket -> {ko_path}")

    return df_matches, df_standings
