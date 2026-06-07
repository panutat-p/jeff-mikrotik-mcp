from typing import Optional

from mcp.server.fastmcp import Context

from ..app import mcp, READ, WRITE, WRITE_IDEMPOTENT, DESTRUCTIVE, annotate
from ..connector import execute_mikrotik_command


# ---------------------------------------------------------------------------
# Scheduler Management
# ---------------------------------------------------------------------------

@mcp.tool(name="query_schedulers", annotations=annotate(READ, "Query Schedulers"))
async def mikrotik_query_schedulers(
    ctx: Context,
    name: Optional[str] = None,
    name_filter: Optional[str] = None,
    disabled_only: bool = False,
) -> str:
    """Lists system schedulers or returns detail for a specific one by name."""
    if name:
        await ctx.info(f"Getting scheduler details: name={name}")
        cmd = f'/system scheduler print detail where name="{name}"'
        result = await execute_mikrotik_command(cmd, ctx)
        if not result or result.strip() == "":
            return f"Scheduler '{name}' not found."
        return f"SCHEDULER DETAILS:\n\n{result}"

    await ctx.info("Listing schedulers")
    cmd = "/system scheduler print"
    filters = []
    if name_filter:
        filters.append(f'name~"{name_filter}"')
    if disabled_only:
        filters.append("disabled=yes")
    if filters:
        cmd += " where " + " ".join(filters)
    result = await execute_mikrotik_command(cmd, ctx)
    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No schedulers found."
    return f"SCHEDULERS:\n\n{result}"


@mcp.tool(name="create_scheduler", annotations=annotate(WRITE, "Create Scheduler"))
async def mikrotik_create_scheduler(
    ctx: Context,
    name: str,
    on_event: str,
    interval: str,
    start_time: Optional[str] = None,
    start_date: Optional[str] = None,
    comment: Optional[str] = None,
    disabled: bool = False,
) -> str:
    """Creates a system scheduler on the MikroTik device.

    Notes:
        on_event: RouterOS command(s) to run e.g. "/system backup save name=daily"
        interval: schedule interval e.g. "1d", "1h", "30m"
        start_time: first run time e.g. "02:00:00"
        start_date: first run date e.g. "jan/01/2026"
    """
    await ctx.info(f"Creating scheduler: name={name}")

    cmd = (
        f'/system scheduler add name="{name}"'
        f' on-event="{on_event}"'
        f" interval={interval}"
    )

    if start_time:
        cmd += f' start-time="{start_time}"'
    if start_date:
        cmd += f' start-date="{start_date}"'
    if comment:
        cmd += f' comment="{comment}"'
    if disabled:
        cmd += " disabled=yes"

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to create scheduler: {result}"

    details_cmd = f'/system scheduler print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Scheduler created successfully:\n\n{details}"
    return "Scheduler created successfully."


@mcp.tool(name="update_scheduler", annotations=annotate(WRITE_IDEMPOTENT, "Update Scheduler"))
async def mikrotik_update_scheduler(
    ctx: Context,
    name: str,
    new_name: Optional[str] = None,
    on_event: Optional[str] = None,
    interval: Optional[str] = None,
    start_time: Optional[str] = None,
    start_date: Optional[str] = None,
    comment: Optional[str] = None,
    disabled: Optional[bool] = None,
) -> str:
    """Updates an existing system scheduler."""
    await ctx.info(f"Updating scheduler: name={name}")

    updates = []
    if new_name:
        updates.append(f'name="{new_name}"')
    if on_event is not None:
        updates.append(f'on-event="{on_event}"')
    if interval is not None:
        updates.append(f"interval={interval}")
    if start_time is not None:
        updates.append(f'start-time="{start_time}"')
    if start_date is not None:
        updates.append(f'start-date="{start_date}"')
    if comment is not None:
        updates.append(f'comment="{comment}"')
    if disabled is not None:
        updates.append(f'disabled={"yes" if disabled else "no"}')

    if not updates:
        return "No updates specified."

    cmd = f'/system scheduler set [find name="{name}"] ' + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to update scheduler: {result}"

    lookup_name = new_name if new_name else name
    details_cmd = f'/system scheduler print detail where name="{lookup_name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    return f"Scheduler updated successfully:\n\n{details}"


@mcp.tool(name="remove_scheduler", annotations=annotate(DESTRUCTIVE, "Remove Scheduler"))
async def mikrotik_remove_scheduler(ctx: Context, name: str) -> str:
    """Removes a system scheduler from the MikroTik device."""
    await ctx.info(f"Removing scheduler: name={name}")

    check_cmd = f'/system scheduler print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"Scheduler '{name}' not found."

    cmd = f'/system scheduler remove [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove scheduler: {result}"

    return f"Scheduler '{name}' removed successfully."


