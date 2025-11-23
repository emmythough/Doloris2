import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def send_test_message():
    """Send a message to yourself via the bot to test end-to-end"""
    print("Testing bot response...")
    print("\nTo test the bot properly:")
    print("1. Open Telegram")
    print("2. Search for @doloris2_bot")
    print("3. Send: 'Hello Doloris'")
    print("\nIf the bot responds, everything is working!")
    print("\nAlternatively, tell me your Telegram User ID and I can send a test message directly.")

if __name__ == "__main__":
    send_test_message()
