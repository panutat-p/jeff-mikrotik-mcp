from typing import Literal, Optional

import re

from mcp.server.fastmcp import Context

from ..app import mcp, READ, WRITE, WRITE_IDEMPOTENT, DESTRUCTIVE, annotate
from ..connector import execute_mikrotik_command

PPPInterfaceType = Literal["pppoe-server", "pppoe-client"]


def _mask_passwords(text: str) -> str:
    return re.sub(r'password="[^"]*"', 'password="***"', text)


def _ppp_interface_path(interface_type: PPPInterfaceType) -> str:
    return f"/interface {interface_type}"


# ---------------------------------------------------------------------------
# PPP Profile Management
# ---------------------------------------------------------------------------

@mcp.tool(name="create_ppp_profile", annotations=annotate(WRITE, "Create PPP Profile"))
async def mikrotik_create_ppp_profile(
    ctx: Context,
    name: str,
    local_address: Optional[str] = None,
    remote_address: Optional[str] = None,
    bridge: Optional[str] = None,
    rate_limit: Optional[str] = None,
    comment: Optional[str] = None,
) -> str:
    """Creates a PPP profile on the MikroTik device.

    Notes:
        local_address: pool name or IP e.g. "ppp-pool" or "10.0.0.1"
        remote_address: pool name or IP range e.g. "ppp-pool"
        rate_limit: upload/download limit e.g. "10M/20M"
    """
    await ctx.info(f"Creating PPP profile: name={name}")

    cmd = f'/ppp profile add name="{name}"'

    if local_address:
        cmd += f' local-address="{local_address}"'
    if remote_address:
        cmd += f' remote-address="{remote_address}"'
    if bridge:
        cmd += f' bridge="{bridge}"'
    if rate_limit:
        cmd += f' rate-limit="{rate_limit}"'
    if comment:
        cmd += f' comment="{comment}"'

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to create PPP profile: {result}"

    details_cmd = f'/ppp profile print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"PPP profile created successfully:\n\n{details}"
    return "PPP profile created successfully."


@mcp.tool(name="query_ppp_profiles", annotations=annotate(READ, "Query PPP Profiles"))
async def mikrotik_query_ppp_profiles(
    ctx: Context,
    name: Optional[str] = None,
    name_filter: Optional[str] = None,
) -> str:
    """Lists PPP profiles or returns detail for a specific one by name."""
    if name:
        await ctx.info(f"Getting PPP profile details: name={name}")
        cmd = f'/ppp profile print detail where name="{name}"'
        result = await execute_mikrotik_command(cmd, ctx)
        if not result or result.strip() == "":
            return f"PPP profile '{name}' not found."
        return f"PPP PROFILE DETAILS:\n\n{result}"

    await ctx.info("Listing PPP profiles")
    cmd = "/ppp profile print"
    if name_filter:
        cmd += f' where name~"{name_filter}"'
    result = await execute_mikrotik_command(cmd, ctx)
    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No PPP profiles found."
    return f"PPP PROFILES:\n\n{result}"


@mcp.tool(name="update_ppp_profile", annotations=annotate(WRITE_IDEMPOTENT, "Update PPP Profile"))
async def mikrotik_update_ppp_profile(
    ctx: Context,
    name: str,
    new_name: Optional[str] = None,
    local_address: Optional[str] = None,
    remote_address: Optional[str] = None,
    bridge: Optional[str] = None,
    rate_limit: Optional[str] = None,
    comment: Optional[str] = None,
) -> str:
    """Updates an existing PPP profile's settings on the MikroTik device."""
    await ctx.info(f"Updating PPP profile: name={name}")

    updates = []
    if new_name:
        updates.append(f'name="{new_name}"')
    if local_address is not None:
        updates.append(f'local-address="{local_address}"')
    if remote_address is not None:
        updates.append(f'remote-address="{remote_address}"')
    if bridge is not None:
        updates.append(f'bridge="{bridge}"')
    if rate_limit is not None:
        updates.append(f'rate-limit="{rate_limit}"')
    if comment is not None:
        updates.append(f'comment="{comment}"')

    if not updates:
        return "No updates specified."

    cmd = f'/ppp profile set [find name="{name}"] ' + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to update PPP profile: {result}"

    lookup_name = new_name if new_name else name
    details_cmd = f'/ppp profile print detail where name="{lookup_name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    return f"PPP profile updated successfully:\n\n{details}"


