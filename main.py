import sys
import threading
from http.server import ThreadingHTTPServer

from api_endpoints import make_handler
from deltabot_cli import BotCli
from deltachat2 import events
from outbound_requests import post_new_message_webhook
from config import WEBHOOK_URL, API_HOST, API_PORT, BOT_CLI_NAME


cli = BotCli(BOT_CLI_NAME)

@cli.on_start
def start_rest_api(bot, args) -> None:
    server = ThreadingHTTPServer((API_HOST, int(API_PORT)), make_handler(bot))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    bot.logger.info(
        "REST API listening on http://%s:%s", API_HOST, API_PORT
    )


@cli.on(events.NewMessage)
def echo(bot, accid, event):
    threading.Thread(
        target=post_new_message_webhook,
        args=(bot, WEBHOOK_URL, getattr(event, "kind", type(event).__name__), event),
        daemon=True,
    ).start()
    bot.logger.info("Message payload: %r", event)
    bot.rpc.markseen_msgs(accid, [event.msg.id])

@cli.on(events.RawEvent)
def log_raw_event(bot, accid, event):
    kind = getattr(event, "kind", type(event).__name__)
    bot.logger.info("Raw event on account %i: %s", accid, kind)
    bot.logger.debug("Raw event payload: %r", event)
    if kind == "ReactionsChanged":
        bot.logger.info("ReactionsChanged payload: %r", event)
    if kind == "IncomingReaction":
        bot.logger.info("IncomingReaction payload: %r", event)


if __name__ == "__main__":
    try:
        cli.start()
    except KeyboardInterrupt:
        print("\nStopping bot...")
        sys.exit(0)
