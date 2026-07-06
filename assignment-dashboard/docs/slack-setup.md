# Slack App Setup Guide

## 1. Create a Slack App

1. Go to https://api.slack.com/apps
2. Click **Create New App** → **From scratch**
3. Name it `Assignment Dashboard`, select your workspace
4. Click **Create App**

---

## 2. Add OAuth Scopes

Under **OAuth & Permissions → Scopes → Bot Token Scopes**, add:

| Scope | Reason |
|---|---|
| `channels:history` | Read message history from public channels |
| `channels:read` | List public channels |
| `groups:history` | Read message history from private channels |
| `users:read` | Resolve Slack user IDs to names |
| `chat:write` | Post messages (used for future Slack alerts) |

---

## 3. Install App to Workspace

Under **OAuth & Permissions**, click **Install to Workspace** and authorize.

Copy the **Bot User OAuth Token** (`xoxb-...`) → this is `SLACK_BOT_TOKEN` in `.env`.

---

## 4. Enable Events API

Under **Event Subscriptions**:

1. Toggle **Enable Events** to ON
2. Set **Request URL** to:
   ```
   https://<your-host>/slack/events
   ```
   > For local development, use [ngrok](https://ngrok.com/):
   > ```bash
   > ngrok http 8000
   > # use the https URL: https://abc123.ngrok.io/slack/events
   > ```
3. Slack will immediately send a `url_verification` challenge — the backend handles this automatically.

---

## 5. Subscribe to Events

Under **Event Subscriptions → Subscribe to bot events**, add:

- `message.channels` — messages posted in public channels the bot is a member of
- `message.groups` — messages posted in private channels (optional)

---

## 6. Get Signing Secret

Under **Basic Information → App Credentials**, copy the **Signing Secret** → this is `SLACK_SIGNING_SECRET` in `.env`.

---

## 7. Invite Bot to Channels

In Slack, invite the bot to the channels you want to monitor:

```
/invite @Assignment Dashboard
```

---

## Testing

Post a message in a monitored channel and verify it appears:

```bash
curl http://localhost:8000/slack/events
```

You should see the raw event with `processed: false` (before NLP runs) or `processed: true` (after extraction).