@mcp.tool(name="remove_ppp_profile", annotations=annotate(DESTRUCTIVE, "Remove PPP Profile"))
async def mikrotik_remove_ppp_profile(ctx: Context, name: str) -> str:
    """Removes a PPP profile from the MikroTik device."""
    await ctx.info(f"Removing PPP profile: name={name}")

    check_cmd = f'/ppp profile print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"PPP profile '{name}' not found."

    cmd = f'/ppp profile remove [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove PPP profile: {result}"

    return f"PPP profile '{name}' removed successfully."


# ---------------------------------------------------------------------------
# PPP Secret Management
# ---------------------------------------------------------------------------

@mcp.tool(name="add_ppp_secret", annotations=annotate(WRITE, "Add PPP Secret"))
async def mikrotik_add_ppp_secret(
    ctx: Context,
    name: str,
    password: str,
    service: str = "any",
    profile: Optional[str] = None,
    remote_address: Optional[str] = None,
    comment: Optional[str] = None,
    disabled: bool = False,
) -> str:
    """Adds a PPP secret (user credential) on the MikroTik device.

    Notes:
        service: "any", "pppoe", "l2tp", "ovpn", "pptp", "sstp", etc.
    """
    await ctx.info(f"Adding PPP secret: name={name}")

    cmd = f'/ppp secret add name="{name}" password="{password}" service={service}'

    if profile:
        cmd += f' profile="{profile}"'
    if remote_address:
        cmd += f' remote-address="{remote_address}"'
    if comment:
        cmd += f' comment="{comment}"'
    if disabled:
        cmd += " disabled=yes"

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to add PPP secret: {result}"

    details_cmd = f'/ppp secret print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"PPP secret added successfully:\n\n{_mask_passwords(details)}"
    return "PPP secret added successfully."


@mcp.tool(name="query_ppp_secrets", annotations=annotate(READ, "Query PPP Secrets"))
async def mikrotik_query_ppp_secrets(
    ctx: Context,
    name: Optional[str] = None,
    name_filter: Optional[str] = None,
    service_filter: Optional[str] = None,
    profile_filter: Optional[str] = None,
    disabled_only: bool = False,
) -> str:
    """Lists PPP secrets or returns detail for a specific one by name."""
    if name:
        await ctx.info(f"Getting PPP secret details: name={name}")
        cmd = f'/ppp secret print detail where name="{name}"'
        result = await execute_mikrotik_command(cmd, ctx)
        if not result or result.strip() == "":
            return f"PPP secret '{name}' not found."
        return f"PPP SECRET DETAILS:\n\n{_mask_passwords(result)}"

    await ctx.info("Listing PPP secrets")
    cmd = "/ppp secret print"
    filters = []
    if name_filter:
        filters.append(f'name~"{name_filter}"')
    if service_filter:
        filters.append(f'service="{service_filter}"')
    if profile_filter:
        filters.append(f'profile="{profile_filter}"')
    if disabled_only:
        filters.append("disabled=yes")
    if filters:
        cmd += " where " + " ".join(filters)
    result = await execute_mikrotik_command(cmd, ctx)
    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No PPP secrets found."
    return f"PPP SECRETS:\n\n{_mask_passwords(result)}"


