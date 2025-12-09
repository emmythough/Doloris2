"""
Doloris 5.3 Configuration
Environment variables and constants
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ======================
# OPENAI MODELS
# ======================
EMPATH_MODEL = "gpt-4o-mini"  # Fast + cheap for empathy simulation
AUDITOR_MODEL = "gpt-4o-mini"  # Risk analysis
EXECUTIVE_MODEL = "gpt-4o-mini"  # Final synthesis - switched to mini for cost savings
REFLEX_MODEL = "gpt-4o-mini"   # Instant responses

# ======================
# SUPABASE
# ======================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # anon key for client
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # for workers

# ======================
# REDIS
# ======================
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

# ======================
# OPENAI
# ======================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ======================
# SECURITY
# ======================
TICKET_SECRET_KEY = os.getenv("TICKET_SECRET_KEY", "change-me-in-production")
TICKET_EXPIRY_SECONDS = 300  # 5 minutes

# ======================
# SESSION & LEARNING
# ======================
SESSION_NAP_INTERVAL_SECONDS = 600  # 10 minutes of inactivity triggers consolidation

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
