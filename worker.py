"""
Autonomous fantasy cricket manager background worker.

Implements an event-driven polling loop that reads live match telemetry,
runs the Gemini-powered ReAct agent, and executes autonomous player trades.

The worker persists state to state.json and logs all actions with timestamps.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types


# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

STATE_FILE = "state.json"
POLLING_INTERVAL_SECONDS = 30
MODEL_ID = "gemini-2.5-flash"


# ============================================================================
# Type Definitions
# ============================================================================

Trade = Dict[str, Any]
LiveTelemetry = Dict[str, Any]
WorkerState = Dict[str, Any]


# ============================================================================
# State Management
# ============================================================================


def load_state() -> WorkerState:
    """
    Load the current worker state from state.json.

    Returns an empty state structure if the file does not exist or is invalid.

    Returns:
        WorkerState: The loaded state or an initialized default state.
    """
    if not Path(STATE_FILE).exists():
        logger.info(f"State file {STATE_FILE} not found. Initializing new state.")
        return _initialize_state()

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
            logger.debug(f"Loaded state from {STATE_FILE}")
            return state
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load state from {STATE_FILE}: {e}. Reinitializing.")
        return _initialize_state()


def _initialize_state() -> WorkerState:
    """
    Create a fresh worker state with default values.

    Returns:
        WorkerState: A newly initialized state structure.
    """
    return {
        "live_telemetry": {
            "score": "0/0",
            "over": 0.0,
            "pitch_condition": "Unknown",
            "projected_target": 0,
        },
        "trade_ledger": [],
        "last_run": None,
    }


def save_state(state: WorkerState) -> bool:
    """
    Atomically write the worker state to state.json.

    Uses a temporary file and rename pattern to ensure atomic writes
    and prevent corruption if the process is interrupted.

    Args:
        state: The state dictionary to persist.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        temp_file = f"{STATE_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

        os.replace(temp_file, STATE_FILE)
        logger.debug(f"Saved state to {STATE_FILE}")
        return True
    except IOError as e:
        logger.error(f"Failed to save state to {STATE_FILE}: {e}")
        return False


def has_telemetry_changed(old_telemetry: LiveTelemetry, new_telemetry: LiveTelemetry) -> bool:
    """
    Detect if the live telemetry has meaningfully changed.

    Args:
        old_telemetry: Previous telemetry snapshot.
        new_telemetry: Current telemetry snapshot.

    Returns:
        bool: True if any telemetry value has changed.
    """
    return old_telemetry != new_telemetry


# ============================================================================
# Tool Function (Gemini Tool Binding)
# ============================================================================


def execute_player_trade(
    current_player_id: str,
    new_player_id: str,
    tactical_reasoning: str,
) -> str:
    """
    Execute a player substitution and record the trade to the ledger.

    This function is invoked by the Gemini agent via tool calling.
    It appends the trade to the in-memory state and persists it.

    Args:
        current_player_id: ID of the player being replaced.
        new_player_id: ID of the incoming player.
        tactical_reasoning: Explanation for the trade decision.

    Returns:
        str: Confirmation message.
    """
    trade: Trade = {
        "out": current_player_id,
        "in": new_player_id,
        "reason": tactical_reasoning,
        "timestamp": datetime.now().isoformat(),
    }

    global _current_state
    _current_state["trade_ledger"].append(trade)

    logger.info(
        f"Trade executed: {current_player_id} → {new_player_id} | "
        f"Reason: {tactical_reasoning}"
    )

    return f"SUCCESS: Transacted {current_player_id} for {new_player_id}."


# ============================================================================
# Gemini Agent Integration
# ============================================================================


def initialize_gemini_client() -> Optional[genai.Client]:
    """
    Create and return a configured Gemini client.

    Attempts to read the API key from environment variables.
    Supports multiple key names: GOOGLE_API_KEY, GEMINI_API_KEY, GENAI_API_KEY.

    Returns:
        Optional[genai.Client]: Initialized client or None if API key is missing.
    """
    for key_name in ["GOOGLE_API_KEY", "GEMINI_API_KEY", "GENAI_API_KEY"]:
        api_key = os.getenv(key_name)
        if api_key:
            logger.info(f"Using API key from {key_name}")
            return genai.Client(api_key=api_key)

    logger.error("No Gemini API key found in environment variables.")
    return None