@mcp.tool(name="update_ppp_secret", annotations=annotate(WRITE_IDEMPOTENT, "Update PPP Secret"))
async def mikrotik_update_ppp_secret(
    ctx: Context,
    name: str,
    new_name: Optional[str] = None,
    password: Optional[str] = None,
    service: Optional[str] = None,
    profile: Optional[str] = None,
    remote_address: Optional[str] = None,
    comment: Optional[str] = None,
    disabled: Optional[bool] = None,
) -> str:
    """Updates an existing PPP secret's settings on the MikroTik device."""
    await ctx.info(f"Updating PPP secret: name={name}")

    updates = []
    if new_name:
        updates.append(f'name="{new_name}"')
    if password:
        updates.append(f'password="{password}"')
    if service:
        updates.append(f"service={service}")
    if profile is not None:
        updates.append(f'profile="{profile}"')
    if remote_address is not None:
        updates.append(f'remote-address="{remote_address}"')
    if comment is not None:
        updates.append(f'comment="{comment}"')
    if disabled is not None:
        updates.append(f'disabled={"yes" if disabled else "no"}')

    if not updates:
        return "No updates specified."

    cmd = f'/ppp secret set [find name="{name}"] ' + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to update PPP secret: {result}"

    lookup_name = new_name if new_name else name
    details_cmd = f'/ppp secret print detail where name="{lookup_name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    return f"PPP secret updated successfully:\n\n{_mask_passwords(details)}"


@mcp.tool(name="remove_ppp_secret", annotations=annotate(DESTRUCTIVE, "Remove PPP Secret"))
async def mikrotik_remove_ppp_secret(ctx: Context, name: str) -> str:
    """Removes a PPP secret from the MikroTik device."""
    await ctx.info(f"Removing PPP secret: name={name}")

    check_cmd = f'/ppp secret print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"PPP secret '{name}' not found."

    cmd = f'/ppp secret remove [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove PPP secret: {result}"

    return f"PPP secret '{name}' removed successfully."


# ---------------------------------------------------------------------------
# PPP Interface Management (PPPoE Server / Client)
# ---------------------------------------------------------------------------

@mcp.tool(name="add_ppp_interface", annotations=annotate(WRITE, "Add PPP Interface"))
async def mikrotik_add_ppp_interface(
    ctx: Context,
    interface_type: PPPInterfaceType,
    name: str,
    interface: str,
    service_name: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    default_profile: Optional[str] = None,
    comment: Optional[str] = None,
    disabled: bool = False,
) -> str:
    """Adds a PPPoE server or client interface on the MikroTik device.

    Notes:
        interface_type: "pppoe-server" or "pppoe-client"
        interface: parent interface e.g. "ether1"
        service_name: required for pppoe-server e.g. "internet"
        user/password: required for pppoe-client
    """
    await ctx.info(f"Adding PPP interface: type={interface_type}, name={name}")

    path = _ppp_interface_path(interface_type)
    cmd = f'{path} add name="{name}" interface="{interface}"'

    if interface_type == "pppoe-server":
        if service_name:
            cmd += f' service-name="{service_name}"'
        if default_profile:
            cmd += f' default-profile="{default_profile}"'
    else:
        if user:
            cmd += f' user="{user}"'
        if password:
            cmd += f' password="{password}"'

    if comment:
        cmd += f' comment="{comment}"'
    if disabled:
        cmd += " disabled=yes"

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to add PPP interface: {result}"

    details_cmd = f'{path} print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"PPP interface added successfully:\n\n{_mask_passwords(details)}"
    return "PPP interface added successfully."


@mcp.tool(name="query_ppp_interfaces", annotations=annotate(READ, "Query PPP Interfaces"))
async def mikrotik_query_ppp_interfaces(
    ctx: Context,
    name: Optional[str] = None,
    interface_type: Optional[PPPInterfaceType] = None,
    name_filter: Optional[str] = None,
    disabled_only: bool = False,
    running_only: bool = False,
) -> str:
    """Lists PPPoE interfaces or returns detail for a specific one by name and type."""
    if name:
        if not interface_type:
            return "interface_type is required when querying a specific PPP interface by name."
        await ctx.info(f"Getting PPP interface details: type={interface_type}, name={name}")
        path = _ppp_interface_path(interface_type)
        cmd = f'{path} print detail where name="{name}"'
        result = await execute_mikrotik_command(cmd, ctx)
        if not result or result.strip() == "":
            return f"PPP interface '{name}' not found."
        return f"PPP INTERFACE DETAILS:\n\n{_mask_passwords(result)}"

    await ctx.info("Listing PPP interfaces")
    types_to_list: list[PPPInterfaceType]
    if interface_type:
        types_to_list = [interface_type]
    else:
        types_to_list = ["pppoe-server", "pppoe-client"]
    sections = []
    for ppp_type in types_to_list:
        path = _ppp_interface_path(ppp_type)
        cmd = f"{path} print"
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
        if result and result.strip() and result.strip() != "no such item":
            sections.append(f"{ppp_type.upper()}:\n\n{_mask_passwords(result)}")
    if not sections:
        return "No PPP interfaces found."
    return "PPP INTERFACES:\n\n" + "\n\n".join(sections)


