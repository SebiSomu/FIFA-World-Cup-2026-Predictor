<script lang="ts">
  import { getFlagUrl } from './flags';
  let { teams } = $props<{ teams: any[] }>();
  
  let sortedTeams = $derived([...teams].sort((a, b) => {
    if (b.points !== a.points) return b.points - a.points;
    if (b.goal_diff !== a.goal_diff) return b.goal_diff - a.goal_diff;
    return b.goals_for - a.goals_for;
  }));
</script>

<div class="third-placed-container premium-card">
  <h4>Ranking of 3rd Placed Teams</h4>
  <p class="subtitle">Top 8 qualify for the Round of 32</p>
  
  <div class="table-responsive">
    <table>
      <thead>
        <tr>
          <th>Pos</th>
          <th>Grp</th>
          <th>Team</th>
          <th>P</th>
          <th>W</th>
          <th>D</th>
          <th>L</th>
          <th>GD</th>
          <th>Pts</th>
        </tr>
      </thead>
      <tbody>
        {#each sortedTeams as team, index}
          <tr class={index < 8 ? 'qualified' : ''}>
            <td class="position">{index + 1}</td>
            <td class="group">{team.group}</td>
            <td class="team-cell">
              <div class="team-content">
                {#if getFlagUrl(team.team)}
                  <img src={getFlagUrl(team.team)} class="table-flag" alt={team.team} />
                {/if}
                <span class="team-name">{team.team}</span>
              </div>
            </td>
            <td>{team.played}</td>
            <td>{team.wins}</td>
            <td>{team.draws}</td>
            <td>{team.losses}</td>
            <td class={team.goal_diff > 0 ? 'positive' : team.goal_diff < 0 ? 'negative' : ''}>
              {team.goal_diff > 0 ? `+${team.goal_diff}` : team.goal_diff}
            </td>
            <td class="points"><strong>{team.points}</strong></td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</div>

<style>
  .third-placed-container {
    padding: 1rem;
    margin-bottom: 2rem;
    background: rgba(255, 255, 255, 0.01);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }

  h4 {
    margin-top: 0;
    margin-bottom: 0.5rem;
    color: #fff;
    font-size: 1.2rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .subtitle {
    color: var(--color-text-muted);
    font-size: 0.85rem;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    padding-bottom: 1rem;
    font-weight: 600;
  }

  .table-responsive {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    min-width: 500px;
  }

  th, td {
    padding: 0.6rem 0.4rem;
    text-align: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.03);
  }

  th {
    color: var(--color-text-muted);
    font-weight: 800;
    text-transform: uppercase;
    font-size: 0.65rem;
    letter-spacing: 1px;
  }

  .team-cell {
    text-align: left;
  }

  .team-content {
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }

  .table-flag {
    width: 20px;
    height: 13px;
    object-fit: cover;
    border-radius: 1px;
    opacity: 0.8;
  }

  .team-name {
    font-weight: 700;
    white-space: nowrap;
    color: #eee;
  }

  .position {
    color: #444;
    font-weight: 900;
    font-size: 0.9rem;
  }

  .group {
    font-weight: 900;
    color: var(--color-accent-blue);
    opacity: 0.8;
  }

  .points {
    color: #fff;
    font-size: 1rem;
  }

  tr:hover {
    background: rgba(255, 255, 255, 0.02);
  }

  .qualified .team-name {
    color: var(--color-accent-green);
  }

  tr:not(.qualified) {
    opacity: 0.3;
  }

  tr:not(.qualified) .team-name {
    text-decoration: line-through;
    color: var(--color-accent-magenta);
  }

  .positive { color: var(--color-accent-green); opacity: 0.8; }
  .negative { color: var(--color-accent-magenta); opacity: 0.8; }
</style>
