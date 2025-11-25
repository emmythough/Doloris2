import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Model names (update when GPT-5 is available)
GPT_5_NANO_MODEL = os.getenv("GPT_5_NANO_MODEL", "gpt-4o-mini")  # Fast intent classification
GPT_5_MINI_MODEL = os.getenv("GPT_5_MINI_MODEL", "gpt-4o")  # Main assistant brain
GPT_5_1_MODEL = os.getenv("GPT_5_1_MODEL", "o1-mini")  # Deep reasoning

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
APP_BASE_URL = os.getenv("APP_BASE_URL")

# GitHub Configuration (for R.D 2.1)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "emmythough/Doloris2")
