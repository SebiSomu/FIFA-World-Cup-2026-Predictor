<script lang="ts">
  import { tick } from "svelte";
  import "../app.css";
  import GroupTable from "./GroupTable.svelte";
  import ThirdPlacedTable from "./ThirdPlacedTable.svelte";
  import KnockoutBracket from "./KnockoutBracket.svelte";
  import { getFlagUrl } from "./flags";

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
    group?: string;
  }

  interface Simulation {
    id: number;
    created_at: string;
    champion: string;
    runner_up: string;
    third_place: string;
    total_matches: number;
    simulation_type: 'modern' | 'all_time';
  }

  type SimulationType = 'modern' | 'all_time';

  interface SimulationData {
    status: string;
    simulation: Simulation;
    matches_by_stage: Record<string, Match[]>;
    standings: Record<string, TeamRecord[]>;
  }

  let results: SimulationData | null = null;
  let loading = false;
  let error: string | null = null;
  let errorDetail: string | null = null;
  let selectedType: SimulationType = 'modern';

  // Progression state
  let currentStageIndex = -1;
  const stages = [
    "Group Stage",
    "Third-Placed Teams",
    "Round of 32",
    "Round of 16",
    "Quarter-Final",
    "Semi-Final",
    "Third Place",
    "Final",
    "Champion",
  ];

  $: visibleStages = stages.slice(2, currentStageIndex + 1);

  const API_URL = "http://localhost:8000/api";

  async function loadSimulation() {
    loading = true;
    error = null;
    errorDetail = null;
    currentStageIndex = -1;
    results = null;

    try {
      const response = await fetch(`${API_URL}/results/full/?type=${selectedType}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMsg =
          errorData.message || `HTTP error! status: ${response.status}`;

        if (response.status === 404) {
          throw new Error(
            `${errorMsg}\n\nRun: python manage.py run_simulation`,
          );
        }
        throw new Error(errorMsg);
      }

      const data: SimulationData = await response.json();

      // Inject group name into team records for third-placed calculation
      for (const [groupName, teams] of Object.entries(data.standings)) {
        for (const team of teams) {
          team.group = groupName;
        }
      }

      results = data;
      currentStageIndex = 0; // Show group stage immediately after loading
    } catch (e) {
      error = e instanceof Error ? e.message : "Unknown error";
      errorDetail =
        "Failed to load data - check if Django server is running on port 8000";
      console.error("Load error:", e);
    } finally {
      loading = false;
    }
  }

  async function nextStage() {
    if (currentStageIndex < stages.length - 1) {
      currentStageIndex++;

      await tick();

      if (currentStageIndex === 6) {
        const el = document.querySelector(".third-place-section");
        if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
      } else if (currentStageIndex === 7) {
        const el = document.querySelector(".final-section");
        if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
      } else if (currentStageIndex === 8) {
        const el = document.querySelector(".champion-card-container");
        if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
      } else {
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    }
  }

  function getThirdPlacedTeams(): TeamRecord[] {
    if (!results) return [];
    let thirds: TeamRecord[] = [];
    for (const teams of Object.values(results.standings)) {
      if (teams.length >= 3) {
        thirds.push(teams[2]); // 0-indexed, so 2 is 3rd place
      }
    }
    return thirds;
  }

  // Label formatting for the button
  function getStageLabel(stageName: string) {
    if (stageName === "Quarter-Final") return "Quarter-finals";
    if (stageName === "Semi-Final") return "Semi-finals";
    if (stageName === "Third Place") return "Third place final";
    return stageName;
  }
</script>

<div class="simulation-container">
  <div class="header">
    <h2>FIFA World Cup 2026 Predictor</h2>
      {#if !results && !loading}
      <div class="controls-row">
        <div class="simulation-toggle">
          <span class="toggle-label">Simulation:</span>
          <div class="toggle-buttons">
            <button
              class="toggle-btn"
              class:active={selectedType === 'modern'}
              on:click={() => selectedType = 'modern'}
            >
              Modern
            </button>
            <button
              class="toggle-btn"
              class:active={selectedType === 'all_time'}
              on:click={() => selectedType = 'all_time'}
            >
              All-Time
            </button>
          </div>
        </div>
        <button class="primary-button" on:click={loadSimulation}>
          Load Simulation
        </button>
      </div>
    {/if}

    {#if results && currentStageIndex < stages.length - 1}
      <div class="controls">
        <button class="next-button" on:click={nextStage}>
          Next Stage ({getStageLabel(stages[currentStageIndex + 1])})
        </button>
      </div>
    {/if}
  </div>

  {#if error}
    <div class="error">
      <strong>Error:</strong>
      <pre>{error}</pre>
      {#if errorDetail}
        <p class="error-hint">{errorDetail}</p>
      {/if}
    </div>
  {/if}

  {#if loading}
    <div class="loading">
      <p>Loading simulation data from database...</p>
      <div class="spinner"></div>
    </div>
  {/if}

  {#if results && currentStageIndex >= 0}
    <div class="simulation-badge" class:modern={results.simulation.simulation_type === 'modern'} class:all-time={results.simulation.simulation_type === 'all_time'}>
      {results.simulation.simulation_type === 'modern' ? 'Modern (recency weighted)' : 'All-Time (equal weights for all years)'}
    </div>
    <div class="results">
      <!-- Group Stage View -->
      {#if currentStageIndex === 0}
        <div class="stage-section fade-in">
          <h3>Group Standings</h3>
          <div class="groups-grid">
            {#each Object.entries(results.standings) as [group, teams]}
              <GroupTable groupName={group} {teams} />
            {/each}
          </div>
        </div>
      {/if}

      <!-- Third Placed Teams View -->
      {#if currentStageIndex === 1}
        <div class="stage-section fade-in">
          <ThirdPlacedTable teams={getThirdPlacedTeams()} />
        </div>
      {/if}

      <!-- Knockout Stage Bracket View -->
      {#if currentStageIndex >= 2 && currentStageIndex <= 7}
        <div class="stage-section fade-in">
          <h3>Knockout Stage</h3>
          <KnockoutBracket
            matchesByStage={results.matches_by_stage}
            {visibleStages}
          />
        </div>
      {/if}

      <!-- Champion View -->
      {#if currentStageIndex === 8}
        <div class="stage-section fade-in final-results">
          <h3>World Cup Champion</h3>
          <div class="champion-card-container">
            <div class="champion-card">
              <span class="place-label">Winner</span>
              {#if getFlagUrl(results.simulation.champion)}
                <img
                  src={getFlagUrl(results.simulation.champion)}
                  class="champion-flag"
                  alt={results.simulation.champion}
                />
              {/if}
              <span class="team-name">{results.simulation.champion}</span>
            </div>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #ecf0f1;
    flex-wrap: wrap;
    gap: 1rem;
  }

  h2 {
    margin: 0;
    color: #2c3e50;
    font-size: 1.8rem;
  }

  .primary-button,
  .next-button {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s;
    background-color: #3498db;
    color: white;
    box-shadow: 0 4px 6px rgba(52, 152, 219, 0.2);
  }

  .primary-button:hover,
  .next-button:hover {
    background-color: #2980b9;
    transform: translateY(-2px);
    box-shadow: 0 6px 8px rgba(52, 152, 219, 0.3);
  }

  .next-button {
    background-color: #2ecc71;
    box-shadow: 0 4px 6px rgba(46, 204, 113, 0.2);
  }

  .next-button:hover {
    background-color: #27ae60;
    box-shadow: 0 6px 8px rgba(46, 204, 113, 0.3);
  }

  .controls {
    display: flex;
    gap: 1rem;
  }

  .controls-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .simulation-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .toggle-label {
    font-size: 0.9rem;
    color: #666;
    font-weight: 500;
  }

  .toggle-buttons {
    display: flex;
    background: #ecf0f1;
    border-radius: 8px;
    padding: 3px;
    gap: 3px;
  }

  .toggle-btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: #666;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .toggle-btn:hover {
    color: #333;
  }

  .toggle-btn.active {
    background: white;
    color: #2c3e50;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .simulation-badge {
    display: inline-block;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 500;
    margin-bottom: 1.5rem;
    text-align: center;
  }

  .simulation-badge.modern {
    background: linear-gradient(135deg, #3498db, #2980b9);
    color: white;
  }

  .simulation-badge.all-time {
    background: linear-gradient(135deg, #9b59b6, #8e44ad);
    color: white;
  }

  .stage-section {
    margin-bottom: 3rem;
  }

  h3 {
    color: #2c3e50;
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .groups-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
    gap: 1.5rem;
  }

  .fade-in {
    animation: fadeInStage 0.6s ease-out forwards;
  }

  @keyframes fadeInStage {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid rgba(52, 152, 219, 0.2);
    border-top: 4px solid #3498db;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 1rem auto;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  /* Champion Card Styles */
  .champion-card-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: 2rem;
  }

  .champion-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 5rem;
    border-radius: 16px;
    background: linear-gradient(135deg, #f1c40f, #f39c12);
    color: white;
    box-shadow: 0 10px 20px rgba(243, 156, 18, 0.3);
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0% {
      transform: scale(1);
      box-shadow: 0 10px 20px rgba(243, 156, 18, 0.3);
    }
    50% {
      transform: scale(1.02);
      box-shadow: 0 15px 30px rgba(243, 156, 18, 0.4);
    }
    100% {
      transform: scale(1);
      box-shadow: 0 10px 20px rgba(243, 156, 18, 0.3);
    }
  }

  .champion-flag {
    width: 80px;
    height: 50px;
    object-fit: cover;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    margin-bottom: 1rem;
  }

  .place-label {
    font-size: 1.2rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    opacity: 0.9;
    margin-bottom: 1rem;
    font-weight: 600;
  }

  .team-name {
    font-size: 3rem;
    font-weight: 800;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    text-align: center;
  }

  @media (max-width: 768px) {
    .groups-grid {
      grid-template-columns: 1fr;
    }
    .champion-card {
      padding: 2rem 3rem;
    }
    .team-name {
      font-size: 2rem;
    }
  }
</style>
