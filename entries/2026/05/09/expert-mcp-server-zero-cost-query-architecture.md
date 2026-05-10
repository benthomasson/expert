# Expert MCP Server — Zero-Cost Query Architecture

**Date:** 2026-05-09
**Time:** 20:07

## Summary

Built an MCP server for expert-service that eliminates all server-side LLM calls at query time. The user's own LLM (Claude Code, etc.) calls expert-service tools directly via MCP, gets structured data back in milliseconds, and does its own synthesis. Token cost on expert-service drops from ~300k tokens per query to zero.

## The Insight

Expert-service was running LLM calls at query time to synthesize answers from search results. But if the caller is already an LLM (Claude Code, a chat agent, any MCP client), that synthesis is redundant — the calling LLM will process the answer anyway. By exposing the search and retrieval tools directly, we eliminate the double-LLM tax.

## What Was Built

### expert MCP server (~/git/expert)

Added to the existing expert CLI package. 8 tools exposed via FastMCP over stdio:

- `search` — FTS across beliefs, entries, source chunks
- `explain_belief` — Justification chain (why IN/OUT)
- `what_if` — Simulate retract/assert cascade
- `list_beliefs` — All beliefs, filterable by IN/OUT
- `get_belief` — Full belief details with justifications
- `list_entries` — Analysis entries/reports
- `get_entry` — Read entry content
- `list_projects` — Available knowledge bases

Each tool calls expert-service HTTP endpoints via the existing httpx client. The MCP server handles auth (API key or Google OAuth) and project resolution automatically.

### Installation

```bash
uv tool install git+https://github.com/benthomasson/expert
claude mcp add expert -s user -- expert mcp
```

### New client functions

Added to expert_cli/client.py: `what_if()`, `list_beliefs()`, `list_entries()`, `get_entry()` — these were missing from the HTTP client and needed for the MCP tools.

## Architecture Shift

### Before (server-side LLM)
```
User's LLM -> expert ask -> expert-service LLM (300k tokens) -> synthesized answer -> User's LLM
Latency: 15-30s per query
Cost: ~300k tokens per query on expert-service
```

### After (client-side LLM)
```
User's LLM -> MCP tool call -> expert-service FTS -> structured data -> User's LLM synthesizes
Latency: ~50ms for tool call, total depends on user's LLM
Cost: 0 tokens on expert-service
```

## Why This Works

The entire intelligence pipeline has been moved to pre-request time:

1. **Build time** (agents-python, runs once): LLM analyzes sources, derives beliefs, resolves contradictions, produces reasons.db
2. **Import time** (one-time): `expert import-reasons` loads beliefs into expert-service with FTS indexing
3. **Query time** (every request): FTS lookup + access tag filter -> structured data -> user's LLM presents

All expensive LLM reasoning happens once during the analysis phase. The knowledge base is a compiled artifact — like compiling source code once and running the binary forever. Every subsequent query is a database lookup.

Access control is also pre-computed: beliefs get `access_tags` at build time, and query-time filtering is a set intersection in the WHERE clause. No runtime LLM needed for PII or security checks.

## Performance

- **Token cost**: 300k -> 0 per query (infinite improvement)
- **Tool call latency**: ~50ms (vs 15-30s for server-side LLM)
- **Concurrency**: Every user's LLM synthesizes in parallel — no shared LLM bottleneck
- **Scaling**: The service becomes a pure data layer, horizontally scalable

## Key Files

- `expert_cli/mcp_server.py` — FastMCP server with 8 tools
- `expert_cli/client.py` — HTTP client (added what_if, list_beliefs, list_entries, get_entry)
- `expert_cli/cli.py` — Added `expert mcp` command
- `pyproject.toml` — Added mcp[cli] dependency, expert-mcp entry point
