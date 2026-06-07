import io
import logging
import time
from typing import Optional

import paramiko

logger = logging.getLogger(__name__)

DEFAULT_COMMAND_TIMEOUT = 30.0


class MikroTikSSHClient:
    """SSH client for MikroTik devices."""

    def __init__(self, host: str, username: str, password: str, key_filename: Optional[str], port: int = 22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None
        self.channel = None
        self.key_filename = key_filename

    @staticmethod
    def _decode_output(data: bytes) -> str:
        """Decode raw SSH output bytes with a multi-encoding fallback chain."""
        if not data:
            return ""
        for encoding in ("utf-8", "cp1252", "latin-1"):
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="replace")

    @staticmethod
    def _normalize_remote_path(filename: str) -> str:
        """Return RouterOS SFTP path for a file in the device root."""
        name = filename.lstrip("/")
        return f"/{name}"

    def connect(self):
        """Establish SSH connection to MikroTik device."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                key_filename=self.key_filename,
                look_for_keys=False,
                allow_agent=False,
                timeout=10,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MikroTik: {e}")
            return False

    def _read_channel(self, stdout, stderr, timeout: Optional[float]) -> tuple[str, str]:
        """Read stdout/stderr from exec_command channels with optional timeout."""
        if not hasattr(stdout, "channel"):
            output = self._decode_output(stdout.read())
            error = self._decode_output(stderr.read())
            return output, error

        deadline = time.monotonic() + timeout if timeout is not None else None
        out_chunks: list[bytes] = []
        err_chunks: list[bytes] = []

        while True:
            if stdout.channel.recv_ready():
                out_chunks.append(stdout.channel.recv(4096))
            if stderr.channel.recv_stderr_ready():
                err_chunks.append(stderr.channel.recv_stderr(4096))

            if stdout.channel.exit_status_ready():
                while stdout.channel.recv_ready():
                    out_chunks.append(stdout.channel.recv(4096))
                while stderr.channel.recv_stderr_ready():
                    err_chunks.append(stderr.channel.recv_stderr(4096))
                break

            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError(f"Command timed out after {timeout}s")

            time.sleep(0.05)

        output = self._decode_output(b"".join(out_chunks))
        error = self._decode_output(b"".join(err_chunks))
        return output, error

    def execute_command(self, command: str, timeout: Optional[float] = None) -> str:
        """Execute a command on MikroTik device using exec_command."""
        if not self.client:
            raise Exception("Not connected to MikroTik device")

        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            output, error = self._read_channel(stdout, stderr, timeout)

            if error and not output:
                return error

            return output
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            raise

    def upload_file(self, filename: str, data: bytes) -> None:
        """Upload bytes to the MikroTik filesystem via SFTP."""
        if not self.client:
            raise Exception("Not connected to MikroTik device")

        remote_path = self._normalize_remote_path(filename)
        sftp = self.client.open_sftp()
        try:
            sftp.putfo(io.BytesIO(data), remote_path)
        finally:
            sftp.close()

    def download_file(self, filename: str) -> bytes:
        """Download a file from the MikroTik filesystem via SFTP."""
        if not self.client:
            raise Exception("Not connected to MikroTik device")

        remote_path = self._normalize_remote_path(filename)
        sftp = self.client.open_sftp()
        try:
            buf = io.BytesIO()
            sftp.getfo(remote_path, buf)
            return buf.getvalue()
        finally:
            sftp.close()

    @classmethod
    def wait_for_ssh(
        cls,
        host: str,
        username: str,
        password: str,
        key_filename: Optional[str],
        port: int = 22,
        timeout: float = 120.0,
        interval: float = 3.0,
    ) -> bool:
        """Poll until SSH becomes reachable or timeout expires."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            client = cls(host, username, password, key_filename, port)
            if client.connect():
                client.disconnect()
                return True
            time.sleep(interval)
        return False

    def disconnect(self):
        """Close SSH connection."""
        if self.client:
            self.client.close()
