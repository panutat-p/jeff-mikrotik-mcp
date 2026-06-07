import asyncio
import inspect

import pytest

from tests.conftest import FakeExecutor, make_dummy_value


SCOPE_MODULES = [
    "backup",
    "bridge",
    "certificates",
    "containers",
    "device_mode",
    "dhcp",
    "dns",
    "firewall_filter",
    "firewall_nat",
    "hotspot",
    "ip_address",
    "ip_pool",
    "logs",
    "messaging",
    "packages",
    "poe",
    "ppp",
    "queue",
    "routes",
    "scheduler",
    "snmp",
    "system",
    "users",
    "vlan",
    "vpn",
    "wireless",
    "wireguard",
]

BROKEN_WRAPPER_FUNCS: set[str] = set()


@pytest.mark.parametrize("module_name", SCOPE_MODULES)
def test_scope_module_functions_return_string(module_name, ctx, monkeypatch):
    module = __import__(f"mcp_mikrotik.scope.{module_name}", fromlist=["*"])

    # Patch module-level executor (each scope imports it directly)
    fake = FakeExecutor()
    monkeypatch.setattr(module, "execute_mikrotik_command", fake, raising=True)
    if hasattr(module, "wait_for_router_ssh"):
        monkeypatch.setattr(module, "wait_for_router_ssh", lambda *a, **k: True, raising=True)
    async def _noop_sleep(*_a, **_k):
        return None

    monkeypatch.setattr(asyncio, "sleep", _noop_sleep)
    if hasattr(module, "upload_file_to_router"):
        async def _fake_upload(filename, content, ctx):
            return ""
        monkeypatch.setattr(module, "upload_file_to_router", _fake_upload, raising=True)
    if hasattr(module, "download_file_from_router"):
        async def _fake_download(filename, ctx):
            return b"data", ""
        monkeypatch.setattr(module, "download_file_from_router", _fake_download, raising=True)

    # Run every coroutine function once with dummy args.
    for name, fn in inspect.getmembers(module, inspect.iscoroutinefunction):
        if not name.startswith("mikrotik_"):
            continue

        sig = inspect.signature(fn)
        kwargs = {}
        for param in sig.parameters.values():
            if param.name == "ctx":
                kwargs["ctx"] = ctx
                continue
            if param.default is not inspect._empty:
                continue
            kwargs[param.name] = make_dummy_value(param)

        if name in BROKEN_WRAPPER_FUNCS:
            with pytest.raises(TypeError):
                asyncio.run(fn(**kwargs))
            continue

        result = asyncio.run(fn(**kwargs))
        assert isinstance(result, str)
