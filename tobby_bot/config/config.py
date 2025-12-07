import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB
    DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH", "./downloads")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    RAILWAY_STATIC_URL = os.getenv("RAILWAY_STATIC_URL")
    RAILWAY_ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT")
    RAILWAY_SERVICE_NAME = os.getenv("RAILWAY_SERVICE_NAME")
    RAILWAY_PROJECT_ID = os.getenv("RAILWAY_PROJECT_ID")
