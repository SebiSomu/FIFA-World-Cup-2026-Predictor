from django.db import models


class Team(models.Model):
    """Master table for all WC2026 teams."""
    name = models.CharField(max_length=100, unique=True)
    fifa_code = models.CharField(max_length=10, blank=True)
    confederation = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SimulationRun(models.Model):
    """Stores metadata about a simulation run."""
    SIMULATION_TYPES = [
        ('modern', 'Modern (Recency Weighted)'),
        ('all_time', 'All-Time (Equal Weights)'),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    champion = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='championships')
    runner_up = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='runner_up_placements')
    third_place = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='third_place_placements')
    total_matches = models.IntegerField(default=104)
    simulation_type = models.CharField(
        max_length=20,
        choices=SIMULATION_TYPES,
        default='modern',
        db_index=True,
        help_text='Type of simulation: modern (recency weighted) or all_time (equal weights for all years)'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['simulation_type', '-created_at']),
        ]

    def __str__(self):
        return f"Simulation {self.id} ({self.simulation_type}) - {self.champion.name} (champion) at {self.created_at}"


class Match(models.Model):
    """Stores a single match result."""
    simulation = models.ForeignKey(SimulationRun, on_delete=models.CASCADE, related_name='matches')
    match_id = models.CharField(max_length=10)
    fifa_match_number = models.IntegerField(null=True, blank=True)
    stage = models.CharField(max_length=50)
    group = models.CharField(max_length=10, blank=True)
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    home_score = models.IntegerField()
    away_score = models.IntegerField()
    score_detail = models.TextField(blank=True)
    winner = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='wins', null=True, blank=True)
    prob_home_win = models.FloatField(null=True, blank=True)
    prob_draw = models.FloatField(null=True, blank=True)
    prob_away_win = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['match_id']

    def __str__(self):
        return f"{self.match_id}: {self.home_team.name} {self.home_score}-{self.away_score} {self.away_team.name}"


class GroupStanding(models.Model):
    """Stores final group standings."""
    simulation = models.ForeignKey(SimulationRun, on_delete=models.CASCADE, related_name='standings')
    group = models.CharField(max_length=10)
    position = models.IntegerField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='group_standings')
    played = models.IntegerField()
    wins = models.IntegerField()
    draws = models.IntegerField()
    losses = models.IntegerField()
    goals_for = models.IntegerField()
    goals_against = models.IntegerField()
    goal_diff = models.IntegerField()
    points = models.IntegerField()

    class Meta:
        ordering = ['group', 'position']

    def __str__(self):
        return f"Group {self.group} #{self.position}: {self.team.name} ({self.points} pts)"


class TeamStatistic(models.Model):
    """Stores aggregated team statistics for the tournament."""
    simulation = models.ForeignKey(SimulationRun, on_delete=models.CASCADE, related_name='team_stats')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='tournament_stats')
    stage_reached = models.CharField(max_length=50)
    matches_played = models.IntegerField()
    wins = models.IntegerField()
    draws = models.IntegerField()
    losses = models.IntegerField()
    goals_for = models.IntegerField()
    goals_against = models.IntegerField()
    goal_diff = models.IntegerField()
    group = models.CharField(max_length=10)
    group_position = models.IntegerField()

    class Meta:
        ordering = ['-stage_reached', '-wins', '-goal_diff']

    def __str__(self):
        return f"{self.team.name}: {self.stage_reached}, {self.matches_played} matches"
