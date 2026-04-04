import sys
import threading
from http.server import ThreadingHTTPServer

from api_endpoints import make_handler
from deltabot_cli import BotCli
from deltachat2 import events
from outbound_requests import post_new_message_webhook
from config import WEBHOOK_URL, API_HOST, API_PORT, BOT_CLI_NAME, ENABLE_WEBHOOK, LOG_LEVEL


cli = BotCli(BOT_CLI_NAME, log_level=LOG_LEVEL)

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
    kind = getattr(event, "kind", type(event).__name__)
    if ENABLE_WEBHOOK and WEBHOOK_URL:
        threading.Thread(
            target=post_new_message_webhook,
            args=(bot, WEBHOOK_URL, kind, event),
            daemon=True,
        ).start()
    bot.logger.info("Message #%i received from %s (chat #%i): %s", event.msg.id, event.msg.sender.address, event.msg.chat_id, event.msg.text)
    bot.logger.debug("Message payload: %r", event)
    bot.rpc.markseen_msgs(accid, [event.msg.id])

@cli.on(events.RawEvent)
def log_raw_event(bot, accid, event):
    kind = getattr(event, "kind", type(event).__name__)
    bot.logger.info("Raw event on account %i: %s", accid, kind)
    #bot.logger.debug("Raw event payload: %r", event) # Uncomment this line to log the full payload of all raw events, but be aware that this can create a lot of log output.
    if kind == "ReactionsChanged":
        bot.logger.debug("ReactionsChanged payload: %r", event)
    if kind == "IncomingReaction":
        bot.logger.debug("IncomingReaction payload: %r", event)
    
    # I suggest to not allow to send all events to a webhook, as they might create huge amounts of traffic.
    # Instead, you can filter for specific event types that you want to receive in your webhook handler and only send those
    # For example, if you only want to receive new messages and reactions, you can do something like this:
    #if ENABLE_WEBHOOK and WEBHOOK_URL and kind in ("NewMessage", "IncomingReaction"):
    #    threading.Thread(
    #        target=post_new_message_webhook,
    #        args=(bot, WEBHOOK_URL, kind, event),
    #        daemon=True,
    #    ).start()


if __name__ == "__main__":
    try:
        cli.start()
    except KeyboardInterrupt:
        print("\nStopping bot...")
        sys.exit(0)
