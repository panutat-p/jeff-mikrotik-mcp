from typing import Optional

import re

from mcp.server.fastmcp import Context

from ..app import mcp, READ, WRITE, WRITE_IDEMPOTENT, DESTRUCTIVE, annotate
from ..connector import execute_mikrotik_command


def _mask_passwords(text: str) -> str:
    return re.sub(r'password="[^"]*"', 'password="***"', text)


# ---------------------------------------------------------------------------
# Hotspot Server Management
# ---------------------------------------------------------------------------

@mcp.tool(name="create_hotspot_server", annotations=annotate(WRITE, "Create Hotspot Server"))
async def mikrotik_create_hotspot_server(
    ctx: Context,
    name: str,
    interface: str,
    address_pool: str,
    profile: str = "default",
    idle_timeout: Optional[str] = None,
    keepalive_timeout: Optional[str] = None,
    comment: Optional[str] = None,
    disabled: bool = False,
) -> str:
    """Creates a Hotspot server on the MikroTik device.

    Notes:
        idle_timeout: duration e.g. "5m", "1h"
        keepalive_timeout: duration e.g. "2m", "none"
    """
    await ctx.info(f"Creating Hotspot server: name={name}, interface={interface}")

    cmd = (
        f'/ip hotspot add name="{name}" interface="{interface}"'
        f' address-pool="{address_pool}" profile="{profile}"'
    )

    if idle_timeout:
        cmd += f" idle-timeout={idle_timeout}"
    if keepalive_timeout:
        cmd += f" keepalive-timeout={keepalive_timeout}"
    if comment:
        cmd += f' comment="{comment}"'
    if disabled:
        cmd += " disabled=yes"

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to create Hotspot server: {result}"

    details_cmd = f'/ip hotspot print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Hotspot server created successfully:\n\n{details}"
    return "Hotspot server created successfully."


@mcp.tool(name="list_hotspot_servers", annotations=annotate(READ, "List Hotspot Servers"))
async def mikrotik_list_hotspot_servers(
    ctx: Context,
    name_filter: Optional[str] = None,
    interface_filter: Optional[str] = None,
    disabled_only: bool = False,
) -> str:
    """Lists Hotspot servers on the MikroTik device."""
    await ctx.info("Listing Hotspot servers")

    cmd = "/ip hotspot print"

    filters = []
    if name_filter:
        filters.append(f'name~"{name_filter}"')
    if interface_filter:
        filters.append(f'interface="{interface_filter}"')
    if disabled_only:
        filters.append("disabled=yes")

    if filters:
        cmd += " where " + " ".join(filters)

    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No Hotspot servers found."

    return f"HOTSPOT SERVERS:\n\n{result}"


@mcp.tool(name="get_hotspot_server", annotations=annotate(READ, "Get Hotspot Server"))
async def mikrotik_get_hotspot_server(ctx: Context, name: str) -> str:
    """Gets detailed information about a specific Hotspot server."""
    await ctx.info(f"Getting Hotspot server details: name={name}")

    cmd = f'/ip hotspot print detail where name="{name}"'
    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "":
        return f"Hotspot server '{name}' not found."

    return f"HOTSPOT SERVER DETAILS:\n\n{result}"


@mcp.tool(name="update_hotspot_server", annotations=annotate(WRITE_IDEMPOTENT, "Update Hotspot Server"))
async def mikrotik_update_hotspot_server(
    ctx: Context,
    name: str,
    new_name: Optional[str] = None,
    interface: Optional[str] = None,
    address_pool: Optional[str] = None,
    profile: Optional[str] = None,
    idle_timeout: Optional[str] = None,
    keepalive_timeout: Optional[str] = None,
    comment: Optional[str] = None,
    disabled: Optional[bool] = None,
) -> str:
    """Updates an existing Hotspot server's settings on the MikroTik device."""
    await ctx.info(f"Updating Hotspot server: name={name}")

    updates = []
    if new_name:
        updates.append(f'name="{new_name}"')
    if interface:
        updates.append(f'interface="{interface}"')
    if address_pool:
        updates.append(f'address-pool="{address_pool}"')
    if profile:
        updates.append(f'profile="{profile}"')
    if idle_timeout is not None:
        updates.append(f"idle-timeout={idle_timeout}")
    if keepalive_timeout is not None:
        updates.append(f"keepalive-timeout={keepalive_timeout}")
    if comment is not None:
        updates.append(f'comment="{comment}"')
    if disabled is not None:
        updates.append(f'disabled={"yes" if disabled else "no"}')

    if not updates:
        return "No updates specified."

    cmd = f'/ip hotspot set [find name="{name}"] ' + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to update Hotspot server: {result}"

    lookup_name = new_name if new_name else name
    details_cmd = f'/ip hotspot print detail where name="{lookup_name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    return f"Hotspot server updated successfully:\n\n{details}"


