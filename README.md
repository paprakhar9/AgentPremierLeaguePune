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