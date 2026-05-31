import json
import time
import streamlit as st
from google.genai import types


def execute_player_trade(current_player_id: str, new_player_id: str, tactical_reasoning: str) -> str:
    st.session_state.latest_trade = {
        "out": current_player_id,
        "in": new_player_id,
        "reason": tactical_reasoning,
        "timestamp": time.strftime("%H:%M:%S"),
    }
    return f"SUCCESS: Transacted swap of {current_player_id} for {new_player_id}."


def run_agent_cycle(client, match_state):
    system_instruction = (
        "You are an elite, autonomous fantasy cricket manager. Your sole objective is to maximize "
        "total points based on live match conditions. Analyze the match state. If a player substitution "
        "offers a major statistical advantage based on the pitch or run rate, call execute_player_trade. "
        "Be decisive but conservative; do not waste trades on marginal benefits."
    )

    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[execute_player_trade],
            temperature=0.1,
        ),
    )

    response = chat.send_message(f"Current telemetry context: {json.dumps(match_state)}")
    return response.text
