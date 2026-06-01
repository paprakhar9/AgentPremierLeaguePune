# This file has been replaced with a production-grade state management module.
# The previous configuration settings have been removed.
# Please refer to the new state management functions below.
"""
config.py - State Management & Settings

Handles persistent state (state.json) through atomic file operations.
Defines global constants and provides helper functions for state I/O.
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
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
STATE_FILE: str = "state.json"
POLLING_INTERVAL_SECONDS: int = 30
MODEL_ID: str = "gemini-2.5-flash"
# API key environment variable names (checked in priority order)
API_KEY_ENV_NAMES: list[str] = [
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
    "GENAI_API_KEY",
    "GENAI_KEY",
    "GENAI_APIKEY",
    "OPENAI_API_KEY",
]

# ============================================================================
# Type Definitions
# ============================================================================
Trade = Dict[str, Any]
LiveTelemetry = Dict[str, Any]
WorkerState = Dict[str, Any]
# ============================================================================
# State Management Functions
# ============================================================================

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

def read_state() -> WorkerState:
    """
    Load the current worker state from state.json.
    Returns an empty state structure if the file does not exist or is invalid.

    Returns:
        WorkerState: The loaded state or an initialized default state.
    """
    if not Path(STATE_FILE).exists():
        logger.info(f"State file '{STATE_FILE}' not found. Initializing new state.")
        return _initialize_state()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        logger.debug(f"Successfully loaded state from '{STATE_FILE}'")
        return state
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in '{STATE_FILE}': {e}. Reinitializing.")
        return _initialize_state()
    except IOError as e:
        logger.error(f"I/O error reading '{STATE_FILE}': {e}. Reinitializing.")
        return _initialize_state()
    except Exception as e:
        logger.error(f"Unexpected error loading state: {e}. Reinitializing.")
        return _initialize_state()

def save_state(state: WorkerState) -> bool:
    """
    Atomically write the worker state to state.json.
    Uses a temporary file and rename pattern to ensure atomic writes
    and prevent corruption if the process is interrupted mid-write.

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
        logger.debug(f"Successfully saved state to '{STATE_FILE}'")
        return True
    except IOError as e:
        logger.error(f"I/O error saving state to '{STATE_FILE}': {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving state: {e}")
        return False

def update_telemetry(
    telemetry: LiveTelemetry,
    score: Optional[str] = None,
    over: Optional[float] = None,
    pitch_condition: Optional[str] = None,
    projected_target: Optional[int] = None,
) -> LiveTelemetry:
    """
    Update telemetry fields. Returns a new telemetry dict without mutation.

    Args:
        telemetry: The current telemetry dictionary.
        score: Updated score (e.g., "142/5").
        over: Updated over count (e.g., 15.2).
        pitch_condition: Updated pitch condition.
        projected_target: Updated projected target.

    Returns:
        LiveTelemetry: Updated telemetry dictionary.
    """
    updated = telemetry.copy()
    if score is not None:
        updated["score"] = score
    if over is not None:
        updated["over"] = over
    if pitch_condition is not None:
        updated["pitch_condition"] = pitch_condition
    if projected_target is not None:
        updated["projected_target"] = projected_target
    return updated

def add_trade(trades: list[Trade], trade: Trade) -> list[Trade]:
    """
    Add a trade record to the trade ledger.

    Args:
        trades: Current trade ledger.
        trade: New trade to append.

    Returns:
        list[Trade]: Updated trade ledger.
    """
    return trades + [trade]

def create_trade(
    current_player_id: str,
    new_player_id: str,
    tactical_reasoning: str,
) -> Trade:
    """
    Create a trade record with timestamp.

    Args:
        current_player_id: ID of the player being replaced.
        new_player_id: ID of the incoming player.
        tactical_reasoning: Explanation for the trade decision.

    Returns:
        Trade: Formatted trade dictionary.
    """
    return {
        "out": current_player_id,
        "in": new_player_id,
        "reason": tactical_reasoning,
        "timestamp": datetime.now().isoformat(),
    }

def has_telemetry_changed(
    old_telemetry: LiveTelemetry,
    new_telemetry: LiveTelemetry,
) -> bool:
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
# Environment & API Key Management
# ============================================================================

def load_env_file(path: str = ".env") -> None:
    """
    Load environment variables from a .env file.

    Skips comments, empty lines, and variables already set in os.environ.

    Args:
        path: Path to .env file.
    """
    if not os.path.exists(path):
        logger.debug(f"No .env file found at '{path}'")
        return

    try:
        with open(path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
        logger.debug(f"Loaded environment variables from '{path}'")
    except IOError as e:
        logger.warning(f"Failed to read .env file '{path}': {e}")
    except Exception as e:
        logger.warning(f"Error parsing .env file: {e}")

def get_api_key() -> Optional[str]:
    """
    Retrieve the Gemini API key from environment variables.

    Checks multiple environment variable names in priority order.
    Attempts to load .env file first if present.

    Returns:
        Optional[str]: API key if found, None otherwise.
    """
    load_env_file(".env")

    for key_name in API_KEY_ENV_NAMES:
        value = os.getenv(key_name)
        if value:
            logger.info(f"Using API key from environment variable '{key_name}'")
            return value

    logger.warning("No Gemini API key found in environment variables")
    return None

