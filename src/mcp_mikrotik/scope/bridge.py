from typing import Literal, Optional

from mcp.server.fastmcp import Context

from ..app import mcp, READ, WRITE, WRITE_IDEMPOTENT, DESTRUCTIVE, annotate
from ..connector import execute_mikrotik_command


# ---------------------------------------------------------------------------
# Bridge Interface Management
# ---------------------------------------------------------------------------

@mcp.tool(name="create_bridge", annotations=annotate(WRITE, "Create Bridge"))
async def mikrotik_create_bridge(
    ctx: Context,
    name: str,
    vlan_filtering: bool = False,
    protocol_mode: Literal["none", "rstp", "mstp", "stp"] = "rstp",
    comment: Optional[str] = None,
    disabled: bool = False,
) -> str:
    """Creates a bridge interface on the MikroTik device."""
    await ctx.info(f"Creating bridge: name={name}")

    cmd = f'/interface bridge add name="{name}" protocol-mode={protocol_mode}'

    if vlan_filtering:
        cmd += " vlan-filtering=yes"
    if comment:
        cmd += f' comment="{comment}"'
    if disabled:
        cmd += " disabled=yes"

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to create bridge: {result}"

    details_cmd = f'/interface bridge print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Bridge created successfully:\n\n{details}"
    return "Bridge created successfully."


@mcp.tool(name="list_bridges", annotations=annotate(READ, "List Bridges"))
async def mikrotik_list_bridges(
    ctx: Context,
    name_filter: Optional[str] = None,
    disabled_only: bool = False,
    running_only: bool = False,
) -> str:
    """Lists bridge interfaces on the MikroTik device."""
    await ctx.info("Listing bridges")

    cmd = "/interface bridge print"

    filters = []
    if name_filter:
        filters.append(f'name~"{name_filter}"')
    if disabled_only:
        filters.append("disabled=yes")
    if running_only:
        filters.append("running=yes")

    if filters:
        cmd += " where " + " ".join(filters)

    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No bridges found."

    return f"BRIDGES:\n\n{result}"


@mcp.tool(name="get_bridge", annotations=annotate(READ, "Get Bridge"))
async def mikrotik_get_bridge(ctx: Context, name: str) -> str:
    """Gets detailed information about a specific bridge interface."""
    await ctx.info(f"Getting bridge details: name={name}")

    cmd = f'/interface bridge print detail where name="{name}"'
    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "":
        return f"Bridge '{name}' not found."

    return f"BRIDGE DETAILS:\n\n{result}"


@mcp.tool(name="update_bridge", annotations=annotate(WRITE_IDEMPOTENT, "Update Bridge"))
async def mikrotik_update_bridge(
    ctx: Context,
    name: str,
    new_name: Optional[str] = None,
    vlan_filtering: Optional[bool] = None,
    protocol_mode: Optional[Literal["none", "rstp", "mstp", "stp"]] = None,
    comment: Optional[str] = None,
    disabled: Optional[bool] = None,
) -> str:
    """Updates an existing bridge interface's settings on the MikroTik device."""
    await ctx.info(f"Updating bridge: name={name}")

    updates = []
    if new_name:
        updates.append(f'name="{new_name}"')
    if vlan_filtering is not None:
        updates.append(f'vlan-filtering={"yes" if vlan_filtering else "no"}')
    if protocol_mode:
        updates.append(f"protocol-mode={protocol_mode}")
    if comment is not None:
        updates.append(f'comment="{comment}"')
    if disabled is not None:
        updates.append(f'disabled={"yes" if disabled else "no"}')

    if not updates:
        return "No updates specified."

    cmd = f'/interface bridge set [find name="{name}"] ' + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to update bridge: {result}"

    lookup_name = new_name if new_name else name
    details_cmd = f'/interface bridge print detail where name="{lookup_name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    return f"Bridge updated successfully:\n\n{details}"


@mcp.tool(name="remove_bridge", annotations=annotate(DESTRUCTIVE, "Remove Bridge"))
async def mikrotik_remove_bridge(ctx: Context, name: str) -> str:
    """Removes a bridge interface from the MikroTik device."""
    await ctx.info(f"Removing bridge: name={name}")

    check_cmd = f'/interface bridge print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"Bridge '{name}' not found."

    cmd = f'/interface bridge remove [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove bridge: {result}"

    return f"Bridge '{name}' removed successfully."


# ---------------------------------------------------------------------------
# Bridge Port Management
# ---------------------------------------------------------------------------

