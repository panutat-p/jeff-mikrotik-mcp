# Context Length Optimization

MikroTik MCP ships **281 tools** (down from 318 after consolidating read
pairs). At full verbosity the tool schema can occupy a large share of the
context window for local LLMs (LM Studio, Ollama, etc.).

Two complementary strategies reduce prompt bloat:

1. **`title` annotations** (MCP spec 2025-03-26) plus trimmed descriptions
2. **`query_X` tool consolidation** — one read tool per resource instead of
   separate `list_X` + `get_X` pairs

---

## What changed

### 1. `title` in `ToolAnnotations`

Every `@mcp.tool()` call passes `annotations=annotate(READ|WRITE|…, "Short Title")`.

```python
# before
@mcp.tool(name="create_queue_type", annotations=WRITE)

# after
@mcp.tool(name="create_queue_type", annotations=annotate(WRITE, "Create Queue Type"))
```

The `title` field is part of the [MCP Tool Annotations spec][spec].  
MCP clients that support it can display a compact tool list using only the
title — without rendering the full description text — significantly shrinking
the prompt context they pass to the LLM.

### 2. Trimmed descriptions

Verbose multi-paragraph docstrings with redundant `Args:` / `Returns:`
sections have been replaced by concise one-liners.  The function signature
already carries full type information; the description only needs to convey
*what* the tool does.

Estimated description-token savings from trimming: **≈ 75 % reduction** on
per-tool description text.

### 3. Tool consolidation (`query_X`)

Thirty-five `list_X` / `get_X` pairs were merged into single **`query_X`**
tools, removing **35 tools** from the MCP surface (318 → **281**).

| Pattern | Example | Behaviour |
|---------|---------|-----------|
| Name-based detail | `query_schedulers` | Omit `name` → list with filters; set `name` → `print detail where name=…` |
| ID-based detail | `query_filter_rules` | Omit `rule_id` → list; set `rule_id` → `print detail where .id=…` |
| Singleton config | `query_container_config` | Default → summary print; `detail=true` → detailed print |

```python
# List schedulers matching a filter
query_schedulers(name_filter="backup")

# Get one scheduler by exact name
query_schedulers(name="daily-backup")

# Get a firewall rule by .id from list output
query_filter_rules(rule_id="*3")
```

**Why this helps:** Fewer similarly-named tools means less LLM confusion when
choosing between `list_users` vs `get_user`. One `query_users` covers both
discovery and detail views with the same parameter schema.

Singleton reads (`get_dns_settings`, `get_system_resource`, `get_poe_monitor`,
etc.) and list-only tools (`list_backups`, `list_hotspot_active`, …) were
left unchanged.

---

## How to benefit

### MCP clients that use `title`

Any client following the MCP spec can read `tool.annotations.title` and show
that short string in its tool list rather than the full description.  If you
are building an integration, prefer displaying the title in compact views.

### Local LLMs with small context windows

Trimmed descriptions and fewer tools both reduce tokens consumed at MCP
initialisation. After consolidation the tool count dropped by **~11 %**
(35 fewer schemas in the tool list).

> **Further reduction:** If you only need a subset of tools (e.g. only DNS
> and WireGuard), comment out the unused scope imports in
> `src/mcp_mikrotik/app.py` to drop those tools entirely.

---

## Developer notes

The `annotate()` helper lives in `src/mcp_mikrotik/app.py`:

```python
def annotate(base: ToolAnnotations, title: str) -> ToolAnnotations:
    """Return a copy of *base* with a human-readable *title* attached."""
    return ToolAnnotations(
        title=title,
        readOnlyHint=base.readOnlyHint,
        destructiveHint=base.destructiveHint,
        idempotentHint=base.idempotentHint,
        openWorldHint=base.openWorldHint,
    )
```

When adding new read tools, prefer a single **`query_<resource>`** with an
optional identity parameter (`name`, `rule_id`, etc.) instead of separate
list and get tools:

```python
# ✅ preferred — one tool for list and detail
@mcp.tool(name="query_schedulers", annotations=annotate(READ, "Query Schedulers"))
async def mikrotik_query_schedulers(ctx, name: Optional[str] = None, ...): ...

# ❌ avoid — doubles the tool count for the same RouterOS path
@mcp.tool(name="list_schedulers", ...)
@mcp.tool(name="get_scheduler", ...)
```

Always use `annotate()` instead of a bare annotation constant:

```python
# ✅ correct
@mcp.tool(name="my_new_tool", annotations=annotate(READ, "My New Tool"))

# ❌ avoid — omits the title
@mcp.tool(name="my_new_tool", annotations=READ)
```

[spec]: https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/
