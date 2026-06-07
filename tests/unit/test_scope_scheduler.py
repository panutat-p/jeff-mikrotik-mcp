"""Unit tests for the scheduler scope."""

import asyncio

from tests.conftest import FakeExecutor


def _run(coro):
    return asyncio.run(coro)


def test_create_scheduler_command(ctx, monkeypatch):
    from mcp_mikrotik.scope import scheduler

    fake = FakeExecutor()
    monkeypatch.setattr(scheduler, "execute_mikrotik_command", fake, raising=True)

    _run(
        scheduler.mikrotik_create_scheduler(
            ctx,
            name="daily-backup",
            on_event="/system backup save name=daily",
            interval="1d",
        )
    )
    assert fake.commands[0] == (
        '/system scheduler add name="daily-backup"'
        ' on-event="/system backup save name=daily"'
        " interval=1d"
    )


def test_remove_scheduler_by_name(ctx, monkeypatch):
    from mcp_mikrotik.scope import scheduler

    fake = FakeExecutor()
    monkeypatch.setattr(scheduler, "execute_mikrotik_command", fake, raising=True)

    _run(scheduler.mikrotik_remove_scheduler(ctx, name="daily-backup"))
    assert fake.commands[0] == '/system scheduler print count-only where name="daily-backup"'
    assert fake.commands[1] == '/system scheduler remove [find name="daily-backup"]'


def test_run_script_command(ctx, monkeypatch):
    from mcp_mikrotik.scope import scheduler

    fake = FakeExecutor()
    monkeypatch.setattr(scheduler, "execute_mikrotik_command", fake, raising=True)

    _run(scheduler.mikrotik_run_script(ctx, name="my-script"))
    assert fake.commands[-1] == '/system script run [find name="my-script"]'
