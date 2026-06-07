from typing import Literal, Optional

from mcp.server.fastmcp import Context

from ..app import mcp, READ, WRITE, annotate
from ..connector import execute_mikrotik_command


@mcp.tool(name="get_email_settings", annotations=annotate(READ, "Email Settings"))
async def mikrotik_get_email_settings(ctx: Context) -> str:
    """Gets RouterOS email (SMTP) tool configuration."""
    await ctx.info("Getting email settings")

    cmd = "/tool e-mail print"
    result = await execute_mikrotik_command(cmd, ctx)

    if not result:
        return "Unable to retrieve email settings."

    return f"EMAIL SETTINGS:\n\n{result}"


@mcp.tool(name="set_email_settings", annotations=annotate(WRITE, "Set Email Settings"))
async def mikrotik_set_email_settings(
    ctx: Context,
    address: Optional[str] = None,
    from_address: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    port: Optional[int] = None,
    start_tls: Optional[Literal["none", "yes", "tls-only"]] = None,
) -> str:
    """Sets RouterOS email (SMTP) tool configuration."""
    await ctx.info("Setting email configuration")

    updates = []
    if address is not None:
        updates.append(f'address="{address}"')
    if from_address is not None:
        updates.append(f'from="{from_address}"')
    if user is not None:
        updates.append(f'user="{user}"')
    if password is not None:
        updates.append(f'password="{password}"')
    if port is not None:
        updates.append(f"port={port}")
    if start_tls is not None:
        updates.append(f"start-tls={start_tls}")

    if not updates:
        return "No updates specified."

    cmd = "/tool e-mail set " + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if result.strip() and "failure:" in result.lower():
        return f"Failed to update email settings: {result}"

    details = await execute_mikrotik_command("/tool e-mail print", ctx)
    return f"Email settings updated successfully:\n\n{details}"


@mcp.tool(name="send_test_email", annotations=annotate(WRITE, "Send Test Email"))
async def mikrotik_send_test_email(
    ctx: Context,
    to: str,
    subject: str = "MikroTik test email",
    body: str = "This is a test email from MikroTik.",
) -> str:
    """Sends a test email using the configured SMTP settings."""
    await ctx.info(f"Sending test email to: {to}")

    cmd = f'/tool e-mail send to="{to}" subject="{subject}" body="{body}"'
    result = await execute_mikrotik_command(cmd, ctx)

    if result.strip() and "failure:" in result.lower():
        return f"Failed to send test email: {result}"

    if not result.strip():
        return f"Test email sent to '{to}' successfully."
    return f"Test email result:\n{result}"


@mcp.tool(name="get_sms_settings", annotations=annotate(READ, "SMS Settings"))
async def mikrotik_get_sms_settings(ctx: Context) -> str:
    """Gets RouterOS SMS tool configuration."""
    await ctx.info("Getting SMS settings")

    cmd = "/tool sms print"
    result = await execute_mikrotik_command(cmd, ctx)

    if not result:
        return "Unable to retrieve SMS settings."

    return f"SMS SETTINGS:\n\n{result}"


@mcp.tool(name="set_sms_settings", annotations=annotate(WRITE, "Set SMS Settings"))
async def mikrotik_set_sms_settings(
    ctx: Context,
    port: Optional[str] = None,
    channel: Optional[int] = None,
    secret: Optional[str] = None,
) -> str:
    """Sets RouterOS SMS tool configuration."""
    await ctx.info("Setting SMS configuration")

    updates = []
    if port is not None:
        updates.append(f"port={port}")
    if channel is not None:
        updates.append(f"channel={channel}")
    if secret is not None:
        updates.append(f'secret="{secret}"')

    if not updates:
        return "No updates specified."

    cmd = "/tool sms set " + " ".join(updates)
    result = await execute_mikrotik_command(cmd, ctx)

    if result.strip() and "failure:" in result.lower():
        return f"Failed to update SMS settings: {result}"

    details = await execute_mikrotik_command("/tool sms print", ctx)
    return f"SMS settings updated successfully:\n\n{details}"


@mcp.tool(name="send_sms", annotations=annotate(WRITE, "Send SMS"))
async def mikrotik_send_sms(
    ctx: Context,
    phone_number: str,
    message: str,
) -> str:
    """Sends an SMS message using the configured SMS tool."""
    await ctx.info(f"Sending SMS to: {phone_number}")

    cmd = f'/tool sms send phone-number="{phone_number}" message="{message}"'
    result = await execute_mikrotik_command(cmd, ctx)

    if result.strip() and "failure:" in result.lower():
        return f"Failed to send SMS: {result}"

    if not result.strip():
        return f"SMS sent to '{phone_number}' successfully."
    return f"SMS send result:\n{result}"
