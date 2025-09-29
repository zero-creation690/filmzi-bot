import re
import logging
from typing import Dict, Any
from urllib.parse import quote

logger = logging.getLogger(__name__)

class MovieUtils:
    @staticmethod
    def parse_movie_info(filename: str) -> Dict[str, Any]:
        """Extract movie information from filename"""
        try:
            info = {
                'movie_name': filename,
                'year': None,
                'quality': '480p',
                'language': 'English',
                'category': 'movie'
            }
            
            # Extract year
            year_match = re.search(r'\((\d{4})\)', filename)
            if year_match:
                info['year'] = int(year_match.group(1))
                info['movie_name'] = re.sub(r'\(\d{4}\)', '', filename).strip()
            
            # Extract quality
            quality_patterns = [
                r'(\d{3,4}p)', r'(HDTV)', r'(BluRay)', r'(WEB-DL)', 
                r'(720p)', r'(1080p)', r'(480p)', r'(4K)'
            ]
            for pattern in quality_patterns:
                quality_match = re.search(pattern, filename, re.IGNORECASE)
                if quality_match:
                    info['quality'] = quality_match.group(1).upper()
                    break
            
            # Extract language
            lang_patterns = {
                'hindi': ['hindi', 'hin'],
                'tamil': ['tamil', 'tam'],
                'telugu': ['telugu', 'tel'],
                'english': ['english', 'eng']
            }
            
            for lang, patterns in lang_patterns.items():
                if any(pattern in filename.lower() for pattern in patterns):
                    info['language'] = lang.capitalize()
                    break
            
            # Clean movie name
            info['movie_name'] = re.sub(r'[\[\]]', '', info['movie_name'])
            info['movie_name'] = re.sub(r'\.mkv$|\.mp4$|\.avi$', '', info['movie_name'])
            info['movie_name'] = info['movie_name'].strip()
            
            return info
        except Exception as e:
            logger.error(f"Error parsing movie info: {e}")
            return {'movie_name': filename, 'quality': '480p', 'language': 'English'}
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Convert bytes to human readable format"""
        try:
            if size_bytes == 0:
                return "0 B"
            
            size_names = ["B", "KB", "MB", "GB", "TB"]
            i = 0
            while size_bytes >= 1024 and i < len(size_names) - 1:
                size_bytes /= 1024.0
                i += 1
            
            return f"{size_bytes:.2f} {size_names[i]}"
        except:
            return "N/A"
    
    @staticmethod
    def create_movie_caption(movie_data: Dict[str, Any]) -> str:
        """Create formatted caption for movie"""
        caption = f"**🎬 {movie_data['movie_name']}**"
        
        if movie_data.get('year'):
            caption += f" ({movie_data['year']})"
        
        caption += f"\n\n📊 **Size:** {movie_data.get('file_size', 'N/A')}"
        caption += f"\n🎭 **Language:** {movie_data.get('language', 'English')}"
        caption += f"\n⭐ **Quality:** {movie_data.get('quality', '480p')}"
        
        return caption

class BotUtils:
    @staticmethod
    def get_welcome_message(first_name: str) -> str:
        """Generate welcome message"""
        return f"""ʜᴇʏ {first_name}, ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ 🌞

ɪ ᴀᴍ ᴛʜᴇ ᴍᴏsᴛ ᴘᴏᴡᴇʀғᴜʟ ᴀᴜᴛᴏ ғɪʟᴛᴇʀ ʙᴏᴛ ᴡɪᴛʜ ᴘʀᴇᴍɪᴜᴍ 
I ᴄᴀɴ ᴘʀᴏᴠɪᴅᴇ ᴍᴏᴠɪᴇs ᴊᴜsᴛ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴏʀ sᴇɴᴅ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ᴀɴᴅ ᴇɴᴊᴏʏ
Nᴇᴇᴅ Pʀᴇᴍɪᴜᴍ 👉🏻 /plan"""

    @staticmethod
    def get_premium_plans() -> str:
        """Generate premium plans message"""
        return """🎬 **FILMZI PREMIUM PLANS** 🎬

✨ **BASIC PLAN**
• ₹99/month
• Access to all movies
• Faster downloads
• Ad-free experience

✨ **PRO PLAN** 
• ₹249/3 months
• All Basic features
• Priority support
• Early access to new releases

✨ **ULTIMATE PLAN**
• ₹799/year
• All Pro features
• 4K streaming
• Multiple devices

💳 **Payment Methods:** UPI, Credit Card, PayPal

Click /start to go back"""
