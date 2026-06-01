import streamlit as st


def inject_styles():
    st.markdown(
        """
        <style>
        .metric-container { background-color: #1e222b; padding: 16px; border-radius: 12px; border-left: 6px solid #ff4b4b; }
        .agent-box { background-color: #12161f; padding: 22px; border-radius: 14px; border: 1px solid #2d3139; }
        .small-muted { color: #a5acb8; font-size: 0.95rem; }
        
        /* Loading screen styles */
        .loading-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 4rem 2rem;
            background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%);
            border-radius: 12px;
            gap: 2rem;
            text-align: center;
        }
        .loading-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: #e3eaf7;
            margin: 0;
        }
        .loading-subtitle {
            font-size: 1.1rem;
            color: #a5acb8;
            margin: 0;
        }
        
        /* Cricket animation */
        .cricket-animation {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            height: 200px;
            width: 100%;
        }
        .bat {
            font-size: 3rem;
            display: inline-block;
            animation: bat-swing 1.2s ease-in-out infinite;
            transform-origin: right center;
        }
        .ball {
            font-size: 2rem;
            display: inline-block;
            animation: ball-motion 1.2s ease-in-out infinite;
        }
        
        @keyframes bat-swing {
            0% { transform: rotate(-45deg); }
            50% { transform: rotate(45deg); }
            100% { transform: rotate(-45deg); }
        }
        
        @keyframes ball-motion {
            0% { transform: translateX(-100px) translateY(0); opacity: 1; }
            50% { transform: translateX(0) translateY(-60px); opacity: 1; }
            100% { transform: translateX(100px) translateY(0); opacity: 0.3; }
        }
        
        .loading-dots {
            display: inline-flex;
            gap: 0.5rem;
            justify-content: center;
            margin-top: 0.5rem;
        }
        .dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: #ff4b4b;
            animation: dot-pulse 1.4s ease-in-out infinite;
            display: inline-block;
        }
        .dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        .dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes dot-pulse {
            0%, 100% { opacity: 0.3; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.2); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_loading_screen():
    """Display an animated loading screen with cricket bat and ball."""
    st.markdown(
        """
        <div class="loading-container">
            <div class="loading-title">🏏 Agentic Premier League</div>
            <div class="loading-subtitle">Autonomous Fantasy Cricket Manager</div>
            
            <div class="cricket-animation">
                <div class="bat">🏏</div>
                <div class="ball">🔴</div>
            </div>
            
            <div class="loading-subtitle">
                Initializing agent
                <div class="loading-dots">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def init_session_state():
    if "latest_trade" not in st.session_state:
        st.session_state.latest_trade = None
    if "agent_summary" not in st.session_state:
        st.session_state.agent_summary = None


def render_live_matches_bar(live_matches):
    if live_matches:
        columns = st.columns(len(live_matches), gap="large")
        for column, match in zip(columns, live_matches):
            column.markdown(
                f"""
                <div style='background:#12161f; padding:14px 16px; border-radius:12px; border:1px solid #2d3139; min-height:120px;'>
                    <div style='font-size:0.85rem; color:#a5acb8; margin-bottom:6px;'>{match['status']}</div>
                    <div style='font-size:1.05rem; font-weight:700; margin-bottom:6px;'>{match['team_a']} vs {match['team_b']}</div>
                    <div style='font-size:0.98rem; color:#e3eaf7;'>{match.get('score', 'N/A')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No live matches currently. Check back later.")


def render_sidebar():
    st.sidebar.title("🎮 Live Match Telemetry")
    st.sidebar.markdown(
        "Adjust the match state to simulate a live fantasy cricket situation. The agent will then recommend a tactical substitution."
    )

    with st.sidebar.expander("How to use", expanded=True):
        st.write("1. Update the score, over, pitch, and target.")
        st.write("2. Click the action button to run the agent.")
        st.write("3. Review the reasoning and transaction output.")
        st.write("4. Optionally inspect the raw match state below.")

    st.sidebar.markdown("**New to cricket? These terms are explained in simple language:**")
    st.sidebar.markdown("- **Current Score**: runs/wickets. Example `142/5` means 142 runs and 5 wickets lost.")
    st.sidebar.markdown("- **Current Over**: one over is 6 balls. Example `15.2` means 15 overs plus 2 balls.")
    st.sidebar.markdown("- **Pitch State**: how the field is playing, which affects batting or bowling.")
    st.sidebar.markdown("- **Target / Projected Score**: the score the batting team is trying to reach.")

    sim_score = st.sidebar.text_input("Current Score", "142/5")
    sim_over = st.sidebar.slider("Current Over", min_value=0.1, max_value=20.0, value=15.2, step=0.1)
    sim_pitch = st.sidebar.selectbox(
        "Pitch State",
        ["Dry & Turning", "Flat Batter's Paradise", "Green / Heavy Dew"],
    )
    sim_target = st.sidebar.number_input("Target / Projected Score", value=195, min_value=0)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Current Squad")
    st.sidebar.write("- **p_siraj** (bowling next)")

    st.sidebar.subheader("Bench Available")
    st.sidebar.write("- p_chahal")
    st.sidebar.write("- r_ashwin")
    st.sidebar.write("- m_shami")

    show_match_state = st.sidebar.checkbox("Show raw match state", value=False)
    return sim_score, sim_over, sim_pitch, sim_target, show_match_state


def render_main(match_state, show_match_state, live_matches):
    render_live_matches_bar(live_matches)
    st.title("⚡ Agentic Premier League: Autonomous Fantasy Engine")
    st.markdown(
        "Use the dashboard to simulate a live match decision, then let the autonomous agent determine whether a substitution improves the chase."
    )
    st.markdown(
        "If you are not familiar with cricket, the inputs below are simple match values that the agent uses to decide whether a substitution is helpful."
    )
    st.info(
        "Current Score is runs/wickets, Over shows how many 6-ball sets have been bowled, Pitch Condition describes the field, and Target is the score the batting team wants to reach."
    )
    st.markdown("---")

    runs_scored = None
    current_run_rate = None
    required_run_rate = None
    invalid_score = False

    try:
        runs_scored = float(match_state["score"].split("/")[0])
        if float(match_state["over"]):
            current_run_rate = round(runs_scored / float(match_state["over"]), 2)
        if 20.0 - float(match_state["over"]) > 0:
            required_run_rate = round((match_state["projected_target"] - runs_scored) / (20.0 - float(match_state["over"])), 2)
    except Exception:
        invalid_score = True

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(label="Live Score", value=match_state["score"], delta=f"Over {match_state['over']}")
        st.markdown("<div class='small-muted'>Live batting score and overs completed.</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(label="Pitch Condition", value=match_state["pitch_condition"])
        st.markdown("<div class='small-muted'>Tactical surface information for the next spell.</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(label="Current Run Rate", value=f"{current_run_rate or '—'} RPO")
        st.markdown("<div class='small-muted'>Runs per over so far.</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(label="Required Run Rate", value=f"{required_run_rate or '—'} RPO")
        st.markdown("<div class='small-muted'>Runs needed to reach target in remaining overs.</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if invalid_score:
        st.error("Enter a valid score like 142/5 to enable accurate run-rate metrics.")

    st.markdown("---")
    left_panel, right_panel = st.columns([1.1, 0.9])

    with left_panel:
        st.subheader("🤖 Agent Control Center")
        st.write(
            "Run the autonomous processing cycle to let the model analyze the current match state and propose the best substitution."
        )
        run_requested = st.button("🚀 Run Autonomous Strategy", use_container_width=True)

        if st.session_state.agent_summary:
            st.markdown('<div class="agent-box">', unsafe_allow_html=True)
            st.markdown("### Agent Executive Summary")
            st.write(st.session_state.agent_summary)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Run the agent to generate a reasoned substitution recommendation.")

        if show_match_state:
            with st.expander("Match state snapshot", expanded=True):
                st.json(match_state)

    with right_panel:
        st.subheader("📈 Live Transaction Ledger")
        st.write("The ledger displays the latest substitution decision and the reason it was executed.")

        if st.session_state.latest_trade:
            trade = st.session_state.latest_trade
            st.success("✅ Substitution recommended")
            st.metric(label="Confirmation time", value=trade["timestamp"])
            st.markdown(f"**Out:** {trade['out']}  \\n**In:** {trade['in']}")
            st.markdown(f"**Reason:** {trade['reason']}")
        else:
            st.warning("No trade has been executed yet. Run the agent to see the recommendation.")

        st.markdown("---")
        st.subheader("Quick facts")
        st.write("- The agent evaluates pitch, run rate, and bench strength before recommending a trade.")
        st.write("- It avoids marginal substitutions and only trades when the expected value is clear.")

    return run_requested
