# Expert-Service Sprint — Citation Quality, Chat UI, Langfuse Observability

**Date:** 2026-05-12
**Time:** 10:30

## Summary

Major quality and observability sprint across expert-service and expert CLI. The system went from producing hallucinated references and unreadable streaming output to clean, verified, cost-tracked answers across three model tiers.

## What Was Done

### 1. Citation Hallucination Stripping (expert-service + expert CLI)

LLMs — especially smaller models like Gemma3 — fabricate reference citations. `[5]`, `[2, 7]`, `[ec2-pay-per-instance-second]` would appear in answers pointing to nonexistent sources.

**Fix:** Post-processing validates every `[bracketed]` reference against the set of valid keys from the retrieval step. Invalid refs are removed entirely (not just de-bracketed — the content was meaningless without the reference). Applied in both:
- Server-side: `_strip_hallucinated_refs()` in `chat/loop.py`, runs on `dual_ask` and `dual_chat_stream`
- Client-side: `clean_refs()` in `expert_cli/synthesis.py`, runs on `ask-local`

A programmatic Sources/Beliefs section is appended after stripping, built from the actual retrieval metadata rather than trusting the LLM to format it.

### 2. Chat UI Overhaul (expert-service web)

- **Switched from streaming SSE to non-streaming `/ask`.** Streaming looked cool but rendered raw markdown — unreadable in practice. Non-streaming allows full post-processing (hallucination stripping, source section building) before display, then renders via marked.js.
- **Clickable citation scroll links.** `[7]` in an answer becomes a link that smooth-scrolls to the corresponding source entry at the bottom. IDs are scoped per message (`ref-{msgId}-{N}`) to avoid collisions across multiple chat turns.
- **Source verification panel.** "Verify Sources" button fetches each cited belief/entry/source from the API and shows checkmarks (found, IN) or warnings (OUT, not found). Includes an inline "Why?" button that sends an explain query.
- **Tightened citation extraction regex.** Source refs now only match inside `[Source: slug]` brackets to avoid false positives from labels like "network" being treated as belief IDs.

### 3. Connector Short-Circuit Fix

"Who is jboyer?" returned nothing despite Snowflake being configured. Root cause: `_tms_answer_iterative` returned early on empty beliefs before the LLM could see the `query_data` tool. Fix: only short-circuit when no connectors are available; pass placeholder text when beliefs are empty but connectors exist.

### 4. Error Handling for Missing Beliefs

`/beliefs/{node_id}` and `/beliefs/{node_id}/explain` were returning 500 on KeyError when a belief ID didn't exist. Now returns `{"error": "Belief not found", "id": "..."}`.

### 5. SQLite FTS5 OR Queries

Multi-word queries like "Can I run OpenShift on AWS?" returned zero results on SQLite. FTS5 treats spaces as implicit AND. Fix: strip stop words via `_get_terms()`, join with `" OR "` for the MATCH clause.

### 6. /api/version Endpoint

Authenticated endpoint returning `{"version": "0.2.0", "git_hash": "2da23d6"}`. Git hash baked into wheel at build time via hatch build hook (`hatch_build.py`), with `finalize()` to restore source after build.

### 7. Expert CLI Enhancements

- `expert deep-search` — raw retrieval output (beliefs + source chunks) without LLM synthesis
- `expert ask-local` — now shows `[model: X]` on stderr, strips hallucinated refs, appends programmatic sources section
- Both `clean_refs()` and `build_sources_section()` available for any client-side synthesis pipeline

### 8. Langfuse Integration

Added `_langfuse_config()` helper wired into all 6 LLM calls in the dual-path pipeline. First real measurements:

| Model | Tokens/Query | Cost/Query |
|-------|-------------|------------|
| Opus 4.6 | ~10k | ~$0.36 |
| Sonnet 4.6 | ~12k | ~$0.07 |
| Gemma3 27B | ~5.4k | $0.00 |

Key insight: expert-service uses **10k tokens per query vs 300k in agents-python** — a 30x reduction from moving retrieval out of the LLM loop.

## Architecture Validation

This sprint validated the core thesis: expensive LLM reasoning happens once at build time (source analysis → belief derivation → contradiction resolution → reasons.db). Query time is just FTS lookup + 3 synthesis calls. The result is fast, cheap, and auditable — every claim traces back to a belief or source chunk, and hallucinated references are caught in post-processing.

## Commits

**expert-service:**
- `c5e7d1c` — Langfuse integration for dual-path LLM calls
- `a9d1d24` — Citation stripping, non-streaming chat UI, connector fix
- `4c9fd54` — /api/version endpoint, SQLite FTS5 OR queries

**expert CLI:**
- `7d3766c` — deep-search command, citation post-processing, model display
- `f3a5643` — ask-local command, deep_search MCP tool
