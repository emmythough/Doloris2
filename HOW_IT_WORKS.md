# How Doloris 2 Works - Simple Explanation

## The Big Picture

Doloris 2 is a Telegram bot that acts as your personal AI assistant. Think of it like having a smart friend who remembers everything you tell them and can help you stay organized.

---

## The 4 Main Parts

### 1. **The Brain** 🧠 (OpenAI GPT-4)
- **What it does**: Understands your messages and decides what to do
- **Example**: When you say "Remind me to call mom tomorrow", the brain understands you want a task created

### 2. **The Memory** 💾 (Supabase Database)
- **What it does**: Stores everything permanently
- **What it remembers**:
  - Your tasks and reminders
  - Your conversation history
  - Your personal instructions (like "Call me Captain")
  - Your mood logs and notes

### 3. **The Body** 📱 (Telegram)
- **What it does**: The interface you interact with
- **How**: You send messages on Telegram, Doloris responds

### 4. **The Nervous System** ⚡ (FastAPI Backend on Render)
- **What it does**: Connects everything together
- **Where**: Running 24/7 on Render's servers

---

## How a Message Flows Through the System

Let's say you send: **"Remind me to buy milk tomorrow at 3pm"**

### Step 1: Telegram Receives Your Message
- You type in the Telegram app
- Telegram sends it to Render via a "webhook"

### Step 2: Render Receives the Webhook
- File: `app/telegram_webhook.py`
- Extracts your user ID and message text
- Passes it to the Agent

### Step 3: The Agent Processes Your Message
- File: `app/agent.py`
- Checks if it's a command (like `/today`)
- If not, it builds context:
  - Fetches your recent messages
  - Fetches your personal instructions
  - Fetches your recent logs

### Step 4: OpenAI Decides What to Do
- File: `app/openai_client.py`
- Sends your message + context to GPT-4
- GPT-4 sees you want a task and calls the `add_task` tool

### Step 5: The Tool Executes
- File: `app/tools.py`
- The `add_task` function runs
- Saves "Buy milk" to the database with due date "tomorrow 3pm"

### Step 6: Database Stores It
- File: `app/db.py`
- Connects to Supabase
- Inserts the task into the `tasks` table

### Step 7: Response Sent Back
- OpenAI generates a friendly response: "Got it! I'll remind you to buy milk tomorrow at 3pm."
- The agent returns this to the webhook
- The webhook sends it back to Telegram
- You see the message in your chat

---

## The Database Tables

### `users`
- Stores your Telegram ID, name, timezone

### `messages`
- Every message you send and receive (for context)

### `tasks`
- Your to-do items and reminders

### `instructions`
- Personal rules you've set (e.g., "Call me Captain")

### `logs`
- Notes about your mood, sleep, activities

### `nudges`
- Proactive messages the bot wants to send you

---

## The Special Tools (Functions)

The brain can call these "tools" to interact with your data:

1. **`add_task`**: Creates a new reminder/task
2. **`list_tasks`**: Shows your pending tasks
3. **`update_instruction`**: Saves a new personal rule
4. **`create_log`**: Records a note about you (mood, sleep, etc.)
5. **`propose_nudge`**: Suggests a proactive message to send you

---

## The Slash Commands (Quick Actions)

These bypass OpenAI to save tokens and respond instantly:

- **`/today`**: Shows tasks + recent logs
- **`/tasks`**: Lists all pending tasks
- **`/settings`**: Shows your timezone and instructions

---

## The Heartbeat (Autonomous Mode)

- **Endpoint**: `/heartbeat/trigger`
- **What it does**: Runs every hour (via a cron job)
- **Purpose**: Checks if the bot should proactively message you
- **Example**: If you have a task due soon, it might nudge you

---

## File Structure

```
app/
├── main.py              # Starts the FastAPI server
├── config.py            # Loads environment variables
├── telegram_webhook.py  # Receives messages from Telegram
├── agent.py             # Main logic orchestrator
├── openai_client.py     # Talks to OpenAI API
├── db.py                # Talks to Supabase database
├── tools.py             # Defines what the AI can do
├── heartbeat.py         # Autonomous check-ins
└── models.py            # Data structures (User, Task, etc.)
```

---

## Environment Variables (Secrets)

These are stored in `.env` locally and on Render:

- `OPENAI_API_KEY`: Your OpenAI account key
- `SUPABASE_URL`: Your database URL
- `SUPABASE_SERVICE_ROLE_KEY`: Database admin key
- `TELEGRAM_BOT_TOKEN`: Your bot's unique ID
- `APP_BASE_URL`: Where your app is hosted (Render URL)

---

## Common Issues & Fixes

### Bot receives messages but doesn't respond
- **Cause**: Old token on Render
- **Fix**: Update `TELEGRAM_BOT_TOKEN` in Render's Environment tab

### "404 Not Found" in logs
- **Not an error**: Someone tried to visit your URL directly
- **Ignore it**: Your bot only responds to `/telegram/webhook`

### OpenAI errors
- **Check**: Your API key is valid and has credits
- **Check**: Logs for "OpenAI API error"

### Database errors
- **Check**: Supabase URL and keys are correct
- **Check**: Tables were created via `setup.sql`

---

## How to Debug

1. **Check Render Logs**:
   - Go to Render Dashboard → Your Service → Logs
   - Look for errors after sending a test message

2. **Run Local Tests**:
   - `python test_bot.py` - Checks token, webhook, health
   - `python test_full_flow.py` - Tests agent logic
   - `python test_commands.py` - Tests slash commands

3. **Check Database**:
   - Go to Supabase Dashboard
   - Table Editor → Check if data is being saved

---

## The Flow in One Sentence

**You message Telegram → Telegram webhooks to Render → Render calls the Agent → Agent asks OpenAI → OpenAI calls Tools → Tools update Database → Response goes back to Telegram → You see the reply.**

---

## Next Steps

- Set up a cron job to hit `/heartbeat/trigger` every hour
- Customize the system prompt in `agent.py` to change personality
- Add more tools in `tools.py` for new features