@mcp.tool(name="remove_hotspot_server", annotations=annotate(DESTRUCTIVE, "Remove Hotspot Server"))
async def mikrotik_remove_hotspot_server(ctx: Context, name: str) -> str:
    """Removes a Hotspot server from the MikroTik device."""
    await ctx.info(f"Removing Hotspot server: name={name}")

    check_cmd = f'/ip hotspot print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"Hotspot server '{name}' not found."

    cmd = f'/ip hotspot remove [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove Hotspot server: {result}"

    return f"Hotspot server '{name}' removed successfully."


@mcp.tool(name="enable_hotspot_server", annotations=annotate(WRITE_IDEMPOTENT, "Enable Hotspot Server"))
async def mikrotik_enable_hotspot_server(ctx: Context, name: str) -> str:
    """Enables a Hotspot server."""
    await ctx.info(f"Enabling Hotspot server: name={name}")

    cmd = f'/ip hotspot enable [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to enable Hotspot server: {result}"

    return f"Hotspot server '{name}' enabled successfully."


@mcp.tool(name="disable_hotspot_server", annotations=annotate(WRITE_IDEMPOTENT, "Disable Hotspot Server"))
async def mikrotik_disable_hotspot_server(ctx: Context, name: str) -> str:
    """Disables a Hotspot server."""
    await ctx.info(f"Disabling Hotspot server: name={name}")

    cmd = f'/ip hotspot disable [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to disable Hotspot server: {result}"

    return f"Hotspot server '{name}' disabled successfully."


# ---------------------------------------------------------------------------
# Hotspot Profile Management
# ---------------------------------------------------------------------------

@mcp.tool(name="create_hotspot_profile", annotations=annotate(WRITE, "Create Hotspot Profile"))
async def mikrotik_create_hotspot_profile(
    ctx: Context,
    name: str,
    hotspot_address: Optional[str] = None,
    dns_name: Optional[str] = None,
    html_directory: Optional[str] = None,
    rate_limit: Optional[str] = None,
    comment: Optional[str] = None,
) -> str:
    """Creates a Hotspot profile on the MikroTik device.

    Notes:
        hotspot_address: gateway IP for hotspot clients e.g. "192.168.88.1"
        dns_name: DNS name for hotspot portal e.g. "hotspot.local"
        rate_limit: upload/download limit e.g. "5M/10M"
    """
    await ctx.info(f"Creating Hotspot profile: name={name}")

    cmd = f'/ip hotspot profile add name="{name}"'

    if hotspot_address:
        cmd += f" hotspot-address={hotspot_address}"
    if dns_name:
        cmd += f' dns-name="{dns_name}"'
    if html_directory:
        cmd += f' html-directory="{html_directory}"'
    if rate_limit:
        cmd += f' rate-limit="{rate_limit}"'
    if comment:
        cmd += f' comment="{comment}"'

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to create Hotspot profile: {result}"

    details_cmd = f'/ip hotspot profile print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Hotspot profile created successfully:\n\n{details}"
    return "Hotspot profile created successfully."


@mcp.tool(name="list_hotspot_profiles", annotations=annotate(READ, "List Hotspot Profiles"))
async def mikrotik_list_hotspot_profiles(
    ctx: Context,
    name_filter: Optional[str] = None,
) -> str:
    """Lists Hotspot profiles on the MikroTik device."""
    await ctx.info("Listing Hotspot profiles")

    cmd = "/ip hotspot profile print"

    if name_filter:
        cmd += f' where name~"{name_filter}"'

    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No Hotspot profiles found."

    return f"HOTSPOT PROFILES:\n\n{result}"


@mcp.tool(name="get_hotspot_profile", annotations=annotate(READ, "Get Hotspot Profile"))
async def mikrotik_get_hotspot_profile(ctx: Context, name: str) -> str:
    """Gets detailed information about a specific Hotspot profile."""
    await ctx.info(f"Getting Hotspot profile details: name={name}")

    cmd = f'/ip hotspot profile print detail where name="{name}"'
    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "":
        return f"Hotspot profile '{name}' not found."

    return f"HOTSPOT PROFILE DETAILS:\n\n{result}"


