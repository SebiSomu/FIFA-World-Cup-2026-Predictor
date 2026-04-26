<script lang="ts">
  import { tick } from "svelte";
  import { fade, fly } from "svelte/transition";
  import "../app.css";
  import GroupTable from "./GroupTable.svelte";
  import ThirdPlacedTable from "./ThirdPlacedTable.svelte";
  import KnockoutBracket from "./KnockoutBracket.svelte";
  import Footer from "./Footer.svelte";
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
    simulation_type: "modern" | "all_time";
  }

  type SimulationType = "modern" | "all_time";

  interface SimulationData {
    status: string;
    simulation: Simulation;
    matches_by_stage: Record<string, Match[]>;
    standings: Record<string, TeamRecord[]>;
  }

  let results = $state<SimulationData | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);
  let errorDetail = $state<string | null>(null);
  let selectedType = $state<SimulationType>("modern");

  let currentStageIndex = $state(-1);
  let revealingCurrentKnockout = $state(false);

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

  let visibleStages = $derived(stages.slice(2, currentStageIndex + 1));
  let showResultsFor = $derived(
    revealingCurrentKnockout
      ? stages[currentStageIndex]
      : currentStageIndex > 2
        ? stages[currentStageIndex - 1]
        : null,
  );

  const API_URL = "http://localhost:8000/api";

  async function loadSimulation() {
    loading = true;
    error = null;
    errorDetail = null;
    currentStageIndex = -1;
    revealingCurrentKnockout = false;
    results = null;

    try {
      const response = await fetch(
        `${API_URL}/results/full/?type=${selectedType}`,
      );

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

      for (const [groupName, teams] of Object.entries(data.standings)) {
        for (const team of teams) {
          team.group = groupName;
        }
      }

      results = data;
      currentStageIndex = 0;
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
      const isKnockout = currentStageIndex >= 2 && currentStageIndex <= 7;

      if (isKnockout && !revealingCurrentKnockout) {
        revealingCurrentKnockout = true;
      } else {
        currentStageIndex++;
        revealingCurrentKnockout = currentStageIndex < 2; // Groups and Third-placed don't have reveal step
      }

      await tick();

      // Scroll logic
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
        // window.scrollTo({ top: 0, behavior: "smooth" });
      }
    }
  }

  function getThirdPlacedTeams(): TeamRecord[] {
    if (!results) return [];
    let thirds: TeamRecord[] = [];
    for (const teams of Object.values(results.standings)) {
      if (teams.length >= 3) {
        thirds.push(teams[2]);
      }
    }
    return thirds;
  }

  function getStageLabel(stageName: string) {
    if (stageName === "Quarter-Final") return "Quarter-finals";
    if (stageName === "Semi-Final") return "Semi-finals";
    if (stageName === "Third Place") return "Third place final";
    return stageName;
  }

  function getButtonText() {
    if (currentStageIndex < 0) return "Load Simulation";

    const isKnockout = currentStageIndex >= 2 && currentStageIndex <= 7;
    if (isKnockout && !revealingCurrentKnockout) {
      return `Reveal ${getStageLabel(stages[currentStageIndex])} Results`;
    }

    if (currentStageIndex === stages.length - 1) return "Simulation Complete";

    return `Next: ${getStageLabel(stages[currentStageIndex + 1])}`;
  }
</script>

