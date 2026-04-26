<script>
  import Hero from './lib/Hero.svelte'
  import SimulationResults from './lib/SimulationResults.svelte'
  
  let showSimulation = $state(false);

  function handleStart() {
    showSimulation = true;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
</script>

<main>
  {#if !showSimulation}
    <Hero onstart={handleStart} />
  {:else}
    <div class="simulation-view">
      <SimulationResults />
    </div>
  {/if}
</main>

<style>
  main {
    min-height: 100vh;
    background-color: var(--color-bg);
    color: var(--color-text);
  }

  .simulation-view {
    animation: fadeIn 0.8s ease-out;
  }
</style>
