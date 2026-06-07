"""Unit tests for monitor_logs polling behavior."""

import asyncio

from tests.conftest import FakeExecutor


def _run(coro):
    return asyncio.run(coro)


async def _noop_sleep(*_args, **_kwargs):
    return None


def test_monitor_logs_polls_with_time_filter(ctx, monkeypatch):
    from mcp_mikrotik.scope import logs

    fake = FakeExecutor()
    monkeypatch.setattr(logs, "execute_mikrotik_command", fake, raising=True)
    monkeypatch.setattr(asyncio, "sleep", _noop_sleep)

    out = _run(logs.mikrotik_monitor_logs(ctx, topics="system", duration=4))

    assert all("time>([:timestamp]-5s)" in cmd for cmd in fake.commands)
    assert 'topics~"system"' in fake.commands[0]
    assert "LOG MONITOR (4s" in out
