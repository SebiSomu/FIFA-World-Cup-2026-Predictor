<script lang="ts">
  import MatchResult from './MatchResult.svelte';
  import { fade, fly } from 'svelte/transition';
  
  let { 
    matchesByStage, 
    visibleStages, 
    showResultsFor = null 
  } = $props<{
    matchesByStage: Record<string, any[]>;
    visibleStages: string[];
    showResultsFor?: string | null;
  }>();
  
  // Stages that have their own columns
  const standardStages = [
    "Round of 32", 
    "Round of 16", 
    "Quarter-Final", 
    "Semi-Final"
  ];
</script>

<div class="bracket-wrapper" in:fade>
  <div class="bracket">
    {#each standardStages as stage}
      {#if visibleStages.includes(stage)}
        <div class="bracket-column" in:fly={{ x: 20, duration: 500 }}>
          <h4 class="stage-title">
            {stage === 'Quarter-Final' ? 'Quarter-finals' : stage === 'Semi-Final' ? 'Semi-finals' : stage}
          </h4>
          <div class="matches-container">
            {#each (matchesByStage[stage] || []) as match}
              <div class="match-wrapper">
                <MatchResult 
                  {...match} 
                  hideResults={stage === showResultsFor ? false : (visibleStages.indexOf(stage) > visibleStages.indexOf(showResultsFor || '') ? true : false)} 
                />
              </div>
            {/each}
          </div>
        </div>
      {/if}
    {/each}

    <!-- Combined column for Final and Third Place -->
    {#if visibleStages.includes("Final") || visibleStages.includes("Third Place")}
      <div class="bracket-column finals-column" in:fly={{ x: 20, duration: 500 }}>
        {#if visibleStages.includes("Final")}
          <div class="final-section">
            <h4 class="stage-title">Final</h4>
            <div class="matches-container">
              {#each (matchesByStage["Final"] || []) as match}
                <div class="match-wrapper">
                  <MatchResult 
                    {...match} 
                    hideResults={showResultsFor !== "Final" && showResultsFor !== "Champion"}
                  />
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
                  <MatchResult 
                    {...match} 
                    hideResults={showResultsFor !== "Third Place" && showResultsFor !== "Final" && showResultsFor !== "Champion"}
                  />
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
    padding: 3rem 2rem;
    background: rgba(255, 255, 255, 0.01);
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    margin-bottom: 2rem;
    scrollbar-width: thin;
    scrollbar-color: var(--color-accent-blue) transparent;
  }
  
  .bracket {
    display: flex;
    justify-content: flex-start;
    align-items: stretch;
    min-width: max-content;
    gap: 4rem;
  }
  
  .bracket-column {
    display: flex;
    flex-direction: column;
    min-width: 260px;
    position: relative;
  }
  
  .matches-container {
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    flex-grow: 1;
    gap: 2rem;
    padding: 2rem 0;
  }
  
  .stage-title {
    text-align: left;
    color: #fff;
    margin-top: 0;
    margin-bottom: 2rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    font-size: 0.9rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 2px;
    opacity: 0.6;
  }
  
  .finals-column {
    display: flex;
    flex-direction: column;
    gap: 4rem;
    justify-content: center;
    flex-grow: 1;
  }
  
  .final-section, .third-place-section {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }

  .match-wrapper {
    position: relative;
    width: 100%;
    max-width: 240px;
    min-height: 120px; /* Consistent height for alignment */
    display: flex;
    align-items: center;
  }

  .match-wrapper::after {
    content: '';
    position: absolute;
    right: -4rem;
    width: 4rem;
    height: 1px;
    background: rgba(255, 255, 255, 0.05);
  }

  .bracket-column:last-child .match-wrapper::after {
    display: none;
  }

  /* Custom Scrollbar */
  .bracket-wrapper::-webkit-scrollbar {
    height: 4px;
  }
  .bracket-wrapper::-webkit-scrollbar-track {
    background: transparent;
  }
  .bracket-wrapper::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
  }
</style>
