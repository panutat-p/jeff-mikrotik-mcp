from typing import Optional

from mcp.server.fastmcp import Context

from ..app import mcp, READ, WRITE, WRITE_IDEMPOTENT, DESTRUCTIVE, annotate
from ..connector import execute_mikrotik_command


# ---------------------------------------------------------------------------
# Container Management
# ---------------------------------------------------------------------------

@mcp.tool(name="list_containers", annotations=annotate(READ, "List Containers"))
async def mikrotik_list_containers(
    ctx: Context,
    name_filter: Optional[str] = None,
    disabled_only: bool = False,
) -> str:
    """Lists containers on the MikroTik device."""
    await ctx.info("Listing containers")

    cmd = "/container print"

    filters = []
    if name_filter:
        filters.append(f'name~"{name_filter}"')
    if disabled_only:
        filters.append("disabled=yes")

    if filters:
        cmd += " where " + " ".join(filters)

    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No containers found."

    return f"CONTAINERS:\n\n{result}"


@mcp.tool(name="get_container", annotations=annotate(READ, "Get Container"))
async def mikrotik_get_container(ctx: Context, name: str) -> str:
    """Gets detailed information about a specific container."""
    await ctx.info(f"Getting container details: name={name}")

    cmd = f'/container print detail where name="{name}"'
    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "":
        return f"Container '{name}' not found."

    return f"CONTAINER DETAILS:\n\n{result}"


