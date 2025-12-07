import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the bot"""
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    REDIS_URL = os.getenv("REDIS_URL")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")
    
    # Video settings
    MAX_FILE_SIZE = 49_000_000  # 49MB in bytes
    VIDEO_QUALITY = 'best[height<=720]'
    
    # Supported platforms
    SUPPORTED_PLATFORMS = [
        "youtube", "youtu.be", "tiktok", 
        "instagram", "x.com", "twitter"
    ]
    
    # Validation
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is required")
    
    if not REDIS_URL:
        raise ValueError("REDIS_URL environment variable is required")