@mcp.tool(name="remove_ppp_interface", annotations=annotate(DESTRUCTIVE, "Remove PPP Interface"))
async def mikrotik_remove_ppp_interface(
    ctx: Context,
    interface_type: PPPInterfaceType,
    name: str,
) -> str:
    """Removes a PPPoE server or client interface from the MikroTik device."""
    await ctx.info(f"Removing PPP interface: type={interface_type}, name={name}")

    path = _ppp_interface_path(interface_type)

    check_cmd = f'{path} print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"PPP interface '{name}' not found."

    cmd = f'{path} remove [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove PPP interface: {result}"

    return f"PPP interface '{name}' removed successfully."


@mcp.tool(name="enable_ppp_interface", annotations=annotate(WRITE_IDEMPOTENT, "Enable PPP Interface"))
async def mikrotik_enable_ppp_interface(
    ctx: Context,
    interface_type: PPPInterfaceType,
    name: str,
) -> str:
    """Enables a PPPoE server or client interface."""
    await ctx.info(f"Enabling PPP interface: type={interface_type}, name={name}")

    path = _ppp_interface_path(interface_type)
    cmd = f'{path} enable [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to enable PPP interface: {result}"

    return f"PPP interface '{name}' enabled successfully."


@mcp.tool(name="disable_ppp_interface", annotations=annotate(WRITE_IDEMPOTENT, "Disable PPP Interface"))
async def mikrotik_disable_ppp_interface(
    ctx: Context,
    interface_type: PPPInterfaceType,
    name: str,
) -> str:
    """Disables a PPPoE server or client interface."""
    await ctx.info(f"Disabling PPP interface: type={interface_type}, name={name}")

    path = _ppp_interface_path(interface_type)
    cmd = f'{path} disable [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to disable PPP interface: {result}"

    return f"PPP interface '{name}' disabled successfully."


# ---------------------------------------------------------------------------
# PPP Active Sessions
# ---------------------------------------------------------------------------

@mcp.tool(name="list_ppp_active", annotations=annotate(READ, "List PPP Active"))
async def mikrotik_list_ppp_active(
    ctx: Context,
    name_filter: Optional[str] = None,
    service_filter: Optional[str] = None,
    address_filter: Optional[str] = None,
) -> str:
    """Lists active PPP sessions on the MikroTik device."""
    await ctx.info("Listing active PPP sessions")

    cmd = "/ppp active print"

    filters = []
    if name_filter:
        filters.append(f'name~"{name_filter}"')
    if service_filter:
        filters.append(f'service="{service_filter}"')
    if address_filter:
        filters.append(f'address="{address_filter}"')

    if filters:
        cmd += " where " + " ".join(filters)

    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No active PPP sessions found."

    return f"PPP ACTIVE SESSIONS:\n\n{result}"


@mcp.tool(name="disconnect_ppp_active", annotations=annotate(DESTRUCTIVE, "Disconnect PPP Active"))
async def mikrotik_disconnect_ppp_active(ctx: Context, session_id: str) -> str:
    """Disconnects an active PPP session by ID.

    Notes:
        session_id: "*N" or "N" from list output e.g. "*2"
    """
    await ctx.info(f"Disconnecting active PPP session: session_id={session_id}")

    check_cmd = f"/ppp active print count-only where .id={session_id}"
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"Active PPP session with ID '{session_id}' not found."

    cmd = f"/ppp active remove {session_id}"
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to disconnect active PPP session: {result}"

    return f"Active PPP session '{session_id}' disconnected successfully."
