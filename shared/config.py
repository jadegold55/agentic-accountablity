from dotenv import load_dotenv
import os


load_dotenv()

GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
