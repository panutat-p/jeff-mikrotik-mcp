from typing import Literal, Optional

from mcp.server.fastmcp import Context

from ..app import mcp, READ, WRITE, WRITE_IDEMPOTENT, DESTRUCTIVE, annotate
from ..connector import execute_mikrotik_command


@mcp.tool(name="get_snmp_settings", annotations=annotate(READ, "SNMP Settings"))
async def mikrotik_get_snmp_settings(ctx: Context) -> str:
    """Gets current SNMP service configuration."""
    await ctx.info("Getting SNMP settings")

    cmd = "/snmp print"
    result = await execute_mikrotik_command(cmd, ctx)

    if not result:
        return "Unable to retrieve SNMP settings."

    return f"SNMP SETTINGS:\n\n{result}"


@mcp.tool(name="set_snmp_settings", annotations=annotate(WRITE, "Set SNMP Settings"))
async def mikrotik_set_snmp_settings(
    ctx: Context,
    enabled: Optional[bool] = None,
    contact: Optional[str] = None,
    location: Optional[str] = None,
    trap_version: Optional[Literal[1, 2, 3]] = None,
    trap_community: Optional[str] = None,
    engine_id: Optional[str] = None,
) -> str:
    """Sets SNMP service configuration."""
    await ctx.info("Setting SNMP configuration")

    updates = []
    if enabled is not None:
        updates.append(f'enabled={"yes" if enabled else "no"}')
    if contact is not None:
        updates.append(f'contact="{contact}"')
    if location is not None:
        updates.append(f'location="{location}"')
    if trap_version is not None:
        updates.append(f"trap-version={trap_version}")
    if trap_community is not None:
        updates.append(f'trap-community="{trap_community}"')
    if engine_id is not None:
        updates.append(f'engine-id="{engine_id}"')

    if not updates:
        return "No updates specified."

    cmd = "/snmp set " + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if result.strip() and "failure:" in result.lower():
        return f"Failed to update SNMP settings: {result}"

    details = await execute_mikrotik_command("/snmp print", ctx)
    return f"SNMP settings updated successfully:\n\n{details}"


@mcp.tool(name="list_snmp_communities", annotations=annotate(READ, "List SNMP Communities"))
async def mikrotik_list_snmp_communities(
    ctx: Context,
    name_filter: Optional[str] = None,
) -> str:
    """Lists SNMP communities."""
    await ctx.info(f"Listing SNMP communities: name_filter={name_filter}")

    cmd = "/snmp community print"
    if name_filter:
        cmd += f' where name~"{name_filter}"'

    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No SNMP communities found matching the criteria."

    return f"SNMP COMMUNITIES:\n\n{result}"


@mcp.tool(name="get_snmp_community", annotations=annotate(READ, "Get SNMP Community"))
async def mikrotik_get_snmp_community(ctx: Context, community_id: str) -> str:
    """Gets details of a specific SNMP community by .id (e.g. *1)."""
    await ctx.info(f"Getting SNMP community: community_id={community_id}")

    cmd = f"/snmp community print detail where .id={community_id}"
    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "":
        return f"SNMP community with ID '{community_id}' not found."

    return f"SNMP COMMUNITY DETAILS:\n\n{result}"


@mcp.tool(name="add_snmp_community", annotations=annotate(WRITE, "Add SNMP Community"))
async def mikrotik_add_snmp_community(
    ctx: Context,
    name: str,
    addresses: Optional[str] = None,
    read_access: bool = True,
    write_access: bool = False,
    authentication_protocol: Optional[Literal["MD5", "SHA1"]] = None,
    encryption_protocol: Optional[Literal["DES", "AES"]] = None,
    security: Optional[Literal["none", "authorized", "private"]] = None,
    comment: Optional[str] = None,
    disabled: bool = False,
) -> str:
    """Adds an SNMP community."""
    await ctx.info(f"Adding SNMP community: name={name}")

    cmd = f'/snmp community add name="{name}"'
    cmd += f' read-access={"yes" if read_access else "no"}'
    cmd += f' write-access={"yes" if write_access else "no"}'

    if addresses:
        cmd += f" addresses={addresses}"
    if authentication_protocol:
        cmd += f" authentication-protocol={authentication_protocol}"
    if encryption_protocol:
        cmd += f" encryption-protocol={encryption_protocol}"
    if security:
        cmd += f" security={security}"
    if comment:
        cmd += f' comment="{comment}"'
    if disabled:
        cmd += " disabled=yes"

    result = await execute_mikrotik_command(cmd, ctx)

    if result.strip():
        if "*" in result or result.strip().isdigit():
            community_id = result.strip()
            details_cmd = f"/snmp community print detail where .id={community_id}"
            details = await execute_mikrotik_command(details_cmd, ctx)
            if details.strip():
                return f"SNMP community added successfully:\n\n{details}"
            return f"SNMP community added with ID: {result}"
        return f"Failed to add SNMP community: {result}"

    details_cmd = f'/snmp community print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)
    if details.strip():
        return f"SNMP community added successfully:\n\n{details}"
    return "SNMP community addition completed but unable to verify."


