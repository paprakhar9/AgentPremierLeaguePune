import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import config
import tools
import agent


@pytest.fixture
def temp_state_file(tmp_path, monkeypatch):
    """Create a temporary state.json and patch config.STATE_FILE to point to it.

    Yields the Path to the temp file. Restores the original STATE_FILE after test.
    """
    temp_file = tmp_path / "state.json"
    initial = {
        "live_telemetry": {
            "score": "0/0",
            "over": 0.0,
            "pitch_condition": "Unknown",
            "projected_target": 0,
        },
        "trade_ledger": [],
        "last_run": None,
    }
    temp_file.write_text(json.dumps(initial))

    original_state_file = config.STATE_FILE
    monkeypatch.setattr(config, "STATE_FILE", str(temp_file))

    yield temp_file

    # Teardown: restore original STATE_FILE (tmp_path cleanup is automatic)
    monkeypatch.setattr(config, "STATE_FILE", original_state_file)


def test_execute_player_trade_appends_trade(temp_state_file):
    # Load the temp state and inject into tools
    state = config.read_state()
    tools.set_worker_state(state)

    # Execute a trade via the tool
    result = tools.execute_player_trade("p_siraj", "p_chahal", "Use legspin on turning pitch")
    assert "SUCCESS" in result

    # Persist the in-memory state to disk and verify the trade was appended
    assert isinstance(tools._current_state, dict)
    saved = config.save_state(tools._current_state)
    assert saved is True

    disk = json.loads(Path(str(temp_state_file)).read_text(encoding="utf-8"))
    assert "trade_ledger" in disk
    assert len(disk["trade_ledger"]) == 1
    trade = disk["trade_ledger"][0]
    assert trade["out"] == "p_siraj"
    assert trade["in"] == "p_chahal"
    assert "legspin" in trade["reason"].lower()


def test_agent_run_cycle_with_mocked_genai(monkeypatch):
    # Ensure agent.get_api_key returns a deterministic test key
    monkeypatch.setattr(agent, "get_api_key", lambda: "fake-key")

    # Build mocked client/chat/response chain
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Mocked agent decision: no trade"
    mock_chat.send_message.return_value = mock_response
    mock_client.chats.create.return_value = mock_chat

    # Patch the genai.Client constructor used in agent.create_gemini_client
    with patch("agent.genai.Client", return_value=mock_client) as mock_client_cls:
        client = agent.create_gemini_client()
        # Ensure the constructor was called with the API key
        mock_client_cls.assert_called_once_with(api_key="fake-key")

        # Run one agent cycle and assert we received the mocked response
        telemetry = {
            "score": "120/2",
            "over": 15.2,
            "pitch_condition": "Turning",
            "projected_target": 250,
        }

        response_text = agent.run_agent_cycle(client, telemetry)
        assert response_text == "Mocked agent decision: no trade"

        # Confirm the chat creation and send_message call happened
        mock_client.chats.create.assert_called_once()
        expected_message = agent._format_telemetry_message(telemetry)
        mock_chat.send_message.assert_called_once_with(expected_message)


def test_read_state_initializes_when_missing(tmp_path, monkeypatch):
    missing = tmp_path / "no_state.json"
    monkeypatch.setattr(config, "STATE_FILE", str(missing))
    state = config.read_state()
    assert isinstance(state, dict)
    assert state.get("trade_ledger") == []


def test_read_state_reinitializes_on_corrupt_json(tmp_path, monkeypatch):
    corrupt = tmp_path / "state.json"
    corrupt.write_text("{ not: valid json }")
    monkeypatch.setattr(config, "STATE_FILE", str(corrupt))
    state = config.read_state()
    assert isinstance(state, dict)
    assert state.get("trade_ledger") == []


def test_save_state_failure(monkeypatch, tmp_path):
    tmp = tmp_path / "state.json"
    # write initial content to simulate existing good state that must not be corrupted
    tmp.write_text(json.dumps({"trade_ledger": [], "meta": "original"}))
    monkeypatch.setattr(config, "STATE_FILE", str(tmp))

    original_content = tmp.read_text(encoding="utf-8")

    # Simulate os.replace raising an OSError during save
    def fake_replace(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", fake_replace)
    ok = config.save_state({"trade_ledger": []})
    assert ok is False

    # Ensure original file content was not corrupted
    assert tmp.read_text(encoding="utf-8") == original_content


def test_add_trade_no_mutation():
    original = []
    trade = {"out": "a", "in": "b", "reason": "test", "timestamp": "t"}
    new = config.add_trade(original, trade)
    assert new != original
    assert original == []
    assert new[-1]["out"] == "a"


def test_execute_player_trade_handles_exception():
    # Inject a state missing the expected 'trade_ledger' key
    tools.set_worker_state({})
    resp = tools.execute_player_trade("p_x", "p_y", "reason")
    assert isinstance(resp, str)
    assert resp.startswith("FAILED")


def test_create_gemini_client_no_key(monkeypatch):
    monkeypatch.setattr(agent, "get_api_key", lambda: None)
    client = agent.create_gemini_client()
    assert client is None


def test_run_agent_cycle_client_none():
    out = agent.run_agent_cycle(None, {})
    assert isinstance(out, str)
    assert out.startswith("ERROR")


def test_agent_run_cycle_handles_client_exception(monkeypatch):
    # Create a client whose chats.create raises
    mock_client = MagicMock()
    mock_client.chats.create.side_effect = Exception("chat failed")

    # Ensure create_gemini_client won't override our client by bypassing it
    result = agent.run_agent_cycle(mock_client, {"score": "10/1", "over": 1.2})
    assert result.startswith("ERROR")


def test_worker_main_handles_agent_exception(monkeypatch):
    # Patch create_gemini_client to return a dummy client
    dummy_client = MagicMock()
    monkeypatch.setattr(agent, "create_gemini_client", lambda: dummy_client)

    # Force read_state to return a state with telemetry change
    base_state = {"live_telemetry": {"score": "0/0"}, "trade_ledger": [], "last_run": None}
    # First call returns base_state, second call returns same to simulate no further changes
    monkeypatch.setattr('config.read_state', lambda: base_state)

    # Make run_agent_cycle raise to simulate API failure
    monkeypatch.setattr('agent.run_agent_cycle', lambda client, telemetry: (_ for _ in ()).throw(Exception("api fail")))

    # Make time.sleep raise KeyboardInterrupt to stop the loop after one iteration
    import time as _time
    monkeypatch.setattr('time.sleep', lambda s: (_ for _ in ()).throw(KeyboardInterrupt()))

    # Run worker.main and ensure it exits without raising
    import worker as worker_module
    worker_module.main()
