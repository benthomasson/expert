"""CLI for expert-service.

Usage:
    expert ask <question> [--project NAME] [--model MODEL]
    expert search <query> [--project NAME]
    expert projects
    expert chat <message> [--project NAME] [--model MODEL]
    expert login                         Google OAuth login (browser flow)
    expert logout                        Clear cached credentials
    expert status                        Check authentication status
    expert init                          Create config at ~/.config/expert/config.toml

Config file (~/.config/expert/config.toml):
    [default]
    url = "https://expert.example.com"
    project = "redhat-expert"
    google_client_id = "your-id.apps.googleusercontent.com"
    google_client_secret = "your-secret"

Environment variables override config file. CLI flags override both.
"""

import sys

from . import client
from .config import load_config


def _get_project(args: list[str]) -> str:
    """Extract --project from args or fall back to EXPERT_PROJECT env var."""
    project = None
    if "--project" in args:
        idx = args.index("--project")
        if idx + 1 < len(args):
            project = args[idx + 1]
            del args[idx:idx + 2]
        else:
            print("Error: --project requires a value")
            sys.exit(1)
    elif "-p" in args:
        idx = args.index("-p")
        if idx + 1 < len(args):
            project = args[idx + 1]
            del args[idx:idx + 2]
        else:
            print("Error: -p requires a value")
            sys.exit(1)

    if not project:
        project = load_config()["project"]

    if not project:
        print("Error: specify --project or set EXPERT_PROJECT")
        sys.exit(1)

    return client.resolve_project(project)


def _get_model(args: list[str]) -> str | None:
    """Extract --model from args."""
    if "--model" in args:
        idx = args.index("--model")
        if idx + 1 < len(args):
            model = args[idx + 1]
            del args[idx:idx + 2]
            return model
    return None


def cmd_ask(args: list[str]):
    model = _get_model(args)
    project_id = _get_project(args)
    question = " ".join(args)
    if not question:
        print("Usage: expert ask <question> [--project NAME]")
        sys.exit(1)

    result = client.ask(project_id, question, model=model)
    print(result.get("answer", result))


def cmd_search(args: list[str]):
    project_id = _get_project(args)
    query = " ".join(args)
    if not query:
        print("Usage: expert search <query> [--project NAME]")
        sys.exit(1)

    result = client.search(project_id, query)

    beliefs = result.get("beliefs", [])
    entries = result.get("entries", [])

    if beliefs:
        print(f"=== Beliefs ({len(beliefs)}) ===")
        for b in beliefs:
            status = b.get("truth_value", "?")
            print(f"  [{status}] {b['text'][:120]}")

    if entries:
        print(f"\n=== Entries ({len(entries)}) ===")
        for e in entries:
            print(f"  {e.get('title', e.get('topic', '?'))}")

    sources = result.get("sources", [])
    if sources:
        print(f"\n=== Sources ({len(sources)}) ===")
        for s in sources:
            label = s.get("source_slug", "?")
            if s.get("section"):
                label += f" / {s['section']}"
            snippet = s.get("snippet", "")[:120]
            print(f"  [{label}] {snippet}")
            if s.get("source_url"):
                print(f"    {s['source_url']}")

    if not beliefs and not entries and not sources:
        print("No results.")


def cmd_projects(_args: list[str]):
    projects = client.list_projects()
    if not projects:
        print("No projects.")
        return
    print(f"{'Name':<30} {'Domain':<25} {'Beliefs':<10} {'Entries':<10} {'Sources':<10}")
    print("-" * 95)
    for p in projects:
        print(f"{p['name']:<30} {p['domain']:<25} {p.get('belief_count', '?'):<10} "
              f"{p.get('entry_count', '?'):<10} {p.get('source_count', '?'):<10}")


def cmd_chat(args: list[str]):
    model = _get_model(args)
    project_id = _get_project(args)
    message = " ".join(args)
    if not message:
        print("Usage: expert chat <message> [--project NAME]")
        sys.exit(1)

    for chunk in client.chat_stream(project_id, message, model=model):
        print(chunk, end="", flush=True)
    print()


def cmd_login(args: list[str]):
    from .auth import login
    port = 8085
    if "--port" in args:
        idx = args.index("--port")
        if idx + 1 < len(args):
            port = int(args[idx + 1])
    login(port=port)


def cmd_logout(_args: list[str]):
    from .auth import TOKEN_FILE
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
        print("Logged out. Token removed.")
    else:
        print("No cached token.")


def cmd_status(_args: list[str]):
    from .auth import check_token
    config = load_config()
    print(f"URL: {config['url']}")
    if config["api_key"]:
        print("Auth: static API key")
    elif config["google_client_id"]:
        print("Auth: Google OAuth")
        check_token()
    else:
        print("Auth: none configured")
    if config["project"]:
        print(f"Default project: {config['project']}")


def cmd_install_skill(_args: list[str]):
    from pathlib import Path
    import shutil

    # Find the SKILL.md bundled with the package
    skill_src = Path(__file__).parent.parent / ".claude" / "skills" / "expert" / "SKILL.md"
    if not skill_src.exists():
        # Fallback: try the installed package location
        skill_src = Path(__file__).parent / "SKILL.md"

    if not skill_src.exists():
        print("Error: SKILL.md not found in package")
        sys.exit(1)

    # Determine target directory
    skill_dir = None
    if "--skill-dir" in _args:
        idx = _args.index("--skill-dir")
        if idx + 1 < len(_args):
            skill_dir = Path(_args[idx + 1])

    if not skill_dir:
        # Default: user-level skill
        skill_dir = Path.home() / ".claude" / "skills" / "expert"

    skill_dir.mkdir(parents=True, exist_ok=True)
    dest = skill_dir / "SKILL.md"
    shutil.copy2(skill_src, dest)
    print(f"Skill installed: {dest}")


def cmd_init(_args: list[str]):
    from .config import init_config
    init_config()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "ask": cmd_ask,
        "search": cmd_search,
        "projects": cmd_projects,
        "chat": cmd_chat,
        "login": cmd_login,
        "logout": cmd_logout,
        "status": cmd_status,
        "init": cmd_init,
        "install-skill": cmd_install_skill,
    }

    if command in commands:
        try:
            commands[command](args)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
