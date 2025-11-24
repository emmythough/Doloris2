# How Doloris 2.0 Works - System Architecture

## The Vision
Doloris 2.0 is a scalable, multi-model AI assistant platform designed to be your "Jarvis". She is autonomous, self-aware, and capable of handling files, managing your calendar, and organizing your life across multiple platforms.

---

## The Core Architecture

Doloris 2.0 is built on a modular **Layered Architecture**:

### 1. **The Brain (Core Layer)** 🧠
The central intelligence engine that orchestrates everything.
- **`Brain`**: The main controller. It builds context, manages the conversation flow, and decides what to do.
- **`Model Router`**: Automatically switches between models based on complexity:
  - **Tier 1 (`gpt-4o-mini`)**: Fast & cheap. Used for simple greetings ("Hi", "Thanks").
  - **Tier 2 (`gpt-4o`)**: The main workhorse. Used for general conversations and tool usage.
  - **Tier 3 (`o1-mini`)**: Deep reasoning. Used for complex analysis or when you ask to "think deeply".
- **`Self Model`**: Doloris's personality and goals, stored in the database. She knows who she is and what her mission is.

### 2. **The Nervous System (API Gateway)** ⚡
A FastAPI application that routes incoming requests.
- **`/api/v1/message`**: Handles text messages.
- **`/api/v1/file`**: Handles file uploads (PDFs, images).
- **`/telegram/webhook`**: Receives updates from Telegram.

### 3. **The Senses (Channels Layer)** 👁️
Adapters that connect Doloris to the outside world.
- **`TelegramAdapter`**: Handles messages and file downloads from Telegram. It uploads files to your personal cloud storage before showing them to the Brain.
- *(Future)*: WhatsApp Adapter, Web Interface.

### 4. **The Hands (Services Layer)** 🛠️
Modules that perform actual actions.
- **`StorageService`**: Manages your personal Supabase Storage bucket.
- **`CalendarService`**: Connects to Google Calendar (OAuth).
- **`TasksService`**: Manages your to-do list in the database.
- **`ToolsOrchestrator`**: Securely executes tools requested by OpenAI.

---

## How a File is Processed 📂

1.  **You send a PDF** to Telegram.
2.  **TelegramAdapter** detects the file.
3.  It calls **`StorageService`** to ensure you have a personal bucket.
4.  It **downloads** the file and **uploads** it to your Supabase Storage.
5.  It gets a **public URL** for the file.
6.  It sends the **URL + Metadata** to the **Brain**.
7.  The **Brain** sees the URL and passes it to OpenAI.
8.  **OpenAI reads the file directly** and Doloris answers your questions about it.

---

## The Database Schema 🗄️

Doloris 2.0 uses a robust Supabase PostgreSQL schema:

-   **`users`**: Your profile and timezone.
-   **`preferences`**: Your settings (e.g., "friendly" tone, "deep" thinking mode).
-   **`system_state`**: Doloris's global personality and version.
-   **`files`**: Metadata of every file you've uploaded.
-   **`storage_spaces`**: Tracks your personal storage bucket ID.
-   **`connections`**: OAuth tokens for Google Calendar, etc.
-   **`tasks`** & **`logs`**: Your data.

---

## Autonomous Tools 🛠️

Doloris can decide to use these tools on her own:

-   **`add_task`**: "Remind me to..."
-   **`create_supabase_bucket`**: "I'm sending you a file..." (Auto-created on first upload)
-   **`list_tasks`**: "What do I have to do?"
-   **`update_instruction`**: "Call me Captain from now on."
-   **`create_log`**: "I'm feeling tired." (Logs mood)

---

## Directory Structure

```
app/
├── api/                # API Gateway & Endpoints
├── channels/           # Telegram/WhatsApp Adapters
├── core/               # Brain, Model Router, Self Model
├── services/           # Calendar, Storage, Tasks
├── config.py           # Environment Variables
├── db.py               # Database Client
└── main.py             # Entry point
```

---

## Key Features

-   **Multi-Model Cost Savings**: Doesn't waste expensive models on "Hello".
-   **Privacy**: Files are stored in your own isolated bucket.
-   **Extensibility**: Easy to add WhatsApp or Email support later.
-   **Resilience**: If one tool fails, the Brain can recover and apologize.

---

## How to Deploy

1.  **Push to GitHub**: `git push origin main`
2.  **Render**: Auto-deploys the new version.
3.  **Database**: Run `setup_v2.sql` in Supabase to create the new tables.
