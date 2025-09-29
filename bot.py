import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from database import db
import asyncio
import aiohttp

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FilmziBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("plan", self.plan_command))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_search))
        
        # Callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
    
    async def start_command(self, update: Update, context: CallbackContext):
        user = update.effective_user
        db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        welcome_text = f"""ʜᴇʏ {user.first_name}, ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ 🌞

ɪ ᴀᴍ ᴛʜᴇ ᴍᴏsᴛ ᴘᴏᴡᴇʀғᴜʟ ᴀᴜᴛᴏ ғɪʟᴛᴇʀ ʙᴏᴛ ᴡɪᴛʜ ᴘʀᴇᴍɪᴜᴍ 
I ᴄᴀɴ ᴘʀᴏᴠɪᴅᴇ ᴍᴏᴠɪᴇs ᴊᴜsᴛ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴏʀ sᴇɴᴅ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ᴀɴᴅ ᴇɴᴊᴏʏ
Nᴇᴇᴅ Pʀᴇᴍɪᴜᴍ 👉🏻 /plan"""
        
        await update.message.reply_photo(
            photo='https://ar-hosting.pages.dev/1759107724318.jpg',
            caption=welcome_text,
            parse_mode='HTML'
        )
    
    async def plan_command(self, update: Update, context: CallbackContext):
        plan_text = """🎬 <b>Filmzi Premium Plans</b> 🎬

<b>✨ Basic Plan</b>
• Unlimited movie searches
• HD quality downloads
• Priority support
• ₹99/month

<b>🚀 Pro Plan</b>
• All Basic features
• 4K quality available
• Early access to new releases
• Multiple downloads
• ₹199/month

<b>💎 Enterprise Plan</b>
• All Pro features
• Custom requests
• Dedicated support
• Group access
• ₹499/month

To subscribe, contact @your_admin_username"""
        
        await update.message.reply_text(plan_text, parse_mode='HTML')
    
    async def handle_search(self, update: Update, context: CallbackContext):
        query = update.message.text
        user_id = update.effective_user.id
        
        # Add to search history
        db.add_search_history(user_id, query)
        
        # Search for movies
        results = db.search_movies(query)
        
        if not results:
            await update.message.reply_text(
                f"❌ No results found for: <b>{query}</b>\n\nTry with different keywords or check the spelling.",
                parse_mode='HTML'
            )
            return
        
        # Format results
        response_text = f"🎬 <b>Search Results for:</b> {query}\n\n"
        
        keyboard = []
        for movie in results[:5]:  # Show first 5 results
            movie_id, title, file_id, file_size, quality, year, created_at = movie
            response_text += f"📁 <b>{title}</b>\n"
            response_text += f"   🎞️ Quality: {quality}\n"
            response_text += f"   💾 Size: {file_size}\n"
            response_text += f"   🗓️ Year: {year}\n\n"
            
            keyboard.append([InlineKeyboardButton(
                f"📥 Download {quality}",
                callback_data=f"download_{movie_id}"
            )])
        
        response_text += "🔍 <i>Click the buttons below to download</i>"
        
        await update.message.reply_text(
            response_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    async def handle_callback(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith('download_'):
            movie_id = data.split('_')[1]
            await self.send_movie_file(query, movie_id)
    
    async def send_movie_file(self, query, movie_id):
        # Get movie details from database
        cursor = db.conn.cursor()
        cursor.execute('SELECT * FROM movies WHERE id = ?', (movie_id,))
        movie = cursor.fetchone()
        
        if not movie:
            await query.edit_message_text("❌ Movie not found!")
            return
        
        movie_id, title, file_id, file_size, quality, year, created_at = movie
        
        try:
            # Forward the movie file from channel
            await query.message.reply_document(
                document=file_id,
                caption=f"""🎬 <b>{title}</b>

📊 Quality: {quality}
💾 Size: {file_size}
🗓️ Year: {year}

<b>⚠️ IMPORTANT:</b>
• File will be deleted in 10 minutes due to copyright
• Forward this file to saved messages immediately
• Use VLC Media Player for best experience

<b>🎉 Enjoy your movie!</b>""",
                parse_mode='HTML'
            )
            
            # Edit original message to show success
            await query.edit_message_text(
                f"✅ <b>Download started for:</b> {title}\n\n"
                f"📊 <b>Quality:</b> {quality}\n"
                f"💾 <b>Size:</b> {file_size}\n\n"
                f"<i>Check above message for download link!</i>",
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error sending file: {e}")
            await query.edit_message_text(
                "❌ Error sending file. Please try again later."
            )

    def run(self):
        self.application.run_polling()

if __name__ == '__main__':
    bot = FilmziBot()
    bot.run()
