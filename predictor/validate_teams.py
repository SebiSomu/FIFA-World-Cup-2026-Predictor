"""
Quick validation script for WC2026 teams.
"""
import pandas as pd
from pathlib import Path

# Load data relative to script location
script_dir = Path(__file__).parent
data_dir = script_dir / 'data'

# Check if data directory exists, if not try looking in current directory
if not data_dir.exists():
    data_dir = Path('data')

results = pd.read_csv(data_dir / 'results.csv')
wc2026 = pd.read_csv(data_dir / 'wc2026_groups.csv')
former = pd.read_csv(data_dir / 'former_names.csv')

print("=" * 60)
print("WC2026 TEAM VALIDATION")
print("=" * 60)

# Get unique teams from results
home_teams = set(results['home_team'].unique())
away_teams = set(results['away_team'].unique())
all_historical = home_teams | away_teams
print(f"\nHistorical teams in dataset: {len(all_historical)}")

# Build name mapping
name_map = {}
for _, row in former.iterrows():
    name_map[row['former']] = row['current']

# Add manual mappings
manual = {
    'USA': 'United States',
    'Korea Republic': 'South Korea',
    'Czechia': 'Czech Republic',
    'Türkiye': 'Turkey',
}
name_map.update(manual)

# Add reverse mappings for WC2026 names
reverse_mappings = {
    'Cabo Verde': 'Cape Verde',    # WC2026 name -> historical
    'Congo DR': 'DR Congo',        # WC2026 name -> historical
    "Côte d'Ivoire": 'Ivory Coast',  # WC2026 name -> historical
}

def normalize(name):
    # First check reverse mappings (for WC2026 names)
    if name in reverse_mappings:
        return reverse_mappings[name]
    # Then check standard mappings
    return name_map.get(name, name)

# Get WC2026 teams
wc_teams = set(wc2026['team'].unique())
print(f"WC2026 teams: {len(wc_teams)}")

# Normalize and check
norm_teams = {normalize(t) for t in wc_teams}
found = norm_teams & all_historical
missing = norm_teams - all_historical

print(f"\nFound in historical data: {len(found)}/48 ({len(found)/48*100:.1f}%)")
print(f"Missing: {len(missing)}")

if missing:
    print("\nMissing teams:")
    for t in sorted(missing):
        print(f"  - {t}")

# Show sample matches for a few teams
print("\n" + "=" * 60)
print("SAMPLE DATA CHECK")
print("=" * 60)

sample_teams = ['Brazil', 'Argentina', 'Germany', 'Spain', 'France']
for team in sample_teams:
    team_matches = results[(results['home_team'] == team) | (results['away_team'] == team)]
    print(f"\n{team}: {len(team_matches)} matches")
    if len(team_matches) > 0:
        print(f"  First: {team_matches.iloc[0]['date']}")
        print(f"  Last: {team_matches.iloc[-1]['date']}")

print("\n" + "=" * 60)
print("VALIDATION COMPLETE")
print("=" * 60)
