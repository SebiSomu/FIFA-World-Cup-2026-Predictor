<script lang="ts">
  import { getFlagUrl } from './flags';

  export let home_team: string;
  export let away_team: string;
  export let home_score: number;
  export let away_score: number;
  export let winner: string | null = null;
  export let score_detail: string | null = null;
</script>

<div class="match-card">
  <div class="team-row" class:winner={winner === home_team}>
    <div class="team-info">
      {#if getFlagUrl(home_team)}
        <img src={getFlagUrl(home_team)} class="flag" alt={home_team} />
      {/if}
      <span class="team-name">{home_team}</span>
    </div>
    <span class="team-score">{home_score}</span>
  </div>
  
  <div class="team-row" class:winner={winner === away_team}>
    <div class="team-info">
      {#if getFlagUrl(away_team)}
        <img src={getFlagUrl(away_team)} class="flag" alt={away_team} />
      {/if}
      <span class="team-name">{away_team}</span>
    </div>
    <span class="team-score">{away_score}</span>
  </div>

  {#if score_detail}
    <div class="match-detail">{score_detail}</div>
  {/if}
</div>

<style>
  .match-card {
    background: white;
    border-radius: 6px;
    padding: 0.5rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    transition: transform 0.2s, box-shadow 0.2s;
    border: 1px solid #e1e4e8;
    margin-bottom: 0.4rem;
    width: 100%;
    max-width: 220px;
  }
  .match-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }
  .team-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.25rem;
    border-radius: 4px;
    margin-bottom: 2px;
  }
  .team-row.winner {
    background-color: #f0f2f5;
  }
  .team-row.winner .team-name, .team-row.winner .team-score {
    font-weight: 800;
    color: #1a252f;
  }
  .team-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex: 1;
    overflow: hidden;
  }
  .flag {
    width: 20px;
    height: 14px;
    object-fit: cover;
    border-radius: 2px;
    box-shadow: 0 0 2px rgba(0,0,0,0.2);
  }
  .team-name {
    font-size: 0.85rem;
    font-weight: 600;
    color: #2c3e50;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .team-score {
    font-size: 0.95rem;
    font-weight: 700;
    color: #34495e;
    min-width: 20px;
    text-align: right;
  }
  .match-detail {
    text-align: center;
    font-size: 0.7rem;
    color: #4a5568;
    margin-top: 0.3rem;
    padding-top: 0.3rem;
    border-top: 1px dashed #cbd5e0;
    font-weight: 500;
  }
</style>
