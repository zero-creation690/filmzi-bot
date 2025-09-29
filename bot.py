import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from database import db
import asyncio

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
CHANNEL_ID = os.getenv('CHANNEL_ID')

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
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("debug", self.debug_command))
        self.application.add_handler(CommandHandler("searchdb", self.search_db_command))
        
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
        
        keyboard = [
            [InlineKeyboardButton("🔍 Search Movies", switch_inline_query_current_chat="")],
            [InlineKeyboardButton("📊 Stats", callback_data="stats"),
             InlineKeyboardButton("💎 Premium", callback_data="premium")]
        ]
        
        try:
            await update.message.reply_photo(
                photo='https://ar-hosting.pages.dev/1759107724318.jpg',
                caption=welcome_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            await update.message.reply_text(welcome_text, parse_mode='HTML')
    
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
    
    async def stats_command(self, update: Update, context: CallbackContext):
        cursor = db.conn.cursor()
        
        # Get total movies count
        cursor.execute('SELECT COUNT(*) FROM movies')
        total_movies = cursor.fetchone()[0]
        
        # Get total users count
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Get recent movies
        cursor.execute('SELECT title FROM movies ORDER BY id DESC LIMIT 3')
        recent_movies = [row[0] for row in cursor.fetchall()]
        
        stats_text = f"""📊 <b>Filmzi Bot Statistics</b>

🎬 Total Movies: <b>{total_movies}</b>
👥 Total Users: <b>{total_users}</b>
⚡ Status: <b>Online</b>

<b>Recent Movies:</b>
"""
        for i, movie in enumerate(recent_movies, 1):
            stats_text += f"{i}. {movie}\n"
        
        stats_text += "\n💡 <i>Use /plan to upgrade to premium</i>"
        
        await update.message.reply_text(stats_text, parse_mode='HTML')
    
    async def debug_command(self, update: Update, context: CallbackContext):
        """Debug command to check database status"""
        cursor = db.conn.cursor()
        
        # Get all movies
        cursor.execute('SELECT id, title, file_size, quality, year FROM movies ORDER BY id DESC LIMIT 10')
        movies = cursor.fetchall()
        
        debug_text = f"🔧 <b>Debug Information</b>\n\n"
        debug_text += f"📁 Total Movies: {len(movies)}\n\n"
        
        if movies:
            debug_text += "<b>Recent Movies in DB:</b>\n"
            for movie in movies:
                movie_id, title, file_size, quality, year = movie
                debug_text += f"• {title} ({year}) - {quality} - {file_size}\n"
        else:
            debug_text += "❌ No movies found in database!\n"
            debug_text += "Check if channel monitor is running and can access your channel."
        
        await update.message.reply_text(debug_text, parse_mode='HTML')
    
    async def search_db_command(self, update: Update, context: CallbackContext):
        """Search the database directly"""
        if not context.args:
            await update.message.reply_text("Usage: /searchdb <movie_name>")
            return
        
        query = ' '.join(context.args)
        cursor = db.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM movies 
            WHERE title LIKE ? 
            ORDER BY id DESC
        ''', (f'%{query}%',))
        
        results = cursor.fetchall()
        
        if not results:
            await update.message.reply_text(f"❌ No results in DB for: <b>{query}</b>", parse_mode='HTML')
            return
        
        response_text = f"🔍 <b>Database Results for:</b> {query}\n\n"
        
        for movie in results[:5]:
            movie_id, title, file_id, file_size, quality, year, created_at = movie
            response_text += f"🎬 <b>{title}</b>\n"
            response_text += f"   📊 {quality} | 💾 {file_size} | 🗓️ {year}\n"
            response_text += f"   🆔 {movie_id}\n\n"
        
        await update.message.reply_text(response_text, parse_mode='HTML')
    
    async def handle_search(self, update: Update, context: CallbackContext):
        query = update.message.text
        user_id = update.effective_user.id
        
        # Add to search history
        db.add_search_history(user_id, query)
        
        # Search for movies
        results = db.search_movies(query)
        
        if not results:
            # Try fuzzy search
            cursor = db.conn.cursor()
            cursor.execute('''
                SELECT * FROM movies 
                WHERE title LIKE ? 
                ORDER BY id DESC
            ''', (f'%{query}%',))
            results = cursor.fetchall()
        
        if not results:
            await update.message.reply_text(
                f"❌ No results found for: <b>{query}</b>\n\n"
                f"Try with different keywords or check the spelling.\n"
                f"Use /debug to check database status.",
                parse_mode='HTML'
            )
            return
        
        # Format results
        response_text = f"🎬 <b>Search Results for:</b> {query}\n"
        response_text += f"📁 <b>Total Files:</b> {len(results)}\n"
        response_text += f"⚡ <b>Result in:</b> 0.5 seconds\n\n"
        
        keyboard = []
        for movie in results[:5]:  # Show first 5 results
            movie_id, title, file_id, file_size, quality, year, created_at = movie
            response_text += f"✅ {title} ({year})\n"
            response_text += f"   🎞️ {quality} | 💾 {file_size}\n\n"
            
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
        elif data == 'stats':
            await self.stats_callback(query)
        elif data == 'premium':
            await self.plan_callback(query)
    
    async def send_movie_file(self, query, movie_id):
        # Get movie details from database
        cursor = db.conn.cursor()
        cursor.execute('SELECT * FROM movies WHERE id = ?', (movie_id,))
        movie = cursor.fetchone()
        
        if not movie:
            await query.edit_message_text("❌ Movie not found in database!")
            return
        
        movie_id, title, file_id, file_size, quality, year, created_at = movie
        
        try:
            # Send the movie file
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
                f"❌ Error sending file: {str(e)}\n\nPlease try again later."
            )
    
    async def stats_callback(self, query):
        cursor = db.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM movies')
        total_movies = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        stats_text = f"""📊 <b>Filmzi Bot Statistics</b>

🎬 Total Movies: <b>{total_movies}</b>
👥 Total Users: <b>{total_users}</b>
⚡ Status: <b>Online</b>

💡 <i>Use /plan to upgrade to premium</i>"""
        
        await query.edit_message_text(stats_text, parse_mode='HTML')
    
    async def plan_callback(self, query):
        plan_text = """🎬 <b>Filmzi Premium Plans</b> 🎬

<b>✨ Basic Plan</b>
• Unlimited movie searches
• HD quality downloads
• Priority support
• ₹99/month

To subscribe, contact @your_admin_username"""
        
        await query.edit_message_text(plan_text, parse_mode='HTML')

    def run(self):
        logger.info("Starting Filmzi Bot...")
        self.application.run_polling()

if __name__ == '__main__':
    bot = FilmziBot()
    bot.run()