def run_agent_cycle(client: genai.Client, telemetry: LiveTelemetry) -> None:
    """
    Execute one cycle of the autonomous agent's ReAct loop.

    Sends the current match telemetry to the Gemini model, which evaluates
    the situation and may decide to call the execute_player_trade tool.

    Args:
        client: The initialized Gemini client.
        telemetry: Current live match telemetry.
    """
    try:
        system_instruction = (
            "You are an elite, cold, analytical fantasy cricket manager. "
            "Your sole objective is to maximize total points based on live match conditions. "
            "Analyze the match state provided. If a player substitution offers a major "
            "statistical advantage based on the pitch or run rate, call execute_player_trade. "
            "Be decisive but conservative; do not waste trades on marginal benefits."
        )

        chat = client.chats.create(
            model=MODEL_ID,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[execute_player_trade],
                temperature=0.1,
            ),
        )

        message_content = (
            f"Current match telemetry:\n"
            f"- Score: {telemetry['score']}\n"
            f"- Over: {telemetry['over']}\n"
            f"- Pitch: {telemetry['pitch_condition']}\n"
            f"- Target: {telemetry['projected_target']}\n\n"
            f"Analyze and decide if a substitution is warranted."
        )

        response = chat.send_message(message_content)

        logger.info(f"Agent analysis: {response.text[:200]}...")

    except Exception as e:
        logger.error(f"Error during agent cycle: {e}")


# ============================================================================
# Main Polling Loop
# ============================================================================

_current_state: WorkerState = {}


def main() -> None:
    """
    Start the autonomous worker polling loop.

    Runs indefinitely, waking up every POLLING_INTERVAL_SECONDS to:
    1. Load the current state from disk.
    2. Check if telemetry has changed.
    3. If changed, run an agent cycle to make autonomous decisions.
    4. Persist the updated state (including any new trades).
    5. Log all operations with timestamps.

    The loop is designed to be interrupt-safe and recoverable from errors.
    """
    global _current_state

    logger.info("=" * 70)
    logger.info("Autonomous Fantasy Cricket Manager Worker Starting")
    logger.info(f"Polling interval: {POLLING_INTERVAL_SECONDS} seconds")
    logger.info("=" * 70)

    client = initialize_gemini_client()
    if not client:
        logger.error("Gemini client initialization failed. Exiting.")
        return

    _current_state = load_state()

    iteration = 0

    try:
        while True:
            iteration += 1
            cycle_start = time.time()
            logger.info(f"--- Polling Cycle {iteration} ---")

            # Load the latest state from disk
            _current_state = load_state()
            old_telemetry = _current_state["live_telemetry"].copy()

            # In a real deployment, telemetry would be updated from external sources
            # (e.g., live match APIs, user inputs, Streamlit state).
            # For now, telemetry is loaded from state.json as-is.

            # Check if telemetry has changed
            if has_telemetry_changed(old_telemetry, _current_state["live_telemetry"]):
                logger.info("Telemetry change detected. Running agent cycle.")
                run_agent_cycle(client, _current_state["live_telemetry"])
            else:
                logger.debug("No telemetry change. Skipping agent cycle.")

            # Persist the state (including any new trades from execute_player_trade)
            _current_state["last_run"] = datetime.now().isoformat()
            save_state(_current_state)

            # Calculate sleep duration to maintain polling interval
            elapsed = time.time() - cycle_start
            sleep_duration = max(0, POLLING_INTERVAL_SECONDS - elapsed)

            logger.info(
                f"Cycle {iteration} complete. "
                f"(elapsed: {elapsed:.2f}s, next wake: +{sleep_duration:.2f}s)"
            )

            time.sleep(sleep_duration)

    except KeyboardInterrupt:
        logger.info("Worker interrupted by user. Gracefully shutting down.")
        _current_state["last_run"] = datetime.now().isoformat()
        save_state(_current_state)
        logger.info("State saved. Goodbye.")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
        _current_state["last_run"] = datetime.now().isoformat()
        save_state(_current_state)
        raise


if __name__ == "__main__":
    main()
