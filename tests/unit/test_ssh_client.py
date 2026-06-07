import io

import pytest


# ---------------------------------------------------------------------------
# _decode_output: encoding fallback (issue #58)
# ---------------------------------------------------------------------------

class TestDecodeOutput:
    """Unit tests for MikroTikSSHClient._decode_output."""

    def setup_method(self):
        from mcp_mikrotik.mikrotik_ssh_client import MikroTikSSHClient
        self.decode = MikroTikSSHClient._decode_output

    def test_empty_bytes_returns_empty_string(self):
        assert self.decode(b"") == ""

    def test_pure_ascii_decoded_correctly(self):
        assert self.decode(b"hello world") == "hello world"

    def test_valid_utf8_decoded_correctly(self):
        # UTF-8 encoded euro sign and em-dash
        data = "€—".encode("utf-8")
        assert self.decode(data) == "€—"

    def test_cp1252_swedish_chars_decoded_correctly(self):
        # Swedish å ä ö — encoded as CP1252 / Latin-1 overlapping bytes
        # CP1252: å=0xE5, ä=0xE4, ö=0xF6
        data = "från Gör om ö".encode("cp1252")
        result = self.decode(data)
        assert "å" in result or "\xe5" in result  # å
        assert "ö" in result or "\xf6" in result  # ö

    def test_latin1_only_bytes_decoded_without_error(self):
        # Bytes that are valid latin-1 but not valid UTF-8 or CP1252
        # 0x9D is undefined in CP1252 but valid latin-1
        data = bytes([0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x9D])
        result = self.decode(data)
        assert isinstance(result, str)
        assert result.startswith("Hello")

    def test_cp1252_nat_rule_comment_does_not_raise(self):
        # Simulated RouterOS NAT print output with a Swedish comment
        # b"\xf6" = ö in cp1252
        raw = b"chain=srcnat action=masquerade comment=\"\xf6ppet n\xe4t\""
        result = self.decode(raw)
        assert isinstance(result, str)
        assert "ppet" in result  # partial match regardless of exact char

    def test_swedish_bytes_reported_in_issue_do_not_raise(self):
        # Exact bytes mentioned in the issue: 0xf6 (ö) and 0xe5 (å)
        raw = bytes([0xF6, 0x20, 0xE5])
        result = self.decode(raw)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# execute_command with non-ASCII stdout/stderr
# ---------------------------------------------------------------------------

def test_execute_command_handles_cp1252_stdout(monkeypatch):
    from mcp_mikrotik.mikrotik_ssh_client import MikroTikSSHClient
    import mcp_mikrotik.mikrotik_ssh_client as mod

    # Simulate RouterOS returning CP1252-encoded bytes on stdout
    cp1252_bytes = "comment=\"från\"".encode("cp1252")

    class DummySSH:
        def set_missing_host_key_policy(self, _): pass
        def connect(self, **kwargs): pass
        def exec_command(self, command):
            return (None, io.BytesIO(cp1252_bytes), io.BytesIO(b""))
        def close(self): pass

    monkeypatch.setattr(mod.paramiko, "SSHClient", lambda: DummySSH())

    client = MikroTikSSHClient(host="h", username="u", password="p", key_filename=None)
    assert client.connect() is True
    result = client.execute_command("/ip firewall nat print")
    assert isinstance(result, str)
    assert "comment=" in result


def test_execute_command_handles_cp1252_stderr(monkeypatch):
    from mcp_mikrotik.mikrotik_ssh_client import MikroTikSSHClient
    import mcp_mikrotik.mikrotik_ssh_client as mod

    # Non-ASCII bytes on stderr, empty stdout → should return decoded stderr
    cp1252_err = "failure: ej till\xe5ten".encode("cp1252")

    class DummySSH:
        def set_missing_host_key_policy(self, _): pass
        def connect(self, **kwargs): pass
        def exec_command(self, command):
            return (None, io.BytesIO(b""), io.BytesIO(cp1252_err))
        def close(self): pass

    monkeypatch.setattr(mod.paramiko, "SSHClient", lambda: DummySSH())

    client = MikroTikSSHClient(host="h", username="u", password="p", key_filename=None)
    assert client.connect() is True
    result = client.execute_command("/ip firewall nat print")
    assert isinstance(result, str)
    assert "failure" in result


