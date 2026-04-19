"""
FIFA World Cup 2026 knockout bracket — structure from official diagram / regulations.

Round of 32: matches 73–88 (fixed pairings).
Round of 16: 89–96 pair winners of specific R32 games.
Third place: 103 (losers of semis 101–102). Final: 104.

Third-place teams are assigned to the eight \"3…\" slots with a small DFS so each
qualifying third is used exactly once and only in a slot whose allowed group set
contains its group letter (same feasibility idea as FIFA Annex C).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from simulation.wc2026_groups import TeamRecord

# Order = FIFA match numbers 73 … 88
ROUND_OF_32: List[Tuple[str, str, int]] = [
    ("2A", "2B", 73),
    ("1E", "3ABCDF", 74),
    ("1F", "2C", 75),
    ("1C", "2F", 76),
    ("1I", "3CDFGH", 77),
    ("2E", "2I", 78),
    ("1A", "3CEFHI", 79),
    ("1L", "3EHIJK", 80),
    ("1D", "3BEFIJ", 81),
    ("1G", "3AEHIJ", 82),
    ("2K", "2L", 83),
    ("1H", "2J", 84),
    ("1B", "3EFGIJ", 85),
    ("1J", "2H", 86),
    ("1K", "3DEIJL", 87),
    ("2D", "2G", 88),
]

# Order = FIFA match numbers 89 … 96
ROUND_OF_16: List[Tuple[str, str, int]] = [
    ("W74", "W77", 89),
    ("W73", "W75", 90),
    ("W76", "W78", 91),
    ("W79", "W80", 92),
    ("W83", "W84", 93),
    ("W81", "W82", 94),
    ("W86", "W88", 95),
    ("W85", "W87", 96),
]

QUARTER_FINALS: List[Tuple[str, str, int]] = [
    ("W89", "W90", 97),
    ("W93", "W94", 98),
    ("W91", "W92", 99),
    ("W95", "W96", 100),
]

SEMI_FINALS: List[Tuple[str, str, int]] = [
    ("W97", "W98", 101),
    ("W99", "W100", 102),
]

THIRD_PLACE_MATCH = 103
FINAL_MATCH = 104


def _parse_w(code: str) -> int:
    if not code.startswith("W"):
        raise ValueError(f"Expected W-prefixed winner code, got {code!r}")
    return int(code[1:])


def _third_allowed_letters(code: str) -> frozenset:
    if not code.startswith("3"):
        raise ValueError(code)
    return frozenset(code[1:])


def _assign_third_place_teams(
    third_by_group: Dict[str, str],
) -> Optional[Dict[int, str]]:
    """
    Map FIFA R32 match number -> third-place team name for that slot.
    `third_by_group`: group letter -> team name (exactly 8 groups).
    """
    slots: List[Tuple[int, frozenset]] = []
    for home_c, away_c, mnum in ROUND_OF_32:
        if away_c.startswith("3"):
            slots.append((mnum, _third_allowed_letters(away_c)))
        elif home_c.startswith("3"):
            slots.append((mnum, _third_allowed_letters(home_c)))
    slots.sort(key=lambda x: x[0])

    groups = list(third_by_group.keys())

    def dfs(i: int, used: frozenset, assign: Dict[int, str]) -> Optional[Dict[int, str]]:
        if i >= len(slots):
            return assign
        mnum, allowed = slots[i]
        for g in groups:
            if g in used or g not in allowed:
                continue
            sub = dfs(i + 1, used | frozenset([g]), {**assign, mnum: third_by_group[g]})
            if sub is not None:
                return sub
        return None

    return dfs(0, frozenset(), {})


def _resolve_slot(
    code: str,
    match_num: int,
    winners_1st: Dict[str, str],
    runners_2nd: Dict[str, str],
    third_in_match: Dict[int, str],
) -> str:
    if code.startswith("1"):
        return winners_1st[code[1]]
    if code.startswith("2"):
        return runners_2nd[code[1]]
    if code.startswith("3"):
        return third_in_match[match_num]
    raise ValueError(f"Unknown slot code {code!r}")


def build_round_of_32_fixtures(
    qualified_by_group: Dict[str, Tuple[TeamRecord, TeamRecord]],
    best_thirds: List[TeamRecord],
) -> List[Tuple[str, str, int]]:
    """
    Return list of (home_team, away_team, fifa_match_number) for matches 73–88.
    """
    winners_1st = {g: qualified_by_group[g][0].team for g in qualified_by_group}
    runners_2nd = {g: qualified_by_group[g][1].team for g in qualified_by_group}
    third_by_group = {t.group: t.team for t in best_thirds}

    third_in_match = _assign_third_place_teams(third_by_group)
    if third_in_match is None:
        raise RuntimeError(
            "Could not assign 8 third-place teams to FIFA bracket slots; "
            "check qualification / group letters."
        )

    fixtures: List[Tuple[str, str, int]] = []
    for home_c, away_c, mnum in ROUND_OF_32:
        home = _resolve_slot(home_c, mnum, winners_1st, runners_2nd, third_in_match)
        away = _resolve_slot(away_c, mnum, winners_1st, runners_2nd, third_in_match)
        fixtures.append((home, away, mnum))
    return fixtures


def build_round_of_16_fixtures(winners_r32: Dict[int, str]) -> List[Tuple[str, str, int]]:
    out: List[Tuple[str, str, int]] = []
    for c1, c2, mnum in ROUND_OF_16:
        t1 = winners_r32[_parse_w(c1)]
        t2 = winners_r32[_parse_w(c2)]
        out.append((t1, t2, mnum))
    return out


def build_quarter_final_fixtures(winners_r16: Dict[int, str]) -> List[Tuple[str, str, int]]:
    out: List[Tuple[str, str, int]] = []
    for c1, c2, mnum in QUARTER_FINALS:
        out.append((winners_r16[_parse_w(c1)], winners_r16[_parse_w(c2)], mnum))
    return out


def build_semi_final_fixtures(winners_qf: Dict[int, str]) -> List[Tuple[str, str, int]]:
    out: List[Tuple[str, str, int]] = []
    for c1, c2, mnum in SEMI_FINALS:
        out.append((winners_qf[_parse_w(c1)], winners_qf[_parse_w(c2)], mnum))
    return out


def loser_from_result(res: Dict) -> str:
    if res["winner"] == res["home_team"]:
        return res["away_team"]
    return res["home_team"]


def build_third_place_fixture(
    semi_results_by_num: Dict[int, Dict],
) -> List[Tuple[str, str, int]]:
    r101 = semi_results_by_num[101]
    r102 = semi_results_by_num[102]
    return [(loser_from_result(r101), loser_from_result(r102), THIRD_PLACE_MATCH)]


def build_final_fixture(
    semi_results_by_num: Dict[int, Dict],
) -> List[Tuple[str, str, int]]:
    return [
        (
            semi_results_by_num[101]["winner"],
            semi_results_by_num[102]["winner"],
            FINAL_MATCH,
        )
    ]


if __name__ == "__main__":
    print("R32 (FIFA match numbers):")
    for h, a, n in ROUND_OF_32:
        print(f"  {n}: {h} vs {a}")
    print("\nR16:")
    for h, a, n in ROUND_OF_16:
        print(f"  {n}: {h} vs {a}")
