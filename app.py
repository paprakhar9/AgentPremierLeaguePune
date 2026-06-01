"""
app.py - Streamlit Frontend Application

This is the main Streamlit UI for the Autonomous Fantasy Cricket Manager.

Responsibilities:
- Display the user interface (dashboard, sidebars, metrics).
- Read state from config.py (state.json).
- Orchestrate layout and rendering via ui.py.
- NO AI/GenAI logic is included here (see agent.py for that).
"""

import streamlit as st

from config import read_state
from live_data import fetch_live_matches_from_google
from ui import inject_styles, init_session_state, render_loading_screen, render_main, render_sidebar

# ============================================================================
# Page Configuration & Styling
# ============================================================================

st.set_page_config(
    page_title="APL | Autonomous Fantasy Manager",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()
init_session_state()

# Show loading screen on first run
if "page_loaded" not in st.session_state:
    render_loading_screen()
    st.session_state.page_loaded = True
    import time
    time.sleep(1.5)
    st.rerun()

# ============================================================================
# Data Collection & Display
# ============================================================================

# Get input from sidebar (telemetry simulation)
sim_score, sim_over, sim_pitch, sim_target, show_match_state = render_sidebar()

# Load live matches (cached)
@st.cache_data(ttl=300)
def load_live_matches() -> list[dict]:
    """Fetch live cricket matches from Google search."""
    return fetch_live_matches_from_google()

live_matches = load_live_matches()

# Construct the match state object from sidebar inputs
match_state = {
    "score": sim_score,
    "over": f"{sim_over:.1f}",
    "pitch_condition": sim_pitch,
    "projected_target": sim_target,
    "current_squad_bowling_next": "p_siraj",
    "bench_available": ["p_chahal", "r_ashwin", "m_shami"],
}

# ============================================================================
# Render Main Dashboard
# ============================================================================

run_requested = render_main(match_state, show_match_state, live_matches)

# If agent run is requested, display info about the background worker
if run_requested:
    st.session_state.latest_trade = None
    st.session_state.agent_summary = None

    # Read state from disk to show recent trades
    try:
        current_state = read_state()
        trades = current_state.get("trade_ledger", [])
        if trades:
            latest_trade = trades[-1]
            st.session_state.latest_trade = {
                "out": latest_trade.get("out"),
                "in": latest_trade.get("in"),
                "reason": latest_trade.get("reason"),
                "timestamp": latest_trade.get("timestamp"),
            }
            st.success("✅ Trade recorded by background worker")
        else:
            st.info(
                "📊 The background worker (worker.py) is autonomously analyzing "
                "match conditions every 30 seconds. Trades will appear here when executed."
            )
    except Exception as e:
        st.error(f"Could not read worker state: {e}")
