# Delta Chat Bots REST API Connector

This project exposes [`Delta Chat`](https://delta.chat/) bot RPC functionality through a small local REST API.

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
WEBHOOK_AUTH_TOKEN=supersecrettoken

API_PORT=8000
API_HOST=127.0.0.1
API_KEY=supersecretkey
```

### Environment variables

- `BOT_CLI_NAME`: optional, defaults to `REST_API_Relay`
- `LOG_LEVEL`: optional, defaults to `info`
- `ENABLE_WEBHOOK`: optional, set to `true` to send webhook events
- `WEBHOOK_URL`: required if `ENABLE_WEBHOOK=true`
- `WEBHOOK_AUTH_TOKEN`: optional, set if you want this to be included as a Bearer Token in Authorization header of an outbound request
- `API_HOST`: optional, defaults to `127.0.0.1`
- `API_PORT`: optional, defaults to `8000`
- `API_KEY`: required, used for REST API authentication
- `MEDIA_DIR`: optional, directory path for storing uploaded media files, defaults to system temp directory

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

## Media endpoints

### `POST /media`

Uploads a file to the server for temporary storage. Files are stored in the directory specified by `MEDIA_DIR`.

The request must be a multipart form with a `file` field. Optionally, you can include a `filename` field to specify a custom name for the uploaded file.

Example:

```bash
curl --request POST \
  --url http://127.0.0.1:8000/media \
  --header "Authorization: Bearer supersecretkey" \
  --form "file=@/path/to/image.png"
```

With custom filename:

```bash
curl --request POST \
  --url http://127.0.0.1:8000/media \
  --header "Authorization: Bearer supersecretkey" \
  --form "file=@/path/to/image.png" \
  --form "filename=my-custom-name.png"
```

Response:

```json
{
  "status": "created",
  "name": "image.png"
}
```

You can send this file afterwards like that:
```
{
  "method": "send_msg",
  "params": [
    1,
    10,
    {
      "text": "Test Image Send",
      "file": "/tmp/DeltaChatBotsRestAPI_media/filename=my-custom-name.png",
      "filename": "image.png"
    }
  ]
}
```

### `DELETE /media?name=<filename>`

Deletes a previously uploaded file from the media directory.

Example:

```bash
curl --request DELETE \
  --url "http://127.0.0.1:8000/media?name=image.png" \
  --header "Authorization: Bearer supersecretkey"
```

Response:

```json
{
  "status": "deleted",
  "name": "image.png"
}
```

If the file doesn't exist, returns `404 Not Found`.

## Webhook Payloads

If webhook forwarding is enabled, incoming messages are sent as:

```json
{
  "type": "NewMessage",
  "account_id": 1,
  "payload": {
    "...": "event data"
  }
}
```

The payload is a JSON-safe version of the Delta Chat event object.

## Bruno Collection

The repository includes a Bruno (https://www.usebruno.com/) collection in [`Bruno Requests`](Bruno%20Requests) for testing the API manually.

At minimum, set your `API_KEY` in the Bruno environment before sending requests.

## Long-Run as systemd (on Linux)

### Setup
Create a service file:

```bash
sudo nano /etc/systemd/system/DeltaChatBotsRestAPI.service
```

Paste the following (replace the paths with your actual project path):

```ini
[Unit]
Description=Delta Chat Bots REST API
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/home/your_user/projects/Delta-Chat-Bots---REST-API
Environment="PATH=/home/your_user/projects/Delta-Chat-Bots---REST-API/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/your_user/projects/Delta-Chat-Bots---REST-API/.venv/bin/python main.py serve
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Key points:

- Set `User` to the user that should run the service (not root)
- Set `WorkingDirectory` to your project path
- Set `Environment=PATH=...` to include the venv's bin directory so all previously installed dependencies are found
- `Type=simple` is appropriate for long-running services
- `RestartSec=10` waits 10 seconds before restarting on failure

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable DeltaChatBotsRestAPI
sudo systemctl start DeltaChatBotsRestAPI
```

### Check the status:

```bash
sudo systemctl status DeltaChatBotsRestAPI
```

View logs in real time:

```bash
sudo journalctl -u DeltaChatBotsRestAPI -f
```

View recent logs:

```bash
sudo journalctl -u DeltaChatBotsRestAPI -n 50
```

Stop the service:

```bash
sudo systemctl stop DeltaChatBotsRestAPI
```

## Troubleshooting

- To increase log detail, set `LOG_LEVEL=debug`
- For CLI help, run `python ./main.py -h`
- To deactivate the virtual environment, run `deactivate`

## Delta Chat RPC References

Delta Chat RPC documentation is still limited. These references were useful while building this project:

- Delta Chat bots quickstart: https://bots.delta.chat/quickstart.html
- Delta Chat JSON-RPC source reference: https://github.com/chatmail/core/blob/main/deltachat-jsonrpc/src/api.rs#L742
- Additional JSON-RPC Automatically Generated Docu for nodeJS (really helpful one): https://js.jsonrpc.delta.chat/classes/RawClient.html

If you need to figure out a request shape, another practical option is searching installed packages for similar RPC usage patterns.

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).
