# MikroTik MCP Server — Limitations

Server: `user-mikrotik-mcp` ([mcp-server-mikrotik](https://github.com/jeff-nasseri/mikrotik-mcp))  
Transport: SSH (not REST). **~317 tools** across 29 scope modules.

This document summarizes remaining constraints and operational caveats.

## Resolved (previously missing)

The following RouterOS areas now have full MCP tool coverage:

| Area | Scope module | Example tools |
|------|--------------|---------------|
| **Packages** | `packages.py` | `list_packages`, `enable_package`, `apply_package_changes` |
| **Containers** | `containers.py` | `create_container`, `start_container`, `list_container_mounts` |
| **Device mode** | `device_mode.py` | `get_device_mode`, `update_device_mode` |
| **Certificates** | `certificates.py` | `create_certificate`, `sign_certificate`, `export_certificate` |
| **System** | `system.py` | `reboot_system`, `shutdown_system`, `check_for_updates` |
| **Scheduler / scripts** | `scheduler.py` | `create_scheduler`, `run_script` |
| **Hotspot** | `hotspot.py` | `create_hotspot_server`, `add_hotspot_user` |
| **PPP** | `ppp.py` | `create_ppp_profile`, `add_ppp_secret` |
| **VPN (OVPN/IPsec)** | `vpn.py` | `create_ovpn_server`, `add_ipsec_peer` |
| **Bridge / bonding** | `bridge.py` | `create_bridge`, `add_bridge_port`, `create_bonding` |
| **SNMP / graphing** | `snmp.py` | `get_snmp_settings`, `set_graphing_interface` |
| **Email / SMS** | `messaging.py` | `send_test_email`, `send_sms` |

Previously stubbed tools are now implemented:

- **`upload_file` / `download_file`** — SFTP transfer via Paramiko (not CLI text hack)
- **`monitor_logs`** — polls log buffer over the requested duration (max 60s)
- **Enable/disable wrappers** — fixed positional-arg bugs in filter/NAT/route/DNS/user tools

## Operational constraints

| Constraint | Detail |
|------------|--------|
| **SSH permissions** | User needs `write` or `full` group; group changes require reboot |
| **Safe Mode** | Optional for firewall/routes; changes held in memory until `commit_safe_mode` |
| **Rule ordering** | Firewall/NAT updates need `move_filter_rule` / `move_nat_rule`; order matters |
| **IDs not names** | Update/remove tools require `.id` from list output (`*1`, `*A`) |
| **Physical confirm** | Device-mode changes (container, etc.) need reset button or power-cycle |
| **Package apply** | `apply_package_changes` reboots the router; polls SSH until back (120s default) |
| **Command timeouts** | Long-running commands (device-mode, updates) use extended timeouts; may still block |
| **Connection config** | Credentials in `~/.cursor/mcp.json` |

## Commands that hang over SSH

These block the SSH session until timeout or user action:

- `/system device-mode update container=yes` — waits for physical confirmation (~5 min window)
- Some interactive prompts if RouterOS expects terminal input

Tools pass extended timeouts and return clear messages when physical steps are required.

## What MCP is not

- **Not a full RouterOS CLI** — only registered tools; no arbitrary command execution
- **Not Winbox** — no GUI automation
- **Not real-time log streaming** — `monitor_logs` polls; does not attach a persistent follow session

## Wireless v6 legacy

RouterOS v7.x WiFi (`/interface wifi`, `/interface wifiwave2`) does not use legacy security profiles or access lists. Tools named `*_wireless_security_profile` and `*_wireless_access_list` return guidance messages on v7 devices.

## Observed during testing (RouterOS 7.x)

- Container package install requires `enable_package` + `apply_package_changes` (reboot)
- Device-mode `container=yes` still requires physical reset (SSH and REST both trigger it)
- `upload_file` + `import_configuration` now works via SFTP upload
