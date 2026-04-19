"""
Print full group standings + all group matches + knockout by round
from predictor/output/predictions/*.csv (run run_simulation.py first).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

_REPO = Path(__file__).resolve().parent
_OUT = _REPO / "predictor" / "output" / "predictions"


def main() -> None:
    pred_path = _OUT / "wc2026_predictions.csv"
    std_path = _OUT / "group_standings.csv"
    if not pred_path.exists():
        raise SystemExit(f"Missing {pred_path} — run: python run_simulation.py")

    df = pd.read_csv(pred_path)
    std = pd.read_csv(std_path)

    lines: list[str] = []
    w = lines.append

    w("=" * 72)
    w("  FIFA WORLD CUP 2026 - FULL SIMULATION REPORT")
    w("=" * 72)

    w("\n--- GROUP STANDINGS ---\n")
    for g in sorted(std["group"].unique()):
        w(f"  Group {g}")
        sub = std[std["group"] == g].sort_values("position")
        for _, r in sub.iterrows():
            w(
                f"    {int(r['position'])}. {r['team']:<28} "
                f"Pts {int(r['points']):>2}  "
                f"Games {int(r['played'])}  "
                f"W/D/L {int(r['wins'])}/{int(r['draws'])}/{int(r['losses'])}  "
                f"GF {int(r['goals_for']):>2} GA {int(r['goals_against']):>2}  "
                f"GD {int(r['goal_diff']):+d}"
            )
        w("")

    w("\n--- GROUP STAGE (72 matches) ---\n")
    gs = df[df["stage"] == "Group Stage"].copy()
    for g in sorted(gs["group"].dropna().unique()):
        w(f"  Group {g}")
        for _, r in gs[gs["group"] == g].iterrows():
            scr = f"{int(r['predicted_home_score'])}-{int(r['predicted_away_score'])}"
            w(
                f"    {r['home_team']:<26} {scr:^5} {r['away_team']:<26}  "
                f"(1X2 {r['prob_home_win']:.2f} / {r['prob_draw']:.2f} / {r['prob_away_win']:.2f})"
            )
        w("")

    stage_order = [
        "Round of 32",
        "Round of 16",
        "Quarter-Final",
        "Semi-Final",
        "Third Place",
        "Final",
    ]
    w("\n--- KNOCKOUT ---\n")
    for stage in stage_order:
        ko = df[df["stage"] == stage]
        if ko.empty:
            continue
        if "fifa_match_number" in ko.columns:
            ko = ko.sort_values("fifa_match_number", kind="stable")
        w(f"  {stage}")
        for _, r in ko.iterrows():
            det = r.get("score_detail")
            if pd.isna(det) or not str(det).strip():
                det = f"{int(r['predicted_home_score'])}-{int(r['predicted_away_score'])}"
            w(
                f"    {r['match_id']}: {r['home_team']:<22} vs {r['away_team']:<22}  "
                f"{det}  -> {r['winner']}"
            )
        w("")

    fin = df[df["stage"] == "Final"]
    tp = df[df["stage"] == "Third Place"]
    if not fin.empty and not tp.empty:
        w("--- PODIUM (from this run) ---\n")
        w(f"  Champion:   {fin.iloc[0]['winner']}")
        r = fin.iloc[0]
        loser = r["away_team"] if r["winner"] == r["home_team"] else r["home_team"]
        w(f"  Runner-up:  {loser}")
        w(f"  Third place: {tp.iloc[0]['winner']}\n")

    w("=" * 72)
    text = "\n".join(lines)
    print(text)
    out_txt = _OUT / "full_simulation_report.txt"
    out_txt.write_text(text, encoding="utf-8")
    print(f"\n(Saved copy to {out_txt})")


if __name__ == "__main__":
    main()
