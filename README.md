# Delta Chat Bots - REST API Connector
Code in this repository gives an access to the Delta Chat - Bot APIs (RPC) via REST API

Small private Delta Chat bot project with:

- a local REST API for Delta Chat RPC calls
- outbound webhook delivery for incoming messages
- simple event logging for Delta Chat raw events

## Setup
### Step 1. Environment Variables
Create a `.env` file in the project root:

```env
ENABLE_WEBHOOK=true
WEBHOOK_URL=https://webhook.site/your-webhook-url

API_PORT=8000
API_HOST=127.0.0.1
API_KEY=supersecretkey
BOT_CLI_NAME=REST_API_Relay
```

### Step 2. Create virtual environment
#### On Windows:
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### On Linux
```
python3 -m venv .venv
source .venv/bin/activate
```
### Step 3. Install requirements
```
pip install -r requirements.txt
```
Note: sometimes you might need to run pip3 instead of pip.

### Step 4. Create new Bot account in Delta Chat
Run the following CLI command:
```
python ./main.py init DCACCOUNT:https://nine.testrun.org/new
```


## Start
### Step 1. Activate virtual environment
Note: if you run it right after the setup step, you can skip this step.
#### On Windows:
```
.\.venv\Scripts\Activate.ps1
```

#### On Linux
```
source .venv/bin/activate
```

### Step 2. Activate virtual environment

### Hints:

#### To deactivate a virtual environment
```
deactivate
```