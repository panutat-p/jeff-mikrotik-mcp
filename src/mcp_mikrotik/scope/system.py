from typing import Optional

from mcp.server.fastmcp import Context

from ..app import mcp, READ, WRITE, WRITE_IDEMPOTENT, DANGEROUS, annotate
from ..connector import execute_mikrotik_command


# ---------------------------------------------------------------------------
# System Information
# ---------------------------------------------------------------------------

@mcp.tool(name="get_system_resource", annotations=annotate(READ, "System Resource"))
async def mikrotik_get_system_resource(ctx: Context) -> str:
    """Gets system resource information (CPU, memory, uptime, version)."""
    await ctx.info("Getting system resource information")

    cmd = "/system resource print"
    result = await execute_mikrotik_command(cmd, ctx)

    if not result:
        return "Unable to retrieve system resource information."

    return f"SYSTEM RESOURCE:\n\n{result}"


@mcp.tool(name="get_system_health", annotations=annotate(READ, "System Health"))
async def mikrotik_get_system_health(ctx: Context) -> str:
    """Gets system health metrics (temperature, voltage, etc.) if supported."""
    await ctx.info("Getting system health information")

    cmd = "/system health print"
    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No system health data available (may not be supported on this device)."

    return f"SYSTEM HEALTH:\n\n{result}"


@mcp.tool(name="get_system_clock", annotations=annotate(READ, "System Clock"))
async def mikrotik_get_system_clock(ctx: Context) -> str:
    """Gets the current system clock and time zone settings."""
    await ctx.info("Getting system clock")

    cmd = "/system clock print"
    result = await execute_mikrotik_command(cmd, ctx)

    if not result:
        return "Unable to retrieve system clock."

    return f"SYSTEM CLOCK:\n\n{result}"


@mcp.tool(name="set_system_clock", annotations=annotate(WRITE_IDEMPOTENT, "Set System Clock"))
async def mikrotik_set_system_clock(
    ctx: Context,
    date: Optional[str] = None,
    time: Optional[str] = None,
    time_zone_name: Optional[str] = None,
    gmt_offset: Optional[str] = None,
) -> str:
    """Sets the system clock or time zone on the MikroTik device.

    Notes:
        date: date string e.g. "jun/07/2026"
        time: time string e.g. "14:30:00"
        time_zone_name: IANA zone e.g. "America/New_York"
        gmt_offset: offset string e.g. "-05:00"
    """
    await ctx.info("Setting system clock")

    updates = []
    if date is not None:
        updates.append(f'date="{date}"')
    if time is not None:
        updates.append(f'time="{time}"')
    if time_zone_name is not None:
        updates.append(f'time-zone-name="{time_zone_name}"')
    if gmt_offset is not None:
        updates.append(f'gmt-offset="{gmt_offset}"')

    if not updates:
        return "No updates specified."

    cmd = "/system clock set " + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to set system clock: {result}"

    details = await execute_mikrotik_command("/system clock print", ctx)
    return f"System clock updated successfully:\n\n{details}"


@mcp.tool(name="get_system_identity", annotations=annotate(READ, "System Identity"))
async def mikrotik_get_system_identity(ctx: Context) -> str:
    """Gets the system identity (router name)."""
    await ctx.info("Getting system identity")

    cmd = "/system identity print"
    result = await execute_mikrotik_command(cmd, ctx)

    if not result:
        return "Unable to retrieve system identity."

    return f"SYSTEM IDENTITY:\n\n{result}"


@mcp.tool(name="set_system_identity", annotations=annotate(WRITE_IDEMPOTENT, "Set System Identity"))
async def mikrotik_set_system_identity(ctx: Context, name: str) -> str:
    """Sets the system identity (router name)."""
    await ctx.info(f"Setting system identity: name={name}")

    cmd = f'/system identity set name="{name}"'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to set system identity: {result}"

    details = await execute_mikrotik_command("/system identity print", ctx)
    return f"System identity updated successfully:\n\n{details}"


@mcp.tool(name="get_routerboard", annotations=annotate(READ, "RouterBoard Info"))
async def mikrotik_get_routerboard(ctx: Context) -> str:
    """Gets RouterBoard hardware information."""
    await ctx.info("Getting RouterBoard information")

    cmd = "/system routerboard print"
    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No RouterBoard information available."

    return f"ROUTERBOARD:\n\n{result}"


@mcp.tool(name="get_license", annotations=annotate(READ, "License Info"))
async def mikrotik_get_license(ctx: Context) -> str:
    """Gets RouterOS license information."""
    await ctx.info("Getting license information")

    cmd = "/system license print"
    result = await execute_mikrotik_command(cmd, ctx)

    if not result:
        return "Unable to retrieve license information."

    return f"LICENSE:\n\n{result}"


# ---------------------------------------------------------------------------
# System Control (DANGEROUS)
# ---------------------------------------------------------------------------

@mcp.tool(name="reboot_system", annotations=annotate(DANGEROUS, "Reboot System"))
async def mikrotik_reboot_system(ctx: Context) -> str:
    """Reboots the MikroTik device. DANGEROUS — disconnects all sessions."""
    await ctx.info("Rebooting system")

    result = await execute_mikrotik_command("/system reboot", ctx, timeout=10.0)

    if result.startswith("Error"):
        return f"Reboot command failed: {result}"

    return "Reboot initiated. The device will restart and SSH will be unavailable briefly."


@mcp.tool(name="shutdown_system", annotations=annotate(DANGEROUS, "Shutdown System"))
async def mikrotik_shutdown_system(ctx: Context) -> str:
    """Shuts down the MikroTik device. DANGEROUS — requires manual power-on."""
    await ctx.info("Shutting down system")

    result = await execute_mikrotik_command("/system shutdown", ctx, timeout=10.0)

    if result.startswith("Error"):
        return f"Shutdown command failed: {result}"

    return "Shutdown initiated. The device will power off and require manual restart."


# ---------------------------------------------------------------------------
# Package Updates (DANGEROUS)
# ---------------------------------------------------------------------------

@mcp.tool(name="check_for_updates", annotations=annotate(READ, "Check For Updates"))
async def mikrotik_check_for_updates(ctx: Context) -> str:
    """Checks for RouterOS package updates."""
    await ctx.info("Checking for package updates")

    cmd = "/system package update check-for-updates"
    result = await execute_mikrotik_command(cmd, ctx, timeout=120.0)

    if not result:
        return "Update check completed with no output."

    return f"UPDATE CHECK:\n\n{result}"


@mcp.tool(name="install_updates", annotations=annotate(DANGEROUS, "Install Updates"))
async def mikrotik_install_updates(ctx: Context) -> str:
    """Installs downloaded RouterOS package updates. DANGEROUS — may reboot the device."""
    await ctx.info("Installing package updates")

    result = await execute_mikrotik_command(
        "/system package update install",
        ctx,
        timeout=300.0,
    )

    if result.startswith("Error"):
        return f"Update installation failed: {result}"

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to install updates: {result}"

    return (
        "Update installation initiated. The device may reboot automatically. "
        "Poll SSH connectivity before running further commands."
    )