@mcp.tool(name="set_scheduler_enabled", annotations=annotate(WRITE_IDEMPOTENT, "Set Scheduler Enabled"))
async def mikrotik_set_scheduler_enabled(ctx: Context, name: str, enabled: bool) -> str:
    """Enables or disables a system scheduler."""
    action = "enable" if enabled else "disable"
    await ctx.info(f"Setting scheduler {action}d: name={name}")
    cmd = f'/system scheduler {action} [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)
    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to {action} scheduler: {result}"
    return f"Scheduler '{name}' {action}d successfully."


# ---------------------------------------------------------------------------
# Script Management
# ---------------------------------------------------------------------------

@mcp.tool(name="query_scripts", annotations=annotate(READ, "Query Scripts"))
async def mikrotik_query_scripts(
    ctx: Context,
    name: Optional[str] = None,
    name_filter: Optional[str] = None,
    policy_filter: Optional[str] = None,
) -> str:
    """Lists system scripts or returns detail for a specific one by name."""
    if name:
        await ctx.info(f"Getting script details: name={name}")
        cmd = f'/system script print detail where name="{name}"'
        result = await execute_mikrotik_command(cmd, ctx)
        if not result or result.strip() == "":
            return f"Script '{name}' not found."
        return f"SCRIPT DETAILS:\n\n{result}"

    await ctx.info("Listing scripts")
    cmd = "/system script print"
    filters = []
    if name_filter:
        filters.append(f'name~"{name_filter}"')
    if policy_filter:
        filters.append(f'policy~"{policy_filter}"')
    if filters:
        cmd += " where " + " ".join(filters)
    result = await execute_mikrotik_command(cmd, ctx)
    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No scripts found."
    return f"SCRIPTS:\n\n{result}"


@mcp.tool(name="create_script", annotations=annotate(WRITE, "Create Script"))
async def mikrotik_create_script(
    ctx: Context,
    name: str,
    source: str,
    policy: Optional[str] = None,
    comment: Optional[str] = None,
    dont_require_permissions: bool = False,
) -> str:
    """Creates a system script on the MikroTik device.

    Notes:
        source: RouterOS script body e.g. ":log info \"hello\""
        policy: comma-separated permissions e.g. "read,write,policy,test"
    """
    await ctx.info(f"Creating script: name={name}")

    cmd = f'/system script add name="{name}" source="{source}"'

    if policy:
        cmd += f" policy={policy}"
    if comment:
        cmd += f' comment="{comment}"'
    if dont_require_permissions:
        cmd += " dont-require-permissions=yes"

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to create script: {result}"

    details_cmd = f'/system script print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Script created successfully:\n\n{details}"
    return "Script created successfully."


@mcp.tool(name="update_script", annotations=annotate(WRITE_IDEMPOTENT, "Update Script"))
async def mikrotik_update_script(
    ctx: Context,
    name: str,
    new_name: Optional[str] = None,
    source: Optional[str] = None,
    policy: Optional[str] = None,
    comment: Optional[str] = None,
    dont_require_permissions: Optional[bool] = None,
) -> str:
    """Updates an existing system script."""
    await ctx.info(f"Updating script: name={name}")

    updates = []
    if new_name:
        updates.append(f'name="{new_name}"')
    if source is not None:
        updates.append(f'source="{source}"')
    if policy is not None:
        updates.append(f"policy={policy}")
    if comment is not None:
        updates.append(f'comment="{comment}"')
    if dont_require_permissions is not None:
        updates.append(
            f'dont-require-permissions={"yes" if dont_require_permissions else "no"}'
        )

    if not updates:
        return "No updates specified."

    cmd = f'/system script set [find name="{name}"] ' + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to update script: {result}"

    lookup_name = new_name if new_name else name
    details_cmd = f'/system script print detail where name="{lookup_name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    return f"Script updated successfully:\n\n{details}"


@mcp.tool(name="remove_script", annotations=annotate(DESTRUCTIVE, "Remove Script"))
async def mikrotik_remove_script(ctx: Context, name: str) -> str:
    """Removes a system script from the MikroTik device."""
    await ctx.info(f"Removing script: name={name}")

    check_cmd = f'/system script print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"Script '{name}' not found."

    cmd = f'/system script remove [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove script: {result}"

    return f"Script '{name}' removed successfully."


@mcp.tool(name="run_script", annotations=annotate(WRITE, "Run Script"))
async def mikrotik_run_script(ctx: Context, name: str) -> str:
    """Runs a system script immediately."""
    await ctx.info(f"Running script: name={name}")

    check_cmd = f'/system script print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"Script '{name}' not found."

    cmd = f'/system script run [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to run script: {result}"

    if result.strip():
        return f"Script '{name}' executed:\n\n{result}"
    return f"Script '{name}' executed successfully."
