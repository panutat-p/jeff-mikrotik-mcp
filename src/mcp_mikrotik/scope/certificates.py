import base64
from typing import Literal, Optional

from mcp.server.fastmcp import Context

from ..app import mcp, READ, WRITE, WRITE_IDEMPOTENT, DESTRUCTIVE, annotate
from ..connector import (
    execute_mikrotik_command,
    upload_file_to_router,
    download_file_from_router,
)

# ---------------------------------------------------------------------------
# Certificate Management
# ---------------------------------------------------------------------------

@mcp.tool(name="query_certificates", annotations=annotate(READ, "Query Certificates"))
async def mikrotik_query_certificates(
    ctx: Context,
    name: Optional[str] = None,
    name_filter: Optional[str] = None,
    expired_only: bool = False,
) -> str:
    """Lists certificates or returns detail for a specific one by name."""
    if name:
        await ctx.info(f"Getting certificate details: name={name}")
        cmd = f'/certificate print detail where name="{name}"'
        result = await execute_mikrotik_command(cmd, ctx)
        if not result or result.strip() == "":
            return f"Certificate '{name}' not found."
        return f"CERTIFICATE DETAILS:\n\n{result}"

    await ctx.info("Listing certificates")
    cmd = "/certificate print"
    filters = []
    if name_filter:
        filters.append(f'name~"{name_filter}"')
    if expired_only:
        filters.append("expired=yes")
    if filters:
        cmd += " where " + " ".join(filters)
    result = await execute_mikrotik_command(cmd, ctx)
    if not result or result.strip() == "" or result.strip() == "no such item":
        return "No certificates found."
    return f"CERTIFICATES:\n\n{result}"


@mcp.tool(name="create_certificate", annotations=annotate(WRITE, "Create Certificate"))
async def mikrotik_create_certificate(
    ctx: Context,
    name: str,
    common_name: Optional[str] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    locality: Optional[str] = None,
    organization: Optional[str] = None,
    unit: Optional[str] = None,
    key_size: int = 2048,
    days_valid: int = 365,
    subject_alt_name: Optional[str] = None,
    key_usage: Optional[str] = None,
) -> str:
    """Creates a new certificate (CSR/key pair) on the MikroTik device.

    Notes:
        common_name: CN for the certificate e.g. "router.example.com"
        key_size: 2048 or 4096
        subject_alt_name: comma-separated SANs e.g. "DNS:router.example.com,IP:10.0.0.1"
        key_usage: comma-separated e.g. "digital-signature,key-encipherment"
    """
    await ctx.info(f"Creating certificate: name={name}")

    cmd = f'/certificate add name="{name}" key-size={key_size} days-valid={days_valid}'

    if common_name:
        cmd += f' common-name="{common_name}"'
    if country:
        cmd += f' country="{country}"'
    if state:
        cmd += f' state="{state}"'
    if locality:
        cmd += f' locality="{locality}"'
    if organization:
        cmd += f' organization="{organization}"'
    if unit:
        cmd += f' unit="{unit}"'
    if subject_alt_name:
        cmd += f' subject-alt-name="{subject_alt_name}"'
    if key_usage:
        cmd += f' key-usage={key_usage}'

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to create certificate: {result}"

    details_cmd = f'/certificate print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Certificate created successfully:\n\n{details}"
    return "Certificate created successfully."


@mcp.tool(name="update_certificate", annotations=annotate(WRITE_IDEMPOTENT, "Update Certificate"))
async def mikrotik_update_certificate(
    ctx: Context,
    name: str,
    new_name: Optional[str] = None,
    common_name: Optional[str] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    locality: Optional[str] = None,
    organization: Optional[str] = None,
    unit: Optional[str] = None,
    subject_alt_name: Optional[str] = None,
    trusted: Optional[bool] = None,
) -> str:
    """Updates certificate metadata on the MikroTik device."""
    await ctx.info(f"Updating certificate: name={name}")

    updates = []
    if new_name:
        updates.append(f'name="{new_name}"')
    if common_name is not None:
        updates.append(f'common-name="{common_name}"')
    if country is not None:
        updates.append(f'country="{country}"')
    if state is not None:
        updates.append(f'state="{state}"')
    if locality is not None:
        updates.append(f'locality="{locality}"')
    if organization is not None:
        updates.append(f'organization="{organization}"')
    if unit is not None:
        updates.append(f'unit="{unit}"')
    if subject_alt_name is not None:
        updates.append(f'subject-alt-name="{subject_alt_name}"')
    if trusted is not None:
        updates.append(f'trusted={"yes" if trusted else "no"}')

    if not updates:
        return "No updates specified."

    cmd = f'/certificate set [find name="{name}"] ' + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to update certificate: {result}"

    lookup_name = new_name if new_name else name
    details_cmd = f'/certificate print detail where name="{lookup_name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    return f"Certificate updated successfully:\n\n{details}"