<div class="simulation-container">
  <div class="header premium-card" in:fade>
    <div class="title-section">
      <h2>FIFA World Cup 2026™</h2>
      <p class="tagline">Road to North America</p>
    </div>

    {#if !results && !loading}
      <div class="controls-row">
        <div class="simulation-toggle">
          <span class="toggle-label">Algorithm:</span>
          <div class="toggle-buttons">
            <button
              class={`toggle-btn ${selectedType === "modern" ? "active" : ""}`}
              onclick={() => (selectedType = "modern")}
            >
              Modern
            </button>
            <button
              class={`toggle-btn ${selectedType === "all_time" ? "active" : ""}`}
              onclick={() => (selectedType = "all_time")}
            >
              All-Time
            </button>
          </div>
        </div>
        <button class="btn-primary" onclick={loadSimulation}>
          Start Simulation
        </button>
      </div>
    {/if}

    {#if results && currentStageIndex < stages.length - 1}
      <div class="controls">
        <button class="btn-primary next-button" onclick={nextStage}>
          {getButtonText()}
        </button>
      </div>
    {/if}
  </div>

  {#if error}
    <div class="error premium-card" in:fly={{ y: 20 }}>
      <strong>Simulation Error</strong>
      <pre>{error}</pre>
      {#if errorDetail}
        <p class="error-hint">{errorDetail}</p>
      {/if}
    </div>
  {/if}

  {#if loading}
    <div class="loading" in:fade>
      <div class="spinner"></div>
      <p>Processing millions of permutations...</p>
    </div>
  {/if}

  {#if results && currentStageIndex >= 0}
    <div class="main-content" in:fade>
      <div class="info-bar">
        <div
          class={`simulation-badge ${results.simulation.simulation_type === "modern" ? "modern" : "all-time"}`}
        >
          {results.simulation.simulation_type === "modern"
            ? "Modern Methodology"
            : "All-Time Historical Data"}
        </div>
        <div class="current-stage-badge">
          Current: {getStageLabel(stages[currentStageIndex])}
        </div>
      </div>

      <div class="results">
        <!-- Group Stage View -->
        {#if currentStageIndex === 0}
          <div class="stage-section" in:fly={{ y: 30, duration: 800 }}>
            <h3 class="section-title">Group Standings</h3>
            <div class="groups-grid">
              {#each Object.entries(results.standings) as [group, teams]}
                <GroupTable groupName={group} {teams} />
              {/each}
            </div>
          </div>
        {/if}

        <!-- Third Placed Teams View -->
        {#if currentStageIndex === 1}
          <div class="stage-section" in:fly={{ y: 30, duration: 800 }}>
            <ThirdPlacedTable teams={getThirdPlacedTeams()} />
          </div>
        {/if}

        <!-- Knockout Stage Bracket View -->
        {#if currentStageIndex >= 2 && currentStageIndex <= 7}
          <div class="stage-section" in:fly={{ y: 30, duration: 800 }}>
            <h3 class="section-title">Final Tournament Bracket</h3>
            <KnockoutBracket
              matchesByStage={results.matches_by_stage}
              {visibleStages}
              {showResultsFor}
            />
          </div>
        {/if}

        <!-- Champion View -->
        {#if currentStageIndex === 8}
          <div class="stage-section final-results" in:fade={{ duration: 1000 }}>
            <h3 class="section-title">World Cup Champion</h3>
            <div class="champion-card-container">
              <div class="champion-card">
                <span class="place-label">World Champion 2026</span>
                {#if getFlagUrl(results.simulation.champion)}
                  <div class="flag-wrapper">
                    <img
                      src={getFlagUrl(results.simulation.champion)}
                      class="champion-flag"
                      alt={results.simulation.champion}
                    />
                  </div>
                {/if}
                <span class="team-name">{results.simulation.champion}</span>
                <div class="footer-msg">UNITED BY 26</div>
              </div>
            </div>
          </div>
        {/if}
      </div>
    </div>
  {/if}

  <Footer />
</div>

<style>
  .simulation-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4rem;
    flex-wrap: wrap;
    gap: 2rem;
    padding: 2rem 3rem;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.05);
  }

  .title-section h2 {
    margin: 0;
    font-size: 2.5rem;
    font-weight: 900;
    letter-spacing: -1px;
    color: #fff;
    text-transform: uppercase;
  }

  .tagline {
    margin: 0;
    font-size: 0.8rem;
    color: var(--color-accent-blue);
    letter-spacing: 4px;
    text-transform: uppercase;
    font-weight: 800;
  }

  .controls-row {
    display: flex;
    align-items: center;
    gap: 3rem;
  }

  .simulation-toggle {
    display: flex;
    align-items: center;
    gap: 1.5rem;
  }

  .toggle-label {
    font-size: 0.8rem;
    color: var(--color-text-muted);
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .toggle-buttons {
    display: flex;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 4px;
    padding: 4px;
    gap: 4px;
    border: 1px solid rgba(255, 255, 255, 0.05);
  }

  .toggle-btn {
    padding: 0.6rem 1.5rem;
    border: none;
    border-radius: 2px;
    background: transparent;
    color: #666;
    font-size: 0.75rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    transition: var(--transition-smooth);
  }

  .toggle-btn.active {
    background: #fff;
    color: #000;
  }

  .info-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 3rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }

  .simulation-badge {
    padding: 0.5rem 1.2rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .simulation-badge.modern {
    border-color: var(--color-accent-blue);
    color: var(--color-accent-blue);
    box-shadow: 0 0 10px rgba(0, 102, 255, 0.2);
  }

  .simulation-badge.all-time {
    border-color: var(--color-accent-gold);
    color: var(--color-accent-gold);
    box-shadow: 0 0 10px rgba(255, 215, 0, 0.2);
  }

  .current-stage-badge {
    font-size: 0.8rem;
    font-weight: 900;
    color: #fff;
    text-transform: uppercase;
    letter-spacing: 2px;
    opacity: 0.8;
  }

  .section-title {
    font-size: 2rem;
    font-weight: 900;
    margin-bottom: 3rem;
    text-align: left;
    color: #fff;
    text-transform: uppercase;
    letter-spacing: -0.5px;
  }

  .groups-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
    gap: 2rem;
  }

  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 5rem;
    color: var(--color-text-muted);
  }

  .spinner {
    width: 50px;
    height: 50px;
    border: 3px solid rgba(52, 152, 219, 0.1);
    border-top: 3px solid var(--color-accent-blue);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1.5rem;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .champion-card {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 5rem;
    border-radius: 4px;
    background: #000;
    border: 2px solid var(--color-accent-gold);
    box-shadow: 0 0 30px rgba(255, 215, 0, 0.2);
    overflow: hidden;
  }

  .flag-wrapper {
    margin-bottom: 2.5rem;
    padding: 8px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .champion-flag {
    width: 150px;
    height: 94px;
    object-fit: cover;
    border-radius: 2px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8);
  }

  .place-label {
    font-size: 1.2rem;
    text-transform: uppercase;
    letter-spacing: 6px;
    font-weight: 900;
    margin-bottom: 2rem;
    color: var(--color-accent-gold);
    opacity: 0.9;
  }

  .team-name {
    font-size: 5rem;
    font-weight: 900;
    text-align: center;
    letter-spacing: -2px;
    color: #fff;
    text-transform: uppercase;
  }

  .footer-msg {
    margin-top: 3rem;
    font-weight: 900;
    letter-spacing: 4px;
    opacity: 0.4;
    font-size: 0.8rem;
  }

  .simulation-footer {
    margin-top: 8rem;
    padding: 4rem 2rem;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    background: #050505;
  }

  .footer-content {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2rem;
  }

  .footer-brand {
    font-weight: 800;
    font-size: 1.1rem;
    letter-spacing: 1px;
    opacity: 0.8;
  }

  .footer-links {
    display: flex;
    gap: 3rem;
    font-size: 0.9rem;
    color: var(--color-text-muted);
    font-weight: 500;
  }

  .footer-copy {
    font-size: 0.8rem;
    color: var(--color-text-muted);
    opacity: 0.5;
  }

  @media (max-width: 768px) {
    .groups-grid {
      grid-template-columns: 1fr;
    }
    .champion-card {
      padding: 3rem 2rem;
    }
    .team-name {
      font-size: 2.5rem;
    }
    .header {
      flex-direction: column;
      align-items: stretch;
    }
    .controls-row {
      flex-direction: column;
    }
  }
</style>
