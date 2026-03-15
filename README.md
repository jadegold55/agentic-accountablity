# Agentic Accountability

Agentic Accountability is an AI-powered accountability system built around AWS Lambda, Telegram, Google Calendar, Groq, and Supabase. It watches a daily calendar, schedules reminders and follow-up nudges, accepts replies through a Telegram bot, logs outcomes in Supabase, and sends a weekly summary with charts and a short natural-language recap.

This project is designed for one primary user flow:

- You keep your real calendar in Google Calendar.
- The system reads that calendar each day.
- It creates scheduled check-ins around your events.
- A Telegram bot reminds you when something is starting.
- A follow-up nudge asks how it went.
- Your reply is interpreted and stored.
- A weekly summary is generated and saved.

## What This Project Can Do

### Bot capabilities

The Telegram bot can:

- Receive direct user messages through a webhook.
- Classify whether a message is a scheduling command, a rating, or something else.
- Accept simple numeric replies from `0` to `5`.
- Infer completion from natural replies such as "I got through most of it".
- Ask a clarifying question when a follow-up reply is too vague.
- Send reminder, nudge, and acknowledgment messages back to the user.

### Agent capabilities

The scheduler agent can:

- Read Google Calendar events for a day.
- Add calendar events.
- Update existing calendar events.
- Match calendar events by exact or fuzzy title matching.
- Create or refresh EventBridge Scheduler schedules for check-ins and nudges.
- Respond conversationally to direct scheduling commands from Telegram.

The summary agent can:

- Read check-in history from Supabase.
- Compute weekly per-task and per-day averages.
- Include short completion notes extracted from user replies.
- Generate a bar chart and heatmap when there is enough data.
- Write a weekly summary record to Supabase.
- Send the final summary text and charts to Telegram.

### Operational capabilities

The system also:

- Runs a daily setup Lambda that clears stale schedules and creates fresh ones for the current day.
- Stores check-ins, check-in items, and weekly summaries in Supabase.
- Uses AWS Systems Manager Parameter Store for secrets in deployment.
- Uses a shared Lambda layer for common code.

## What This Project Does Not Do

This repository is useful, but it is not a general-purpose personal assistant.

- It is not a multi-user SaaS product.
- It is not a production-hardened admin dashboard.
- It does not include a frontend UI.
- It does not currently manage recurring habits as first-class automated workflows beyond what exists in your calendar and database.
- It does not support arbitrary free-form chat or broad question answering.
- It does not include full auth, billing, tenancy, or permissions for teams.
- It assumes you are comfortable configuring AWS, Google Calendar API access, Telegram bot settings, and Supabase manually.

## Architecture Overview

The deployed system is made of four Lambda functions and one shared layer.

### 1. Daily setup Lambda

Path: `lambda/daily_setup/`

Responsibilities:

- Read calendar events for the day.
- Remove old schedules.
- Create new one-time EventBridge Scheduler jobs for:
	- check-in reminders when an event starts
	- nudges 30 minutes after an event ends

### 2. Scheduler agent Lambda

Path: `lambda/scheduler_agent/`

Responsibilities:

- Handle direct command requests from Telegram, such as moving or creating events.
- Process scheduled event payloads for check-ins and nudges.
- Log check-in and nudge state transitions.
- Generate short, human-sounding reminder and nudge copy.

### 3. Inbound message Lambda

Path: `lambda/inbound/`

Responsibilities:

- Receive Telegram webhook payloads.
- Match replies to open check-ins.
- Parse numeric ratings.
- Infer completion level from natural-language replies.
- Invoke the scheduler agent asynchronously for direct calendar commands.

### 4. Summary agent Lambda

Path: `lambda/summary_agent/`

Responsibilities:

- Query recent check-in data from Supabase.
- Analyze performance over the last 7 days.
- Generate charts.
- Generate a weekly written summary.
- Persist that weekly summary into the `weekly_summaries` table.
- Send the summary to Telegram.

### 5. Shared layer

Path: `layers/shared/`