@mcp.tool(name="add_bridge_port", annotations=annotate(WRITE, "Add Bridge Port"))
async def mikrotik_add_bridge_port(
    ctx: Context,
    bridge: str,
    interface: str,
    pvid: Optional[int] = None,
    frame_types: Optional[Literal["admit-all", "admit-only-vlan-tagged", "admit-only-untagged-and-priority-tagged"]] = None,
    comment: Optional[str] = None,
    disabled: bool = False,
) -> str:
    """Adds an interface as a port to a bridge on the MikroTik device."""
    await ctx.info(f"Adding bridge port: bridge={bridge}, interface={interface}")

    cmd = f'/interface bridge port add bridge="{bridge}" interface="{interface}"'

    if pvid is not None:
        cmd += f" pvid={pvid}"
    if frame_types:
        cmd += f" frame-types={frame_types}"
    if comment:
        cmd += f' comment="{comment}"'
    if disabled:
        cmd += " disabled=yes"

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to add bridge port: {result}"

    details_cmd = (
        f'/interface bridge port print detail where'
        f' bridge="{bridge}" interface="{interface}"'
    )
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Bridge port added successfully:\n\n{details}"
    return "Bridge port added successfully."


@mcp.tool(name="list_bridge_ports", annotations=annotate(READ, "List Bridge Ports"))
async def mikrotik_list_bridge_ports(
    ctx: Context,
    bridge_filter: Optional[str] = None,
    interface_filter: Optional[str] = None,
    disabled_only: bool = False,
) -> str:
    """Lists bridge ports on the MikroTik device."""
    await ctx.info("Listing bridge ports")

    cmd = "/interface bridge port print"

    filters = []
    if bridge_filter:
        filters.append(f'bridge="{bridge_filter}"')
    if interface_filter:
        filters.append(f'interface="{interface_filter}"')
    if disabled_only:
        filters.append("disabled=yes")

    if filters:
        cmd += " where " + " ".join(filters)

    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No bridge ports found."

    return f"BRIDGE PORTS:\n\n{result}"


@mcp.tool(name="update_bridge_port", annotations=annotate(WRITE_IDEMPOTENT, "Update Bridge Port"))
async def mikrotik_update_bridge_port(
    ctx: Context,
    port_id: str,
    bridge: Optional[str] = None,
    interface: Optional[str] = None,
    pvid: Optional[int] = None,
    frame_types: Optional[Literal["admit-all", "admit-only-vlan-tagged", "admit-only-untagged-and-priority-tagged"]] = None,
    comment: Optional[str] = None,
    disabled: Optional[bool] = None,
) -> str:
    """Updates an existing bridge port's settings on the MikroTik device.

    Notes:
        port_id: "*N" or "N" from list output e.g. "*2"
    """
    await ctx.info(f"Updating bridge port: port_id={port_id}")

    updates = []
    if bridge:
        updates.append(f'bridge="{bridge}"')
    if interface:
        updates.append(f'interface="{interface}"')
    if pvid is not None:
        updates.append(f"pvid={pvid}")
    if frame_types:
        updates.append(f"frame-types={frame_types}")
    if comment is not None:
        updates.append(f'comment="{comment}"')
    if disabled is not None:
        updates.append(f'disabled={"yes" if disabled else "no"}')

    if not updates:
        return "No updates specified."

    cmd = f"/interface bridge port set {port_id} " + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to update bridge port: {result}"

    details_cmd = f"/interface bridge port print detail where .id={port_id}"
    details = await execute_mikrotik_command(details_cmd, ctx)

    return f"Bridge port updated successfully:\n\n{details}"


@mcp.tool(name="remove_bridge_port", annotations=annotate(DESTRUCTIVE, "Remove Bridge Port"))
async def mikrotik_remove_bridge_port(ctx: Context, port_id: str) -> str:
    """Removes a bridge port by ID.

    Notes:
        port_id: "*N" or "N" from list output e.g. "*2"
    """
    await ctx.info(f"Removing bridge port: port_id={port_id}")

    check_cmd = f"/interface bridge port print count-only where .id={port_id}"
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"Bridge port with ID '{port_id}' not found."

    cmd = f"/interface bridge port remove {port_id}"
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove bridge port: {result}"

    return f"Bridge port '{port_id}' removed successfully."


# ---------------------------------------------------------------------------
# Bonding Interface Management
# ---------------------------------------------------------------------------

