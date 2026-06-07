from typing import Literal, Optional

import re

from mcp.server.fastmcp import Context

from ..app import mcp, READ, WRITE, WRITE_IDEMPOTENT, DESTRUCTIVE, annotate
from ..connector import execute_mikrotik_command


def _mask_passwords(text: str) -> str:
    return re.sub(r'password="[^"]*"', 'password="***"', text)


# ---------------------------------------------------------------------------
# OVPN Server Management
# ---------------------------------------------------------------------------

@mcp.tool(name="create_ovpn_server", annotations=annotate(WRITE, "Create OVPN Server"))
async def mikrotik_create_ovpn_server(
    ctx: Context,
    name: str,
    port: int = 1194,
    mode: Literal["ip", "ethernet"] = "ip",
    certificate: Optional[str] = None,
    auth: Optional[str] = None,
    cipher: Optional[str] = None,
    comment: Optional[str] = None,
    disabled: bool = False,
) -> str:
    """Creates an OpenVPN server interface on the MikroTik device.

    Notes:
        certificate: server certificate name from /certificate
        auth: authentication algorithm e.g. "sha1", "sha256"
        cipher: encryption cipher e.g. "aes256", "aes128"
    """
    await ctx.info(f"Creating OVPN server: name={name}")

    cmd = f'/interface ovpn-server add name="{name}" port={port} mode={mode}'

    if certificate:
        cmd += f' certificate="{certificate}"'
    if auth:
        cmd += f" auth={auth}"
    if cipher:
        cmd += f" cipher={cipher}"
    if comment:
        cmd += f' comment="{comment}"'
    if disabled:
        cmd += " disabled=yes"

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to create OVPN server: {result}"

    details_cmd = f'/interface ovpn-server print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"OVPN server created successfully:\n\n{details}"
    return "OVPN server created successfully."


@mcp.tool(name="query_ovpn_servers", annotations=annotate(READ, "Query OVPN Servers"))
async def mikrotik_query_ovpn_servers(
    ctx: Context,
    name: Optional[str] = None,
    name_filter: Optional[str] = None,
    disabled_only: bool = False,
    running_only: bool = False,
) -> str:
    """Lists OpenVPN server interfaces or returns detail for a specific one by name."""
    if name:
        await ctx.info(f"Getting OVPN server details: name={name}")
        cmd = f'/interface ovpn-server print detail where name="{name}"'
        result = await execute_mikrotik_command(cmd, ctx)
        if not result or result.strip() == "":
            return f"OVPN server '{name}' not found."
        return f"OVPN SERVER DETAILS:\n\n{result}"

    await ctx.info("Listing OVPN servers")
    cmd = "/interface ovpn-server print"
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
        return "No OVPN servers found."
    return f"OVPN SERVERS:\n\n{result}"


@mcp.tool(name="update_ovpn_server", annotations=annotate(WRITE_IDEMPOTENT, "Update OVPN Server"))
async def mikrotik_update_ovpn_server(
    ctx: Context,
    name: str,
    new_name: Optional[str] = None,
    port: Optional[int] = None,
    mode: Optional[Literal["ip", "ethernet"]] = None,
    certificate: Optional[str] = None,
    auth: Optional[str] = None,
    cipher: Optional[str] = None,
    comment: Optional[str] = None,
    disabled: Optional[bool] = None,
) -> str:
    """Updates an existing OpenVPN server interface's settings on the MikroTik device."""
    await ctx.info(f"Updating OVPN server: name={name}")

    updates = []
    if new_name:
        updates.append(f'name="{new_name}"')
    if port is not None:
        updates.append(f"port={port}")
    if mode:
        updates.append(f"mode={mode}")
    if certificate is not None:
        updates.append(f'certificate="{certificate}"')
    if auth is not None:
        updates.append(f"auth={auth}")
    if cipher is not None:
        updates.append(f"cipher={cipher}")
    if comment is not None:
        updates.append(f'comment="{comment}"')
    if disabled is not None:
        updates.append(f'disabled={"yes" if disabled else "no"}')

    if not updates:
        return "No updates specified."

    cmd = f'/interface ovpn-server set [find name="{name}"] ' + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to update OVPN server: {result}"

    lookup_name = new_name if new_name else name
    details_cmd = f'/interface ovpn-server print detail where name="{lookup_name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    return f"OVPN server updated successfully:\n\n{details}"


