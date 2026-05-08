# Expert CLI and Skill End-to-End Milestone

**Date:** 2026-05-08
**Time:** 18:11

## Summary

The `expert` CLI client and Claude Code skill are working end-to-end. A user can install the CLI, authenticate via Google OAuth, and query expert-service knowledge bases from any terminal or Claude Code session.

## What Was Built

### expert CLI (~/git/expert)

Thin HTTP client for expert-service. Only dependency is httpx.

- `expert ask` — non-streaming question answering via dual-path retrieval (TMS beliefs + FTS) plus data connectors (Snowflake, Dataverse)
- `expert search` — keyword search over beliefs and entries
- `expert chat` — streaming chat responses
- `expert projects` — list available knowledge bases
- `expert login` — Google OAuth browser flow with PKCE, localhost callback, token caching
- `expert logout` / `expert status` — credential management
- `expert init` — create ~/.config/expert/config.toml
- `expert install-skill` — install Claude Code skill

### Config (~/.config/expert/config.toml)

Simple TOML config with url, project, google_client_id, google_client_secret. Environment variables override config. CLI flags override both.

### Google OAuth for CLI (expert-service side)

Added Google ID token verification as a new auth path in verify_auth(). The auth chain is now:

1. Static API key (Bearer token matching EXPERT_SERVICE_API_KEY)
2. Google ID token (verified via Google tokeninfo endpoint, email looked up in users table for RBAC)
3. OAuth session cookie (browser)
4. Dev mode bypass (when GOOGLE_CLIENT_ID unset)

This gives CLI users per-user identity and role-based access control, not just a shared API key.

### Claude Code Skill

SKILL.md enables /expert slash command in Claude Code sessions.

## End-to-End Verification

Successfully ran `/expert ask "Who is Ben Thomasson?"` from Claude Code. The request flowed:

1. Claude Code invoked the expert skill
2. expert CLI loaded config from ~/.config/expert/config.toml
3. Authenticated via cached Google OAuth ID token
4. Resolved project name "redhat-expert" to UUID
5. POST to expert-service /api/projects/{id}/ask
6. expert-service ran dual-path search (TMS beliefs + FTS sources)
7. Snowflake connector queried live employee directory
8. Response returned: Senior Principal Software Engineer, Engineering, Red Hat

## Architecture

```
Claude Code -> /expert skill -> expert CLI (httpx)
                                    |
                           expert-service (FastAPI)
                            +-- TMS beliefs (PostgreSQL)
                            +-- FTS sources (tsvector)
                            +-- Connectors
                                 +-- Snowflake (live data)
                                 +-- Dataverse (business data)
                                 +-- PageIndex (document retrieval, planned)
```

## Repos

- github.com/benthomasson/expert — CLI client + skill
- github.com/benthomasson/expert-service — main service
- github.com/benthomasson/expert-pageindex — PageIndex connector (scaffold)
- github.com/benthomasson/expert-snowflake — Snowflake connector
- github.com/benthomasson/expert-dataverse — Dataverse connector

