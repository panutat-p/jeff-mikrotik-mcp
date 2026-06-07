import asyncio
import logging
from typing import Optional

from mcp.server.fastmcp import Context

from . import config
from .mikrotik_ssh_client import MikroTikSSHClient

logger = logging.getLogger(__name__)


def _make_ssh_client() -> MikroTikSSHClient:
    return MikroTikSSHClient(
        host=config.mikrotik_config.host,
        username=config.mikrotik_config.username,
        password=config.mikrotik_config.password,
        key_filename=config.mikrotik_config.key_filename,
        port=config.mikrotik_config.port,
    )


def _execute_sync(command: str, timeout: Optional[float] = None) -> str:
    """Execute a MikroTik command via SSH and return the output (blocking)."""
    logger.info(f"Executing MikroTik command: {command}")

    ssh_client = _make_ssh_client()

    try:
        if not ssh_client.connect():
            return "Error: Failed to connect to MikroTik device"

        result = ssh_client.execute_command(command, timeout=timeout)
        logger.info(f"Command result: {repr(result)}")
        return result
    except TimeoutError as e:
        error_msg = f"Error executing command: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error executing command: {str(e)}"
        logger.error(error_msg)
        return error_msg
    finally:
        ssh_client.disconnect()


def _upload_file_sync(filename: str, content: bytes) -> str:
    """Upload a file to the MikroTik device via SFTP (blocking)."""
    ssh_client = _make_ssh_client()
    try:
        if not ssh_client.connect():
            return "Error: Failed to connect to MikroTik device"
        ssh_client.upload_file(filename, content)
        return ""
    except Exception as e:
        return f"Error uploading file: {str(e)}"
    finally:
        ssh_client.disconnect()


def _download_file_sync(filename: str) -> tuple[bytes, str]:
    """Download a file from the MikroTik device via SFTP (blocking)."""
    ssh_client = _make_ssh_client()
    try:
        if not ssh_client.connect():
            return b"", "Error: Failed to connect to MikroTik device"
        return ssh_client.download_file(filename), ""
    except Exception as e:
        return b"", f"Error downloading file: {str(e)}"
    finally:
        ssh_client.disconnect()


def wait_for_router_ssh(timeout: float = 120.0, interval: float = 3.0) -> bool:
    """Poll until the configured router accepts SSH connections."""
    return MikroTikSSHClient.wait_for_ssh(
        host=config.mikrotik_config.host,
        username=config.mikrotik_config.username,
        password=config.mikrotik_config.password,
        key_filename=config.mikrotik_config.key_filename,
        port=config.mikrotik_config.port,
        timeout=timeout,
        interval=interval,
    )


async def execute_mikrotik_command(
    command: str,
    ctx: Context,
    timeout: Optional[float] = None,
) -> str:
    """Execute a MikroTik command via SSH and return the output."""
    from .safe_mode import get_safe_mode_manager

    safe_mgr = get_safe_mode_manager()
    if safe_mgr.is_active:
        await ctx.info(f"Executing (safe mode): {command}")
        try:
            result = await asyncio.to_thread(safe_mgr.execute, command)
        except Exception as e:
            result = f"Error executing command in safe mode session: {str(e)}"
    else:
        await ctx.info(f"Executing MikroTik command: {command}")
        result = await asyncio.to_thread(_execute_sync, command, timeout)

    logger.info(f"Command result: {repr(result)}")
    if result.startswith("Error"):
        await ctx.error(result)
    return result


async def upload_file_to_router(filename: str, content: bytes, ctx: Context) -> str:
    """Upload a file to the MikroTik device via SFTP."""
    await ctx.info(f"Uploading file via SFTP: {filename}")
    error = await asyncio.to_thread(_upload_file_sync, filename, content)
    if error:
        await ctx.error(error)
    return error


async def download_file_from_router(filename: str, ctx: Context) -> tuple[bytes, str]:
    """Download a file from the MikroTik device via SFTP."""
    await ctx.info(f"Downloading file via SFTP: {filename}")
    data, error = await asyncio.to_thread(_download_file_sync, filename)
    if error:
        await ctx.error(error)
    return data, error
