import asyncio


def test_upload_file_sync_success(monkeypatch):
    from mcp_mikrotik import connector

    disconnected = {"called": 0}
    uploaded = {"filename": None, "content": None}

    class DummyClient:
        def connect(self):
            return True

        def upload_file(self, filename: str, content: bytes) -> None:
            uploaded["filename"] = filename
            uploaded["content"] = content

        def disconnect(self):
            disconnected["called"] += 1

    monkeypatch.setattr(connector, "MikroTikSSHClient", lambda **kw: DummyClient())
    result = connector._upload_file_sync("config.rsc", b"data")
    assert result == ""
    assert uploaded["filename"] == "config.rsc"
    assert uploaded["content"] == b"data"
    assert disconnected["called"] == 1


def test_upload_file_sync_connect_failure(monkeypatch):
    from mcp_mikrotik import connector

    disconnected = {"called": 0}

    class DummyClient:
        def connect(self):
            return False

        def disconnect(self):
            disconnected["called"] += 1

    monkeypatch.setattr(connector, "MikroTikSSHClient", lambda **kw: DummyClient())
    result = connector._upload_file_sync("config.rsc", b"data")
    assert result.startswith("Error: Failed to connect")
    assert disconnected["called"] == 1


def test_upload_file_sync_exception(monkeypatch):
    from mcp_mikrotik import connector

    disconnected = {"called": 0}

    class DummyClient:
        def connect(self):
            return True

        def upload_file(self, filename: str, content: bytes) -> None:
            raise RuntimeError("sftp boom")

        def disconnect(self):
            disconnected["called"] += 1

    monkeypatch.setattr(connector, "MikroTikSSHClient", lambda **kw: DummyClient())
    result = connector._upload_file_sync("config.rsc", b"data")
    assert result.startswith("Error uploading file: sftp boom")
    assert disconnected["called"] == 1


def test_download_file_sync_success(monkeypatch):
    from mcp_mikrotik import connector

    disconnected = {"called": 0}

    class DummyClient:
        def connect(self):
            return True

        def download_file(self, filename: str) -> bytes:
            assert filename == "backup.backup"
            return b"backup-bytes"

        def disconnect(self):
            disconnected["called"] += 1

    monkeypatch.setattr(connector, "MikroTikSSHClient", lambda **kw: DummyClient())
    data, error = connector._download_file_sync("backup.backup")
    assert data == b"backup-bytes"
    assert error == ""
    assert disconnected["called"] == 1


def test_download_file_sync_connect_failure(monkeypatch):
    from mcp_mikrotik import connector

    disconnected = {"called": 0}

    class DummyClient:
        def connect(self):
            return False

        def disconnect(self):
            disconnected["called"] += 1

    monkeypatch.setattr(connector, "MikroTikSSHClient", lambda **kw: DummyClient())
    data, error = connector._download_file_sync("backup.backup")
    assert data == b""
    assert error.startswith("Error: Failed to connect")
    assert disconnected["called"] == 1


def test_download_file_sync_exception(monkeypatch):
    from mcp_mikrotik import connector

    disconnected = {"called": 0}

    class DummyClient:
        def connect(self):
            return True

        def download_file(self, filename: str) -> bytes:
            raise RuntimeError("download boom")

        def disconnect(self):
            disconnected["called"] += 1

    monkeypatch.setattr(connector, "MikroTikSSHClient", lambda **kw: DummyClient())
    data, error = connector._download_file_sync("backup.backup")
    assert data == b""
    assert error.startswith("Error downloading file: download boom")
    assert disconnected["called"] == 1


def test_upload_file_to_router_logs_error(ctx, monkeypatch):
    from mcp_mikrotik import connector

    async def fake_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(
        connector,
        "_upload_file_sync",
        lambda filename, content: "Error uploading file: nope",
    )

    result = asyncio.run(connector.upload_file_to_router("x.rsc", b"x", ctx))
    assert result == "Error uploading file: nope"
    assert ctx.error.await_count == 1


def test_download_file_from_router_logs_error(ctx, monkeypatch):
    from mcp_mikrotik import connector

    async def fake_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(
        connector,
        "_download_file_sync",
        lambda filename: (b"", "Error downloading file: nope"),
    )

    data, error = asyncio.run(connector.download_file_from_router("x.backup", ctx))
    assert data == b""
    assert error == "Error downloading file: nope"
    assert ctx.error.await_count == 1
