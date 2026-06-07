from typing import Literal, Optional
from ..connector import execute_mikrotik_command
from mcp.server.fastmcp import Context
from ..app import mcp, READ, WRITE_IDEMPOTENT, annotate


@mcp.tool(name="query_interfaces", annotations=annotate(READ, "Query Interfaces"))
async def mikrotik_query_interfaces(
    ctx: Context,
    name: Optional[str] = None,
    type_filter: Optional[Literal[
        "ether", "wg", "bridge", "vlan", "pppoe-out", "pppoe-server",
        "wifi", "wireless", "lte", "loopback", "sfp", "sfp-sfpplus"
    ]] = None,
    name_filter: Optional[str] = None,
    running_only: bool = False,
    disabled_only: bool = False,
) -> str:
    """Lists all interfaces or returns detail for a specific one by name."""
    if name:
        await ctx.info(f"Getting interface details: name={name}")
        cmd = f'/interface print detail where name="{name}"'
        result = await execute_mikrotik_command(cmd, ctx)
        if not result or result.strip() == "":
            return f"Interface '{name}' not found."
        return f"INTERFACE DETAILS:\n\n{result}"

    await ctx.info("Listing all interfaces")
    cmd = "/interface print"
    filters = []
    if type_filter:
        filters.append(f'type="{type_filter}"')
    if name_filter:
        filters.append(f'name~"{name_filter}"')
    if running_only:
        filters.append("running=yes")
    if disabled_only:
        filters.append("disabled=yes")
    if filters:
        cmd += " where " + " ".join(filters)
    result = await execute_mikrotik_command(cmd, ctx)
    if not result or result.strip() == "":
        return "No interfaces found matching the criteria."
    return f"INTERFACES:\n\n{result}"


@mcp.tool(name="set_interface_enabled", annotations=annotate(WRITE_IDEMPOTENT, "Set Interface Enabled"))
async def mikrotik_set_interface_enabled(ctx: Context, name: str, enabled: bool) -> str:
    """Enables or disables an interface on the MikroTik device."""
    action = "enable" if enabled else "disable"
    await ctx.info(f"Setting interface {action}d: name={name}")
    cmd = f'/interface {action} [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)
    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to {action} interface '{name}': {result}"
    check_cmd = f'/interface print detail where name="{name}"'
    details = await execute_mikrotik_command(check_cmd, ctx)
    if not details.strip():
        return f"Interface '{name}' not found."
    return f"Interface '{name}' {action}d successfully:\n\n{details}"
