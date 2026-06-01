"""
agent.py - LLM Integration & ReAct Agent Loop

Handles Gemini client initialization and provides the main agent cycle wrapper.
Encapsulates all GenAI-specific logic and tool binding.
"""

import json
import logging
from typing import Any, Dict, Optional

from google import genai
from google.genai import types

from config import LiveTelemetry, MODEL_ID, get_api_key
from tools import execute_player_trade

# ============================================================================
# Logging Configuration
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# System Instruction
# ============================================================================

SYSTEM_INSTRUCTION: str = (
    "You are an elite, cold, analytical autonomous fantasy cricket manager. "
    "Your sole objective is to maximize total fantasy points based on live match conditions. "
    "\n\n"
    "**Your Analysis Process:**\n"
    "1. Evaluate the current match state: score, overs played, pitch condition, target.\n"
    "2. Consider the bench strength and current bowling lineup.\n"
    "3. Assess if a substitution would provide a MAJOR statistical advantage.\n"
    "4. Be decisive but conservative: do NOT waste trades on marginal benefits.\n"
    "\n"
    "**Tool Availability:**\n"
    "- You can call execute_player_trade() to swap a player.\n"
    "- Provide clear tactical reasoning for every substitution.\n"
    "\n"
    "**Output Format:**\n"
    "Begin with a brief analysis. If a trade is warranted, call the tool. "
    "End with a concise executive summary."
)


# ============================================================================
# Gemini Client Initialization
# ============================================================================


def create_gemini_client() -> Optional[genai.Client]:
    """
    Initialize and return a configured Gemini client.

    Attempts to load the API key from environment variables.
    Logs errors if initialization fails.

    Returns:
        Optional[genai.Client]: Initialized client or None if API key is missing.
    """
    api_key = get_api_key()
    if not api_key:
        logger.error("No Gemini API key found. Cannot initialize client.")
        return None

    try:
        client = genai.Client(api_key=api_key)
        logger.info("Gemini client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        return None


# ============================================================================
# Agent Cycle Execution
# ============================================================================


def run_agent_cycle(
    client: genai.Client,
    telemetry: LiveTelemetry,
) -> str:
    """
    Execute one cycle of the autonomous agent's ReAct loop.

    Sends the current match telemetry to the Gemini model with tool binding.
    The model evaluates the situation and may call execute_player_trade.

    **Process:**
    1. Format the match telemetry as a message.
    2. Create a chat session with system instruction and tool binding.
    3. Send the message and let the model process.
    4. Return the model's analysis text.

    Args:
        client: The initialized Gemini client.
        telemetry: Current live match telemetry dictionary.
                  Expected keys: score, over, pitch_condition, projected_target.

    Returns:
        str: The agent's analysis and recommendations (plain text).
    """
    if not client:
        logger.error("Gemini client is not initialized")
        return "ERROR: Gemini client not initialized."

    try:
        # Format telemetry into a readable message
        message_content = _format_telemetry_message(telemetry)

        # Create a chat session with system instruction and tool binding
        chat = client.chats.create(
            model=MODEL_ID,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[execute_player_trade],
                temperature=0.1,
            ),
        )

        # Send the message to the model
        response = chat.send_message(message_content)

        # Extract and log the response
        response_text = response.text if hasattr(response, "text") else str(response)
        logger.info(f"Agent analysis complete: {response_text[:150]}...")

        return response_text

    except Exception as e:
        logger.error(f"Error during agent cycle: {e}", exc_info=True)
        return f"ERROR: Agent cycle failed with error: {str(e)}"


def _format_telemetry_message(telemetry: LiveTelemetry) -> str:
    """
    Format match telemetry into a readable message for the agent.

    Args:
        telemetry: The live telemetry dictionary.

    Returns:
        str: Formatted message for the agent.
    """
    score = telemetry.get("score", "N/A")
    over = telemetry.get("over", 0.0)
    pitch = telemetry.get("pitch_condition", "Unknown")
    target = telemetry.get("projected_target", 0)

    return (
        f"Current Match Telemetry:\n"
        f"- Live Score: {score}\n"
        f"- Overs Played: {over}\n"
        f"- Pitch Condition: {pitch}\n"
        f"- Projected Target: {target}\n"
        f"- Current Bowling: p_siraj\n"
        f"- Bench Available: p_chahal, r_ashwin, m_shami\n"
        f"\n"
        f"Analyze this match state and decide if a substitution is warranted. "
        f"If you recommend a trade, use the execute_player_trade tool."
    )
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