@mcp.tool(name="update_hotspot_profile", annotations=annotate(WRITE_IDEMPOTENT, "Update Hotspot Profile"))
async def mikrotik_update_hotspot_profile(
    ctx: Context,
    name: str,
    new_name: Optional[str] = None,
    hotspot_address: Optional[str] = None,
    dns_name: Optional[str] = None,
    html_directory: Optional[str] = None,
    rate_limit: Optional[str] = None,
    comment: Optional[str] = None,
) -> str:
    """Updates an existing Hotspot profile's settings on the MikroTik device."""
    await ctx.info(f"Updating Hotspot profile: name={name}")

    updates = []
    if new_name:
        updates.append(f'name="{new_name}"')
    if hotspot_address is not None:
        updates.append(f"hotspot-address={hotspot_address}")
    if dns_name is not None:
        updates.append(f'dns-name="{dns_name}"')
    if html_directory is not None:
        updates.append(f'html-directory="{html_directory}"')
    if rate_limit is not None:
        updates.append(f'rate-limit="{rate_limit}"')
    if comment is not None:
        updates.append(f'comment="{comment}"')

    if not updates:
        return "No updates specified."

    cmd = f'/ip hotspot profile set [find name="{name}"] ' + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to update Hotspot profile: {result}"

    lookup_name = new_name if new_name else name
    details_cmd = f'/ip hotspot profile print detail where name="{lookup_name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    return f"Hotspot profile updated successfully:\n\n{details}"


@mcp.tool(name="remove_hotspot_profile", annotations=annotate(DESTRUCTIVE, "Remove Hotspot Profile"))
async def mikrotik_remove_hotspot_profile(ctx: Context, name: str) -> str:
    """Removes a Hotspot profile from the MikroTik device."""
    await ctx.info(f"Removing Hotspot profile: name={name}")

    check_cmd = f'/ip hotspot profile print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"Hotspot profile '{name}' not found."

    cmd = f'/ip hotspot profile remove [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove Hotspot profile: {result}"

    return f"Hotspot profile '{name}' removed successfully."


# ---------------------------------------------------------------------------
# Hotspot User Management
# ---------------------------------------------------------------------------

@mcp.tool(name="add_hotspot_user", annotations=annotate(WRITE, "Add Hotspot User"))
async def mikrotik_add_hotspot_user(
    ctx: Context,
    name: str,
    password: str,
    profile: Optional[str] = None,
    server: Optional[str] = None,
    limit_uptime: Optional[str] = None,
    limit_bytes_total: Optional[str] = None,
    comment: Optional[str] = None,
    disabled: bool = False,
) -> str:
    """Adds a Hotspot user on the MikroTik device.

    Notes:
        limit_uptime: duration e.g. "1d", "2h30m"
        limit_bytes_total: byte limit e.g. "1G", "500M"
    """
    await ctx.info(f"Adding Hotspot user: name={name}")

    cmd = f'/ip hotspot user add name="{name}" password="{password}"'

    if profile:
        cmd += f' profile="{profile}"'
    if server:
        cmd += f' server="{server}"'
    if limit_uptime:
        cmd += f" limit-uptime={limit_uptime}"
    if limit_bytes_total:
        cmd += f" limit-bytes-total={limit_bytes_total}"
    if comment:
        cmd += f' comment="{comment}"'
    if disabled:
        cmd += " disabled=yes"

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to add Hotspot user: {result}"

    details_cmd = f'/ip hotspot user print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Hotspot user added successfully:\n\n{_mask_passwords(details)}"
    return "Hotspot user added successfully."


@mcp.tool(name="list_hotspot_users", annotations=annotate(READ, "List Hotspot Users"))
async def mikrotik_list_hotspot_users(
    ctx: Context,
    name_filter: Optional[str] = None,
    profile_filter: Optional[str] = None,
    server_filter: Optional[str] = None,
    disabled_only: bool = False,
) -> str:
    """Lists Hotspot users on the MikroTik device."""
    await ctx.info("Listing Hotspot users")

    cmd = "/ip hotspot user print"

    filters = []
    if name_filter:
        filters.append(f'name~"{name_filter}"')
    if profile_filter:
        filters.append(f'profile="{profile_filter}"')
    if server_filter:
        filters.append(f'server="{server_filter}"')
    if disabled_only:
        filters.append("disabled=yes")

    if filters:
        cmd += " where " + " ".join(filters)

    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No Hotspot users found."

    return f"HOTSPOT USERS:\n\n{_mask_passwords(result)}"


