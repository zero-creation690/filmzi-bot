import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH")
    CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
    ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
    
    # Database
    DB_NAME = "filmzi_bot.db"
    
    # Bot Settings
    BOT_NAME = "Filmzi Movie & TV Series Bot"
    WELCOME_IMAGE = "https://ar-hosting.pages.dev/1759107724318.jpg"
    MAX_RESULTS = 10
    MOVIE_EXPIRY_MINUTES = 10
    
    # Koyeb Specific
    PORT = int(os.getenv("PORT", 8080))
    
    @classmethod
    def validate_config(cls):
        """Validate that all required environment variables are set"""
        required_vars = ['BOT_TOKEN', 'API_ID', 'API_HASH', 'CHANNEL_ID']
        missing_vars = [var for var in required_vars if not getattr(cls, var, None)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