@mcp.tool(name="create_container", annotations=annotate(WRITE, "Create Container"))
async def mikrotik_create_container(
    ctx: Context,
    name: str,
    interface: str,
    remote_image: Optional[str] = None,
    file: Optional[str] = None,
    root_dir: Optional[str] = None,
    envlist: Optional[str] = None,
    mountlists: Optional[str] = None,
    hostname: Optional[str] = None,
    cmd: Optional[str] = None,
    entrypoint: Optional[str] = None,
    workdir: Optional[str] = None,
    dns: Optional[str] = None,
    domain_name: Optional[str] = None,
    logging: Optional[bool] = None,
    start_on_boot: Optional[bool] = None,
    comment: Optional[str] = None,
    disabled: bool = False,
) -> str:
    """Creates a container on the MikroTik device.

    Notes:
        remote_image: image from configured registry e.g. "pihole/pihole"
        file: path to a local .tar archive on the router
        envlist: comma-separated env list names from /container/envs
        mountlists: comma-separated mount list names from /container/mounts
    """
    await ctx.info(f"Creating container: name={name}")

    if not remote_image and not file:
        return "Either remote_image or file must be specified."

    create_cmd = f'/container add name="{name}" interface="{interface}"'

    if remote_image:
        create_cmd += f' remote-image="{remote_image}"'
    if file:
        create_cmd += f' file="{file}"'
    if root_dir:
        create_cmd += f' root-dir="{root_dir}"'
    if envlist:
        create_cmd += f' envlist="{envlist}"'
    if mountlists:
        create_cmd += f' mountlists="{mountlists}"'
    if hostname:
        create_cmd += f' hostname="{hostname}"'
    if cmd:
        create_cmd += f' cmd="{cmd}"'
    if entrypoint:
        create_cmd += f' entrypoint="{entrypoint}"'
    if workdir:
        create_cmd += f' workdir="{workdir}"'
    if dns:
        create_cmd += f' dns="{dns}"'
    if domain_name:
        create_cmd += f' domain-name="{domain_name}"'
    if logging is not None:
        create_cmd += f' logging={"yes" if logging else "no"}'
    if start_on_boot is not None:
        create_cmd += f' start-on-boot={"yes" if start_on_boot else "no"}'
    if comment:
        create_cmd += f' comment="{comment}"'
    if disabled:
        create_cmd += " disabled=yes"

    result = await execute_mikrotik_command(create_cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to create container: {result}"

    details_cmd = f'/container print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Container created successfully:\n\n{details}"
    return "Container created successfully."


@mcp.tool(name="update_container", annotations=annotate(WRITE_IDEMPOTENT, "Update Container"))
async def mikrotik_update_container(
    ctx: Context,
    name: str,
    new_name: Optional[str] = None,
    interface: Optional[str] = None,
    envlist: Optional[str] = None,
    mountlists: Optional[str] = None,
    hostname: Optional[str] = None,
    cmd: Optional[str] = None,
    entrypoint: Optional[str] = None,
    workdir: Optional[str] = None,
    dns: Optional[str] = None,
    domain_name: Optional[str] = None,
    logging: Optional[bool] = None,
    start_on_boot: Optional[bool] = None,
    comment: Optional[str] = None,
    disabled: Optional[bool] = None,
) -> str:
    """Updates an existing container's settings."""
    await ctx.info(f"Updating container: name={name}")

    updates = []
    if new_name:
        updates.append(f'name="{new_name}"')
    if interface:
        updates.append(f'interface="{interface}"')
    if envlist is not None:
        updates.append(f'envlist="{envlist}"')
    if mountlists is not None:
        updates.append(f'mountlists="{mountlists}"')
    if hostname is not None:
        updates.append(f'hostname="{hostname}"')
    if cmd is not None:
        updates.append(f'cmd="{cmd}"')
    if entrypoint is not None:
        updates.append(f'entrypoint="{entrypoint}"')
    if workdir is not None:
        updates.append(f'workdir="{workdir}"')
    if dns is not None:
        updates.append(f'dns="{dns}"')
    if domain_name is not None:
        updates.append(f'domain-name="{domain_name}"')
    if logging is not None:
        updates.append(f'logging={"yes" if logging else "no"}')
    if start_on_boot is not None:
        updates.append(f'start-on-boot={"yes" if start_on_boot else "no"}')
    if comment is not None:
        updates.append(f'comment="{comment}"')
    if disabled is not None:
        updates.append(f'disabled={"yes" if disabled else "no"}')

    if not updates:
        return "No updates specified."

    update_cmd = f'/container set [find name="{name}"] ' + " ".join(updates)
    result = await execute_mikrotik_command(update_cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to update container: {result}"

    lookup_name = new_name if new_name else name
    details_cmd = f'/container print detail where name="{lookup_name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    return f"Container updated successfully:\n\n{details}"


@mcp.tool(name="remove_container", annotations=annotate(DESTRUCTIVE, "Remove Container"))
async def mikrotik_remove_container(ctx: Context, name: str) -> str:
    """Removes a container from the MikroTik device."""
    await ctx.info(f"Removing container: name={name}")

    check_cmd = f'/container print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"Container '{name}' not found."

    cmd = f'/container remove [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove container: {result}"

    return f"Container '{name}' removed successfully."


@mcp.tool(name="start_container", annotations=annotate(WRITE_IDEMPOTENT, "Start Container"))
async def mikrotik_start_container(ctx: Context, name: str) -> str:
    """Starts a container."""
    await ctx.info(f"Starting container: name={name}")

    cmd = f'/container start [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to start container: {result}"

    details_cmd = f'/container print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Container '{name}' started:\n\n{details}"
    return f"Container '{name}' started successfully."


@mcp.tool(name="stop_container", annotations=annotate(WRITE_IDEMPOTENT, "Stop Container"))
async def mikrotik_stop_container(ctx: Context, name: str) -> str:
    """Stops a running container."""
    await ctx.info(f"Stopping container: name={name}")

    cmd = f'/container stop [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to stop container: {result}"

    details_cmd = f'/container print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Container '{name}' stopped:\n\n{details}"
    return f"Container '{name}' stopped successfully."


@mcp.tool(name="enable_container", annotations=annotate(WRITE_IDEMPOTENT, "Enable Container"))
async def mikrotik_enable_container(ctx: Context, name: str) -> str:
    """Enables a container."""
    await ctx.info(f"Enabling container: name={name}")

    cmd = f'/container enable [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to enable container: {result}"

    return f"Container '{name}' enabled successfully."


@mcp.tool(name="disable_container", annotations=annotate(WRITE_IDEMPOTENT, "Disable Container"))
async def mikrotik_disable_container(ctx: Context, name: str) -> str:
    """Disables a container."""
    await ctx.info(f"Disabling container: name={name}")

    cmd = f'/container disable [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to disable container: {result}"

    return f"Container '{name}' disabled successfully."


# ---------------------------------------------------------------------------
# Container Mounts
# ---------------------------------------------------------------------------

@mcp.tool(name="list_container_mounts", annotations=annotate(READ, "List Container Mounts"))
async def mikrotik_list_container_mounts(
    ctx: Context,
    list_filter: Optional[str] = None,
    disabled_only: bool = False,
) -> str:
    """Lists container mount definitions."""
    await ctx.info("Listing container mounts")

    cmd = "/container/mounts print"

    filters = []
    if list_filter:
        filters.append(f'list="{list_filter}"')
    if disabled_only:
        filters.append("disabled=yes")

    if filters:
        cmd += " where " + " ".join(filters)

    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No container mounts found."

    return f"CONTAINER MOUNTS:\n\n{result}"


@mcp.tool(name="add_container_mount", annotations=annotate(WRITE, "Add Container Mount"))
async def mikrotik_add_container_mount(
    ctx: Context,
    list_name: str,
    src: str,
    dst: str,
    read_only: Optional[bool] = None,
    comment: Optional[str] = None,
    disabled: bool = False,
) -> str:
    """Adds a bind-mount definition for use with containers.

    Notes:
        list_name: mount list identifier referenced by mountlists on containers
        src: host path on RouterOS e.g. "disk1/volumes/app"
        dst: path inside the container e.g. "/etc/app"
    """
    await ctx.info(f"Adding container mount: list={list_name}, src={src}, dst={dst}")

    cmd = (
        f'/container/mounts add list="{list_name}"'
        f' src="{src}" dst="{dst}"'
    )

    if read_only is not None:
        cmd += f' read-only={"yes" if read_only else "no"}'
    if comment:
        cmd += f' comment="{comment}"'
    if disabled:
        cmd += " disabled=yes"

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to add container mount: {result}"

    details_cmd = (
        f'/container/mounts print detail where list="{list_name}"'
        f' src="{src}" dst="{dst}"'
    )
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Container mount added successfully:\n\n{details}"
    return "Container mount added successfully."


@mcp.tool(name="remove_container_mount", annotations=annotate(DESTRUCTIVE, "Remove Container Mount"))
async def mikrotik_remove_container_mount(ctx: Context, mount_id: str) -> str:
    """Removes a container mount definition.

    Notes:
        mount_id: "*N" or "N" from list output e.g. "*2"
    """
    await ctx.info(f"Removing container mount: mount_id={mount_id}")

    check_cmd = f"/container/mounts print count-only where .id={mount_id}"
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"Container mount with ID '{mount_id}' not found."

    cmd = f"/container/mounts remove {mount_id}"
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove container mount: {result}"

    return f"Container mount '{mount_id}' removed successfully."


# ---------------------------------------------------------------------------
# Container Environment Variables
# ---------------------------------------------------------------------------

@mcp.tool(name="list_container_envs", annotations=annotate(READ, "List Container Envs"))
async def mikrotik_list_container_envs(
    ctx: Context,
    list_filter: Optional[str] = None,
    disabled_only: bool = False,
) -> str:
    """Lists container environment variable definitions."""
    await ctx.info("Listing container environment variables")

    cmd = "/container/envs print"

    filters = []
    if list_filter:
        filters.append(f'list="{list_filter}"')
    if disabled_only:
        filters.append("disabled=yes")

    if filters:
        cmd += " where " + " ".join(filters)

    result = await execute_mikrotik_command(cmd, ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No container environment variables found."

    return f"CONTAINER ENVS:\n\n{result}"


@mcp.tool(name="add_container_env", annotations=annotate(WRITE, "Add Container Env"))
async def mikrotik_add_container_env(
    ctx: Context,
    list_name: str,
    key: str,
    value: str,
    comment: Optional[str] = None,
    disabled: bool = False,
) -> str:
    """Adds an environment variable definition for use with containers.

    Notes:
        list_name: env list identifier referenced by envlist on containers
    """
    await ctx.info(f"Adding container env: list={list_name}, key={key}")

    cmd = (
        f'/container/envs add list="{list_name}"'
        f' key="{key}" value="{value}"'
    )

    if comment:
        cmd += f' comment="{comment}"'
    if disabled:
        cmd += " disabled=yes"

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to add container env: {result}"

    details_cmd = (
        f'/container/envs print detail where list="{list_name}" key="{key}"'
    )
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Container env added successfully:\n\n{details}"
    return "Container env added successfully."


@mcp.tool(name="remove_container_env", annotations=annotate(DESTRUCTIVE, "Remove Container Env"))
async def mikrotik_remove_container_env(ctx: Context, env_id: str) -> str:
    """Removes a container environment variable definition.

    Notes:
        env_id: "*N" or "N" from list output e.g. "*2"
    """
    await ctx.info(f"Removing container env: env_id={env_id}")

    check_cmd = f"/container/envs print count-only where .id={env_id}"
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"Container env with ID '{env_id}' not found."

    cmd = f"/container/envs remove {env_id}"
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove container env: {result}"

    return f"Container env '{env_id}' removed successfully."


# ---------------------------------------------------------------------------
# Container Configuration
# ---------------------------------------------------------------------------

@mcp.tool(name="list_container_configs", annotations=annotate(READ, "List Container Configs"))
async def mikrotik_list_container_configs(ctx: Context) -> str:
    """Lists global container configuration."""
    await ctx.info("Listing container configuration")

    result = await execute_mikrotik_command("/container/config print", ctx)

    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No container configuration found."

    return f"CONTAINER CONFIG:\n\n{result}"


@mcp.tool(name="get_container_config", annotations=annotate(READ, "Get Container Config"))
async def mikrotik_get_container_config(ctx: Context) -> str:
    """Gets detailed global container configuration."""
    await ctx.info("Getting container configuration details")

    result = await execute_mikrotik_command("/container/config print detail", ctx)

    if not result or result.strip() == "":
        return "Container configuration not found."

    return f"CONTAINER CONFIG DETAILS:\n\n{result}"


@mcp.tool(name="add_container_config", annotations=annotate(WRITE, "Add Container Config"))
async def mikrotik_add_container_config(
    ctx: Context,
    registry_url: Optional[str] = None,
    tmpdir: Optional[str] = None,
    memory_high: Optional[int] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> str:
    """Sets global container configuration options.

    Notes:
        registry_url: external registry e.g. "https://registry-1.docker.io"
        tmpdir: extraction directory e.g. "disk1/tmp"
        memory_high: RAM limit in bytes (1 = unlimited)
    """
    await ctx.info("Setting container configuration")

    updates = []
    if registry_url is not None:
        updates.append(f'registry-url="{registry_url}"')
    if tmpdir is not None:
        updates.append(f'tmpdir="{tmpdir}"')
    if memory_high is not None:
        updates.append(f"memory-high={memory_high}")
    if username is not None:
        updates.append(f'username="{username}"')
    if password is not None:
        updates.append(f'password="{password}"')

    if not updates:
        return "No configuration options specified."

    cmd = "/container/config set " + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to set container configuration: {result}"

    details = await execute_mikrotik_command("/container/config print detail", ctx)

    return f"Container configuration updated successfully:\n\n{details}"


@mcp.tool(name="remove_container_config", annotations=annotate(DESTRUCTIVE, "Remove Container Config"))
async def mikrotik_remove_container_config(ctx: Context, property_name: str) -> str:
    """Clears a global container configuration property.

    Notes:
        property_name: RouterOS property to clear e.g. "registry-url", "tmpdir",
            "memory-high", "username", "password"
    """
    await ctx.info(f"Clearing container config property: {property_name}")

    cmd = f"/container/config set !{property_name}"
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to clear container config property: {result}"

    details = await execute_mikrotik_command("/container/config print detail", ctx)

    return f"Container config property '{property_name}' cleared:\n\n{details}"
