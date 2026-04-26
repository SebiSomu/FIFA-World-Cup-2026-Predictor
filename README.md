# 🏆 FIFA World Cup 2026™ Predictor

A high-fidelity simulation engine and web platform designed to predict the outcome of the **FIFA World Cup 2026**. Using advanced statistical modeling and historical data, this tool simulates all 104 matches of the expanded 48-team tournament, from the initial group stages to the final.

![Neon Pro UI](https://img.shields.io/badge/UI-Neon_Black-blueviolet?style=for-the-badge)
![Engine](https://img.shields.io/badge/Algorithm-Dixon--Coles-green?style=for-the-badge)
![Framework](https://img.shields.io/badge/Svelte-5-ff3e00?style=for-the-badge)

---

## 🧠 The Prediction Engine

The core of this project isn't just random chance; it's a sophisticated mathematical model that understands the "DNA" of international football.

### 1. Dixon-Coles Model
I used a **Dixon-Coles Hybrid Predictor** for predicting the match outcomes. Unlike simple Poisson distributions, this model:
- Accounts for the low-score nature of football.
- Adjusts for "draw inflation" (the fact that 0-0 or 1-1 scores are more common than math predicts).
- Uses a time-decay factor to weigh recent matches more heavily than games played in the 1950s.

### 2. Live Elo Ratings
Every team is assigned a dynamic **Elo Rating** (similar to Chess rankings).
- Ratings update *during* the tournament simulation.
- If an underdog beats a giant in the Group Stage, their confidence and strength (Elo) increase for the Knockout rounds.

### 3. Home Advantage & Recent Form
- **Triple-Host Bonus**: Special statistical weighting is applied to the **USA, Mexico, and Canada** when playing "at home."
- **Momentum Tracking**: We analyze a team's last 5-10 matches to capture their current "heat" or struggle before the tournament starts.

### 4. Weights & Mathematical Parameters
To ensure realism, the engine uses specific weights that balance historical dominance with current momentum:

- **Competition Importance (CompWeight)**: 
    - `4.0x`: FIFA World Cup
    - `3.2x`: UEFA Euro
    - `3.0x`: Copa América
    - `2.5x`: African Cup of Nations, Nations League
    - `2.0x`: AFC Asian Cup
    - `1.5x`: Oceania Nations Cup, CONCACAF Gold Cup
    - `1.0x`: Friendlies
- **The Hybrid Formula (60/40 Rule)**:
  Each match is assigned a `TotalWeight` using the formula:
  $$\text{TotalWeight} = (\text{CompWeight} \times 0.60) + (\text{RecencyWeight} \times 0.40)$$
  This ensures that a World Cup match from 10 years ago and a friendly from yesterday are balanced correctly.

- **Two Simulation Modes**:
    1. **Modern (Recommended)**: Uses exponential decay ($\lambda = 0.25$). Matches from 2 years ago carry ~61% weight, while matches from 8 years ago drop to ~14%.
    2. **All-Time**: Temporally blind. Every match in history is treated with a `RecencyWeight` of `1.0`, emphasizing pure historical prestige.

- **Elo Influence**: Elo differences adjust the base predicted goals by up to **30%**.
- **Extra Time Factor**: Expected goals are reduced by **75%** during the 30 minutes of extra time to reflect player fatigue and tactical caution.

#### 💡 Calculation Example:
If **Argentina (2100 Elo)** plays **Canada (1750 Elo)**:
1. **Base Goals**: Dixon-Coles predicts ~1.8 for Argentina based on historical scoring.
2. **Elo Adjustment**: The 350-point gap increases Argentina's expected goals by ~26%.
3. **Home Advantage**: If played in Canada, Argentina's advantage is slightly mitigated by a +0.1 Elo boost for the hosts.
4. **Final Probability**: Resulting in ~65% Win, 20% Draw, 15% Loss.

Dataset took from https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017 .

---

## 🛠️ Technology Stack

- **Frontend**: [Svelte 5](https://svelte.dev/) (using the latest **Runes** API) for a blazing-fast, reactive interface;
- **Styling**: Custom CSS styles;
- **Backend**: [Django](https://www.djangoproject.com/) (Python) serves as the high-performance API hub;
- **Data Science**: [NumPy](https://numpy.org/) and [Pandas](https://pandas.pydata.org/) handle the heavy mathematical lifting and dataset processing.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Setup the Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py runserver
```

### 2. Setup the Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` to see the simulation in action!

---

## 📅 Tournament Format (FIFA 2026)
This predictor accurately follows the **new 2026 regulations**:
- **48 Teams** split into 12 groups of 4.
- **Round of 32** introduction (Top 2 from each group + 8 best 3rd-placed teams).
- **104 Matches** total simulation.

---

## ⚖️ Legal & Data
The simulation is for entertainment purposes. Historical data is sourced from open-source international football datasets (Kaggle) and up-to-date Elo ratings.

Created by Sebi Somu.