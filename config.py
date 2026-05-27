import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

DB_HOST = os.getenv("DB_HOST", "185.49.165.116")
DB_PORT = int(os.getenv("DB_PORT", 3310))
DB_USER = os.getenv("DB_USER", "liontest_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "nR2aJ6eS2u")
DB_NAME = os.getenv("DB_NAME", "vps_liontest_db")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

AUTHOR_ID = 1748
