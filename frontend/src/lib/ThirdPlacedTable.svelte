<script lang="ts">
  export let teams: any[];
  
  $: sortedTeams = [...teams].sort((a, b) => {
    if (b.points !== a.points) return b.points - a.points;
    if (b.goal_diff !== a.goal_diff) return b.goal_diff - a.goal_diff;
    return b.goals_for - a.goals_for;
  });
</script>

<div class="third-placed-container">
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
          <th>GF</th>
          <th>GA</th>
          <th>GD</th>
          <th>Pts</th>
        </tr>
      </thead>
      <tbody>
        {#each sortedTeams as team, index}
          <tr class:qualified={index < 8}>
            <td class="position">{index + 1}</td>
            <td class="group">{team.group}</td>
            <td class="team-name">{team.team}</td>
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
  .third-placed-container {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    margin-bottom: 2rem;
    border: 1px solid #e1e4e8;
  }
  h4 {
    margin-top: 0;
    margin-bottom: 0.25rem;
    color: #2c3e50;
    font-size: 1.2rem;
  }
  .subtitle {
    color: #7f8c8d;
    font-size: 0.9rem;
    margin-bottom: 1rem;
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
  .team-name {
    text-align: left;
    font-weight: 600;
    white-space: nowrap;
    color: #2c3e50;
  }
  .position {
    color: #2c3e50;
    font-weight: 800;
    font-size: 1rem;
  }
  .group {
    font-weight: 800;
    color: #34495e;
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
  tr:not(.qualified) td {
    opacity: 0.7;
  }
  tr:not(.qualified) .team-name {
    text-decoration: line-through;
    color: #c0392b;
  }
</style>
