---
name: expert
description: Query expert-service knowledge bases — ask questions, search beliefs, list projects
argument-hint: "[ask|search|chat|projects|login|status] [args...]"
allowed-tools: Bash(expert *), Bash(uvx *expert*), Read
---

You are querying expert-service knowledge bases using the `expert` CLI tool. Expert-service is a domain expert system backed by a Truth Maintenance System (TMS) for beliefs and full-text search over source documents.

## Why Use This Tool

Expert-service maintains curated knowledge bases with:
- **TMS beliefs** — facts with truth values (IN/OUT), justifications, and retraction cascades
- **Source documents** — chunked and indexed for full-text search with IDF-weighted re-ranking
- **Live data connectors** — Snowflake, Dataverse for current business data

The `expert` CLI is a thin HTTP client that connects to a running expert-service instance. It handles authentication (Google OAuth or API key) and project resolution automatically.

## How to Run

Try these in order until one works:
1. `expert $ARGUMENTS` (if installed via uv/pip)
2. `uvx --from git+https://github.com/benthomasson/expert expert $ARGUMENTS` (fallback)

## Setup

```bash
expert init                    # creates ~/.config/expert/config.toml
expert login                   # Google OAuth browser login
```

Config file (`~/.config/expert/config.toml`):
```toml
url = "http://localhost:8000"
project = "redhat-expert"
google_client_id = "your-id.apps.googleusercontent.com"
google_client_secret = "your-secret"
```

## Subcommand Behavior

### `ask <question> [--project NAME] [--model MODEL]`
Ask a question and get a complete answer. Uses dual-path retrieval (TMS beliefs + FTS source search) plus any configured data connectors. Returns the full answer text.

Convert natural language to CLI arguments:
- `/expert what are the delivery risks for AAP?` → `expert ask "What are the delivery risks for AAP?"`
- `/expert who is Ben Thomasson` → `expert ask "Who is Ben Thomasson?"`
- `/expert search pipeline risks` → `expert search "pipeline risks"`

```bash
expert ask "What is the current headcount for Platform Engineering?"
expert ask "What are the key risks for Q3?" --project redhat-expert
expert ask "Explain the TMS architecture" --project ftl-reasons-expert
```

### `search <query> [--project NAME]`
Search beliefs and entries by keyword. Returns matching beliefs (with IN/OUT status) and entry titles. Faster than `ask` — no LLM involved, just full-text search.

```bash
expert search "pipeline" --project redhat-expert
expert search "contradiction"
```

### `chat <message> [--project NAME] [--model MODEL]`
Stream a chat response. Same as `ask` but streams tokens as they arrive. Better for long answers.

```bash
expert chat "Summarize the product strategy"
```

### `projects`
List all available projects with belief/entry/source counts.

```bash
expert projects
```

### `login [--port PORT]`
Authenticate via Google OAuth. Opens a browser, caches the token at `~/.config/expert/token.json`. Auto-refreshes on subsequent calls.

### `logout`
Clear cached credentials.

### `status`
Show current authentication state, URL, and default project.

### `init`
Create a default config file at `~/.config/expert/config.toml`.

## When to Use Which Command

| Need | Command |
|------|---------|
| Answer a question with reasoning | `expert ask "..."` |
| Find beliefs/entries by keyword | `expert search "..."` |
| Long answer with streaming | `expert chat "..."` |
| See what projects exist | `expert projects` |
| Check auth is working | `expert status` |

## After Any Command

- If the command returned results, summarize them concisely
- If `ask` returned an answer, present it to the user — don't just say "the answer was returned"
- If `search` returned beliefs, note which are IN vs OUT
- If authentication fails, suggest `expert login`
- Keep responses concise — the tool output speaks for itself
