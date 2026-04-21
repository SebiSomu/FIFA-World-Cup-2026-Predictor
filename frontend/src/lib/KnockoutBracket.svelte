<script lang="ts">
  import MatchResult from './MatchResult.svelte';
  
  export let matchesByStage: Record<string, any[]>;
  export let visibleStages: string[];
  
  // Stages that have their own columns
  const standardStages = [
    "Round of 32", 
    "Round of 16", 
    "Quarter-Final", 
    "Semi-Final"
  ];
</script>

<div class="bracket-wrapper">
  <div class="bracket">
    {#each standardStages as stage}
      {#if visibleStages.includes(stage)}
        <div class="bracket-column">
          <h4 class="stage-title">{stage === 'Quarter-Final' ? 'Quarter-finals' : stage === 'Semi-Final' ? 'Semi-finals' : stage}</h4>
          <div class="matches-container">
            {#each (matchesByStage[stage] || []) as match}
              <div class="match-wrapper">
                <MatchResult {...match} />
              </div>
            {/each}
          </div>
        </div>
      {/if}
    {/each}

    <!-- Combined column for Final and Third Place -->
    {#if visibleStages.includes("Final") || visibleStages.includes("Third Place")}
      <div class="bracket-column finals-column">
        {#if visibleStages.includes("Final")}
          <div class="final-section">
            <h4 class="stage-title">Final</h4>
            <div class="matches-container">
              {#each (matchesByStage["Final"] || []) as match}
                <div class="match-wrapper">
                  <MatchResult {...match} />
                </div>
              {/each}
            </div>
          </div>
        {/if}

        {#if visibleStages.includes("Third Place")}
          <div class="third-place-section">
            <h4 class="stage-title">Third place final</h4>
            <div class="matches-container">
              {#each (matchesByStage["Third Place"] || []) as match}
                <div class="match-wrapper">
                  <MatchResult {...match} />
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .bracket-wrapper {
    overflow-x: auto;
    padding: 1.5rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    border: 1px solid #e1e4e8;
    margin-bottom: 2rem;
  }
  
  .bracket {
    display: flex;
    justify-content: flex-start;
    align-items: stretch;
    min-width: max-content;
    gap: 1rem;
  }
  
  .bracket-column {
    display: flex;
    flex-direction: column;
    min-width: 170px;
    position: relative;
  }
  
  /* Connector lines for bracket visual */
  .bracket-column:not(:last-child)::after {
    content: '';
    position: absolute;
    right: -0.5rem;
    top: 50px;
    bottom: 50px;
    width: 2px;
    background-color: transparent; /* Can add lines if desired */
  }
  
  .matches-container {
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    flex-grow: 1;
    gap: 0.5rem;
    padding: 0.5rem 0;
  }
  
  .matches-container.single {
    max-width: 220px;
  }
  
  .stage-title {
    text-align: center;
    color: #2c3e50;
    margin-top: 0;
    margin-bottom: 0.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #ecf0f1;
    font-size: 1rem;
    position: sticky;
    top: 0;
    background: white;
    z-index: 10;
  }
  
  .finals-column {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    justify-content: center;
    flex-grow: 1;
  }
  
  .final-section, .third-place-section {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .match-wrapper {
    position: relative;
    /* Optional: subtle animations when they appear */
    animation: fadeIn 0.5s ease-out forwards;
    width: 100%;
    max-width: 220px;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
</style>
