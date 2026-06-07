"""Unit tests for backup scope file transfer tools."""

import asyncio
import base64

from tests.conftest import FakeExecutor


def _run(coro):
    return asyncio.run(coro)


def test_download_file_success(ctx, monkeypatch):
    from mcp_mikrotik.scope import backup

    fake = FakeExecutor()
    monkeypatch.setattr(backup, "execute_mikrotik_command", fake, raising=True)

    async def fake_download(filename, _ctx):
        assert filename == "test.backup"
        return b"backup-data", ""

    monkeypatch.setattr(backup, "download_file_from_router", fake_download, raising=True)

    out = _run(backup.mikrotik_download_file(ctx, filename="test.backup"))
    assert out.startswith("FILE_CONTENT_BASE64:")
    encoded = out.split(":", 1)[1]
    assert base64.b64decode(encoded) == b"backup-data"
    assert fake.commands[-1] == "/file print count-only where name=test.backup"


def test_download_file_not_found(ctx, monkeypatch):
    from mcp_mikrotik.scope import backup

    async def fake_exec(command, _ctx):
        if "count-only" in command:
            return "0"
        return ""

    monkeypatch.setattr(backup, "execute_mikrotik_command", fake_exec, raising=True)

    out = _run(backup.mikrotik_download_file(ctx, filename="missing.backup"))
    assert "not found" in out


def test_download_file_connector_error(ctx, monkeypatch):
    from mcp_mikrotik.scope import backup

    async def fake_exec(command, _ctx):
        if "count-only" in command:
            return "1"
        return ""

    async def fake_download(filename, _ctx):
        return b"", "Error downloading file: sftp failed"

    monkeypatch.setattr(backup, "execute_mikrotik_command", fake_exec, raising=True)
    monkeypatch.setattr(backup, "download_file_from_router", fake_download, raising=True)

    out = _run(backup.mikrotik_download_file(ctx, filename="test.backup"))
    assert out == "Error downloading file: sftp failed"


def test_upload_file_success(ctx, monkeypatch):
    from mcp_mikrotik.scope import backup

    fake = FakeExecutor()
    uploaded = {"filename": None, "content": None}

    async def fake_upload(filename, content, _ctx):
        uploaded["filename"] = filename
        uploaded["content"] = content
        return ""

    monkeypatch.setattr(backup, "execute_mikrotik_command", fake, raising=True)
    monkeypatch.setattr(backup, "upload_file_to_router", fake_upload, raising=True)

    payload = base64.b64encode(b"script-body").decode("utf-8")
    out = _run(backup.mikrotik_upload_file(ctx, filename="config.rsc", content_base64=payload))

    assert uploaded["filename"] == "config.rsc"
    assert uploaded["content"] == b"script-body"
    assert "uploaded successfully" in out
    assert fake.commands[-1] == "/file print count-only where name=config.rsc"


def test_upload_file_invalid_base64(ctx, monkeypatch):
    from mcp_mikrotik.scope import backup

    out = _run(backup.mikrotik_upload_file(ctx, filename="config.rsc", content_base64="a"))
    assert "Failed to decode" in out


def test_upload_file_connector_error(ctx, monkeypatch):
    from mcp_mikrotik.scope import backup

    async def fake_upload(filename, content, _ctx):
        return "Error uploading file: sftp failed"

    monkeypatch.setattr(backup, "upload_file_to_router", fake_upload, raising=True)

    payload = base64.b64encode(b"x").decode("utf-8")
    out = _run(backup.mikrotik_upload_file(ctx, filename="config.rsc", content_base64=payload))
    assert out == "Error uploading file: sftp failed"
