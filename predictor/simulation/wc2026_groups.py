"""
WC2026 Groups Setup.
Defines the 12 groups and group-stage match schedule for the 2026 World Cup.
48 teams, 12 groups of 4, 6 matches per group = 72 group stage matches total.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple

# ── Qualified teams by group ──────────────────────────────────────────────────
# Source: FIFA official draw (December 2024, Miami)
GROUPS: Dict[str, List[str]] = {
    'A': ['Mexico', 'South Africa', 'Korea Republic', 'Czechia'],
    'B': ['Canada', 'Bosnia and Herzegovina', 'Qatar', 'Switzerland'],
    'C': ['Brazil', 'Morocco', 'Haiti', 'Scotland'],
    'D': ['United States', 'Paraguay', 'Australia', 'Türkiye'],
    'E': ['Germany', 'Curaçao', "Côte d'Ivoire", 'Ecuador'],
    'F': ['Netherlands', 'Japan', 'Sweden', 'Tunisia'],
    'G': ['Belgium', 'Egypt', 'Iran', 'New Zealand'],
    'H': ['Spain', 'Cabo Verde', 'Saudi Arabia', 'Uruguay'],
    'I': ['France', 'Senegal', 'Norway', 'Iraq'],
    'J': ['Argentina', 'Algeria', 'Austria', 'Jordan'],
    'K': ['Portugal', 'DR Congo', 'Uzbekistan', 'Colombia'],
    'L': ['England', 'Croatia', 'Ghana', 'Panama'],
}

# Each team in a group plays the other 3 teams once.
# We list the 6 matches per group as (home, away) pairs.
# In WC group stage, venue is neutral — home/away is just order for display.
def get_group_matches(group: str) -> List[Tuple[str, str]]:
    """Return the 6 match pairs for a given group."""
    teams = GROUPS[group]
    matches = []
    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            matches.append((teams[i], teams[j]))
    return matches


def get_all_group_matches() -> List[Dict]:
    """Return all 72 group stage matches as list of dicts."""
    all_matches = []
    match_id = 1
    for group, teams in GROUPS.items():
        for home, away in get_group_matches(group):
            all_matches.append({
                'match_id': f'G{match_id:03d}',
                'stage': 'Group Stage',
                'group': group,
                'home_team': home,
                'away_team': away,
            })
            match_id += 1
    return all_matches


@dataclass
class TeamRecord:
    """Running tally for a team during the group stage."""
    team: str
    group: str
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0

    @property
    def goal_diff(self) -> int:
        return self.goals_for - self.goals_against

    def update(self, goals_scored: int, goals_conceded: int):
        self.played += 1
        self.goals_for += goals_scored
        self.goals_against += goals_conceded
        if goals_scored > goals_conceded:
            self.wins += 1
            self.points += 3
        elif goals_scored == goals_conceded:
            self.draws += 1
            self.points += 1
        else:
            self.losses += 1

    def as_dict(self) -> Dict:
        return {
            'group': self.group,
            'team': self.team,
            'played': self.played,
            'wins': self.wins,
            'draws': self.draws,
            'losses': self.losses,
            'goals_for': self.goals_for,
            'goals_against': self.goals_against,
            'goal_diff': self.goal_diff,
            'points': self.points,
        }


def init_group_records() -> Dict[str, Dict[str, TeamRecord]]:
    """Initialize empty TeamRecord for every team in every group."""
    records: Dict[str, Dict[str, TeamRecord]] = {}
    for group, teams in GROUPS.items():
        records[group] = {team: TeamRecord(team=team, group=group) for team in teams}
    return records


def rank_group(records: Dict[str, TeamRecord]) -> List[TeamRecord]:
    """
    Rank teams within a group by:
      1. Points  2. Goal diff  3. Goals for  4. Name (alphabetical tiebreak)
    """
    return sorted(
        records.values(),
        key=lambda r: (r.points, r.goal_diff, r.goals_for, r.team),
        reverse=True,
    )


def determine_qualifiers(
    group_standings: Dict[str, List[TeamRecord]]
) -> Tuple[Dict[str, str], List[TeamRecord]]:
    """
    Apply WC2026 qualification rules:
      - Top 2 from each group (24 teams) qualify directly.
      - Best 8 third-place teams also qualify (8 teams).
    Returns:
      qualified_by_group: {group: [1st, 2nd]}
      best_thirds: sorted list of 8 best 3rd-place teams
    """
    qualified_by_group: Dict[str, Tuple[TeamRecord, TeamRecord]] = {}
    third_place_teams: List[TeamRecord] = []

    for group, ranked in group_standings.items():
        qualified_by_group[group] = (ranked[0], ranked[1])
        if len(ranked) >= 3:
            third_place_teams.append(ranked[2])

    # Rank third-place teams (same criteria as group stage)
    third_place_teams.sort(
        key=lambda r: (r.points, r.goal_diff, r.goals_for, r.team),
        reverse=True,
    )
    best_thirds = third_place_teams[:8]

    return qualified_by_group, best_thirds


if __name__ == '__main__':
    print("WC2026 Groups:")
    for group, teams in GROUPS.items():
        print(f"  Group {group}: {', '.join(teams)}")

    matches = get_all_group_matches()
    print(f"\nTotal group stage matches: {len(matches)}")
