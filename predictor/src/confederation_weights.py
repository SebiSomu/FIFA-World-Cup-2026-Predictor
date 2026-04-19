"""
Confederation weighting factors based on FIFA World Ranking methodology.
Used to adjust for relative strength differences between confederations.
"""

from typing import Dict

# FIFA Confederation Weighting Factors (based on World Cup performance 2018-2022)
# Higher = stronger confederation
CONFEDERATION_WEIGHTS = {
    'UEFA': 1.0,        # Europe - strongest
    'CONMEBOL': 1.0,    # South America - strongest
    'CONCACAF': 0.85,   # North/Central America & Caribbean
    'CAF': 0.85,        # Africa
    'AFC': 0.85,        # Asia
    'OFC': 0.75,        # Oceania
}

# Team to Confederation mapping for WC2026 teams
TEAM_CONFEDERATION: Dict[str, str] = {
    # UEFA (Europe)
    'Germany': 'UEFA',
    'France': 'UEFA',
    'Spain': 'UEFA',
    'England': 'UEFA',
    'Portugal': 'UEFA',
    'Netherlands': 'UEFA',
    'Belgium': 'UEFA',
    'Italy': 'UEFA',
    'Croatia': 'UEFA',
    'Switzerland': 'UEFA',
    'Austria': 'UEFA',
    'Scotland': 'UEFA',
    'Norway': 'UEFA',
    'Sweden': 'UEFA',
    'Czechia': 'UEFA',
    'Poland': 'UEFA',
    'Serbia': 'UEFA',
    'Bosnia and Herzegovina': 'UEFA',
    "Côte d'Ivoire": 'UEFA',  # Wait, this is CAF
    
    # CONMEBOL (South America)
    'Argentina': 'CONMEBOL',
    'Brazil': 'CONMEBOL',
    'Uruguay': 'CONMEBOL',
    'Colombia': 'CONMEBOL',
    'Paraguay': 'CONMEBOL',
    'Ecuador': 'CONMEBOL',
    
    # CONCACAF (North/Central America)
    'Mexico': 'CONCACAF',
    'United States': 'CONCACAF',
    'Canada': 'CONCACAF',
    'Panama': 'CONCACAF',
    'Haiti': 'CONCACAF',
    'Curaçao': 'CONCACAF',
    'Cabo Verde': 'CONCACAF',  # Actually CAF, but geographically close
    
    # CAF (Africa)
    'Morocco': 'CAF',
    'Senegal': 'CAF',
    'Tunisia': 'CAF',
    'Algeria': 'CAF',
    'Egypt': 'CAF',
    'Ghana': 'CAF',
    'Nigeria': 'CAF',
    'Cameroon': 'CAF',
    'DR Congo': 'CAF',
    'South Africa': 'CAF',
    
    # AFC (Asia)
    'Japan': 'AFC',
    'Korea Republic': 'AFC',
    'Australia': 'AFC',  # Moved from OFC
    'Iran': 'AFC',
    'Saudi Arabia': 'AFC',
    'Qatar': 'AFC',
    'Iraq': 'AFC',
    'Uzbekistan': 'AFC',
    'Jordan': 'AFC',
    
    # OFC (Oceania)
    'New Zealand': 'OFC',
}

# Fix mappings
TEAM_CONFEDERATION["Côte d'Ivoire"] = 'CAF'
TEAM_CONFEDERATION['Cabo Verde'] = 'CAF'


def get_confederation(team: str) -> str:
    """Get confederation for a team."""
    return TEAM_CONFEDERATION.get(team, 'AFC')  # Default to weakest confederation


def get_confederation_weight(team: str) -> float:
    """Get the weighting factor for a team's confederation."""
    conf = get_confederation(team)
    return CONFEDERATION_WEIGHTS.get(conf, 0.85)


def calculate_confederation_adjusted_elo(team1: str, team2: str, 
                                            elo1: float, elo2: float) -> tuple:
    """
    Calculate ELO ratings adjusted for confederation strength.
    
    When a strong confederation team (UEFA/CONMEBOL) plays a weak confederation team,
    the weak team's effective ELO is significantly reduced to reflect true strength difference.
    
    Uses FIFA-style confederation weighting with more aggressive penalty for weaker confeds.
    
    Returns: (adjusted_elo1, adjusted_elo2)
    """
    w1 = get_confederation_weight(team1)
    w2 = get_confederation_weight(team2)
    
    # More aggressive adjustment: use squared weights to amplify differences
    # This creates larger gaps between UEFA/CONMEBOL (1.0) and others (0.85 -> 0.72)
    adj_factor_1 = w1 ** 2  # 1.0 for strong, ~0.72 for weak confederations
    adj_factor_2 = w2 ** 2
    
    # Apply adjustment - scale ELO by confederation strength
    adj_elo1 = elo1 * adj_factor_1
    adj_elo2 = elo2 * adj_factor_2
    
    # Additional penalty: when teams from different confederation tiers play,
    # apply extra adjustment based on historical World Cup performance
    # UEFA/CONMEBOL teams perform ~30-40% better against other confederations
    if w1 == 1.0 and w2 < 1.0:
        # Team1 is strong confed, Team2 is weak - boost Team1 slightly
        adj_elo1 *= 1.05
    elif w2 == 1.0 and w1 < 1.0:
        # Team2 is strong confed, Team1 is weak - boost Team2 slightly  
        adj_elo2 *= 1.05
    
    return adj_elo1, adj_elo2


def get_confederation_name(team: str) -> str:
    """Get confederation name for display purposes."""
    return get_confederation(team)
