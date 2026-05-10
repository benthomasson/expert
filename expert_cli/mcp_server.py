"""MCP server for expert-service — exposes knowledge base tools directly.

Lets the user's LLM call expert-service tools without going through
expert-service's own LLM. Zero token cost, millisecond latency.
"""

import json

from mcp.server.fastmcp import FastMCP

from . import client

mcp = FastMCP("expert")


def _resolve(project: str) -> str:
    """Resolve project name to UUID."""
    return client.resolve_project(project)


@mcp.tool()
def search(query: str, project: str = "") -> str:
    """Search across beliefs, entries, and source documents.

    Returns matching beliefs (with IN/OUT truth values), entry titles,
    and source chunk snippets. Uses full-text search with stop-word
    filtering and term extraction.
    """
    project_id = _resolve(project or _default_project())
    result = client.search(project_id, query)
    return json.dumps(result, indent=2)


@mcp.tool()
def explain_belief(node_id: str, project: str = "") -> str:
    """Explain why a belief is IN or OUT.

    Traces the justification chain: what supports this belief,
    what assumptions it rests on, and what would change if it
    were retracted.
    """
    project_id = _resolve(project or _default_project())
    belief = client.get_belief(project_id, node_id)
    explanation = client.explain(project_id, node_id)
    return json.dumps({"belief": belief, "explanation": explanation}, indent=2)


@mcp.tool()
def what_if(node_id: str, action: str = "retract", project: str = "") -> str:
    """Simulate retracting or asserting a belief without modifying the database.

    Shows the cascade: which beliefs would go OUT (retract) or come back IN
    (assert). Use this to understand the impact of changing a belief.

    Args:
        node_id: The belief ID to simulate
        action: "retract" or "assert"
        project: Project name (uses default if empty)
    """
    project_id = _resolve(project or _default_project())
    result = client.what_if(project_id, node_id, action)
    return json.dumps(result, indent=2)


@mcp.tool()
def list_beliefs(status: str = "", project: str = "") -> str:
    """List beliefs in the knowledge base.

    Args:
        status: Filter by truth value — "IN", "OUT", or empty for all
        project: Project name (uses default if empty)
    """
    project_id = _resolve(project or _default_project())
    result = client.list_beliefs(project_id, status=status or None)
    return json.dumps(result, indent=2)


@mcp.tool()
def get_belief(node_id: str, project: str = "") -> str:
    """Get full details for a specific belief including justifications and dependents."""
    project_id = _resolve(project or _default_project())
    result = client.get_belief(project_id, node_id)
    return json.dumps(result, indent=2)


@mcp.tool()
def list_entries(topic: str = "", project: str = "") -> str:
    """List analysis entries (reports, findings, assessments).

    Args:
        topic: Filter by topic slug, or empty for all entries
        project: Project name (uses default if empty)
    """
    project_id = _resolve(project or _default_project())
    result = client.list_entries(project_id, topic=topic or None)
    return json.dumps(result, indent=2)


@mcp.tool()
def get_entry(entry_id: str, project: str = "") -> str:
    """Read the full content of an analysis entry."""
    project_id = _resolve(project or _default_project())
    result = client.get_entry(project_id, entry_id)
    return json.dumps(result, indent=2)


@mcp.tool()
def list_projects() -> str:
    """List all available expert knowledge bases with belief/entry/source counts."""
    result = client.list_projects()
    return json.dumps(result, indent=2)


def _default_project() -> str:
    """Get the default project from config."""
    config = client._get_config()
    project = config.get("project", "")
    if not project:
        raise ValueError("No default project configured. Pass project= or set EXPERT_PROJECT.")
    return project


def main():
    """Entry point for the MCP server."""
    mcp.run()
