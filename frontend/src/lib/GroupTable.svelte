<script lang="ts">
  import { getFlagUrl } from './flags';
  export let groupName: string;
  export let teams: any[];
</script>

<div class="group-table-container">
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
          <th>GF</th>
          <th>GA</th>
          <th>GD</th>
          <th>Pts</th>
        </tr>
      </thead>
      <tbody>
        {#each teams as team, index}
          <tr class:qualified={index < 2} class:third-place-row={index === 2}>
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
            <td>{team.goals_for}</td>
            <td>{team.goals_against}</td>
            <td>{team.goal_diff}</td>
            <td class="points"><strong>{team.points}</strong></td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</div>

<style>
  .group-table-container {
    background: white;
    border-radius: 12px;
    padding: 1.25rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    margin-bottom: 1.5rem;
    border: 1px solid #e1e4e8;
  }
  h4 {
    margin-top: 0;
    margin-bottom: 1rem;
    color: #2c3e50;
    font-size: 1.2rem;
    border-bottom: 2px solid #ecf0f1;
    padding-bottom: 0.5rem;
  }
  .table-responsive {
    overflow-x: auto;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
    min-width: 500px;
  }
  th, td {
    padding: 0.5rem 0.5rem;
    text-align: center;
    border-bottom: 1px solid #ecf0f1;
  }
  th {
    background-color: #2c3e50;
    color: #ffffff;
    font-weight: 700;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.5px;
  }
  .team-cell {
    text-align: left;
  }
  .team-content {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .table-flag {
    width: 20px;
    height: 14px;
    object-fit: cover;
    border-radius: 2px;
    box-shadow: 0 0 2px rgba(0,0,0,0.2);
  }
  .team-name {
    font-weight: 600;
    white-space: nowrap;
    color: #2c3e50;
  }
  .position {
    color: #2c3e50;
    font-weight: 800;
    font-size: 1rem;
  }
  .points {
    color: #2c3e50;
    font-size: 1.1rem;
  }
  tr:hover {
    background-color: #f0f2f5;
  }
  .qualified td {
    background-color: #e8f5e9;
    border-bottom-color: #c8e6c9;
  }
  .qualified .position {
    color: #2e7d32;
  }
  .third-place-row td {
    background-color: #fff3e0;
    border-bottom-color: #ffe0b2;
    color: #2c3e50;
  }
  .third-place-row .position {
    color: #ef6c00;
  }
</style>
