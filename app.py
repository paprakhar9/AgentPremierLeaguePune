import streamlit as st

from agent import run_agent_cycle
from config import create_client, get_api_key
from live_data import fetch_live_matches_from_google
from ui import inject_styles, init_session_state, render_loading_screen, render_main, render_sidebar

api_key = get_api_key()
if not api_key:
    st.error(
        "Missing Gemini API key. Set GOOGLE_API_KEY, GEMINI_API_KEY, GENAI_API_KEY, or OPENAI_API_KEY in the environment or add a .env file to the repository."
    )
    st.stop()

client = create_client(api_key)

# -----------------------------------------------------------------------------
# 1. Page Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="APL | Autonomous Fantasy Manager",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()
init_session_state()

# Show loading screen on first run, then proceed to main app
if "page_loaded" not in st.session_state:
    render_loading_screen()
    st.session_state.page_loaded = True
    import time
    time.sleep(1.5)
    st.rerun()

sim_score, sim_over, sim_pitch, sim_target, show_match_state = render_sidebar()

@st.cache_data(ttl=300)
def load_live_matches():
    return fetch_live_matches_from_google()

live_matches = load_live_matches()

match_state = {
    "score": sim_score,
    "over": f"{sim_over:.1f}",
    "pitch_condition": sim_pitch,
    "projected_target": sim_target,
    "current_squad_bowling_next": "p_siraj",
    "bench_available": ["p_chahal", "r_ashwin", "m_shami"],
}

run_requested = render_main(match_state, show_match_state, live_matches)

if run_requested:
    st.session_state.latest_trade = None
    st.session_state.agent_summary = None

    with st.spinner("Analyzing match conditions and bench strength..."):
        st.session_state.agent_summary = run_agent_cycle(client, match_state)
