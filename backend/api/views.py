"""
API views for FIFA World Cup 2026 Predictor.
Provides endpoints to run simulation and return results.
"""
import json
import sys
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import numpy as np

# Add predictor module to path
PREDICTOR_ROOT = Path(__file__).resolve().parent.parent.parent / 'predictor'
if str(PREDICTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(PREDICTOR_ROOT))

from simulation.tournament import run_tournament


def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({
        'status': 'ok',
        'message': 'WC2026 Predictor API is running'
    })


def test_json(request):
    """Test endpoint that returns sample data without running simulation."""
    sample_data = {
        'status': 'success',
        'test': True,
        'champion': 'Brazil',
        'runner_up': 'Argentina',
        'third_place': 'France',
        'sample_team': {
            'team': 'Brazil',
            'played': 7,
            'wins': 6,
            'draws': 1,
            'losses': 0,
            'goals_for': 18,
            'goals_against': 5,
            'goal_diff': 13,
            'points': 19,
        },
        'sample_match': {
            'match_id': 'GS001',
            'stage': 'Group Stage',
            'group': 'A',
            'home_team': 'Mexico',
            'away_team': 'South Africa',
            'predicted_home_score': 2,
            'predicted_away_score': 1,
        },
        'numbers_test': {
            'int': 42,
            'float': 3.14,
            'bool': True,
        }
    }
    return JsonResponse(sample_data)


@require_http_methods(['GET'])
def run_simulation(request):
    """
    Run the full WC2026 tournament simulation and return all results.
    """
    try:
        # Run the simulation
        results = run_tournament()
        
        # Convert to JSON-serializable format
        response_data = {
            'status': 'success',
            'champion': results['champion'],
            'runner_up': results['runner_up'],
            'third_place': results['third_place'],
            'group_standings': format_group_standings(results['group_standings']),
            'all_results': format_matches(results['all_results']),
            'qualified_by_group': format_qualified(results['qualified_by_group']),
            'best_thirds': format_best_thirds(results['best_thirds']),
        }
        
        return JsonResponse(response_data)
        
    except TypeError as e:
        import traceback
        error_msg = f"JSON Serialization Error: {str(e)}"
        print(f"[API ERROR] {error_msg}")
        print(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'error_type': 'serialization_error',
            'message': error_msg,
            'detail': 'Failed to serialize simulation results to JSON. Check data types.',
            'traceback': traceback.format_exc()
        }, status=500)
    except Exception as e:
        import traceback
        error_msg = f"Simulation Error: {str(e)}"
        print(f"[API ERROR] {error_msg}")
        print(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'error_type': 'simulation_error',
            'message': error_msg,
            'detail': 'An unexpected error occurred during simulation.',
            'traceback': traceback.format_exc()
        }, status=500)


def to_python_type(value):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(value, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(value)
    if isinstance(value, (np.floating, np.float64, np.float32)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value

def format_group_standings(standings):
    """Convert group standings to JSON-serializable format."""
    formatted = {}
    for group, teams in standings.items():
        formatted[group] = []
        for team_record in teams:
            formatted[group].append({
                'team': team_record.team,
                'played': to_python_type(team_record.played),
                'wins': to_python_type(team_record.wins),
                'draws': to_python_type(team_record.draws),
                'losses': to_python_type(team_record.losses),
                'goals_for': to_python_type(team_record.goals_for),
                'goals_against': to_python_type(team_record.goals_against),
                'goal_diff': to_python_type(team_record.goal_diff),
                'points': to_python_type(team_record.points),
            })
    return formatted


def format_qualified(qualified):
    """Format qualified teams by group."""
    # qualified is dict like {group: (TeamRecord_winner, TeamRecord_runner_up)}
    formatted = {}
    for group, teams in qualified.items():
        winner = teams[0].team if hasattr(teams[0], 'team') else str(teams[0])
        runner_up = teams[1].team if hasattr(teams[1], 'team') else str(teams[1])
        formatted[group] = {
            'winner': winner,
            'runner_up': runner_up,
        }
    return formatted


def format_best_thirds(best_thirds):
    """Format best third-place teams."""
    # best_thirds is list of TeamRecord objects
    formatted = []
    for team_record in best_thirds:
        if hasattr(team_record, 'team'):
            # It's a TeamRecord object
            formatted.append({
                'team': team_record.team,
                'played': to_python_type(team_record.played),
                'points': to_python_type(team_record.points),
                'goal_diff': to_python_type(team_record.goal_diff),
                'goals_for': to_python_type(team_record.goals_for),
            })
        elif isinstance(team_record, dict):
            formatted.append({k: to_python_type(v) for k, v in team_record.items()})
        else:
            formatted.append({'team': str(team_record)})
    return formatted

def format_matches(matches):
    """Format match results with proper type conversion."""
    formatted = []
    for match in matches:
        formatted_match = {}
        for key, value in match.items():
            formatted_match[key] = to_python_type(value)
        formatted.append(formatted_match)
    return formatted
