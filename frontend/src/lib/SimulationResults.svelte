<script lang="ts">
  import { onMount } from 'svelte';
  import '../app.css';

  interface Match {
    match_id: string;
    stage: string;
    group?: string;
    home_team: string;
    away_team: string;
    home_score: number;
    away_score: number;
    winner?: string;
    score_detail?: string;
    prob_home_win?: number;
    prob_draw?: number;
    prob_away_win?: number;
  }

  interface TeamRecord {
    team: string;
    played: number;
    wins: number;
    draws: number;
    losses: number;
    goals_for: number;
    goals_against: number;
    goal_diff: number;
    points: number;
  }

  interface Simulation {
    id: number;
    created_at: string;
    champion: string;
    runner_up: string;
    third_place: string;
    total_matches: number;
  }

  interface SimulationData {
    status: string;
    simulation: Simulation;
    matches_by_stage: Record<string, Match[]>;
    standings: Record<string, TeamRecord[]>;
  }

  let results: SimulationData | null = null;
  let loading = true;
  let error: string | null = null;
  let errorDetail: string | null = null;
  let rawJson = '';

  const API_URL = 'http://localhost:8000/api';

  // Load data automatically on mount from database
  async function loadFromDatabase() {
    loading = true;
    error = null;
    errorDetail = null;

    try {
      console.log('Loading simulation data from database...');
      const response = await fetch(`${API_URL}/results/full/`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMsg = errorData.message || `HTTP error! status: ${response.status}`;
        
        if (response.status === 404) {
          throw new Error(`${errorMsg}\n\nRun: python manage.py run_simulation`);
        }
        throw new Error(errorMsg);
      }
      
      const data: SimulationData = await response.json();
      console.log('Data loaded successfully:', data);
      results = data;
      rawJson = JSON.stringify(data, null, 2);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error';
      errorDetail = 'Failed to load data - check if Django server is running on port 8000';
      console.error('Load error:', e);
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    loadFromDatabase();
  });

  function getGroupMatches(group: string): Match[] {
    if (!results) return [];
    return results.matches_by_stage['Group Stage']?.filter(m => m.group === group) || [];
  }

  function getKnockoutMatches(stage: string): Match[] {
    if (!results) return [];
    return results.matches_by_stage[stage] || [];
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString();
  }
</script>

<div class="simulation-container">
  <h2>🏆 FIFA World Cup 2026 Predictor</h2>

  {#if error}
    <div class="error">
      <strong>❌ Error:</strong>
      <pre>{error}</pre>
      {#if errorDetail}
        <p class="error-hint">{errorDetail}</p>
      {/if}
    </div>
  {/if}

  {#if loading && !results}
    <div class="loading">
      <p>⏳ Loading simulation data from database...</p>
    </div>
  {/if}

  {#if results}
    <div class="results">
      <h3>🏅 Final Results</h3>
      <div class="podium">
        <div class="champion">🥇 Champion: {results.simulation.champion}</div>
        <div class="runner-up">🥈 Runner-up: {results.simulation.runner_up}</div>
        <div class="third">🥉 Third place: {results.simulation.third_place}</div>
      </div>

      <h3>📊 Group Standings</h3>
      {#each Object.entries(results.standings) as [group, teams]}
        <div class="group">
          <h4>Group {group}</h4>
          <table>
            <thead>
              <tr>
                <th>Team</th>
                <th>P</th>
                <th>W</th>
                <th>D</th>
                <th>L</th>
                <th>GF</th>
                <th>GA</th>
                <th>GD</th>
                <th>Pts</th>
              </tr>
            </thead>
            <tbody>
              {#each teams as team}
                <tr>
                  <td>{team.team}</td>
                  <td>{team.played}</td>
                  <td>{team.wins}</td>
                  <td>{team.draws}</td>
                  <td>{team.losses}</td>
                  <td>{team.goals_for}</td>
                  <td>{team.goals_against}</td>
                  <td>{team.goal_diff}</td>
                  <td><strong>{team.points}</strong></td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/each}

      <h3>🎮 Knockout Stage Matches</h3>
      {#each Object.entries(results.matches_by_stage).filter(([stage]) => stage !== 'Group Stage') as [stage, matches]}
        <div class="stage">
          <h4>{stage}</h4>
          <div class="matches-grid">
            {#each matches as match}
              <div class="match-card">
                <div class="match-teams">
                  <span class="team" class:winner={match.winner === match.home_team}>
                    {match.home_team}
                  </span>
                  <span class="score">{match.home_score} - {match.away_score}</span>
                  <span class="team" class:winner={match.winner === match.away_team}>
                    {match.away_team}
                  </span>
                </div>
                {#if match.score_detail}
                  <div class="match-detail">{match.score_detail}</div>
                {/if}
              </div>
            {/each}
          </div>
        </div>
      {/each}

      <h3>📋 Full Data (JSON)</h3>
      <pre class="json-output">{rawJson}</pre>
    </div>
  {/if}
</div>
