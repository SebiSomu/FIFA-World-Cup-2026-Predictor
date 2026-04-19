"""
Advanced feature engineering with recency weighting and competition adjustment.
Calculates all-time team statistics, head-to-head, and trends for ML prediction.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, List
from datetime import datetime
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))


# Recency weighting parameters
RECENCY_WINDOW_YEARS = 4
RECENCY_WEIGHT_RECENT = 2.0  # Double weight for recent matches (2022+)
RECENCY_WEIGHT_BASE = 1.0

# Option 2: Exponential decay (new system, recommended)
# λ = 0.25 means: 2026=1.0, 2024=0.61, 2022=0.37, 2020=0.22, 2018=0.14
RECENCY_LAMBDA = 0.25  # Decay parameter - slower decay for better balance

# Hybrid weighting: balance competition importance vs recency
# total_weight = (comp_weight * COMPETITION_WEIGHT_RATIO) + (recency_weight * RECENCY_WEIGHT_RATIO)
COMPETITION_WEIGHT_RATIO = 0.60  # 60% competition importance
RECENCY_WEIGHT_RATIO = 0.40     # 40% recency

# Cap total_weight to prevent extreme values
MAX_TOTAL_WEIGHT = 5.0

# Competition importance weights - adjusted by confederation strength
COMPETITION_WEIGHTS = {
    'FIFA World Cup': 4.0,
    'Confederations Cup': 2.5,
    'UEFA Euro': 3.2,  
    'UEFA Nations League': 2.5,
    "Copa Am\u00e9rica": 3.0, 
    'African Cup of Nations': 2.5,  
    'AFC Asian Cup': 2.0,  
    'CONCACAF Championship': 1.5,  
    'CONCACAF Nations League': 1.5,
    'FIFA World Cup qualification': 2.0,  # Base, adjusted by confederation below
    'UEFA Euro qualification': 2.0,
    'Friendly': 1.0,
    'Default': 1.5
}

# Confederation mappings for WC2026 teams (simplified)
CONFEDERATION_TEAMS = {
    'UEFA': ['Albania', 'Andorra', 'Armenia', 'Austria', 'Azerbaijan', 'Belarus', 'Belgium', 
             'Bosnia and Herzegovina', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 'Denmark', 
             'England', 'Estonia', 'Faroe Islands', 'Finland', 'France', 'Georgia', 'Germany', 
             'Gibraltar', 'Greece', 'Hungary', 'Iceland', 'Ireland', 'Israel', 'Italy', 'Kazakhstan',
             'Kosovo', 'Latvia', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Malta', 'Moldova',
             'Monaco', 'Montenegro', 'Netherlands', 'North Macedonia', 'Northern Ireland', 'Norway',
             'Poland', 'Portugal', 'Romania', 'Russia', 'San Marino', 'Scotland', 'Serbia', 'Slovakia',
             'Slovenia', 'Spain', 'Sweden', 'Switzerland', 'Türkiye', 'Ukraine', 'Wales'],
    
    'CONMEBOL': ['Argentina', 'Bolivia', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Paraguay', 
                 'Peru', 'Uruguay', 'Venezuela'],
    
    'CAF': ['Algeria', 'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi', 'Cameroon',
            'Cape Verde', 'Central African Republic', 'Chad', 'Comoros', 'Congo', 
            'Congo DR', 'Djibouti', 'Egypt', 'Equatorial Guinea', 'Eritrea', 'Eswatini',
            'Ethiopia', 'Gabon', 'Gambia', 'Ghana', 'Guinea', 'Guinea-Bissau', 'Ivory Coast',
            'Kenya', 'Lesotho', 'Liberia', 'Libya', 'Madagascar', 'Malawi', 'Mali',
            'Mauritania', 'Mauritius', 'Morocco', 'Mozambique', 'Namibia', 'Niger', 'Nigeria',
            'Rwanda', 'Sao Tome and Principe', 'Senegal', 'Seychelles', 'Sierra Leone',
            'Somalia', 'South Africa', 'South Sudan', 'Sudan', 'Tanzania', 'Togo', 'Tunisia',
            'Uganda', 'Zambia', 'Zimbabwe'],
    
    'AFC': ['Australia', 'Bahrain', 'Bangladesh', 'Bhutan', 'Brunei', 'Cambodia', 'China',
            'Guam', 'Hong Kong', 'India', 'Indonesia', 'Iran', 'Iraq', 'Japan', 'Jordan',
            'Kuwait', 'Kyrgyzstan', 'Laos', 'Lebanon', 'Macau', 'Malaysia', 'Maldives',
            'Mongolia', 'Myanmar', 'Nepal', 'North Korea', 'Oman', 'Pakistan', 'Palestine',
            'Philippines', 'Qatar', 'Saudi Arabia', 'Singapore', 'South Korea', 'Sri Lanka',
            'Syria', 'Tajikistan', 'Thailand', 'Timor-Leste', 'Turkmenistan', 'UAE',
            'Uzbekistan', 'Vietnam', 'Yemen'],
    
    'CONCACAF': ['Antigua and Barbuda', 'Bahamas', 'Barbados', 'Belize', 'Bermuda', 'Canada',
                 'Costa Rica', 'Cuba', 'Dominica', 'Dominican Republic', 'El Salvador',
                 'Grenada', 'Guatemala', 'Haiti', 'Honduras', 'Jamaica', 'Mexico',
                 'Nicaragua', 'Panama', 'Saint Kitts and Nevis', 'Saint Lucia',
                 'Saint Vincent and the Grenadines', 'Trinidad and Tobago', 'United States'],
    
    'OFC': ['American Samoa', 'Cook Islands', 'Fiji', 'New Caledonia', 'New Zealand',
            'Papua New Guinea', 'Samoa', 'Solomon Islands', 'Tahiti', 'Tonga', 'Vanuatu']
}

# Qualifier weights by confederation strength
# CONMEBOL hardest (10 teams, 6.5 spots = 65% qualification rate)
# UEFA moderate (55 teams, 16 spots = 29% qualification rate)
# Others easier
QUALIFIER_WEIGHTS = {
    'CONMEBOL': 3.0,  # Hardest qualifiers
    'UEFA': 2.5,      # Moderate difficulty
    'CAF': 2.0,       # Easier
    'AFC': 1.8,       # Easier
    'CONCACAF': 1.8,  # Easier
    'OFC': 1.5,       # Easiest (0.5 spots)
    'Unknown': 2.0
}

def get_team_confederation(team: str) -> str:
    """Get confederation for a team."""
    for conf, teams in CONFEDERATION_TEAMS.items():
        if team in teams:
            return conf
    return 'Unknown'

def get_competition_weight(tournament: str, home_team: str = None, away_team: str = None) -> float:
    """
    Get weight for a competition type.
    For World Cup qualifiers, weight by confederation strength.
    """
    if tournament == 'FIFA World Cup qualification' and home_team and away_team:
        # Get confederations for both teams
        home_conf = get_team_confederation(home_team)
        away_conf = get_team_confederation(away_team)
        
        # Use the higher weight (stronger confederation)
        home_weight = QUALIFIER_WEIGHTS.get(home_conf, 2.0)
        away_weight = QUALIFIER_WEIGHTS.get(away_conf, 2.0)
        return max(home_weight, away_weight)
    
    return COMPETITION_WEIGHTS.get(tournament, COMPETITION_WEIGHTS['Default'])


def calculate_recency_weight(match_date: datetime, current_year: int = 2026) -> float:
    """
    Exponential decay recency weighting.
    Weight = exp(-λ * age) where age = current_year - match_year
    Smooth decay avoids binary cliff at RECENCY_WINDOW_YEARS.
    """
    import numpy as np
    match_year = match_date.year if hasattr(match_date, "year") else int(match_date)
    age = current_year - match_year
    return np.exp(-RECENCY_LAMBDA * age)


def calculate_age_penalty(match_date: datetime, current_year: int = 2026) -> float:
    """
    Age penalty multiplier to reduce weights for old competitions.
    Allows weights to go below the competition floor (2.40 for WC, 1.92 for Euro).
    """
    match_year = match_date.year if hasattr(match_date, "year") else int(match_date)
    age = current_year - match_year
    
    # Age penalty tiers (more aggressive decay for older matches)
    if age <= 4:  # 2022-2026
        return 1.0
    elif age <= 8:  # 2018-2020
        return 0.95
    elif age <= 12:  # 2014-2016
        return 0.85
    elif age <= 16:  # 2010-2012
        return 0.70
    elif age <= 20:  # 2006-2008
        return 0.55
    elif age <= 24:  # 2002-2004
        return 0.40
    elif age <= 32:  # 1994-2000
        return 0.30
    elif age <= 40:  # 1986-1992
        return 0.20
    else:  # <1986
        return 0.15


class AdvancedFeatureExtractor:
    """Extract advanced features for ML prediction with recency weighting."""
    
    def __init__(self):
        self.matches_df = None
        self.current_date = datetime(2026, 6, 1)  # WC2026 start
        self._load_data()
    
    def _load_data(self):
        """Load historical matches."""
        # Try multiple paths for results.csv
        possible_paths = [
            Path('predictor/data/results.csv'),
            Path('../data/results.csv'),
            Path(__file__).resolve().parent.parent / 'data' / 'results.csv',
        ]
        
        results_path = None
        for p in possible_paths:
            if p.exists():
                results_path = p
                break
        
        if results_path:
            self.matches_df = pd.read_csv(results_path)
            self.matches_df['date'] = pd.to_datetime(self.matches_df['date'])
            # Keep matches from 1990 onwards
            self.matches_df = self.matches_df[self.matches_df['date'].dt.year >= 1990]
            print(f"Loaded {len(self.matches_df)} historical matches for feature extraction")
    
    def get_team_all_time_stats(self, team: str) -> Dict:
        """
        Calculate all-time statistics for a team with recency and competition weighting.
        """
        if self.matches_df is None:
            return self._default_stats()
        
        # Get all matches for this team (both home and away)
        home_matches = self.matches_df[self.matches_df['home_team'] == team].copy()
        away_matches = self.matches_df[self.matches_df['away_team'] == team].copy()
        
        if len(home_matches) == 0 and len(away_matches) == 0:
            return self._default_stats()
        
        # Add is_home flag
        home_matches['is_home'] = True
        away_matches['is_home'] = False
        
        # Combine
        all_matches = pd.concat([home_matches, away_matches], ignore_index=True)
        
        # Calculate weighted stats
        total_weighted_matches = 0
        weighted_wins = 0
        weighted_draws = 0
        weighted_losses = 0
        weighted_goals_scored = 0
        weighted_goals_conceded = 0
        weighted_clean_sheets = 0
        
        recent_form_scores = []  # For last 20 matches
        
        for _, match in all_matches.iterrows():
            # Determine if team was home or away
            is_home = match['is_home']
            
            # Get goals
            if is_home:
                goals_scored = match['home_score']
                goals_conceded = match['away_score']
            else:
                goals_scored = match['away_score']
                goals_conceded = match['home_score']
            
            # Calculate weights
            comp_weight = get_competition_weight(match.get('tournament', 'Default'))
            recency_weight = calculate_recency_weight(match['date'])
            age_penalty = calculate_age_penalty(match['date'])
            
            # Hybrid formula: balance competition importance vs recency
            total_weight = (comp_weight * COMPETITION_WEIGHT_RATIO) + (recency_weight * RECENCY_WEIGHT_RATIO)
            
            # Apply age penalty to allow weights below competition floor
            total_weight = total_weight * age_penalty
            
            # Update stats
            total_weighted_matches += total_weight
            weighted_goals_scored += goals_scored * total_weight
            weighted_goals_conceded += goals_conceded * total_weight
            
            if goals_conceded == 0:
                weighted_clean_sheets += total_weight
            
            # Result
            if goals_scored > goals_conceded:
                weighted_wins += total_weight
                result_score = 1.0
            elif goals_scored == goals_conceded:
                weighted_draws += total_weight
                result_score = 0.5
            else:
                weighted_losses += total_weight
                result_score = 0.0
            
            # Store for recent form (last 20 chronological matches)
            recent_form_scores.append((match['date'], result_score, total_weight))
        
        # Normalize by total weight
        if total_weighted_matches > 0:
            stats = {
                'total_matches': len(all_matches),
                'weighted_matches': total_weighted_matches,
                'win_rate': weighted_wins / total_weighted_matches,
                'draw_rate': weighted_draws / total_weighted_matches,
                'loss_rate': weighted_losses / total_weighted_matches,
                'avg_goals_scored': weighted_goals_scored / total_weighted_matches,
                'avg_goals_conceded': weighted_goals_conceded / total_weighted_matches,
                'clean_sheet_rate': weighted_clean_sheets / total_weighted_matches,
            }
        else:
            stats = self._default_stats()
        
        # Calculate recent form (last 20 matches, weighted by recency)
        recent_form_scores.sort(key=lambda x: x[0], reverse=True)
        last_20 = recent_form_scores[:20]
        
        if last_20:
            # Weight by both chronological position AND time decay
            # Combination of linear ordering (1.0 to 2.0) and exponential decay
            chronological_weights = np.linspace(1.0, 2.0, len(last_20))  # Recent matches get higher weight
            
            # Time decay based on actual match year
            time_weights = []
            for match_date, _, _ in last_20:  # Unpack 3 values: date, result_score, weight
                age = 2026 - match_date.year
                time_weight = np.exp(-RECENCY_LAMBDA * age)  # Decay with age
                time_weights.append(time_weight)
            time_weights = np.array(time_weights)
            
            # Combined weights: chronological position × time decay
            form_weights = chronological_weights * time_weights
            form_values = [x[1] for x in last_20]  # x[1] is result_score
            stats['recent_form'] = np.average(form_values, weights=form_weights)
        else:
            stats['recent_form'] = 0.5
        
        # Trend: compare last 4 years vs all-time
        recent_matches = [m for m in recent_form_scores if m[0].year >= 2022]
        older_matches = [m for m in recent_form_scores if m[0].year < 2022]
        
        if recent_matches and older_matches:
            recent_avg = np.mean([x[1] for x in recent_matches])
            older_avg = np.mean([x[1] for x in older_matches])
            stats['trend'] = recent_avg - older_avg  # Positive = improving
        else:
            stats['trend'] = 0.0
        
        # Additional trend features: last 4 years vs last 8 years (smoother comparison)
        last_4_years = [m for m in recent_form_scores if m[0].year >= 2022]
        last_8_years = [m for m in recent_form_scores if 2018 <= m[0].year <= 2025]
        
        if last_4_years and last_8_years and len(last_4_years) >= 5:
            last_4_avg = np.mean([x[1] for x in last_4_years])
            # Last 8 years but excluding last 4 (to avoid double counting)
            years_4_to_8 = [m for m in recent_form_scores if 2018 <= m[0].year < 2022]
            if years_4_to_8:
                years_4_to_8_avg = np.mean([x[1] for x in years_4_to_8])
                stats['trend_last_4_vs_8'] = last_4_avg - years_4_to_8_avg
            else:
                stats['trend_last_4_vs_8'] = 0.0
        else:
            stats['trend_last_4_vs_8'] = 0.0
        
        return stats
    
    def _default_stats(self) -> Dict:
        """Return default stats for unknown teams."""
        return {
            'total_matches': 0,
            'weighted_matches': 0,
            'win_rate': 0.5,
            'draw_rate': 0.25,
            'loss_rate': 0.25,
            'avg_goals_scored': 1.0,
            'avg_goals_conceded': 1.0,
            'clean_sheet_rate': 0.2,
            'recent_form': 0.5,
            'trend': 0.0,
            'trend_last_4_vs_8': 0.0,
        }
    
    def get_h2h_stats(self, team1: str, team2: str) -> Dict:
        """Get head-to-head statistics with recency weighting."""
        if self.matches_df is None:
            return {'matches': 0, 'team1_win_rate': 0.5, 'avg_goals': 1.0}
        
        # Find direct matches
        mask1 = (self.matches_df['home_team'] == team1) & (self.matches_df['away_team'] == team2)
        mask2 = (self.matches_df['home_team'] == team2) & (self.matches_df['away_team'] == team1)
        h2h_matches = self.matches_df[mask1 | mask2].copy()
        
        if len(h2h_matches) == 0:
            return {'matches': 0, 'team1_win_rate': 0.5, 'avg_goals': 1.0}
        
        # Calculate weighted stats
        total_weight = 0
        team1_wins = 0
        total_goals = 0
        
        for _, match in h2h_matches.iterrows():
            comp_weight = get_competition_weight(match.get('tournament', 'Default'))
            recency_weight = calculate_recency_weight(match['date'])
            weight = comp_weight * recency_weight
            
            total_weight += weight
            
            if match['home_team'] == team1:
                t1_goals = match['home_score']
                t2_goals = match['away_score']
            else:
                t1_goals = match['away_score']
                t2_goals = match['home_score']
            
            total_goals += (t1_goals + t2_goals) * weight
            
            if t1_goals > t2_goals:
                team1_wins += weight
        
        return {
            'matches': len(h2h_matches),
            'team1_win_rate': team1_wins / total_weight if total_weight > 0 else 0.5,
            'avg_goals': total_goals / total_weight if total_weight > 0 else 1.0,
        }
    
    def build_match_features(self, home_team: str, away_team: str, 
                            elo_home: float, elo_away: float) -> np.ndarray:
        """
        Build feature vector for ML prediction.
        Returns array of features for the match.
        """
        # Get team stats
        home_stats = self.get_team_all_time_stats(home_team)
        away_stats = self.get_team_all_time_stats(away_team)
        
        # Get H2H stats
        h2h = self.get_h2h_stats(home_team, away_team)
        
        # Build feature vector
        features = [
            # Home team stats
            home_stats['win_rate'],
            home_stats['draw_rate'],
            home_stats['avg_goals_scored'],
            home_stats['avg_goals_conceded'],
            home_stats['clean_sheet_rate'],
            home_stats['recent_form'],
            home_stats['trend'],
            
            # Away team stats
            away_stats['win_rate'],
            away_stats['draw_rate'],
            away_stats['avg_goals_scored'],
            away_stats['avg_goals_conceded'],
            away_stats['clean_sheet_rate'],
            away_stats['recent_form'],
            away_stats['trend'],
            
            # H2H
            h2h['matches'] / 100.0,  # Normalize
            h2h['team1_win_rate'],
            h2h['avg_goals'] / 5.0,  # Normalize
            
            # ELO
            elo_home / 2500.0,  # Normalize
            elo_away / 2500.0,
            (elo_home - elo_away) / 500.0,  # ELO diff normalized
        ]
        
        return np.array(features)


if __name__ == '__main__':
    # Test
    extractor = AdvancedFeatureExtractor()
    
    print("\n=== Test Team Stats ===")
    stats = extractor.get_team_all_time_stats('Brazil')
    print(f"Brazil all-time stats:")
    for key, val in stats.items():
        print(f"  {key}: {val:.3f}")
    
    print("\n=== Test H2H ===")
    h2h = extractor.get_h2h_stats('Brazil', 'Argentina')
    print(f"Brazil vs Argentina H2H: {h2h}")
    
    print("\n=== Test Features ===")
    features = extractor.build_match_features('Brazil', 'Argentina', 1984, 2113)
    print(f"Feature vector shape: {features.shape}")
    print(f"Features: {features}")
