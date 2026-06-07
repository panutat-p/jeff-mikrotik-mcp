import asyncio
from typing import Optional

from mcp.server.fastmcp import Context

from ..app import mcp, READ, WRITE, WRITE_IDEMPOTENT, DANGEROUS, annotate
from ..connector import execute_mikrotik_command, wait_for_router_ssh


# ---------------------------------------------------------------------------
# Package Management
# ---------------------------------------------------------------------------

@mcp.tool(name="query_packages", annotations=annotate(READ, "Query Packages"))
async def mikrotik_query_packages(
    ctx: Context,
    name: Optional[str] = None,
    name_filter: Optional[str] = None,
    disabled_only: bool = False,
) -> str:
    """Lists installed RouterOS packages or returns detail for a specific one by name."""
    if name:
        await ctx.info(f"Getting package details: name={name}")
        cmd = f'/system package print detail where name="{name}"'
        result = await execute_mikrotik_command(cmd, ctx)
        if not result or result.strip() == "":
            return f"Package '{name}' not found."
        return f"PACKAGE DETAILS:\n\n{result}"

    await ctx.info("Listing packages")
    cmd = "/system package print"
    filters = []
    if name_filter:
        filters.append(f'name~"{name_filter}"')
    if disabled_only:
        filters.append("disabled=yes")
    if filters:
        cmd += " where " + " ".join(filters)
    result = await execute_mikrotik_command(cmd, ctx)
    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No packages found."
    return f"PACKAGES:\n\n{result}"


@mcp.tool(name="set_package_enabled", annotations=annotate(WRITE_IDEMPOTENT, "Set Package Enabled"))
async def mikrotik_set_package_enabled(ctx: Context, name: str, enabled: bool) -> str:
    """Schedules a package to be enabled or disabled after the next reboot."""
    action = "enable" if enabled else "disable"
    await ctx.info(f"Scheduling package {action}: name={name}")
    cmd = f"/system package {action} {name}"
    result = await execute_mikrotik_command(cmd, ctx)
    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to {action} package: {result}"
    details_cmd = f'/system package print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)
    if details.strip():
        return f"Package '{name}' scheduled for {action} on next reboot:\n\n{details}"
    return f"Package '{name}' scheduled for {action} on next reboot. Run apply_package_changes to reboot."


@mcp.tool(name="uninstall_package", annotations=annotate(DANGEROUS, "Uninstall Package"))
async def mikrotik_uninstall_package(ctx: Context, name: str) -> str:
    """Schedules a package to be removed on the next reboot."""
    await ctx.info(f"Scheduling package uninstall: name={name}")

    check_cmd = f'/system package print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"Package '{name}' not found."

    cmd = f"/system package uninstall {name}"
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to uninstall package: {result}"

    details_cmd = f'/system package print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Package '{name}' scheduled for uninstall on next reboot:\n\n{details}"
    return f"Package '{name}' scheduled for uninstall on next reboot. Run apply_package_changes to reboot."


@mcp.tool(name="apply_package_changes", annotations=annotate(DANGEROUS, "Apply Package Changes"))
async def mikrotik_apply_package_changes(ctx: Context) -> str:
    """Applies scheduled package changes and reboots the router."""
    await ctx.info("Applying scheduled package changes (router will reboot)")

    result = await execute_mikrotik_command("/system package apply-changes", ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to apply package changes: {result}"

    await ctx.info("Waiting for router to reboot and restore SSH (up to 120s)...")
    ready = await asyncio.to_thread(wait_for_router_ssh, 120.0)

    if ready:
        status = await execute_mikrotik_command("/system package print", ctx)
        return f"Package changes applied. Router is back online.\n\n{status}"

    return (
        "Package apply-changes was sent but the router did not respond on SSH "
        "within 120 seconds. It may still be rebooting."
    )
