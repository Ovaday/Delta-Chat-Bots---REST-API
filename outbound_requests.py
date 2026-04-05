import json
from dataclasses import asdict, is_dataclass
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from config import WEBHOOK_AUTH_TOKEN


def to_jsonable(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    if hasattr(value, "__dict__"):
        return {
            key: to_jsonable(item)
            for key, item in vars(value).items()
            if not key.startswith("_")
        }
    return repr(value)


def post_new_message_webhook(bot, endpoint_url: str, event_type: str, data_to_send) -> None:
    payload = {
        "type": event_type,
        "payload": to_jsonable(data_to_send),
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "DeltaChatBot-RestApiRelay/1.0",
    }
    if WEBHOOK_AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {WEBHOOK_AUTH_TOKEN}"
    
    request = Request(
        endpoint_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            bot.logger.info("Webhook delivered with status %s", response.status)
    except HTTPError as exc:
        error_body = ""
        try:
            error_body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            error_body = "<unable to read response body>"
        bot.logger.error(
            "Webhook delivery failed with HTTP %s: %s",
            exc.code,
            error_body,
        )
    except Exception as exc:
        bot.logger.exception("Webhook delivery failed: %s", exc)
