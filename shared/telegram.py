import os
from dotenv import load_dotenv
import requests

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN", "")
chat_id = os.getenv("TELEGRAM_CHAT_ID", "")


def send_message(text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(url, json={"chat_id": chat_id, "text": text})
    return response.json()


send_message("hello its agent")
