<script lang="ts">
  import { getFlagUrl } from './flags';

  let {
    home_team,
    away_team,
    home_score,
    away_score,
    winner = null,
    score_detail = null,
    hideResults = false
  } = $props<{
    home_team: string;
    away_team: string;
    home_score: number;
    away_score: number;
    winner?: string | null;
    score_detail?: string | null;
    hideResults?: boolean;
  }>();
</script>

<div class={`match-card ${hideResults ? 'hidden' : ''}`}>
  <div class={`team-row ${(!hideResults && winner === home_team) ? 'winner' : ''}`}>
    <div class="team-info">
      {#if getFlagUrl(home_team)}
        <img src={getFlagUrl(home_team)} class="flag" alt={home_team} />
      {/if}
      <span class="team-name">{home_team}</span>
    </div>
    <span class="team-score">{hideResults ? '-' : home_score}</span>
  </div>
  
  <div class={`team-row ${(!hideResults && winner === away_team) ? 'winner' : ''}`}>
    <div class="team-info">
      {#if getFlagUrl(away_team)}
        <img src={getFlagUrl(away_team)} class="flag" alt={away_team} />
      {/if}
      <span class="team-name">{away_team}</span>
    </div>
    <span class="team-score">{hideResults ? '-' : away_score}</span>
  </div>

  {#if !hideResults && score_detail}
    <div class="match-detail">{score_detail}</div>
  {/if}
</div>

<style>
  .match-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 0.75rem;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    margin-bottom: 0.6rem;
    width: 100%;
    max-width: 240px;
  }
  
  .match-card:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateX(4px);
    border-color: var(--color-accent-blue);
  }

  .match-card.hidden {
    opacity: 0.8;
  }

  .team-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.4rem;
    border-radius: 8px;
    margin-bottom: 4px;
    transition: background-color 0.3s;
  }
  
  .team-row.winner {
    background: linear-gradient(90deg, rgba(46, 204, 113, 0.15), transparent);
    color: var(--color-accent-green);
  }

  .team-row.winner .team-name {
    font-weight: 700;
  }

  .team-row.winner .team-score {
    color: var(--color-accent-green);
    text-shadow: 0 0 10px rgba(46, 204, 113, 0.3);
  }

  .team-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex: 1;
    overflow: hidden;
  }
  
  .flag {
    width: 24px;
    height: 16px;
    object-fit: cover;
    border-radius: 3px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
  }
  
  .team-name {
    font-size: 0.9rem;
    font-weight: 500;
    color: #e2e8f0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .team-score {
    font-size: 1.1rem;
    font-weight: 800;
    color: #fff;
    min-width: 24px;
    text-align: right;
    font-family: 'Outfit', sans-serif;
  }
  
  .match-detail {
    text-align: center;
    font-size: 0.75rem;
    color: var(--color-accent-teal);
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }
</style>
