"""Unit tests for the packages scope."""

import asyncio

from tests.conftest import FakeExecutor


def _run(coro):
    return asyncio.run(coro)


def test_list_packages_command(ctx, monkeypatch):
    from mcp_mikrotik.scope import packages

    fake = FakeExecutor()
    monkeypatch.setattr(packages, "execute_mikrotik_command", fake, raising=True)

    _run(packages.mikrotik_list_packages(ctx))
    assert fake.commands[-1] == "/system package print"

    _run(packages.mikrotik_list_packages(ctx, name_filter="container"))
    assert fake.commands[-1] == '/system package print where name~"container"'


def test_enable_package_command(ctx, monkeypatch):
    from mcp_mikrotik.scope import packages

    fake = FakeExecutor()
    monkeypatch.setattr(packages, "execute_mikrotik_command", fake, raising=True)

    _run(packages.mikrotik_enable_package(ctx, name="container"))
    assert fake.commands[0] == "/system package enable container"


def test_apply_package_changes_waits_for_ssh(ctx, monkeypatch):
    from mcp_mikrotik.scope import packages

    fake = FakeExecutor()
    monkeypatch.setattr(packages, "execute_mikrotik_command", fake, raising=True)
    monkeypatch.setattr(packages, "wait_for_router_ssh", lambda timeout=120.0: True, raising=True)

    out = _run(packages.mikrotik_apply_package_changes(ctx))
    assert fake.commands[0] == "/system package apply-changes"
    assert "back online" in out
