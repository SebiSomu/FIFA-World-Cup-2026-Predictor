"""
Management command to run WC2026 simulation and save results to database.
Usage: python manage.py run_simulation [--type modern|all_time]
"""
import sys
from pathlib import Path
from django.core.management.base import BaseCommand
from api.models import SimulationRun, Match, GroupStanding, TeamStatistic, Team

# Add predictor module to path
PREDICTOR_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent / 'predictor'
if str(PREDICTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(PREDICTOR_ROOT))

from simulation.tournament import run_tournament, get_wc2026_teams
from simulation.wc2026_groups import GROUPS


class Command(BaseCommand):
    help = 'Run WC2026 simulation and save results to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['modern', 'all_time'],
            default='modern',
            help='Type of simulation: modern (recency weighted) or all_time (equal weights for all years)'
        )

    def handle(self, *args, **options):
        sim_type = options['type']
        self.stdout.write(self.style.NOTICE(f'Running WC2026 simulation (type: {sim_type})...'))

        # Run simulation
        results = run_tournament(simulation_type=sim_type)
        
        # Get or create all teams in master Team table
        team_objects = self._get_or_create_teams()
        
        # Create SimulationRun
        sim_run = SimulationRun.objects.create(
            champion=team_objects[results['champion']],
            runner_up=team_objects[results['runner_up']],
            third_place=team_objects[results['third_place']],
            total_matches=len(results['all_results']),
            simulation_type=sim_type
        )

        self.stdout.write(self.style.SUCCESS(
            f'Created SimulationRun ({sim_type}): {sim_run.champion.name} champion at {sim_run.created_at}'
        ))
        
        # Save all matches
        self._save_matches(sim_run, results['all_results'], team_objects)
        
        # Save group standings
        self._save_standings(sim_run, results['group_standings'], team_objects)
        
        # Save team statistics
        self._save_team_stats(sim_run, results, team_objects)
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully saved {sim_run.matches.count()} matches, '
            f'{sim_run.standings.count()} standings, '
            f'{sim_run.team_stats.count()} team stats'
        ))

    def _get_or_create_teams(self):
        """Get or create all WC2026 teams in master Team table."""
        teams = get_wc2026_teams()
        team_objects = {}
        
        for team_name in teams:
            team, created = Team.objects.get_or_create(
                name=team_name,
                defaults={'fifa_code': '', 'confederation': ''}
            )
            team_objects[team_name] = team
            if created:
                self.stdout.write(f'  Created team: {team_name}')
        
        return team_objects

    def _save_matches(self, sim_run, all_results, team_objects):
        """Save all match results."""
        matches_to_create = []
        
        for match_data in all_results:
            home_team = team_objects[match_data['home_team']]
            away_team = team_objects[match_data['away_team']]
            
            # Handle winner - can be None for group stage draws
            winner = None
            if match_data.get('winner'):
                winner = team_objects.get(match_data['winner'])
            
            matches_to_create.append(Match(
                simulation=sim_run,
                match_id=match_data['match_id'],
                fifa_match_number=match_data.get('fifa_match_number'),
                stage=match_data['stage'],
                group=match_data.get('group', ''),
                home_team=home_team,
                away_team=away_team,
                home_score=match_data['predicted_home_score'],
                away_score=match_data['predicted_away_score'],
                score_detail=match_data.get('score_detail', ''),
                winner=winner,
                prob_home_win=match_data.get('prob_home_win'),
                prob_draw=match_data.get('prob_draw'),
                prob_away_win=match_data.get('prob_away_win'),
            ))
        
        Match.objects.bulk_create(matches_to_create)
        self.stdout.write(f'  Saved {len(matches_to_create)} matches')

    def _save_standings(self, sim_run, group_standings, team_objects):
        """Save final group standings."""
        standings_to_create = []
        
        for group_name, teams in group_standings.items():
            for position, team_record in enumerate(teams, start=1):
                team = team_objects[team_record.team]
                standings_to_create.append(GroupStanding(
                    simulation=sim_run,
                    group=group_name,
                    position=position,
                    team=team,
                    played=team_record.played,
                    wins=team_record.wins,
                    draws=team_record.draws,
                    losses=team_record.losses,
                    goals_for=team_record.goals_for,
                    goals_against=team_record.goals_against,
                    goal_diff=team_record.goal_diff,
                    points=team_record.points,
                ))
        
        GroupStanding.objects.bulk_create(standings_to_create)
        self.stdout.write(f'  Saved {len(standings_to_create)} group standings')

    def _save_team_stats(self, sim_run, results, team_objects):
        """Save aggregated team statistics."""
        # Build lookup from group standings
        team_stats = {}
        
        for group_name, teams in results['group_standings'].items():
            for position, team_record in enumerate(teams, start=1):
                team = team_objects[team_record.team]
                team_stats[team.name] = {
                    'team': team,
                    'stage_reached': 'Group Stage',
                    'matches_played': team_record.played,
                    'wins': team_record.wins,
                    'draws': team_record.draws,
                    'losses': team_record.losses,
                    'goals_for': team_record.goals_for,
                    'goals_against': team_record.goals_against,
                    'goal_diff': team_record.goal_diff,
                    'group': group_name,
                    'group_position': position,
                }
        
        # Determine stage reached from matches
        for match in results['all_results']:
            if match.get('winner'):
                winner_name = match['winner']
                stage = match['stage']
                
                if winner_name in team_stats:
                    # Update stage if it's further in tournament
                    stage_order = {
                        'Group Stage': 1,
                        'Round of 32': 2,
                        'Round of 16': 3,
                        'Quarter-Final': 4,
                        'Semi-Final': 5,
                        'Third Place': 6,
                        'Final': 7,
                    }
                    
                    current_stage = team_stats[winner_name]['stage_reached']
                    if stage_order.get(stage, 0) > stage_order.get(current_stage, 0):
                        team_stats[winner_name]['stage_reached'] = stage
        
        # Set final positions
        team_stats[results['champion']]['stage_reached'] = 'Champion'
        team_stats[results['runner_up']]['stage_reached'] = 'Runner-up'
        team_stats[results['third_place']]['stage_reached'] = 'Third Place'
        
        # Create TeamStatistic objects
        stats_to_create = [
            TeamStatistic(simulation=sim_run, **data)
            for data in team_stats.values()
        ]
        
        TeamStatistic.objects.bulk_create(stats_to_create)
        self.stdout.write(f'  Saved {len(stats_to_create)} team statistics')
