import math
from typing import Dict, Tuple

class EloSystem:
    """
    Implements a custom ELO rating system tailored for international football.
    Includes Margin of Victory (MoV) multiplier and Clean Sheet bonuses.
    """
    
    def __init__(self, initial_rating: float = 1500.0, home_advantage: float = 100.0):
        self.initial_rating = initial_rating
        self.home_advantage = home_advantage
        # Ratings dictionary: {team_name: current_rating}
        self.ratings: Dict[str, float] = {}
        
        # K-Factors based on tournament importance
        self.k_factors = {
            'FIFA World Cup': 60,
            'Confederations Cup': 50,
            'UEFA Euro': 50,
            'Copa América': 50,
            'African Cup of Nations': 50,
            'AFC Asian Cup': 50,
            'CONCACAF Championship': 50,
            'Oceania Nations Cup': 50,
            'FIFA World Cup qualification': 40,
            'UEFA Euro qualification': 40,
            'Friendly': 20,
            'Default': 30
        }

    def get_rating(self, team: str) -> float:
        """Get current rating for a team, initializing it if necessary."""
        if team not in self.ratings:
            self.ratings[team] = self.initial_rating
        return self.ratings[team]

    def get_k_factor(self, tournament: str) -> int:
        """Get K-factor for a given tournament type."""
        # Check for partial matches (e.g., 'qualification' or 'qualification')
        for key, value in self.k_factors.items():
            if key in tournament:
                return value
        return self.k_factors['Default']

    def calculate_expected_outcome(self, rating_a: float, rating_b: float) -> float:
        """Calculate the expected outcome for team A against team B."""
        return 1 / (10 ** (-(rating_a - rating_b) / 400) + 1)

    def get_mov_multiplier(self, home_score: int, away_score: int) -> float:
        """Calculate Margin of Victory multiplier."""
        diff = abs(home_score - away_score)
        if diff <= 1:
            return 1.0
        elif diff == 2:
            return 1.5
        else:
            return (11 + diff) / 8.0

    def update_ratings(self, home_team: str, away_team: str, 
                       home_score: int, away_score: int, 
                       tournament: str, is_neutral: bool) -> Tuple[float, float]:
        """
        Calculates and updates ratings for both teams after a match.
        Returns the (home_change, away_change).
        """
        r_home = self.get_rating(home_team)
        r_away = self.get_rating(away_team)
        
        # Apply home advantage adjustment if not neutral
        adjustment = self.home_advantage if not is_neutral else 0
        
        # Expected outcomes
        e_home = self.calculate_expected_outcome(r_home + adjustment, r_away)
        e_away = 1 - e_home
        
        # Actual outcomes
        if home_score > away_score:
            w_home, w_away = 1.0, 0.0
        elif home_score < away_score:
            w_home, w_away = 0.0, 1.0
        else:
            w_home, w_away = 0.5, 0.5
            
        # K-factor and Multipliers
        k = self.get_k_factor(tournament)
        mov = self.get_mov_multiplier(home_score, away_score)
        
        # Clean Sheet bonus: +10% to the rating gain if kept a clean sheet
        # Only applies if the team won or drew
        home_cs_bonus = 1.1 if (away_score == 0 and w_home >= 0.5) else 1.0
        away_cs_bonus = 1.1 if (home_score == 0 and w_away >= 0.5) else 1.0
        
        # Calculate shifts
        shift_home = k * mov * (w_home - e_home) * home_cs_bonus
        shift_away = k * mov * (w_away - e_away) * away_cs_bonus
        
        # Update state
        self.ratings[home_team] += shift_home
        self.ratings[away_team] += shift_away
        
        return shift_home, shift_away
