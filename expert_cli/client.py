"""HTTP client for expert-service API."""

import os

import httpx


DEFAULT_URL = "http://localhost:8000"
TIMEOUT = 120.0


def _base_url() -> str:
    return os.environ.get("EXPERT_URL", DEFAULT_URL).rstrip("/")


def _headers() -> dict[str, str]:
    headers = {}
    api_key = os.environ.get("EXPERT_API_KEY", "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def list_projects() -> list[dict]:
    """List all projects."""
    resp = httpx.get(
        f"{_base_url()}/api/projects",
        headers=_headers(),
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def resolve_project(name_or_id: str) -> str:
    """Resolve a project name to its UUID. Returns the ID if already a UUID."""
    # If it looks like a UUID, use it directly
    if len(name_or_id) == 36 and name_or_id.count("-") == 4:
        return name_or_id

    projects = list_projects()
    for p in projects:
        if p["name"] == name_or_id:
            return p["id"]

    # Partial match
    matches = [p for p in projects if name_or_id.lower() in p["name"].lower()]
    if len(matches) == 1:
        return matches[0]["id"]
    if len(matches) > 1:
        names = [m["name"] for m in matches]
        raise ValueError(f"Ambiguous project name '{name_or_id}': {names}")

    available = [p["name"] for p in projects]
    raise ValueError(f"Project '{name_or_id}' not found. Available: {available}")


def ask(project_id: str, question: str, model: str | None = None) -> dict:
    """Ask a question (non-streaming, returns complete answer)."""
    body = {"question": question}
    if model:
        body["model"] = model
    resp = httpx.post(
        f"{_base_url()}/api/projects/{project_id}/ask",
        json=body,
        headers=_headers(),
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def search(project_id: str, query: str) -> dict:
    """Search beliefs and entries."""
    resp = httpx.get(
        f"{_base_url()}/api/projects/{project_id}/search",
        params={"q": query},
        headers=_headers(),
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def chat_stream(project_id: str, message: str,
                model: str | None = None,
                thread_id: str | None = None):
    """Stream a chat response via SSE. Yields text chunks."""
    body = {"message": message}
    if model:
        body["model"] = model
    if thread_id:
        body["thread_id"] = thread_id

    with httpx.stream(
        "POST",
        f"{_base_url()}/api/projects/{project_id}/chat",
        json=body,
        headers=_headers(),
        timeout=httpx.Timeout(TIMEOUT, connect=10.0),
    ) as resp:
        resp.raise_for_status()
        yield_thread_id = resp.headers.get("x-thread-id")
        for line in resp.iter_lines():
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                yield data
