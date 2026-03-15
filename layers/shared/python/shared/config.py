from dotenv import load_dotenv
from datetime import datetime
import os
from zoneinfo import ZoneInfo


load_dotenv()

GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
SCHEDULER_AGENT_ARN = os.getenv("SCHEDULER_AGENT_ARN", "")
SCHEDULER_ROLE_ARN = os.getenv("SCHEDULER_ROLE_ARN", "")
APP_TIME_ZONE = os.getenv("APP_TIME_ZONE", "America/New_York")
APP_TZINFO = ZoneInfo(APP_TIME_ZONE)


def local_now() -> datetime:
    return datetime.now(APP_TZINFO)