@mcp.tool(name="get_hotspot_user", annotations=annotate(READ, "Get Hotspot User"))
async def mikrotik_get_hotspot_user(ctx: Context, name: str) -> str:
    """Gets detailed information about a specific Hotspot user."""
    await ctx.info(f"Getting Hotspot user details: name={name}")

    cmd = f'/ip hotspot user print detail where name="{name}"'
    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "":
        return f"Hotspot user '{name}' not found."

    return f"HOTSPOT USER DETAILS:\n\n{_mask_passwords(result)}"


@mcp.tool(name="update_hotspot_user", annotations=annotate(WRITE_IDEMPOTENT, "Update Hotspot User"))
async def mikrotik_update_hotspot_user(
    ctx: Context,
    name: str,
    new_name: Optional[str] = None,
    password: Optional[str] = None,
    profile: Optional[str] = None,
    server: Optional[str] = None,
    limit_uptime: Optional[str] = None,
    limit_bytes_total: Optional[str] = None,
    comment: Optional[str] = None,
    disabled: Optional[bool] = None,
) -> str:
    """Updates an existing Hotspot user's settings on the MikroTik device."""
    await ctx.info(f"Updating Hotspot user: name={name}")

    updates = []
    if new_name:
        updates.append(f'name="{new_name}"')
    if password:
        updates.append(f'password="{password}"')
    if profile is not None:
        updates.append(f'profile="{profile}"')
    if server is not None:
        updates.append(f'server="{server}"')
    if limit_uptime is not None:
        updates.append(f"limit-uptime={limit_uptime}")
    if limit_bytes_total is not None:
        updates.append(f"limit-bytes-total={limit_bytes_total}")
    if comment is not None:
        updates.append(f'comment="{comment}"')
    if disabled is not None:
        updates.append(f'disabled={"yes" if disabled else "no"}')

    if not updates:
        return "No updates specified."

    cmd = f'/ip hotspot user set [find name="{name}"] ' + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to update Hotspot user: {result}"

    lookup_name = new_name if new_name else name
    details_cmd = f'/ip hotspot user print detail where name="{lookup_name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    return f"Hotspot user updated successfully:\n\n{_mask_passwords(details)}"


@mcp.tool(name="remove_hotspot_user", annotations=annotate(DESTRUCTIVE, "Remove Hotspot User"))
async def mikrotik_remove_hotspot_user(ctx: Context, name: str) -> str:
    """Removes a Hotspot user from the MikroTik device."""
    await ctx.info(f"Removing Hotspot user: name={name}")

    check_cmd = f'/ip hotspot user print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"Hotspot user '{name}' not found."

    cmd = f'/ip hotspot user remove [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove Hotspot user: {result}"

    return f"Hotspot user '{name}' removed successfully."


# ---------------------------------------------------------------------------
# Hotspot Active Sessions
# ---------------------------------------------------------------------------

@mcp.tool(name="list_hotspot_active", annotations=annotate(READ, "List Hotspot Active"))
async def mikrotik_list_hotspot_active(
    ctx: Context,
    server_filter: Optional[str] = None,
    user_filter: Optional[str] = None,
    address_filter: Optional[str] = None,
) -> str:
    """Lists active Hotspot sessions on the MikroTik device."""
    await ctx.info("Listing active Hotspot sessions")

    cmd = "/ip hotspot active print"

    filters = []
    if server_filter:
        filters.append(f'server="{server_filter}"')
    if user_filter:
        filters.append(f'user~"{user_filter}"')
    if address_filter:
        filters.append(f'address="{address_filter}"')

    if filters:
        cmd += " where " + " ".join(filters)

    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No active Hotspot sessions found."

    return f"HOTSPOT ACTIVE SESSIONS:\n\n{result}"


@mcp.tool(name="remove_hotspot_active", annotations=annotate(DESTRUCTIVE, "Remove Hotspot Active"))
async def mikrotik_remove_hotspot_active(ctx: Context, session_id: str) -> str:
    """Disconnects an active Hotspot session by ID.

    Notes:
        session_id: "*N" or "N" from list output e.g. "*2"
    """
    await ctx.info(f"Removing active Hotspot session: session_id={session_id}")

    check_cmd = f"/ip hotspot active print count-only where .id={session_id}"
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"Active Hotspot session with ID '{session_id}' not found."

    cmd = f"/ip hotspot active remove {session_id}"
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove active Hotspot session: {result}"

    return f"Active Hotspot session '{session_id}' disconnected successfully."
