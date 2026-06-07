from typing import Literal, Optional

from mcp.server.fastmcp import Context

from ..app import mcp, READ, DANGEROUS, annotate
from ..connector import execute_mikrotik_command


# ---------------------------------------------------------------------------
# Device Mode
# ---------------------------------------------------------------------------

@mcp.tool(name="get_device_mode", annotations=annotate(READ, "Get Device Mode"))
async def mikrotik_get_device_mode(ctx: Context) -> str:
    """Gets the current device-mode status and feature flags."""
    await ctx.info("Getting device-mode status")

    result = await execute_mikrotik_command("/system device-mode print", ctx)

    if not result or result.strip() == "":
        return "Unable to retrieve device-mode status."

    return f"DEVICE MODE:\n\n{result}"


@mcp.tool(name="list_device_mode_settings", annotations=annotate(READ, "List Device Mode Settings"))
async def mikrotik_list_device_mode_settings(ctx: Context) -> str:
    """Lists the active device-mode configuration settings."""
    await ctx.info("Listing device-mode settings")

    result = await execute_mikrotik_command("/system device-mode print config", ctx)

    if not result or result.strip() == "":
        return "No device-mode settings found."

    return f"DEVICE MODE SETTINGS:\n\n{result}"


@mcp.tool(name="update_device_mode", annotations=annotate(DANGEROUS, "Update Device Mode"))
async def mikrotik_update_device_mode(
    ctx: Context,
    mode: Optional[Literal["advanced", "home", "basic", "rose"]] = None,
    container: Optional[bool] = None,
    scheduler: Optional[bool] = None,
    fetch: Optional[bool] = None,
    hotspot: Optional[bool] = None,
    zerotier: Optional[bool] = None,
    sniffer: Optional[bool] = None,
    proxy: Optional[bool] = None,
    socks: Optional[bool] = None,
    email: Optional[bool] = None,
    smb: Optional[bool] = None,
    ipsec: Optional[bool] = None,
    pptp: Optional[bool] = None,
    l2tp: Optional[bool] = None,
    romon: Optional[bool] = None,
    bandwidth_test: Optional[bool] = None,
    traffic_gen: Optional[bool] = None,
    partitions: Optional[bool] = None,
    routerboard: Optional[bool] = None,
    install_any_version: Optional[bool] = None,
    flagged: Optional[bool] = None,
    flagging_enabled: Optional[bool] = None,
    activation_timeout: Optional[str] = None,
) -> str:
    """Requests a device-mode change. Physical confirmation is required before it takes effect.

    Notes:
        After running this command the router waits for physical confirmation
        (press reset/mode button or power-cycle) within the activation timeout
        (default 5 minutes). The device reboots once confirmed.
        mode: replaces the entire device-mode configuration when set.
        activation_timeout: duration e.g. "5m", "10m", "1h"
    """
    await ctx.info("Requesting device-mode update")

    updates = []
    if mode is not None:
        updates.append(f"mode={mode}")
    if container is not None:
        updates.append(f'container={"yes" if container else "no"}')
    if scheduler is not None:
        updates.append(f'scheduler={"yes" if scheduler else "no"}')
    if fetch is not None:
        updates.append(f'fetch={"yes" if fetch else "no"}')
    if hotspot is not None:
        updates.append(f'hotspot={"yes" if hotspot else "no"}')
    if zerotier is not None:
        updates.append(f'zerotier={"yes" if zerotier else "no"}')
    if sniffer is not None:
        updates.append(f'sniffer={"yes" if sniffer else "no"}')
    if proxy is not None:
        updates.append(f'proxy={"yes" if proxy else "no"}')
    if socks is not None:
        updates.append(f'socks={"yes" if socks else "no"}')
    if email is not None:
        updates.append(f'email={"yes" if email else "no"}')
    if smb is not None:
        updates.append(f'smb={"yes" if smb else "no"}')
    if ipsec is not None:
        updates.append(f'ipsec={"yes" if ipsec else "no"}')
    if pptp is not None:
        updates.append(f'pptp={"yes" if pptp else "no"}')
    if l2tp is not None:
        updates.append(f'l2tp={"yes" if l2tp else "no"}')
    if romon is not None:
        updates.append(f'romon={"yes" if romon else "no"}')
    if bandwidth_test is not None:
        updates.append(f'bandwidth-test={"yes" if bandwidth_test else "no"}')
    if traffic_gen is not None:
        updates.append(f'traffic-gen={"yes" if traffic_gen else "no"}')
    if partitions is not None:
        updates.append(f'partitions={"yes" if partitions else "no"}')
    if routerboard is not None:
        updates.append(f'routerboard={"yes" if routerboard else "no"}')
    if install_any_version is not None:
        updates.append(f'install-any-version={"yes" if install_any_version else "no"}')
    if flagged is not None:
        updates.append(f'flagged={"yes" if flagged else "no"}')
    if flagging_enabled is not None:
        updates.append(f'flagging-enabled={"yes" if flagging_enabled else "no"}')
    if activation_timeout is not None:
        updates.append(f"activation-timeout={activation_timeout}")

    if not updates:
        return "No updates specified."

    cmd = "/system device-mode update " + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx, timeout=300)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to update device-mode: {result}"

    return (
        f"Device-mode update requested:\n\n{result}\n\n"
        "PHYSICAL CONFIRMATION REQUIRED: press the reset/mode button or "
        "power-cycle the router within the activation timeout. "
        "The router will reboot once confirmed. "
        "If no physical action is taken, the change is automatically canceled."
    )


@mcp.tool(name="cancel_device_mode_update", annotations=annotate(DANGEROUS, "Cancel Device Mode Update"))
async def mikrotik_cancel_device_mode_update(ctx: Context) -> str:
    """Cancels a pending device-mode update by issuing a secondary update command."""
    await ctx.info("Canceling pending device-mode update")

    result = await execute_mikrotik_command(
        "/system device-mode update activation-timeout=5m", ctx, timeout=30
    )

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to cancel device-mode update: {result}"

    return (
        f"Device-mode update cancellation requested:\n\n{result}\n\n"
        "If a device-mode change was pending, RouterOS cancels both updates "
        "when a second update command is issued during the activation window."
    )
