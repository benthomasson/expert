# expert

CLI client for [expert-service](https://github.com/benthomasson/expert-service) — ask questions, search beliefs, and query domain knowledge bases from the terminal or Claude Code.

## Run Without Installing

```bash
uvx --from git+https://github.com/benthomasson/expert expert ask "Who is Ben Thomasson?"
```

## Install

```bash
pip install git+https://github.com/benthomasson/expert.git
```

Or with uv:

```bash
uv tool install git+https://github.com/benthomasson/expert.git
```

## Quick Start

```bash
# Create config
expert init
# Edit ~/.config/expert/config.toml with your settings

# Authenticate
expert login

# Query
expert ask "What are the delivery risks for AAP?"
expert search "pipeline"
expert projects
```

## Configuration

Config file: `~/.config/expert/config.toml`

```toml
url = "http://localhost:8000"
project = "redhat-expert"
google_client_id = "your-id.apps.googleusercontent.com"
google_client_secret = "your-secret"
```

Environment variables override config file values, CLI flags override both:

| Config Key | Environment Variable | Description |
|---|---|---|
| `url` | `EXPERT_URL` | expert-service base URL |
| `api_key` | `EXPERT_API_KEY` | Static API key (alternative to OAuth) |
| `project` | `EXPERT_PROJECT` | Default project name |
| `google_client_id` | `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `google_client_secret` | `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |

## Commands

### `expert ask <question>`

Ask a question and get a complete answer. Uses dual-path retrieval (TMS beliefs + full-text search) plus any configured data connectors (Snowflake, Dataverse).

```bash
expert ask "Who is Ben Thomasson?"
expert ask "What is the current headcount?" --project redhat-expert
expert ask "Explain the TMS architecture" --project ftl-reasons-expert --model claude-sonnet-4-6
```

### `expert search <query>`

Keyword search over beliefs and entries. No LLM involved — fast full-text search.

```bash
expert search "pipeline risks"
expert search "contradiction" --project meta-expert
```

### `expert chat <message>`

Streaming chat response. Same as `ask` but streams tokens as they arrive.

```bash
expert chat "Summarize the product strategy"
```

### `expert projects`

List all available projects with belief, entry, and source counts.

### `expert login`

Authenticate via Google OAuth. Opens a browser, exchanges an auth code via localhost callback, and caches the token at `~/.config/expert/token.json`. Tokens auto-refresh on subsequent calls.

```bash
expert login
expert login --port 9090
```

### `expert logout`

Clear cached OAuth credentials.

### `expert status`

Show current authentication state, service URL, and default project.

### `expert init`

Create a default config file at `~/.config/expert/config.toml`.

## Authentication

Two authentication methods:

1. **Google OAuth** (recommended) — run `expert login`, tokens are cached and auto-refreshed. Provides per-user identity and RBAC via expert-service's user table.

2. **Static API key** — set `api_key` in config or `EXPERT_API_KEY` env var. Grants admin access. Useful for scripts and CI.

## Claude Code Skill

Install the `/expert` skill for use in Claude Code sessions:

```bash
expert install-skill
```

Then in Claude Code:

```
/expert ask what are the key risks for Q3?
/expert search pipeline
/expert projects
```

## Architecture

```
Claude Code / Terminal
       |
   expert CLI (httpx)
       |
expert-service (FastAPI)
  +-- TMS beliefs (PostgreSQL)
  +-- FTS sources (tsvector)
  +-- Connectors
       +-- Snowflake (live business data)
       +-- Dataverse (live business data)
       +-- PageIndex (document retrieval)
```

## License

MIT
