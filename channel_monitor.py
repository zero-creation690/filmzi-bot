import asyncio
from telethon import TelegramClient
from telethon.events import NewMessage
import os
from database import db
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChannelMonitor:
    def __init__(self):
        self.api_id = int(os.getenv('API_ID'))
        self.api_hash = os.getenv('API_HASH')
        self.channel_id = int(os.getenv('CHANNEL_ID'))
        self.client = TelegramClient('filmzi_session', self.api_id, self.api_hash)
    
    def parse_movie_info(self, text):
        """Extract movie information from caption"""
        if not text:
            return None, None, None, None
            
        # Example: "Cars (2006) 480p BluRay x264 ESubs Audio] O mkv"
        patterns = [
            r'(.*?)\s*\((\d{4})\)\s*(\d+p).*?(\d+\.?\d*\s*[GMK]B)',
            r'(.*?)\s*-\s*(\d{4})\s*-\s*(\d+p).*?(\d+\.?\d*\s*[GMK]B)',
            r'(.*?)\s*\((\d{4})\).*?(\d+p).*?(\d+\.?\d*\s*[GMK]B)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                year = match.group(2)
                quality = match.group(3)
                size = match.group(4)
                return title, year, quality, size
        
        return None, None, None, None
    
    async def start_monitoring(self):
        await self.client.start()
        logger.info("Channel monitor started...")
        
        @self.client.on(NewMessage(chats=self.channel_id))
        async def handler(event):
            try:
                if event.message.document or event.message.video:
                    # Get file information
                    if event.message.document:
                        file_id = event.message.document.id
                        file_size = event.message.document.size
                    else:
                        file_id = event.message.video.id
                        file_size = event.message.video.size
                    
                    # Convert file size to readable format
                    if file_size:
                        if file_size > 1024**3:  # GB
                            size_str = f"{file_size/1024**3:.2f} GB"
                        elif file_size > 1024**2:  # MB
                            size_str = f"{file_size/1024**2:.2f} MB"
                        else:  # KB
                            size_str = f"{file_size/1024:.2f} KB"
                    else:
                        size_str = "Unknown"
                    
                    # Parse caption for movie info
                    caption = event.message.text or event.message.caption or ""
                    title, year, quality, parsed_size = self.parse_movie_info(caption)
                    
                    if title:
                        # Use parsed size if available, otherwise use calculated size
                        final_size = parsed_size or size_str
                        
                        # Add to database
                        db.add_movie(title, file_id, final_size, quality, year)
                        logger.info(f"Added to database: {title} ({year}) - {quality}")
                    else:
                        logger.warning(f"Could not parse movie info from: {caption}")
                        
            except Exception as e:
                logger.error(f"Error processing message: {e}")
        
        logger.info(f"Monitoring channel {self.channel_id} for new movies...")
        await self.client.run_until_disconnected()

if __name__ == '__main__':
    monitor = ChannelMonitor()
    asyncio.run(monitor.start_monitoring())