@mcp.tool(name="update_snmp_community", annotations=annotate(WRITE_IDEMPOTENT, "Update SNMP Community"))
async def mikrotik_update_snmp_community(
    ctx: Context,
    community_id: str,
    name: Optional[str] = None,
    addresses: Optional[str] = None,
    read_access: Optional[bool] = None,
    write_access: Optional[bool] = None,
    authentication_protocol: Optional[Literal["MD5", "SHA1"]] = None,
    encryption_protocol: Optional[Literal["DES", "AES"]] = None,
    security: Optional[Literal["none", "authorized", "private"]] = None,
    comment: Optional[str] = None,
    disabled: Optional[bool] = None,
) -> str:
    """Updates an SNMP community by .id (e.g. *1)."""
    await ctx.info(f"Updating SNMP community: community_id={community_id}")

    updates = []
    if name:
        updates.append(f'name="{name}"')
    if addresses is not None:
        if addresses == "":
            updates.append("!addresses")
        else:
            updates.append(f"addresses={addresses}")
    if read_access is not None:
        updates.append(f'read-access={"yes" if read_access else "no"}')
    if write_access is not None:
        updates.append(f'write-access={"yes" if write_access else "no"}')
    if authentication_protocol is not None:
        updates.append(f"authentication-protocol={authentication_protocol}")
    if encryption_protocol is not None:
        updates.append(f"encryption-protocol={encryption_protocol}")
    if security is not None:
        updates.append(f"security={security}")
    if comment is not None:
        updates.append(f'comment="{comment}"')
    if disabled is not None:
        updates.append(f'disabled={"yes" if disabled else "no"}')

    if not updates:
        return "No updates specified."

    cmd = f"/snmp community set {community_id} " + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to update SNMP community: {result}"

    details_cmd = f"/snmp community print detail where .id={community_id}"
    details = await execute_mikrotik_command(details_cmd, ctx)
    return f"SNMP community updated successfully:\n\n{details}"


@mcp.tool(name="remove_snmp_community", annotations=annotate(DESTRUCTIVE, "Remove SNMP Community"))
async def mikrotik_remove_snmp_community(ctx: Context, community_id: str) -> str:
    """Removes an SNMP community by .id (e.g. *1)."""
    await ctx.info(f"Removing SNMP community: community_id={community_id}")

    check_cmd = f"/snmp community print count-only where .id={community_id}"
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"SNMP community with ID '{community_id}' not found."

    cmd = f"/snmp community remove {community_id}"
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove SNMP community: {result}"

    return f"SNMP community with ID '{community_id}' removed successfully."


@mcp.tool(name="list_graphing_interfaces", annotations=annotate(READ, "List Graphing Interfaces"))
async def mikrotik_list_graphing_interfaces(
    ctx: Context,
    interface_filter: Optional[str] = None,
) -> str:
    """Lists interfaces configured for RouterOS graphing."""
    await ctx.info(f"Listing graphing interfaces: interface_filter={interface_filter}")

    cmd = "/tool graphing interface print"
    if interface_filter:
        cmd += f' where interface~"{interface_filter}"'

    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No graphing interfaces found matching the criteria."

    return f"GRAPHING INTERFACES:\n\n{result}"


@mcp.tool(name="set_graphing_interface", annotations=annotate(WRITE, "Set Graphing Interface"))
async def mikrotik_set_graphing_interface(
    ctx: Context,
    interface: str,
    store_on_disk: Optional[bool] = None,
    allow_address: Optional[str] = None,
    comment: Optional[str] = None,
    disabled: Optional[bool] = None,
) -> str:
    """Enables or updates graphing for an interface."""
    await ctx.info(f"Setting graphing interface: interface={interface}")

    updates = []
    if store_on_disk is not None:
        updates.append(f'store-on-disk={"yes" if store_on_disk else "no"}')
    if allow_address is not None:
        if allow_address == "":
            updates.append("!allow-address")
        else:
            updates.append(f"allow-address={allow_address}")
    if comment is not None:
        updates.append(f'comment="{comment}"')
    if disabled is not None:
        updates.append(f'disabled={"yes" if disabled else "no"}')

    if not updates:
        return "No updates specified."

    cmd = f"/tool graphing interface set {interface} " + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if result.strip() and "failure:" in result.lower():
        return f"Failed to update graphing interface: {result}"

    details_cmd = f'/tool graphing interface print detail where interface="{interface}"'
    details = await execute_mikrotik_command(details_cmd, ctx)
    if details.strip():
        return f"Graphing interface updated successfully:\n\n{details}"
    return f"Graphing settings for interface '{interface}' updated successfully."
