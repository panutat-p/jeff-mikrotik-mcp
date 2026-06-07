"""Unit tests for the bridge scope."""

import asyncio

from tests.conftest import FakeExecutor


def _run(coro):
    return asyncio.run(coro)


def test_create_bridge_command(ctx, monkeypatch):
    from mcp_mikrotik.scope import bridge

    fake = FakeExecutor()
    monkeypatch.setattr(bridge, "execute_mikrotik_command", fake, raising=True)

    _run(bridge.mikrotik_create_bridge(ctx, name="bridge-test", vlan_filtering=True))
    assert fake.commands[0] == (
        '/interface bridge add name="bridge-test" protocol-mode=rstp vlan-filtering=yes'
    )


def test_add_bridge_port_command(ctx, monkeypatch):
    from mcp_mikrotik.scope import bridge

    fake = FakeExecutor()
    monkeypatch.setattr(bridge, "execute_mikrotik_command", fake, raising=True)

    _run(
        bridge.mikrotik_add_bridge_port(
            ctx,
            bridge="bridge1",
            interface="ether2",
        )
    )
    assert fake.commands[0] == (
        '/interface bridge port add bridge="bridge1" interface="ether2"'
    )


def test_list_bonding_command(ctx, monkeypatch):
    from mcp_mikrotik.scope import bridge

    fake = FakeExecutor()
    monkeypatch.setattr(bridge, "execute_mikrotik_command", fake, raising=True)

    _run(bridge.mikrotik_list_bonding(ctx, name_filter="bond"))
    assert fake.commands[-1] == '/interface bonding print where name~"bond"'
