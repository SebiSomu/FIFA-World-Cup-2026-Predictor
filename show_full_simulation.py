import sys
sys.path.append('predictor')
from simulation.tournament import run_tournament

# Run simulation
results = run_tournament()

# Show group standings
print("\n" + "="*60)
print("  FIFA WORLD CUP 2026 - GROUP STANDINGS")
print("="*60)

group_standings = results['group_standings']
for group_name in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']:
    print(f"\nGroup {group_name}:")
    teams = group_standings[group_name]
    for i, team in enumerate(teams):
        status = "Q" if i < 2 else ("q" if i == 2 else " ")
        print(f"  {status} {i+1}. {team.team:25s} Pts:{team.points} GD:{team.goal_diff:+d} GF:{team.goals_for}")

# Show best third-place teams
print("\n" + "="*60)
print("  BEST 3RD-PLACE TEAMS QUALIFYING")
print("="*60)
for team in results['best_thirds']:
    print(f"  {team.team} (Group {team.group}) - Pts:{team.points} GD:{team.goal_diff:+d}")

# Show knockout bracket
print("\n" + "="*60)
print("  KNOCKOUT STAGE - ALL MATCHES")
print("="*60)

ko_results = [r for r in results['all_results'] if r['stage'] != 'Group Stage']
current_stage = None
for match in ko_results:
    if match['stage'] != current_stage:
        current_stage = match['stage']
        print(f"\n{current_stage}:")
    score = f"{match['predicted_home_score']}-{match['predicted_away_score']}"
    if 'score_detail' in match and match['score_detail']:
        score = match['score_detail']
    print(f"  {match['home_team']:20s} vs {match['away_team']:20s} : {score:20s} -> {match['winner']}")

# Show final podium
print("\n" + "="*60)
print("  FINAL PODIUM")
print("="*60)
print(f"  CHAMPION:  {results['champion']}")
print(f"  RUNNER-UP: {results['runner_up']}")
print(f"  3RD PLACE:  {results['third_place']}")
print("="*60)