@mcp.tool(name="remove_ovpn_server", annotations=annotate(DESTRUCTIVE, "Remove OVPN Server"))
async def mikrotik_remove_ovpn_server(ctx: Context, name: str) -> str:
    """Removes an OpenVPN server interface from the MikroTik device."""
    await ctx.info(f"Removing OVPN server: name={name}")

    check_cmd = f'/interface ovpn-server print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"OVPN server '{name}' not found."

    cmd = f'/interface ovpn-server remove [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove OVPN server: {result}"

    return f"OVPN server '{name}' removed successfully."


# ---------------------------------------------------------------------------
# OVPN Server User Management
# ---------------------------------------------------------------------------

@mcp.tool(name="add_ovpn_server_user", annotations=annotate(WRITE, "Add OVPN Server User"))
async def mikrotik_add_ovpn_server_user(
    ctx: Context,
    server: str,
    user: str,
    password: str,
    comment: Optional[str] = None,
    disabled: bool = False,
) -> str:
    """Adds a user to an OpenVPN server on the MikroTik device.

    Notes:
        server: OVPN server interface name e.g. "ovpn-server1"
    """
    await ctx.info(f"Adding OVPN server user: server={server}, user={user}")

    cmd = (
        f'/interface ovpn-server user add server="{server}"'
        f' user="{user}" password="{password}"'
    )

    if comment:
        cmd += f' comment="{comment}"'
    if disabled:
        cmd += " disabled=yes"

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to add OVPN server user: {result}"

    details_cmd = (
        f'/interface ovpn-server user print detail where'
        f' server="{server}" user="{user}"'
    )
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"OVPN server user added successfully:\n\n{_mask_passwords(details)}"
    return "OVPN server user added successfully."


@mcp.tool(name="list_ovpn_server_users", annotations=annotate(READ, "List OVPN Server Users"))
async def mikrotik_list_ovpn_server_users(
    ctx: Context,
    server_filter: Optional[str] = None,
    user_filter: Optional[str] = None,
    disabled_only: bool = False,
) -> str:
    """Lists OpenVPN server users on the MikroTik device."""
    await ctx.info("Listing OVPN server users")

    cmd = "/interface ovpn-server user print"

    filters = []
    if server_filter:
        filters.append(f'server="{server_filter}"')
    if user_filter:
        filters.append(f'user~"{user_filter}"')
    if disabled_only:
        filters.append("disabled=yes")

    if filters:
        cmd += " where " + " ".join(filters)

    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No OVPN server users found."

    return f"OVPN SERVER USERS:\n\n{_mask_passwords(result)}"


@mcp.tool(name="remove_ovpn_server_user", annotations=annotate(DESTRUCTIVE, "Remove OVPN Server User"))
async def mikrotik_remove_ovpn_server_user(ctx: Context, user_id: str) -> str:
    """Removes an OpenVPN server user by ID.

    Notes:
        user_id: "*N" or "N" from list output e.g. "*2"
    """
    await ctx.info(f"Removing OVPN server user: user_id={user_id}")

    check_cmd = f"/interface ovpn-server user print count-only where .id={user_id}"
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"OVPN server user with ID '{user_id}' not found."

    cmd = f"/interface ovpn-server user remove {user_id}"
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove OVPN server user: {result}"

    return f"OVPN server user '{user_id}' removed successfully."


# ---------------------------------------------------------------------------
# IPsec Peer Management
# ---------------------------------------------------------------------------

@mcp.tool(name="add_ipsec_peer", annotations=annotate(WRITE, "Add IPsec Peer"))
async def mikrotik_add_ipsec_peer(
    ctx: Context,
    name: str,
    address: str,
    secret: str,
    exchange_mode: Optional[str] = None,
    comment: Optional[str] = None,
    disabled: bool = False,
) -> str:
    """Adds an IPsec peer on the MikroTik device.

    Notes:
        address: remote peer IP or hostname e.g. "203.0.113.1"
        exchange_mode: "main", "aggressive", "ike2", etc.
    """
    await ctx.info(f"Adding IPsec peer: name={name}, address={address}")

    cmd = f'/ip ipsec peer add name="{name}" address="{address}" secret="{secret}"'

    if exchange_mode:
        cmd += f" exchange-mode={exchange_mode}"
    if comment:
        cmd += f' comment="{comment}"'
    if disabled:
        cmd += " disabled=yes"

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to add IPsec peer: {result}"

    details_cmd = f'/ip ipsec peer print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"IPsec peer added successfully:\n\n{_mask_passwords(details)}"
    return "IPsec peer added successfully."


