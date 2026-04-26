<script lang="ts">
  import { getFlagUrl } from './flags';
  let { groupName, teams } = $props<{ groupName: string; teams: any[] }>();
</script>

<div class="group-table-container premium-card">
  <h4>Group {groupName}</h4>
  <div class="table-responsive">
    <table>
      <thead>
        <tr>
          <th>Pos</th>
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
        {#each teams as team, index}
          <tr class={`${index < 2 ? 'qualified' : ''} ${index === 2 ? 'third-place-row' : ''}`}>
            <td class="position">{index + 1}</td>
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
  .group-table-container {
    padding: 1rem;
    margin-bottom: 1rem;
    background: rgba(255, 255, 255, 0.01);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }
  
  h4 {
    margin-top: 0;
    margin-bottom: 1rem;
    color: #fff;
    font-size: 1.1rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    padding-bottom: 0.5rem;
  }

  .table-responsive {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    min-width: 400px;
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
    letter-spacing: 0.2px;
  }

  .position {
    color: #444;
    font-weight: 900;
    font-size: 0.9rem;
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

  .third-place-row .team-name {
    color: var(--color-accent-blue);
  }

  .positive { color: var(--color-accent-green); opacity: 0.9; }
  .negative { color: var(--color-accent-magenta); opacity: 0.9; }
</style>
