<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import Footer from './Footer.svelte';

  let { onstart } = $props<{ onstart: () => void }>();

  function start() {
    onstart();
  }
</script>

<div class="hero-container" in:fade={{ duration: 800 }}>
  <div class="bg-gradient"></div>
  <div class="bg-elements">
    <div class="neon-ring r1"></div>
    <div class="neon-ring r2"></div>
    <div class="neon-ring r3"></div>
  </div>

  <div class="content-wrapper">
    <div class="content">
      <div class="logo-area" in:fly={{ y: -50, duration: 1000, delay: 200 }}>
        <span class="we-are">WE ARE</span>
        <span class="twenty-six">26</span>
      </div>

      <h1 in:fly={{ y: 30, duration: 1000, delay: 400 }}>FIFA World Cup 2026™ Predictor</h1>
      <p class="subtitle" in:fly={{ y: 30, duration: 1000, delay: 600 }}>
        Simulate the path to glory using state-of-the-art technology and historical data.
      </p>

      <div class="explanation-grid">
        <div class="item" in:fly={{ x: -30, duration: 800, delay: 800 }}>
          <div class="neon-line red"></div>
          <div class="text">
            <h3>Historical Data</h3>
            <p>Analyzing over a century of matches to understand each nation's competitive DNA.</p>
          </div>
        </div>
        <div class="item" in:fly={{ x: 30, duration: 800, delay: 1000 }}>
          <div class="neon-line blue"></div>
          <div class="text">
            <h3>Elo System</h3>
            <p>Sophisticated chess-style rankings tailored for the dynamics of modern football.</p>
          </div>
        </div>
        <div class="item" in:fly={{ x: -30, duration: 800, delay: 1200 }}>
          <div class="neon-line green"></div>
          <div class="text">
            <h3>Home Advantage</h3>
            <p>Calculating the significant impact of local support in the USA, Mexico, and Canada.</p>
          </div>
        </div>
        <div class="item" in:fly={{ x: 30, duration: 800, delay: 1400 }}>
          <div class="neon-line gold"></div>
          <div class="text">
            <h3>Recent Form</h3>
            <p>Prioritizing recent performances to capture the current momentum of every squad.</p>
          </div>
        </div>
      </div>

      <div class="actions" in:fade={{ delay: 1800 }}>
        <button class="btn-primary start-btn" onclick={start}>
          Start Simulation
        </button>
      </div>
    </div>
  </div>
  <Footer />
</div>

<style>
  .hero-container {
    position: relative;
    width: 100%;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    color: white;
  }

  .content-wrapper {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    width: 100%;
  }

  .bg-gradient {
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at center, #0a0a0a 0%, #000 100%);
    z-index: -2;
  }

  .bg-elements {
    position: absolute;
    inset: 0;
    z-index: -1;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }

  .neon-ring {
    position: absolute;
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 20%;
    animation: pulse 10s infinite ease-in-out;
  }

  .r1 { width: 40vw; height: 40vw; border-color: var(--color-accent-blue); opacity: 0.1; animation-delay: 0s; }
  .r2 { width: 60vw; height: 60vw; border-color: var(--color-accent-magenta); opacity: 0.05; animation-delay: -2s; }
  .r3 { width: 80vw; height: 80vw; border-color: var(--color-accent-green); opacity: 0.03; animation-delay: -4s; }

  @keyframes pulse {
    0%, 100% { transform: scale(1) rotate(0deg); opacity: 0.05; }
    50% { transform: scale(1.1) rotate(5deg); opacity: 0.1; }
  }

  .content {
    max-width: 1000px;
    text-align: center;
    z-index: 1;
  }

  .logo-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 2rem;
  }

  .we-are {
    font-size: 1.4rem;
    font-weight: 900;
    letter-spacing: 0.8rem;
    color: #fff;
    margin-bottom: 0.5rem;
    opacity: 0.6;
  }

  .twenty-six {
    font-size: 8rem;
    font-weight: 900;
    line-height: 0.8;
    background: linear-gradient(135deg, #fff 0%, #666 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 20px rgba(255,255,255,0.1));
  }

  h1 {
    font-size: 3.5rem;
    font-weight: 800;
    margin-bottom: 1rem;
    letter-spacing: -0.04em;
    color: #fff;
  }

  .subtitle {
    font-size: 1.4rem;
    color: var(--color-text-muted);
    margin-bottom: 4rem;
    max-width: 700px;
    margin-left: auto;
    margin-right: auto;
    font-weight: 300;
  }

  .explanation-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
    text-align: left;
    margin-bottom: 5rem;
  }

  .item {
    display: flex;
    align-items: flex-start;
    gap: 1.5rem;
    background: rgba(255, 255, 255, 0.02);
    padding: 2rem;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    transition: var(--transition-smooth);
  }

  .item:hover {
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(255, 255, 255, 0.1);
  }

  .neon-line {
    width: 4px;
    height: 40px;
    border-radius: 2px;
    flex-shrink: 0;
  }

  .neon-line.red { background: var(--color-accent-magenta); box-shadow: 0 0 10px var(--color-accent-magenta); }
  .neon-line.blue { background: var(--color-accent-blue); box-shadow: 0 0 10px var(--color-accent-blue); }
  .neon-line.green { background: var(--color-accent-green); box-shadow: 0 0 10px var(--color-accent-green); }
  .neon-line.gold { background: var(--color-accent-gold); box-shadow: 0 0 10px var(--color-accent-gold); }

  .text h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.2rem;
    font-weight: 700;
    color: #fff;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .text p {
    margin: 0;
    font-size: 1rem;
    color: var(--color-text-muted);
    line-height: 1.6;
  }

  .start-btn {
    font-size: 1.2rem;
    padding: 1rem 3rem;
  }

  @media (max-width: 768px) {
    .explanation-grid {
      grid-template-columns: 1fr;
    }
    h1 { font-size: 2rem; }
    .twenty-six { font-size: 4rem; }
  }
</style>
