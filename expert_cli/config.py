"""Configuration file support.

Reads ~/.config/expert/config.toml with the following format:

    [default]
    url = "https://expert.example.com"
    api_key = "your-key"
    project = "redhat-expert"
    google_client_id = "your-id.apps.googleusercontent.com"
    google_client_secret = "your-secret"

Environment variables override config file values.
CLI flags override both.
"""

import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "expert"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def _parse_toml(path: Path) -> dict:
    """Parse a simple TOML file. Handles [sections] and key = "value" pairs.

    Keys before any section header are placed in the "default" section.
    """
    if not path.exists():
        return {}

    config = {}
    current_section = "default"
    config[current_section] = {}

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1].strip()
            config.setdefault(current_section, {})
        elif "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            config[current_section][key] = value

    return config


def load_config() -> dict:
    """Load config from file, returning the [default] section.

    Priority: environment variables > config file values.
    """
    file_config = _parse_toml(CONFIG_FILE).get("default", {})

    return {
        "url": os.environ.get("EXPERT_URL", file_config.get("url", "http://localhost:8000")),
        "api_key": os.environ.get("EXPERT_API_KEY", file_config.get("api_key", "")),
        "project": os.environ.get("EXPERT_PROJECT", file_config.get("project", "")),
        "google_client_id": os.environ.get("GOOGLE_CLIENT_ID", file_config.get("google_client_id", "")),
        "google_client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", file_config.get("google_client_secret", "")),
    }


def init_config():
    """Create a default config file if one doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        print(f"Config already exists: {CONFIG_FILE}")
        return

    CONFIG_FILE.write_text("""\
[default]
url = "http://localhost:8000"
# api_key = "your-api-key"
# project = "redhat-expert"
# google_client_id = "your-id.apps.googleusercontent.com"
# google_client_secret = "your-secret"
""")
    print(f"Created config: {CONFIG_FILE}")
