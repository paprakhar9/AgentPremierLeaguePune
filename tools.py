"""
tools.py - Action Execution & Tool Definitions

Defines all tools (functions) that the Gemini agent can call via ReAct tool calling.
Each tool has strict type hints for seamless Gemini SDK integration.
"""

import logging
from typing import Any, Callable, Dict

from config import WorkerState, create_trade, add_trade

# ============================================================================
# Logging Configuration
# ============================================================================

logger = logging.getLogger(__name__)

# Global state reference (set by worker.py)
_current_state: WorkerState = {}


# ============================================================================
# Tool: Execute Player Trade
# ============================================================================


def execute_player_trade(
    current_player_id: str,
    new_player_id: str,
    tactical_reasoning: str,
) -> str:
    """
    Execute a player substitution and record the trade to the ledger.

    This function is invoked by the Gemini agent via ReAct tool calling.
    It appends the trade to the in-memory state for later persistence.

    **Tool Schema for Gemini SDK:**
    - current_player_id (str): ID of the player being replaced.
    - new_player_id (str): ID of the incoming player.
    - tactical_reasoning (str): Explanation for the trade decision.

    Args:
        current_player_id: ID of the player being replaced (e.g., "p_siraj").
        new_player_id: ID of the incoming player (e.g., "p_chahal").
        tactical_reasoning: Detailed explanation of why this substitution
                          improves the team's fantasy points projection.

    Returns:
        str: Confirmation message summarizing the executed trade.
    """
    try:
        # Create a new trade record with timestamp
        trade = create_trade(
            current_player_id=current_player_id,
            new_player_id=new_player_id,
            tactical_reasoning=tactical_reasoning,
        )

        # Update the global state with the new trade
        global _current_state
        _current_state["trade_ledger"] = add_trade(
            _current_state["trade_ledger"],
            trade,
        )

        logger.info(
            f"Trade executed: {current_player_id} → {new_player_id} | "
            f"Reason: {tactical_reasoning[:100]}"
        )

        return (
            f"SUCCESS: Transacted swap of {current_player_id} for {new_player_id}. "
            f"Reasoning: {tactical_reasoning}"
        )

    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        return f"FAILED: Trade could not be executed. Error: {str(e)}"


# ============================================================================
# Tool Registry
# ============================================================================


def get_tool_registry() -> Dict[str, Callable]:
    """
    Return a dictionary of all available tools for the Gemini agent.

    This registry maps tool names to their callable functions.
    The Gemini SDK uses this to bind and invoke tools during agent cycles.

    Returns:
        Dict[str, Callable]: Dictionary of tool functions.
    """
    return {
        "execute_player_trade": execute_player_trade,
    }


def set_worker_state(state: WorkerState) -> None:
    """
    Inject the current worker state into the tools module.

    Called by worker.py to ensure that tool functions have access
    to the current shared state.

    Args:
        state: The current WorkerState dictionary.
    """
    global _current_state
    _current_state = state
    logger.debug("Worker state injected into tools module")
