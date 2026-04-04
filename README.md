# Delta Chat Bots REST API Connector

This project exposes Delta Chat bot RPC functionality through a small local REST API.

It also includes:

- optional webhook delivery for incoming messages
- simple raw event logging
- a Bruno request collection for quick manual testing

## What It Does

When the bot is running, this project starts an HTTP server and lets you:

- check whether the API is alive with `GET /health`
- call Delta Chat RPC methods with `POST /rpc`
- optionally forward incoming message events to your own webhook endpoint

The REST API is protected by an API key.

## Requirements

- Python 3
- Delta Chat bot dependencies installed through `pip install -r requirements.txt`

## Configuration

Create a `.env` file in the project root. You can copy values from [`.env.example`](.env.example).

```env
BOT_CLI_NAME=REST_API_Relay
LOG_LEVEL=info

ENABLE_WEBHOOK=false
WEBHOOK_URL=https://webhook.site/your-webhook-url

API_PORT=8000
API_HOST=127.0.0.1
API_KEY=supersecretkey
```

### Environment variables

- `BOT_CLI_NAME`: optional, defaults to `REST_API_Relay`
- `LOG_LEVEL`: optional, defaults to `info`
- `ENABLE_WEBHOOK`: optional, set to `true` to send webhook events
- `WEBHOOK_URL`: required if `ENABLE_WEBHOOK=true`
- `API_HOST`: optional, defaults to `127.0.0.1`
- `API_PORT`: optional, defaults to `8000`
- `API_KEY`: required, used for REST API authentication

## Installation

### 1. Create a virtual environment

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
Notes: Depending of the system, there might be back or forward slashes.

Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

If needed, use `pip3` instead of `pip`.

## Create A Bot Account

Create a Delta Chat bot account with:

```bash
python ./main.py init DCACCOUNT:https://nine.testrun.org/new
python ./main.py config displayname "My REST API Bot"
```

If you have multiple accounts, specify the account id:

```bash
python ./main.py -a 1 config displayname "My REST API Bot"
```

You can list accounts with:

```bash
python ./main.py list
```

The `https://nine.testrun.org/new` relay is only an example test relay. You may want to use a different Delta Chat relay in production.

## Generate An Invite Link

Run:

```bash
python ./main.py link
```

Save the generated link and use it later to connect to the bot.

Important: start the bot before using the invite link. Otherwise the connection request may not be accepted.

## Run The Bot And API

If your virtual environment is not active yet, activate it first.

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux:

```bash
source .venv/bin/activate
```

Then start the bot:

```bash
python ./main.py serve
```

When the server starts, it will expose the REST API at:

`http://127.0.0.1:8000` by default

After that, connect to the bot using the invite link from the previous step.

When a user sends a message to the bot, the bot marks that message as seen:

![Bot marks incoming messages as seen](image.png)

If webhook forwarding is enabled, incoming messages are also posted to your configured webhook URL.

## Authentication

Every REST API request must include the API key.

You can send it using either:

- `Authorization: Bearer <API_KEY>`
- `X-API-Key: <API_KEY>`

If the key is missing or invalid, the API returns `401 Unauthorized`.

## API Endpoints

### `GET /health`

Checks whether the REST API is running.

Example:

```bash
curl --request GET \
  --url http://127.0.0.1:8000/health \
  --header "Authorization: Bearer supersecretkey"
```

Example response:

```json
{
  "status": "ok"
}
```

### `POST /rpc`

Calls a public Delta Chat RPC method and returns its result.

Example:

```bash
curl --request POST \
  --url http://127.0.0.1:8000/rpc \
  --header "Authorization: Bearer supersecretkey" \
  --header "Content-Type: application/json" \
  --data '{
    "method": "send_msg",
    "params": [
      1,
      10,
      {
        "text": "hello from rpc"
      }
    ]
  }'
```

In this example:

- `method` is the Delta Chat RPC method name
- `params[0]` is the local account id
- `params[1]` is the target chat id
- `params[2]` is the message payload

Useful ways to discover values:

- account id: `python ./main.py list`
- chat id: inspect logs from incoming messages or your webhook payloads

If the RPC call succeeds, the API responds with JSON containing:

- `method`
- `params`
- `result`

If the RPC call fails, the API returns `500` with an `rpc_failed` error payload.

## Webhook Payloads

If webhook forwarding is enabled, incoming messages are sent as:

```json
{
  "type": "NewMessage",
  "payload": {
    "...": "event data"
  }
}
```

The payload is a JSON-safe version of the Delta Chat event object.

## Bruno Collection

The repository includes a Bruno (https://www.usebruno.com/) collection in [`Bruno Requests`](Bruno%20Requests) for testing the API manually.

At minimum, set your `API_KEY` in the Bruno environment before sending requests.

## Troubleshooting

- To increase log detail, set `LOG_LEVEL=debug`
- For CLI help, run `python ./main.py -h`
- To deactivate the virtual environment, run `deactivate`

## Delta Chat RPC References

Delta Chat RPC documentation is still limited. These references were useful while building this project:

- Delta Chat bots quickstart: https://bots.delta.chat/quickstart.html
- Delta Chat JSON-RPC source reference: https://github.com/chatmail/core/blob/main/deltachat-jsonrpc/src/api.rs#L742

If you need to figure out a request shape, another practical option is searching installed packages for similar RPC usage patterns.

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).
