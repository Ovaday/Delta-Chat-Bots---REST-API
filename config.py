import os
from pathlib import Path


def load_env(env_path: str = ".env") -> None:
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env()

BOT_CLI_NAME = os.environ.get("BOT_CLI_NAME","REST_API_Relay")
LOG_LEVEL = os.environ.get("LOG_LEVEL","info").lower()

ENABLE_WEBHOOK = os.environ.get("ENABLE_WEBHOOK", "false").lower() in ("1", "true", "yes")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
WEBHOOK_AUTH_TOKEN = os.environ.get("WEBHOOK_AUTH_TOKEN")

API_PORT = os.environ.get("API_PORT","8000")
API_HOST = os.environ.get("API_HOST","127.0.0.1")
API_KEY = os.environ.get("API_KEY")
