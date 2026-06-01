"""
worker.py - Autonomous Polling Daemon

Implements a clean event-driven polling loop that reads live match telemetry
from state.json, invokes the Gemini agent for autonomous decisions, and persists
all trades and state changes atomically.
"""

import logging
import time
from datetime import datetime
from typing import Optional

from google import genai

from agent import create_gemini_client, run_agent_cycle
from config import (
    POLLING_INTERVAL_SECONDS,
    WorkerState,
    has_telemetry_changed,
    read_state,
    save_state,
)
from tools import set_worker_state

# ============================================================================
# Logging Configuration
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# Main Polling Loop
# ============================================================================


def main() -> None:
    """
    Start the autonomous worker polling loop.

    Runs indefinitely, waking up every POLLING_INTERVAL_SECONDS to:
    1. Load the current state from disk.
    2. Check if telemetry has changed since last cycle.
    3. If changed, inject state into tools and run an agent cycle.
    4. Persist updated state (including any new trades).
    5. Log all operations with timestamps.

    The loop is designed to be interrupt-safe and recoverable from errors.
    """
    logger.info("=" * 80)
    logger.info("Autonomous Fantasy Cricket Manager Worker Starting")
    logger.info(f"Polling interval: {POLLING_INTERVAL_SECONDS} seconds")
    logger.info("=" * 80)

    # Initialize Gemini client
    client: Optional[genai.Client] = create_gemini_client()
    if not client:
        logger.error("Gemini client initialization failed. Exiting.")
        return

    # Load initial state
    current_state: WorkerState = read_state()
    iteration: int = 0

    try:
        while True:
            iteration += 1
            cycle_start: float = time.time()
            logger.info(f"--- Polling Cycle {iteration} ---")

            # Load the latest state from disk
            old_telemetry = current_state["live_telemetry"].copy()
            current_state = read_state()

            # Check if telemetry has changed
            if has_telemetry_changed(old_telemetry, current_state["live_telemetry"]):
                logger.info("Telemetry change detected. Running agent cycle.")

                # Inject current state into tools module
                set_worker_state(current_state)

                # Run the agent cycle
                analysis = run_agent_cycle(client, current_state["live_telemetry"])
                logger.info(f"Agent analysis: {analysis[:100]}...")

            else:
                logger.debug("No telemetry change. Skipping agent cycle.")

            # Persist the state (including any trades from agent execution)
            current_state["last_run"] = datetime.now().isoformat()
            save_state(current_state)

            # Calculate sleep duration to maintain polling interval
            elapsed: float = time.time() - cycle_start
            sleep_duration: float = max(0, POLLING_INTERVAL_SECONDS - elapsed)

            logger.info(
                f"Cycle {iteration} complete. "
                f"(elapsed: {elapsed:.2f}s, next wake: +{sleep_duration:.2f}s)"
            )

            time.sleep(sleep_duration)

    except KeyboardInterrupt:
        logger.info("Worker interrupted by user. Gracefully shutting down.")
        current_state["last_run"] = datetime.now().isoformat()
        save_state(current_state)
        logger.info("State persisted. Goodbye.")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
        current_state["last_run"] = datetime.now().isoformat()
        save_state(current_state)
        logger.error("State persisted on error. Re-raising exception.")
        raise


if __name__ == "__main__":
    main()