@mcp.tool(name="remove_certificate", annotations=annotate(DESTRUCTIVE, "Remove Certificate"))
async def mikrotik_remove_certificate(ctx: Context, name: str) -> str:
    """Removes a certificate from the MikroTik device."""
    await ctx.info(f"Removing certificate: name={name}")

    check_cmd = f'/certificate print count-only where name="{name}"'
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return f"Certificate '{name}' not found."

    cmd = f'/certificate remove [find name="{name}"]'
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to remove certificate: {result}"

    return f"Certificate '{name}' removed successfully."


@mcp.tool(name="sign_certificate", annotations=annotate(WRITE, "Sign Certificate"))
async def mikrotik_sign_certificate(
    ctx: Context,
    name: str,
    ca_certificate: str,
    days_valid: Optional[int] = None,
) -> str:
    """Signs a certificate using a CA certificate on the MikroTik device.

    Notes:
        name: certificate to sign (must exist and be unsigned)
        ca_certificate: name of the CA certificate used for signing
    """
    await ctx.info(f"Signing certificate: name={name}, ca={ca_certificate}")

    cmd = f'/certificate sign [find name="{name}"] ca-certificate="{ca_certificate}"'

    if days_valid is not None:
        cmd += f" days-valid={days_valid}"

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to sign certificate: {result}"

    details_cmd = f'/certificate print detail where name="{name}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Certificate signed successfully:\n\n{details}"
    return f"Certificate '{name}' signed successfully."


@mcp.tool(name="export_certificate", annotations=annotate(READ, "Export Certificate"))
async def mikrotik_export_certificate(
    ctx: Context,
    name: str,
    file_name: str,
    export_type: Literal["pem", "pkcs12"] = "pem",
    export_passphrase: Optional[str] = None,
    return_file_content: bool = False,
) -> str:
    """Exports a certificate to a file on the MikroTik device.

    Notes:
        file_name: destination filename on the router (no path prefix)
        export_type: "pem" or "pkcs12"
        export_passphrase: required for pkcs12 exports
        return_file_content: if true, downloads the exported file via SFTP
    """
    await ctx.info(f"Exporting certificate: name={name}, file={file_name}")

    cmd = f'/certificate export-certificate [find name="{name}"] type={export_type} file="{file_name}"'

    if export_passphrase:
        cmd += f' export-passphrase="{export_passphrase}"'

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to export certificate: {result}"

    if not return_file_content:
        return f"Certificate '{name}' exported to '{file_name}' successfully."

    data, error = await download_file_from_router(file_name, ctx)
    if error:
        return f"Certificate exported to '{file_name}' but download failed: {error}"
    if not data:
        return f"Certificate exported to '{file_name}' but file content was empty."

    encoded = base64.b64encode(data).decode("utf-8")
    return (
        f"Certificate '{name}' exported to '{file_name}' successfully.\n\n"
        f"FILE_CONTENT_BASE64:{encoded}"
    )