def test_ssh_client_requires_connect_for_execute():
    from mcp_mikrotik.mikrotik_ssh_client import MikroTikSSHClient

    client = MikroTikSSHClient(host="h", username="u", password="p", key_filename=None, port=22)
    with pytest.raises(Exception, match="Not connected"):
        client.execute_command("/system identity print")


def test_ssh_client_connect_and_execute(monkeypatch):
    from mcp_mikrotik.mikrotik_ssh_client import MikroTikSSHClient
    import mcp_mikrotik.mikrotik_ssh_client as mod

    state = {"connect_kwargs": None, "closed": 0}

    class DummySSH:
        def set_missing_host_key_policy(self, _policy):
            pass

        def connect(self, **kwargs):
            state["connect_kwargs"] = kwargs

        def exec_command(self, command: str):
            assert command == "/system identity print"
            return (None, io.BytesIO(b"out"), io.BytesIO(b""))

        def close(self):
            state["closed"] += 1

    monkeypatch.setattr(mod.paramiko, "SSHClient", lambda: DummySSH())

    client = MikroTikSSHClient(host="h", username="u", password="p", key_filename="k", port=2222)
    assert client.connect() is True
    assert state["connect_kwargs"]["hostname"] == "h"
    assert state["connect_kwargs"]["port"] == 2222
    assert state["connect_kwargs"]["username"] == "u"
    assert state["connect_kwargs"]["password"] == "p"
    assert state["connect_kwargs"]["key_filename"] == "k"

    assert client.execute_command("/system identity print") == "out"
    client.disconnect()
    assert state["closed"] == 1


def test_ssh_client_returns_stderr_when_no_stdout(monkeypatch):
    from mcp_mikrotik.mikrotik_ssh_client import MikroTikSSHClient
    import mcp_mikrotik.mikrotik_ssh_client as mod

    class DummySSH:
        def set_missing_host_key_policy(self, _policy):
            pass

        def connect(self, **kwargs):
            pass

        def exec_command(self, command: str):
            return (None, io.BytesIO(b""), io.BytesIO(b"failure: nope"))

        def close(self):
            pass

    monkeypatch.setattr(mod.paramiko, "SSHClient", lambda: DummySSH())

    client = MikroTikSSHClient(host="h", username="u", password="p", key_filename=None, port=22)
    assert client.connect() is True
    assert client.execute_command("/x") == "failure: nope"


# ---------------------------------------------------------------------------
# execute_command timeout, SFTP upload/download, wait_for_ssh
# ---------------------------------------------------------------------------