@mcp.tool(name="query_ipsec_peers", annotations=annotate(READ, "Query IPsec Peers"))
async def mikrotik_query_ipsec_peers(
    ctx: Context,
    name: Optional[str] = None,
    name_filter: Optional[str] = None,
    address_filter: Optional[str] = None,
    disabled_only: bool = False,
) -> str:
    """Lists IPsec peers or returns detail for a specific one by name."""
    if name:
        await ctx.info(f"Getting IPsec peer details: name={name}")
        cmd = f'/ip ipsec peer print detail where name="{name}"'
        result = await execute_mikrotik_command(cmd, ctx)
        if not result or result.strip() == "":
            return f"IPsec peer '{name}' not found."
        return f"IPSEC PEER DETAILS:\n\n{_mask_passwords(result)}"

    await ctx.info("Listing IPsec peers")
    cmd = "/ip ipsec peer print"
    filters = []
    if name_filter:
        filters.append(f'name~"{name_filter}"')
    if address_filter:
        filters.append(f'address="{address_filter}"')
    if disabled_only:
        filters.append("disabled=yes")
    if filters:
        cmd += " where " + " ".join(filters)
    result = await execute_mikrotik_command(cmd, ctx)
    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No IPsec peers found."
    return f"IPSEC PEERS:\n\n{_mask_passwords(result)}"


@mcp.tool(name="remove_ipsec_peer", annotations=annotate(DESTRUCTIVE, "Remove IPsec Peer"))
async def mikrotik_remove_ipsec_peer(ctx: Context, name: str) -> str:
    """Removes an IPsec peer from the MikroTik device."""
    await ctx.info(f"Removing IPsec peer: name={name}")

    check_cmd = f'/ip ipsec peer print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"IPsec peer '{name}' not found."

    cmd = f'/ip ipsec peer remove [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove IPsec peer: {result}"

    return f"IPsec peer '{name}' removed successfully."


# ---------------------------------------------------------------------------
# IPsec Proposal Management
# ---------------------------------------------------------------------------

@mcp.tool(name="add_ipsec_proposal", annotations=annotate(WRITE, "Add IPsec Proposal"))
async def mikrotik_add_ipsec_proposal(
    ctx: Context,
    name: str,
    auth_algorithms: Optional[str] = None,
    enc_algorithms: Optional[str] = None,
    pfs_group: Optional[str] = None,
    comment: Optional[str] = None,
) -> str:
    """Adds an IPsec proposal on the MikroTik device.

    Notes:
        auth_algorithms: comma-separated e.g. "sha256,sha1"
        enc_algorithms: comma-separated e.g. "aes-256,aes-128"
        pfs_group: e.g. "modp2048", "none"
    """
    await ctx.info(f"Adding IPsec proposal: name={name}")

    cmd = f'/ip ipsec proposal add name="{name}"'

    if auth_algorithms:
        cmd += f" auth-algorithms={auth_algorithms}"
    if enc_algorithms:
        cmd += f" enc-algorithms={enc_algorithms}"
    if pfs_group:
        cmd += f" pfs-group={pfs_group}"
    if comment:
        cmd += f' comment="{comment}"'

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to add IPsec proposal: {result}"

    details_cmd = f'/ip ipsec proposal print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"IPsec proposal added successfully:\n\n{details}"
    return "IPsec proposal added successfully."


@mcp.tool(name="query_ipsec_proposals", annotations=annotate(READ, "Query IPsec Proposals"))
async def mikrotik_query_ipsec_proposals(
    ctx: Context,
    name: Optional[str] = None,
    name_filter: Optional[str] = None,
) -> str:
    """Lists IPsec proposals or returns detail for a specific one by name."""
    if name:
        await ctx.info(f"Getting IPsec proposal details: name={name}")
        cmd = f'/ip ipsec proposal print detail where name="{name}"'
        result = await execute_mikrotik_command(cmd, ctx)
        if not result or result.strip() == "":
            return f"IPsec proposal '{name}' not found."
        return f"IPSEC PROPOSAL DETAILS:\n\n{result}"

    await ctx.info("Listing IPsec proposals")
    cmd = "/ip ipsec proposal print"
    if name_filter:
        cmd += f' where name~"{name_filter}"'
    result = await execute_mikrotik_command(cmd, ctx)
    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No IPsec proposals found."
    return f"IPSEC PROPOSALS:\n\n{result}"


@mcp.tool(name="remove_ipsec_proposal", annotations=annotate(DESTRUCTIVE, "Remove IPsec Proposal"))
async def mikrotik_remove_ipsec_proposal(ctx: Context, name: str) -> str:
    """Removes an IPsec proposal from the MikroTik device."""
    await ctx.info(f"Removing IPsec proposal: name={name}")

    check_cmd = f'/ip ipsec proposal print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"IPsec proposal '{name}' not found."

    cmd = f'/ip ipsec proposal remove [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove IPsec proposal: {result}"

    return f"IPsec proposal '{name}' removed successfully."
