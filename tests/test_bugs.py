import pytest
from src.app.bugs import trigger_random_error, memory_leak_cart_session, leaked_sessions
from src.app.config import Config


def test_random_error_disabled():
    Config.ENABLE_BUGS = False
    try:
        trigger_random_error()
    except Exception:
        pytest.fail("Should not raise exception when bugs disabled")


def test_memory_leak():
    leaked_sessions.clear()
    initial_count = len(leaked_sessions)

    Config.ENABLE_BUGS = True
    memory_leak_cart_session({"item": "test"})

    assert len(leaked_sessions) > initial_count