def test_execute_command_timeout(monkeypatch):
    from mcp_mikrotik.mikrotik_ssh_client import MikroTikSSHClient
    import mcp_mikrotik.mikrotik_ssh_client as mod

    class DummyChannel:
        def recv_ready(self):
            return False

        def recv_stderr_ready(self):
            return False

        def exit_status_ready(self):
            return False

        def recv(self, _n):
            return b""

        def recv_stderr(self, _n):
            return b""

    class DummyStdout:
        channel = DummyChannel()

    class DummySSH:
        def set_missing_host_key_policy(self, _policy):
            pass

        def connect(self, **kwargs):
            pass

        def exec_command(self, command: str):
            return (None, DummyStdout(), DummyStdout())

        def close(self):
            pass

    times = iter([0.0, 0.0, 2.0])

    monkeypatch.setattr(mod.paramiko, "SSHClient", lambda: DummySSH())
    monkeypatch.setattr(mod.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(mod.time, "sleep", lambda _s: None)

    client = MikroTikSSHClient(host="h", username="u", password="p", key_filename=None)
    assert client.connect() is True
    with pytest.raises(TimeoutError, match="timed out after 1.0s"):
        client.execute_command("/hang", timeout=1.0)


def test_upload_file_uses_sftp(monkeypatch):
    from mcp_mikrotik.mikrotik_ssh_client import MikroTikSSHClient
    import mcp_mikrotik.mikrotik_ssh_client as mod

    state = {"remote_path": None, "data": None, "sftp_closed": 0}

    class DummySFTP:
        def putfo(self, file_obj, remote_path):
            state["remote_path"] = remote_path
            state["data"] = file_obj.read()

        def close(self):
            state["sftp_closed"] += 1

    class DummySSH:
        def set_missing_host_key_policy(self, _policy):
            pass

        def connect(self, **kwargs):
            pass

        def open_sftp(self):
            return DummySFTP()

        def close(self):
            pass

    monkeypatch.setattr(mod.paramiko, "SSHClient", lambda: DummySSH())

    client = MikroTikSSHClient(host="h", username="u", password="p", key_filename=None)
    assert client.connect() is True
    client.upload_file("config.rsc", b"router-config")
    assert state["remote_path"] == "/config.rsc"
    assert state["data"] == b"router-config"
    assert state["sftp_closed"] == 1


def test_download_file_uses_sftp(monkeypatch):
    from mcp_mikrotik.mikrotik_ssh_client import MikroTikSSHClient
    import mcp_mikrotik.mikrotik_ssh_client as mod

    state = {"remote_path": None, "sftp_closed": 0}

    class DummySFTP:
        def getfo(self, remote_path, file_obj):
            state["remote_path"] = remote_path
            file_obj.write(b"backup-bytes")

        def close(self):
            state["sftp_closed"] += 1

    class DummySSH:
        def set_missing_host_key_policy(self, _policy):
            pass

        def connect(self, **kwargs):
            pass

        def open_sftp(self):
            return DummySFTP()

        def close(self):
            pass

    monkeypatch.setattr(mod.paramiko, "SSHClient", lambda: DummySSH())

    client = MikroTikSSHClient(host="h", username="u", password="p", key_filename=None)
    assert client.connect() is True
    data = client.download_file("/backup.backup")
    assert state["remote_path"] == "/backup.backup"
    assert data == b"backup-bytes"
    assert state["sftp_closed"] == 1


def test_upload_file_requires_connect():
    from mcp_mikrotik.mikrotik_ssh_client import MikroTikSSHClient

    client = MikroTikSSHClient(host="h", username="u", password="p", key_filename=None)
    with pytest.raises(Exception, match="Not connected"):
        client.upload_file("x.rsc", b"x")


def test_download_file_requires_connect():
    from mcp_mikrotik.mikrotik_ssh_client import MikroTikSSHClient

    client = MikroTikSSHClient(host="h", username="u", password="p", key_filename=None)
    with pytest.raises(Exception, match="Not connected"):
        client.download_file("x.backup")


def test_wait_for_ssh_succeeds(monkeypatch):
    from mcp_mikrotik.mikrotik_ssh_client import MikroTikSSHClient
    import mcp_mikrotik.mikrotik_ssh_client as mod

    attempts = {"count": 0}

    def fake_connect(self):
        attempts["count"] += 1
        return attempts["count"] >= 2

    def fake_disconnect(self):
        pass

    monkeypatch.setattr(MikroTikSSHClient, "connect", fake_connect)
    monkeypatch.setattr(MikroTikSSHClient, "disconnect", fake_disconnect)
    monkeypatch.setattr(mod.time, "monotonic", lambda: 0.0)
    monkeypatch.setattr(mod.time, "sleep", lambda _s: None)

    assert MikroTikSSHClient.wait_for_ssh(
        host="h",
        username="u",
        password="p",
        key_filename=None,
        timeout=10.0,
        interval=1.0,
    ) is True
    assert attempts["count"] == 2


def test_wait_for_ssh_times_out(monkeypatch):
    from mcp_mikrotik.mikrotik_ssh_client import MikroTikSSHClient
    import mcp_mikrotik.mikrotik_ssh_client as mod

    times = iter([0.0, 5.0, 11.0])

    monkeypatch.setattr(MikroTikSSHClient, "connect", lambda self: False)
    monkeypatch.setattr(mod.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(mod.time, "sleep", lambda _s: None)

    assert MikroTikSSHClient.wait_for_ssh(
        host="h",
        username="u",
        password="p",
        key_filename=None,
        timeout=10.0,
        interval=1.0,
    ) is False

