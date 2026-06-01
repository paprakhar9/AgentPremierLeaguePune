# 🏏 Autonomous Fantasy Manager (APL Hackathon)

![Agentic Premier League](https://img.shields.io/badge/Hackathon-Agentic_Premier_League-blue)
![Python](https://img.shields.io/badge/Python-3.10+-yellow)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)
![Gemini](https://img.shields.io/badge/AI-Gemini_2.5_Flash-orange)

## 🚀 The Concept
Built for the **Agentic Premier League (APL)**, this project is an autonomous fantasy cricket manager. Instead of acting as a standard Q&A chatbot, this agent monitors live match telemetry (score, pitch conditions, run rate) and autonomously executes mid-match player substitutions using a ReAct (Reasoning and Acting) loop via tool calling.

## ✨ Key Features
* **Autonomous ReAct Loop:** Uses `gemini-2.5-flash` to reason through match conditions and trigger tool calls for strategic player trades.
* **Live Telemetry Dashboard:** A sleek, dark-themed Streamlit control center to monitor pitch states, run rates, and the agent's real-time decision ledger.
* **Background Worker:** A standalone polling service (`worker.py`) that runs autonomously, reads match state, and makes decisions every 30 seconds.
* **Codespace Ready:** Designed to spin up instantly in GitHub Codespaces with built-in CORS bypass for seamless live demos.

## 🛠️ Tech Stack
* **Core AI:** `google-genai` (Gemini 2.5 Flash)
* **Interface:** `streamlit`
* **Live Data:** `requests`, `beautifulsoup4` for Google search scraping
* **Environment:** GitHub Codespaces

## ⚙️ Quick Start (GitHub Codespaces)

1. **Set your API Key:**
   Add your Gemini API key to your GitHub repository secrets as `GEMINI_API_KEY`. Alternatively, export it directly in your terminal:
```bash
export GEMINI_API_KEY="your_api_key_here"
```

2. **Install dependencies:**
```bash
pip install streamlit requests beautifulsoup4 google-genai
```

3. **Run the app:**
```bash
streamlit run app.py
```

The live data section now attempts to fetch current cricket score cards from Google search. If Google access is blocked, the dashboard falls back to a friendly empty state message.
## 🔄 Background Worker Workflow

The **autonomous worker** (`worker.py`) is a standalone service that runs in the background, independent of the Streamlit UI:

### How It Works
1. **Polling Loop:** Wakes up every 30 seconds to read `state.json`.
2. **Change Detection:** Checks if match telemetry (score, over, pitch, target) has changed.
3. **Agent Cycle:** If changes are detected, calls `gemini-2.5-flash` with the current telemetry.
4. **Autonomous Decisions:** The agent analyzes conditions and may call `execute_player_trade()` to recommend substitutions.
5. **Trade Ledger:** All trades are recorded to `state.json` with timestamps and reasoning.
6. **Error Recovery:** Network failures and API errors are caught and logged; the loop resumes on the next interval.

### Running the Worker

In a separate terminal:

```bash
# Ensure your API key is set
export GEMINI_API_KEY="your_api_key_here"

# Run the worker
python worker.py
```

You should see logs like:
```
2026-06-01 10:00:00 [INFO] Autonomous Fantasy Cricket Manager Worker Starting
2026-06-01 10:00:00 [INFO] --- Polling Cycle 1 ---
2026-06-01 10:00:02 [INFO] Cycle 1 complete. (elapsed: 0.45s, next wake: +29.55s)
```

### State File (`state.json`)

The worker reads and updates `state.json`:

```json
{
  "live_telemetry": {
    "score": "142/5",
    "over": 15.2,
    "pitch_condition": "Dry & Turning",
    "projected_target": 195
  },
  "trade_ledger": [
    {
      "out": "p_siraj",
      "in": "p_chahal",
      "reason": "Spinner recommended on turning pitch",
      "timestamp": "2026-06-01T10:05:30.123456"
    }
  ],
  "last_run": "2026-06-01T10:05:32.456789"
}
```

### Integration with Streamlit

The Streamlit app (`app.py`) can display the `trade_ledger` from `state.json` in real time. Both the app and worker read/write to the same state file, creating a two-way feedback loop:
- User updates match conditions in Streamlit → Worker detects changes and runs agent
- Worker executes a trade → Streamlit reads and displays it in the transaction ledger

## 📊 Running Both Services Together

For a complete autonomous fantasy cricket experience:

**Terminal 1** (Streamlit UI):
```bash
streamlit run app.py --server.enableCORS false --server.enableXsrfProtection false
```

**Terminal 2** (Background Worker):
```bash
python worker.py
```

The worker will continuously monitor and make autonomous decisions, while the UI allows you to adjust match conditions and view recommendations in real time.