@mcp.tool(name="create_bonding", annotations=annotate(WRITE, "Create Bonding"))
async def mikrotik_create_bonding(
    ctx: Context,
    name: str,
    mode: Literal[
        "802.3ad", "active-backup", "balance-alb", "balance-rr",
        "balance-tlb", "balance-xor", "broadcast", "none", "static"
    ] = "802.3ad",
    slaves: Optional[str] = None,
    comment: Optional[str] = None,
    disabled: bool = False,
) -> str:
    """Creates a bonding interface on the MikroTik device.

    Notes:
        slaves: comma-separated interface names e.g. "ether1,ether2"
    """
    await ctx.info(f"Creating bonding interface: name={name}")

    cmd = f'/interface bonding add name="{name}" mode={mode}'

    if slaves:
        cmd += f" slaves={slaves}"
    if comment:
        cmd += f' comment="{comment}"'
    if disabled:
        cmd += " disabled=yes"

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to create bonding interface: {result}"

    details_cmd = f'/interface bonding print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Bonding interface created successfully:\n\n{details}"
    return "Bonding interface created successfully."


@mcp.tool(name="list_bonding", annotations=annotate(READ, "List Bonding"))
async def mikrotik_list_bonding(
    ctx: Context,
    name_filter: Optional[str] = None,
    disabled_only: bool = False,
    running_only: bool = False,
) -> str:
    """Lists bonding interfaces on the MikroTik device."""
    await ctx.info("Listing bonding interfaces")

    cmd = "/interface bonding print"

    filters = []
    if name_filter:
        filters.append(f'name~"{name_filter}"')
    if disabled_only:
        filters.append("disabled=yes")
    if running_only:
        filters.append("running=yes")

    if filters:
        cmd += " where " + " ".join(filters)

    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No bonding interfaces found."

    return f"BONDING INTERFACES:\n\n{result}"


@mcp.tool(name="get_bonding", annotations=annotate(READ, "Get Bonding"))
async def mikrotik_get_bonding(ctx: Context, name: str) -> str:
    """Gets detailed information about a specific bonding interface."""
    await ctx.info(f"Getting bonding interface details: name={name}")

    cmd = f'/interface bonding print detail where name="{name}"'
    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "":
        return f"Bonding interface '{name}' not found."

    return f"BONDING DETAILS:\n\n{result}"


@mcp.tool(name="update_bonding", annotations=annotate(WRITE_IDEMPOTENT, "Update Bonding"))
async def mikrotik_update_bonding(
    ctx: Context,
    name: str,
    new_name: Optional[str] = None,
    mode: Optional[Literal[
        "802.3ad", "active-backup", "balance-alb", "balance-rr",
        "balance-tlb", "balance-xor", "broadcast", "none", "static"
    ]] = None,
    slaves: Optional[str] = None,
    comment: Optional[str] = None,
    disabled: Optional[bool] = None,
) -> str:
    """Updates an existing bonding interface's settings on the MikroTik device."""
    await ctx.info(f"Updating bonding interface: name={name}")

    updates = []
    if new_name:
        updates.append(f'name="{new_name}"')
    if mode:
        updates.append(f"mode={mode}")
    if slaves is not None:
        updates.append(f"slaves={slaves}")
    if comment is not None:
        updates.append(f'comment="{comment}"')
    if disabled is not None:
        updates.append(f'disabled={"yes" if disabled else "no"}')

    if not updates:
        return "No updates specified."

    cmd = f'/interface bonding set [find name="{name}"] ' + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to update bonding interface: {result}"

    lookup_name = new_name if new_name else name
    details_cmd = f'/interface bonding print detail where name="{lookup_name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    return f"Bonding interface updated successfully:\n\n{details}"


@mcp.tool(name="remove_bonding", annotations=annotate(DESTRUCTIVE, "Remove Bonding"))
async def mikrotik_remove_bonding(ctx: Context, name: str) -> str:
    """Removes a bonding interface from the MikroTik device."""
    await ctx.info(f"Removing bonding interface: name={name}")

    check_cmd = f'/interface bonding print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"Bonding interface '{name}' not found."

    cmd = f'/interface bonding remove [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove bonding interface: {result}"

    return f"Bonding interface '{name}' removed successfully."


@mcp.tool(name="enable_bonding", annotations=annotate(WRITE_IDEMPOTENT, "Enable Bonding"))
async def mikrotik_enable_bonding(ctx: Context, name: str) -> str:
    """Enables a bonding interface."""
    await ctx.info(f"Enabling bonding interface: name={name}")

    cmd = f'/interface bonding enable [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to enable bonding interface: {result}"

    return f"Bonding interface '{name}' enabled successfully."


@mcp.tool(name="disable_bonding", annotations=annotate(WRITE_IDEMPOTENT, "Disable Bonding"))
async def mikrotik_disable_bonding(ctx: Context, name: str) -> str:
    """Disables a bonding interface."""
    await ctx.info(f"Disabling bonding interface: name={name}")

    cmd = f'/interface bonding disable [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to disable bonding interface: {result}"

    return f"Bonding interface '{name}' disabled successfully."