@mcp.tool(name="import_certificate", annotations=annotate(WRITE, "Import Certificate"))
async def mikrotik_import_certificate(
    ctx: Context,
    file_name: str,
    passphrase: Optional[str] = None,
    content_base64: Optional[str] = None,
) -> str:
    """Imports a certificate file into the MikroTik device.

    Notes:
        file_name: certificate file on the router e.g. "cert.pem" or "cert.p12"
        The file must exist on the router before import — upload it first with
        upload_file, or pass content_base64 to upload automatically.
        passphrase: decryption passphrase for encrypted key/certificate files
    """
    await ctx.info(f"Importing certificate: file={file_name}")

    if content_base64:
        try:
            content = base64.b64decode(content_base64)
        except Exception as e:
            return f"Failed to decode file content: {str(e)}"

        error = await upload_file_to_router(file_name, content, ctx)
        if error:
            return error

    check_cmd = f"/file print count-only where name={file_name}"
    count = await execute_mikrotik_command(check_cmd, ctx)

    if count.strip() == "0":
        return (
            f"Certificate file '{file_name}' not found on the router. "
            "Upload the file first with upload_file or pass content_base64."
        )

    cmd = f'/certificate import file-name="{file_name}"'

    if passphrase:
        cmd += f' passphrase="{passphrase}"'

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to import certificate: {result}"

    if result.strip():
        return f"Certificate imported successfully:\n\n{result}"
    return f"Certificate from '{file_name}' imported successfully."


# ---------------------------------------------------------------------------
# Certificate Settings
# ---------------------------------------------------------------------------

@mcp.tool(name="get_certificate_settings", annotations=annotate(READ, "Certificate Settings"))
async def mikrotik_get_certificate_settings(ctx: Context) -> str:
    """Gets global certificate settings from the MikroTik device."""
    await ctx.info("Getting certificate settings")

    cmd = "/certificate settings print"
    result = await execute_mikrotik_command(cmd, ctx)

    if not result:
        return "Unable to retrieve certificate settings."

    return f"CERTIFICATE SETTINGS:\n\n{result}"


@mcp.tool(name="set_certificate_settings", annotations=annotate(WRITE_IDEMPOTENT, "Set Certificate Settings"))
async def mikrotik_set_certificate_settings(
    ctx: Context,
    crl_use: Optional[bool] = None,
    crl_download: Optional[bool] = None,
    crl_fetch_interval: Optional[str] = None,
    trusted_certs: Optional[Literal["all", "none", "trusted"]] = None,
) -> str:
    """Sets global certificate settings on the MikroTik device.

    Notes:
        crl_fetch_interval: duration string e.g. "1d", "12h"
        trusted_certs: builtin trusted certificate policy
    """
    await ctx.info("Setting certificate settings")

    updates = []
    if crl_use is not None:
        updates.append(f'crl-use={"yes" if crl_use else "no"}')
    if crl_download is not None:
        updates.append(f'crl-download={"yes" if crl_download else "no"}')
    if crl_fetch_interval is not None:
        updates.append(f"crl-fetch-interval={crl_fetch_interval}")
    if trusted_certs is not None:
        updates.append(f"trusted-certs={trusted_certs}")

    if not updates:
        return "No updates specified."

    cmd = "/certificate settings set " + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to update certificate settings: {result}"

    details = await execute_mikrotik_command("/certificate settings print", ctx)
    return f"Certificate settings updated successfully:\n\n{details}"


# ---------------------------------------------------------------------------
# Service Certificate Assignment
# ---------------------------------------------------------------------------

@mcp.tool(name="assign_service_certificate", annotations=annotate(WRITE_IDEMPOTENT, "Assign Service Certificate"))
async def mikrotik_assign_service_certificate(
    ctx: Context,
    service: str,
    certificate: str,
) -> str:
    """Assigns a certificate to an IP service (sets /ip service certificate=).

    Notes:
        service: IP service name e.g. "www-ssl", "api-ssl", "www", "api", "winbox"
        certificate: certificate name, or "" to clear the assignment
    """
    await ctx.info(f"Assigning certificate to service: service={service}, certificate={certificate}")

    if certificate == "":
        cmd = f'/ip service set [find name="{service}"] !certificate'
    else:
        cmd = f'/ip service set [find name="{service}"] certificate="{certificate}"'

    result = await execute_mikrotik_command(cmd, ctx)

    if "failure:" in result.lower() or "error" in result.lower():
        return f"Failed to assign certificate to service: {result}"

    details_cmd = f'/ip service print detail where name="{service}"'
    details = await execute_mikrotik_command(details_cmd, ctx)

    if details.strip():
        return f"Service certificate assigned successfully:\n\n{details}"
    return f"Certificate '{certificate}' assigned to service '{service}' successfully."