Responsibilities:

- Shared config and environment loading.
- Supabase database helpers.
- Telegram helpers.
- Google Calendar helpers.
- Groq API helpers.

## Data Model

The database schema currently includes these main tables:

- `tasks`: active tasks or goals.
- `checkins`: top-level accountability events tied to calendar events.
- `checkin_items`: per-check-in details including `event_title`, `raw_reply_text`, `completion_summary`, and `rating`.
- `weekly_summaries`: stored summary payloads with `completion_json`, summary text, and timestamp.

Schema files live in `db/`:

- `db/schema.sql`
- `db/add_completion_metadata.sql`
- `db/seed.sql`

## Repository Structure

```text
db/                     Supabase schema and SQL migrations
infra/                  AWS SAM template and deployment config
lambda/daily_setup/     Reads calendar and creates daily schedules
lambda/inbound/         Telegram webhook handler
lambda/scheduler_agent/ Scheduling and calendar command agent
lambda/summary_agent/   Weekly analytics and summary agent
layers/shared/          Shared Lambda layer code
shared/                 Local shared code mirror for development/tests
tests/                  Pytest suite
```

## Requirements

You need the following before this project will work end to end:

- Python 3.13
- AWS SAM CLI
- AWS credentials with permission to deploy Lambda, API Gateway, IAM, and EventBridge Scheduler resources
- A Supabase project
- A Telegram bot token and target chat ID
- Google Calendar API credentials with offline access
- A Groq API key

## How To Download The Project

### Option 1: Clone with Git

```bash
git clone https://github.com/<your-username>/agentic-accountablity.git
cd agentic-accountablity
```

### Option 2: Download ZIP from GitHub

1. Open the repository page on GitHub.
2. Click `Code`.
3. Click `Download ZIP`.
4. Extract it locally.
5. Open the extracted folder in VS Code.

## Setup Guide

### 1. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install Python dependencies

This repo splits dependencies by component. For local development, install at least the shared and Lambda-specific packages you plan to work with.

```powershell
pip install -r shared/requirements.txt
pip install -r lambda/daily_setup/requirements.txt
pip install -r lambda/inbound/requirements.txt
pip install -r lambda/scheduler_agent/requirements.txt
pip install -r lambda/summary_agent/requirements.txt
pip install pytest
```

### 3. Configure local environment variables

The shared config reads from environment variables or `.env` during local work.

Expected values:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `GROQ_API_KEY`
- `SCHEDULER_AGENT_ARN`
- `SCHEDULER_ROLE_ARN`
- `APP_TIME_ZONE`

You can place these in a local `.env` file for development. Do not commit that file.

### 4. Set up Google Calendar access

This repo includes `get_token.py`, which uses a local OAuth flow to print a refresh token.

High-level process:

1. Create Google Calendar API credentials in Google Cloud.
2. Put the OAuth client JSON at `credentials.json`.
3. Run:

```powershell
python get_token.py
```

4. Copy the printed refresh token into your local `.env` or AWS SSM Parameter Store.

### 5. Set up Supabase

Create a Supabase project and run the SQL in:

- `db/schema.sql`
- `db/add_completion_metadata.sql`

Optional:

- `db/seed.sql`

You will need:

- your Supabase project URL
- a service-role or API key suitable for this app

### 6. Set up Telegram

You need:

- a Telegram bot token from BotFather
- the chat ID where the bot should send messages

The inbound Lambda exposes a POST webhook route at `/webhook`. After deployment, point your Telegram bot webhook to the deployed API Gateway URL plus `/webhook`.

### 7. Set up AWS Parameter Store values

The SAM template expects these SSM parameter names:

- `/agentic-accountability/google-client-id`
- `/agentic-accountability/google-client-secret`
- `/agentic-accountability/google-refresh-token`
- `/agentic-accountability/groq-api-key`
- `/agentic-accountability/telegram-bot-token`
- `/agentic-accountability/telegram-chat-id`
- `/agentic-accountability/supabase-url`
- `/agentic-accountability/supabase-key`

