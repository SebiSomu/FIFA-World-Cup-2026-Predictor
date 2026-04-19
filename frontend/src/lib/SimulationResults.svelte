<script lang="ts">
  import { onMount } from 'svelte';

  interface Match {
    match_id: string;
    stage: string;
    group?: string;
    home_team: string;
    away_team: string;
    predicted_home_score: number;
    predicted_away_score: number;
    winner?: string;
    score_detail?: string;
  }

  interface TeamRecord {
    team: string;
    played: number;
    won: number;
    drawn: number;
    lost: number;
    goals_for: number;
    goals_against: number;
    goal_diff: number;
    points: number;
  }

  interface SimulationData {
    status: string;
    champion: string;
    runner_up: string;
    third_place: string;
    group_standings: Record<string, TeamRecord[]>;
    all_results: Match[];
  }

  let results: SimulationData | null = null;
  let loading = false;
  let error: string | null = null;
  let errorDetail: string | null = null;
  let rawJson = '';
  let testMode = false;

  const API_URL = 'http://localhost:8000/api';

  async function runTest() {
    loading = true;
    error = null;
    errorDetail = null;
    results = null;
    rawJson = '';
    testMode = true;

    try {
      console.log('Testing /api/test/ endpoint...');
      const response = await fetch(`${API_URL}/test/`);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Test endpoint failed! Status: ${response.status}\n${errorText}`);
      }
      const data = await response.json();
      console.log('Test successful:', data);
      results = data;
      rawJson = JSON.stringify(data, null, 2);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error';
      errorDetail = 'Quick test failed - check console for details';
      console.error('Test error:', e);
    } finally {
      loading = false;
    }
  }

  async function runSimulation() {
    loading = true;
    error = null;
    errorDetail = null;
    results = null;
    rawJson = '';
    testMode = false;

    try {
      console.log('Running full simulation...');
      const response = await fetch(`${API_URL}/simulate/run/`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMsg = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
        throw new Error(`Simulation failed: ${errorMsg}`);
      }
      const data = await response.json();
      console.log('Simulation successful:', data);
      results = data;
      rawJson = JSON.stringify(data, null, 2);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error';
      errorDetail = 'Full simulation failed - check if Django server is running on port 8000';
      console.error('Simulation error:', e);
    } finally {
      loading = false;
    }
  }

  function getGroupMatches(group: string): Match[] {
    if (!results) return [];
    return results.all_results.filter(m => m.group === group && m.stage === 'Group Stage');
  }

  function getKnockoutMatches(stage: string): Match[] {
    if (!results) return [];
    return results.all_results.filter(m => m.stage === stage);
  }
</script>

<div class="simulation-container">
  <h2>🏆 FIFA World Cup 2026 Predictor</h2>
  
  <div class="button-row">
    <button on:click={runTest} disabled={loading} class="test-btn">
      {#if loading && testMode}
        ⏳ Testing...
      {:else}
        🧪 Quick Test
      {/if}
    </button>
    
    <button on:click={runSimulation} disabled={loading} class="run-btn">
      {#if loading && !testMode}
        ⏳ Running Simulation...
      {:else}
        ▶️ Run Full Simulation
      {/if}
    </button>
  </div>

  {#if error}
    <div class="error">
      <strong>❌ Error:</strong>
      <pre>{error}</pre>
      {#if errorDetail}
        <p class="error-hint">{errorDetail}</p>
      {/if}
    </div>
  {/if}

  {#if results}
    <div class="results">
      <h3>🏅 Final Results</h3>
      <div class="podium">
        <div class="champion">🥇 Champion: {results.champion}</div>
        <div class="runner-up">🥈 Runner-up: {results.runner_up}</div>
        <div class="third">🥉 Third place: {results.third_place}</div>
      </div>

      <h3>📊 Group Standings</h3>
      {#each Object.entries(results.group_standings) as [group, teams]}
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
                  <td>{team.won}</td>
                  <td>{team.drawn}</td>
                  <td>{team.lost}</td>
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

      <h3>📋 All Matches (JSON)</h3>
      <pre class="json-output">{rawJson}</pre>
    </div>
  {/if}
</div>

<style>
  .simulation-container {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
  }

  h2 {
    color: #333;
    text-align: center;
  }

  .run-btn {
    display: block;
    margin: 20px auto;
    padding: 15px 30px;
    font-size: 18px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: transform 0.2s;
  }

  .run-btn:hover:not(:disabled) {
    transform: scale(1.05);
  }

  .run-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .error {
    background: #fee;
    color: #c33;
    padding: 15px;
    border-radius: 8px;
    margin: 20px 0;
    text-align: center;
  }

  .results {
    margin-top: 30px;
  }

  .podium {
    display: flex;
    justify-content: center;
    gap: 30px;
    margin: 20px 0;
    flex-wrap: wrap;
  }

  .podium > div {
    padding: 15px 25px;
    border-radius: 10px;
    font-size: 18px;
    font-weight: bold;
  }

  .champion {
    background: linear-gradient(135deg, #ffd700 0%, #ffed4a 100%);
    color: #333;
  }

  .runner-up {
    background: linear-gradient(135deg, #c0c0c0 0%, #e0e0e0 100%);
    color: #333;
  }

  .third {
    background: linear-gradient(135deg, #cd7f32 0%, #daa520 100%);
    color: white;
  }

  .group {
    margin: 20px 0;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 8px;
  }

  .group h4 {
    margin-top: 0;
    color: #555;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }

  th, td {
    padding: 8px 12px;
    text-align: center;
    border-bottom: 1px solid #ddd;
  }

  th {
    background: #667eea;
    color: white;
    font-weight: 600;
  }

  td:first-child {
    text-align: left;
    font-weight: 500;
  }

  tr:hover {
    background: #f0f0f0;
  }

  .json-output {
    background: #2d2d2d;
    color: #f8f8f2;
    padding: 20px;
    border-radius: 8px;
    overflow-x: auto;
    font-size: 12px;
    line-height: 1.5;
    max-height: 500px;
    overflow-y: auto;
  }

  h3 {
    margin-top: 30px;
    padding-bottom: 10px;
    border-bottom: 2px solid #667eea;
    color: #444;
  }

  .button-row {
    display: flex;
    gap: 15px;
    justify-content: center;
    margin: 20px 0;
  }

  .test-btn {
    padding: 15px 30px;
    font-size: 16px;
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: transform 0.2s;
  }

  .test-btn:hover:not(:disabled) {
    transform: scale(1.05);
  }

  .test-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .error pre {
    background: #fee;
    padding: 10px;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 12px;
    margin-top: 10px;
  }

  .error-hint {
    color: #666;
    font-style: italic;
    margin-top: 10px;
  }
</style>
