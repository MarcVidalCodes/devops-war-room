import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 5))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 5))
    ENABLE_BUGS = os.getenv("ENABLE_BUGS", "true").lower() == "true"
    ERROR_RATE_PERCENT = int(os.getenv("ERROR_RATE_PERCENT", 5))
    SLOW_QUERY_DELAY = int(os.getenv("SLOW_QUERY_DELAY", 2))
