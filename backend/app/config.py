import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://evidenceiq:evidenceiq@localhost:5432/evidenceiq"
)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MAX_CONCURRENT_SOURCE_FETCHES = int(os.getenv("MAX_CONCURRENT_SOURCE_FETCHES", "5"))
CACHE_TTL_DAYS = int(os.getenv("CACHE_TTL_DAYS", "30"))
