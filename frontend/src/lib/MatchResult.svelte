<script lang="ts">
  export let home_team: string;
  export let away_team: string;
  export let home_score: number;
  export let away_score: number;
  export let winner: string | null = null;
  export let score_detail: string | null = null;
</script>

<div class="match-card">
  <div class="match-teams">
    <span class="team" class:winner={winner === home_team}>
      {home_team}
    </span>
    <span class="score">{home_score} - {away_score}</span>
    <span class="team" class:winner={winner === away_team}>
      {away_team}
    </span>
  </div>
  {#if score_detail}
    <div class="match-detail">{score_detail}</div>
  {/if}
</div>

<style>
  .match-card {
    background: white;
    border-radius: 8px;
    padding: 0.75rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    transition: transform 0.2s, box-shadow 0.2s;
    border: 1px solid #e1e4e8;
    margin-bottom: 0.5rem;
    min-width: 250px;
  }
  .match-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }
  .match-teams {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
    font-size: 0.95rem;
    color: #2c3e50;
  }
  .team {
    flex: 1;
    text-align: center;
    padding: 0.25rem;
    border-radius: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .team.winner {
    font-weight: 800;
    color: #1a252f;
    background-color: #f0f2f5;
  }
  .score {
    padding: 0.2rem 0.6rem;
    font-size: 1.2rem;
    font-weight: 800;
    color: #ffffff;
    background: #34495e;
    border-radius: 6px;
    white-space: nowrap;
    margin: 0 0.5rem;
  }
  .match-detail {
    text-align: center;
    font-size: 0.8rem;
    color: #4a5568;
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px dashed #cbd5e0;
    font-weight: 500;
  }
</style>
