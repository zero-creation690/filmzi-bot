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
    
    def parse_movie_info(self, text, file_name=None):
        """Extract movie information from caption or file name"""
        if not text and not file_name:
            return None, None, None, None
        
        # Use file name if no text
        content = text or file_name or ""
        
        # Patterns to match different movie file formats
        patterns = [
            # Pattern for: "Code.3.2025.720p.WEB..." or "Mantis.2025.720p.WEBRip.x264.AAC.Filmzi.mp4"
            r'([A-Za-z0-9\.\-\: ]+?)\.?(\d{4})\.?(\d+p).*?(\d+\.?\d*\s*[GMK]B)',
            # Pattern for: "Movie Name (2024) 1080p"
            r'([A-Za-z0-9\.\-\: ]+?)\s*\((\d{4})\)\s*(\d+p).*?(\d+\.?\d*\s*[GMK]B)',
            # Pattern for: "Movie-Name-2024-720p"
            r'([A-Za-z0-9\.\-\: ]+?)\s*[\-\s]\s*(\d{4})\s*[\-\s]\s*(\d+p).*?(\d+\.?\d*\s*[GMK]B)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                title = match.group(1).strip().replace('.', ' ').replace('_', ' ').title()
                year = match.group(2)
                quality = match.group(3)
                size = match.group(4)
                
                # Clean up title
                title = re.sub(r'\s+', ' ', title)  # Remove extra spaces
                
                return title, year, quality, size
        
        # If no pattern matches, try to extract basic info
        return self.extract_basic_info(content)
    
    def extract_basic_info(self, content):
        """Extract basic info when patterns don't match"""
        # Try to find year
        year_match = re.search(r'\.?(\d{4})\.?', content)
        year = year_match.group(1) if year_match else "2025"
        
        # Try to find quality
        quality_match = re.search(r'(\d+p)', content, re.IGNORECASE)
        quality = quality_match.group(1) if quality_match else "720p"
        
        # Try to find size
        size_match = re.search(r'(\d+\.?\d*\s*[GMK]B)', content, re.IGNORECASE)
        size = size_match.group(1) if size_match else "1.0 GB"
        
        # Extract title - take everything before year/quality
        title = content
        if year_match:
            title = content[:year_match.start()].strip()
        
        # Clean title
        title = title.replace('.', ' ').replace('_', ' ').title()
        title = re.sub(r'\s+', ' ', title)
        
        if not title or title.isspace():
            title = "Unknown Movie"
        
        return title, year, quality, size
    
    async def start_monitoring(self):
        await self.client.start()
        logger.info("Channel monitor started...")
        
        # First, let's check existing messages in the channel
        await self.process_existing_messages()
        
        @self.client.on(NewMessage(chats=self.channel_id))
        async def handler(event):
            await self.process_message(event.message)
        
        logger.info(f"Monitoring channel {self.channel_id} for new movies...")
        await self.client.run_until_disconnected()
    
    async def process_existing_messages(self):
        """Process existing messages in the channel"""
        try:
            logger.info("Processing existing messages in channel...")
            async for message in self.client.iter_messages(self.channel_id, limit=100):
                await self.process_message(message)
        except Exception as e:
            logger.error(f"Error processing existing messages: {e}")
    
    async def process_message(self, message):
        """Process a single message"""
        try:
            if message.document or message.video:
                # Get file information
                if message.document:
                    file_id = message.document.id
                    file_size = message.document.size
                    file_name = getattr(message.document, 'file_name', None)
                else:
                    file_id = message.video.id
                    file_size = message.video.size
                    file_name = getattr(message.video, 'file_name', None)
                
                # Convert file size to readable format
                size_str = self.format_file_size(file_size)
                
                # Parse caption for movie info
                caption = message.text or message.caption or ""
                title, year, quality, parsed_size = self.parse_movie_info(caption, file_name)
                
                if title:
                    # Use parsed size if available, otherwise use calculated size
                    final_size = parsed_size or size_str
                    
                    # Add to database
                    db.add_movie(title, file_id, final_size, quality, year)
                    logger.info(f"Added to database: {title} ({year}) - {quality} - {final_size}")
                else:
                    logger.warning(f"Could not parse movie info from: {caption}")
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def format_file_size(self, size_bytes):
        """Convert bytes to human readable format"""
        if not size_bytes:
            return "Unknown"
        
        if size_bytes >= 1024**3:
            return f"{size_bytes/1024**3:.2f} GB"
        elif size_bytes >= 1024**2:
            return f"{size_bytes/1024**2:.2f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes/1024:.2f} KB"
        else:
            return f"{size_bytes} B"

if __name__ == '__main__':
    monitor = ChannelMonitor()
    asyncio.run(monitor.start_monitoring())
