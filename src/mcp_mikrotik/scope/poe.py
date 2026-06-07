from typing import Optional
from ..connector import execute_mikrotik_command
from mcp.server.fastmcp import Context
from ..app import mcp, READ, annotate


@mcp.tool(name="get_poe_monitor", annotations=annotate(READ, "PoE Monitor"))
async def mikrotik_get_poe_monitor(ctx: Context, interfaces: str) -> str:
    """Reads real-time Power-over-Ethernet (PoE) monitor data for one or more
    ethernet interfaces — PoE-out status, voltage, current, and power.

    Runs ``/interface ethernet poe monitor <interfaces> once``.

    Notes:
        interfaces: comma-separated ethernet interface name(s), e.g.
            "ether1" or "ether9-ap,ether10-ap,ether11-ap,ether12-ap"
    """
    await ctx.info(f"Reading PoE monitor for: {interfaces}")

    # `once` is required — without it the monitor streams continuously and the
    # command never returns (it would hang the SSH session).
    cmd = f"/interface ethernet poe monitor {interfaces} once"
    result = await execute_mikrotik_command(cmd, ctx)

    if not result or not result.strip():
        return (
            f"No PoE monitor data returned for: {interfaces}. "
            "The interface(s) may not exist or the device may not support PoE."
        )

    return f"POE MONITOR:\n\n{result}"


@mcp.tool(name="query_poe", annotations=annotate(READ, "Query PoE"))
async def mikrotik_query_poe(
    ctx: Context,
    name: Optional[str] = None,
    interface_filter: Optional[str] = None,
) -> str:
    """Lists PoE configuration or returns detail for a specific ethernet interface by name."""
    if name:
        await ctx.info(f"Getting PoE settings for: {name}")
        cmd = f'/interface ethernet poe print detail where name="{name}"'
        result = await execute_mikrotik_command(cmd, ctx)
        if not result or not result.strip():
            return f"No PoE settings found for interface '{name}'."
        return f"POE SETTINGS:\n\n{result}"

    await ctx.info("Listing PoE configuration")
    cmd = "/interface ethernet poe print"
    if interface_filter:
        cmd += f' where name~"{interface_filter}"'
    result = await execute_mikrotik_command(cmd, ctx)
    if not result or not result.strip():
        return (
            "No PoE-capable ethernet interfaces found. "
            "The device may not support PoE."
        )
    return f"POE CONFIGURATION:\n\n{result}"
