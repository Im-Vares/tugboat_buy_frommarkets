from pyrogram import Client
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "default_session")

def get_pyrogram_client():
    return Client(
        SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH
    )