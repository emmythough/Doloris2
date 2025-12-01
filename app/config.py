import os
from dotenv import load_dotenv

import os
from dotenv import load_dotenv

load_dotenv()

# ======================
# CORE CONFIG
# ======================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your_webhook_secret")
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://doloris2.onrender.com")

# Database
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Redis Streams
STREAM_INBOX = "doloris:inbox"         # User messages
STREAM_OUTBOX = "doloris:outbox"       # Bot responses
STREAM_ACTIONS = "doloris:actions"     # Action tickets
STREAM_MEMORY = "doloris:memory"       # Memory consolidation

# Consumer Groups
GROUP_REFLEX = "reflex-workers"
GROUP_COUNCIL = "council-workers"
GROUP_TOOLS = "tool-workers"
GROUP_MEMORY = "memory-workers"

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# GitHub (for R.D brain)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "emmythough/Doloris2")

# ======================
# DOLORIS 5.3 - TRI-CAMERAL COUNCIL
# ======================
EMPATH_MODEL = "gpt-4o-mini"  # Fast + cheap for empathy simulation
AUDITOR_MODEL = "gpt-4o-mini"  # Risk analysis
EXECUTIVE_MODEL = "gpt-4o"     # Final synthesis (or gpt-4o-mini to save cost)
REFLEX_MODEL = "gpt-4o-mini"   # Instant responses

# Ticket System
TICKET_SECRET_KEY = os.getenv("TICKET_SECRET_KEY", "doloris_secure_secret_key_2025")
TICKET_EXPIRY_SECONDS = 300  # 5 minutes

# Session & Learning
SESSION_NAP_INTERVAL_SECONDS = 600  # 10 minutes

# ======================
# PERFORMANCE
# ======================
MAX_COUNCIL_CONCURRENT = 3  # Max concurrent council deliberations
REFLEX_TIMEOUT_MS = 200     # Reflex must respond within 200ms

# ======================
# DEVELOPMENT
# ======================
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