## Deploying To AWS

The infrastructure is managed with AWS SAM.

### Build

From `infra/`:

```powershell
sam build --template-file template.yaml --no-cached
```

### Deploy

```powershell
sam deploy --profile agentic_schd_jade
```

The deployment config is stored in `infra/samconfig.toml`.

## How The System Works In Practice

### Daily flow

1. `daily_setup` runs on its daily schedule.
2. It reads your Google Calendar for the day.
3. It creates one check-in schedule and one nudge schedule per event.
4. When an event starts, `scheduler_agent` sends a reminder and logs a `sent` check-in.
5. Thirty minutes after the event ends, `scheduler_agent` sends a follow-up nudge and marks it `nudged`.
6. When you reply on Telegram, `inbound_message` logs the response.

### Command flow

You can send a message like:

- "Move dentist appointment tomorrow to 3"
- "Add workout tomorrow at 7 PM"

The inbound handler routes command-like text to the scheduler agent, which inspects the relevant calendar day and attempts to update or add the event.

### Weekly summary flow

1. `summary_agent` runs on its weekly schedule.
2. It loads the last 7 days of check-in items.
3. It calculates averages and completion notes.
4. It creates charts if there is enough signal.
5. It generates a short weekly recap.
6. It writes the summary to `weekly_summaries`.
7. It sends the result to Telegram.

## Example Use Cases

This project is a strong fit for:

- solo accountability systems
- personal planning workflows backed by a real calendar
- lightweight habit and follow-through tracking
- AI-assisted calendar rescheduling through chat
- weekly reflection based on actual logged behavior

## Local Development

### Run tests

```powershell
python -m pytest
```

Or run a targeted file:

```powershell
python -m pytest tests/test_summary_handler.py
```

### Manual Lambda-style testing

You can test handlers locally by importing their modules in Python or by using `sam local invoke` if you want a closer Lambda runtime simulation.

Useful manual targets:

- `lambda/daily_setup/handler.py`
- `lambda/inbound/handler.py`
- `lambda/scheduler_agent/handler.py`
- `lambda/summary_agent/handler.py`

## Important Notes And Constraints

- The project currently assumes a single user/chat flow.
- Secrets should live in SSM Parameter Store for deployment and in `.env` only for local development.
- The daily setup path uses EventBridge Scheduler, not a long-running worker.
- Calendar matching is helpful but not perfect; ambiguous event names can still require clarification.
- The summary agent is designed to be supportive, but the quality of written summaries depends on the quality of logged replies and available data.

## Troubleshooting

### Deployment fails with a CloudFormation changeset error about resource type updates

If you changed a SAM event from `Schedule` to `ScheduleV2`, CloudFormation may refuse an in-place update. Rename the event key in `infra/template.yaml` so SAM generates a new logical resource.

### Weekly summaries are not appearing in Supabase

Check:

- the `weekly_summaries` table exists
- the Lambda has valid `SUPABASE_URL` and `SUPABASE_KEY` values
- the summary handler can reach Supabase
- your deployment includes the latest shared DB helper code

### Telegram messages are not arriving

Check:

- your bot token
- your chat ID
- the Telegram webhook points to the deployed `/webhook` route
- CloudWatch logs for `inbound_message` and `scheduler_agent`

### Google Calendar reads fail

Check:

- your client ID and client secret
- your refresh token
- Google Calendar API enablement in Google Cloud

## Why This Repo Exists

Most task systems fall apart at the moment of execution. This project is built to close that gap by connecting:

- your real calendar
- lightweight conversational nudges
- event-level logging
- weekly reflection

It is less about storing plans and more about creating a loop between intention, execution, response, and review.

## Contributing

If you fork or extend this project, a good next step is to improve one of these areas:

- multi-user support
- stronger retry and error handling
- a web dashboard for history and summaries
- richer task modeling
- better calendar conflict handling
- more structured analytics and reporting

## License

Add the license you want to use for your public GitHub release.
