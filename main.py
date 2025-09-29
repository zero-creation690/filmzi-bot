import os
import logging
import asyncio
import sqlite3
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    BotCommand
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    CallbackQueryHandler,
    ApplicationBuilder
)
import aiohttp
from aiohttp import web
import threading

from config import Config
from database import Database
from utils import MovieUtils, BotUtils

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FilmziBot:
    def __init__(self):
        self.config = Config()
        self.db = Database(self.config.DB_NAME)
        self.movie_utils = MovieUtils()
        self.bot_utils = BotUtils()
        self.application = None
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message when command /start is issued."""
        try:
            user = update.effective_user
            
            # Add user to database
            self.db.add_user(
                user.id, 
                user.username, 
                user.first_name, 
                user.last_name or ""
            )
            
            welcome_text = self.bot_utils.get_welcome_message(user.first_name)
            
            # Send welcome message with image
            await update.message.reply_photo(
                photo=self.config.WELCOME_IMAGE,
                caption=welcome_text,
                reply_markup=self.get_main_keyboard(),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("🚫 An error occurred. Please try again.")
    
    async def plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show premium plans"""
        try:
            plans_text = self.bot_utils.get_premium_plans()
            
            keyboard = [
                [InlineKeyboardButton("💳 Buy Premium", callback_data="buy_premium")],
                [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(plans_text, reply_markup=reply_markup, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in plan command: {e}")
            await update.message.reply_text("🚫 An error occurred. Please try again.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help message"""
        help_text = """
🤖 **Filmzi Bot Help**

**Available Commands:**
/start - Start the bot
/plan - View premium plans  
/help - Show this help message
/request - Request a movie

**How to Use:**
1. Simply type the movie name you want to search
2. Select the quality you prefer
3. Download or stream the movie

**Support:**
For issues contact @your_admin
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle movie search requests"""
        try:
            query = update.message.text.strip()
            
            if len(query) < 2:
                await update.message.reply_text("🔍 Please enter at least 2 characters to search.")
                return
            
            # Show searching message
            search_msg = await update.message.reply_text(f"🔍 Searching for '{query}'...")
            
            # Add quote reaction (using text emoji)
            await update.message.reply_text("💭")
            
            # Search in database
            results = self.db.search_movies(query, self.config.MAX_RESULTS)
            
            if not results:
                await search_msg.edit_text(
                    f"❌ No results found for '{query}'\n\n"
                    "If you can't find your movie, please:\n"
                    "• Check the spelling\n" 
                    "• Use /request to request it\n"
                    "• Try different keywords"
                )
                return
            
            # Format results
            response_text = f"**🎬 Search Results for '{query}'**\n\n"
            
            for i, movie in enumerate(results, 1):
                response_text += f"**{i}.** {movie['movie_name']}"
                if movie.get('year'):
                    response_text += f" ({movie['year']})"
                response_text += f"\n   📁 {movie.get('quality', '480p')} | 📊 {movie.get('file_size', 'N/A')}\n\n"
            
            # Create keyboard with results
            keyboard = []
            for movie in results[:5]:
                btn_text = f"🎬 {movie['movie_name'][:20]}..."
                if movie.get('year'):
                    btn_text += f" ({movie['year']})"
                keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"select_{movie['id']}")])
            
            if len(results) > 5:
                keyboard.append([InlineKeyboardButton("🔍 More Results", callback_data=f"more_{query}")])
            
            keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await search_msg.edit_text(response_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text("🚫 An error occurred while searching. Please try again.")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        try:
            query = update.callback_query
            await query.answer()
            
            data = query.data
            
            if data == "main_menu":
                await self.show_main_menu(query)
            elif data == "buy_premium":
                await self.show_premium_purchase(query)
            elif data.startswith("select_"):
                movie_id = int(data.split("_")[1])
                await self.send_movie_details(query, movie_id)
            elif data.startswith("more_"):
                search_query = data.split("_", 1)[1]
                await self.show_more_results(query, search_query)
            elif data.startswith("quality_"):
                parts = data.split("_")
                movie_id = int(parts[1])
                quality = parts[2]
                await self.send_download_options(query, movie_id, quality)
            elif data.startswith("dl_"):
                file_id = data.split("_")[1]
                await self.send_file(query, file_id)
            elif data.startswith("all_"):
                movie_name = data.split("_", 1)[1]
                await self.send_all_qualities(query, movie_name)
                
        except Exception as e:
            logger.error(f"Error in button handler: {e}")
            try:
                await query.edit_message_text("🚫 An error occurred. Please try again.")
            except:
                pass
    
    async def show_main_menu(self, query):
        """Show main menu"""
        user = query.from_user
        welcome_text = self.bot_utils.get_welcome_message(user.first_name)
        
        await query.message.reply_photo(
            photo=self.config.WELCOME_IMAGE,
            caption=welcome_text,
            reply_markup=self.get_main_keyboard(),
            parse_mode='Markdown'
        )
    
    async def show_premium_purchase(self, query):
        """Show premium purchase options"""
        purchase_text = """💳 **Premium Purchase**

To purchase premium, please contact our admin @your_admin with your preferred plan.

We accept:
• UPI Payments
• Credit/Debit Cards  
• PayPal
• Cryptocurrency

**Benefits:**
✅ Ad-free experience
✅ Faster downloads
✅ Priority support
✅ Early access to new releases"""

        keyboard = [
            [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/your_admin")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(purchase_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def send_movie_details(self, query, movie_id: int):
        """Send movie details with quality options"""
        movie = self.db.get_movie_by_id(movie_id)
        if not movie:
            await query.edit_message_text("❌ Movie not found in database!")
            return
        
        # Get all available qualities for this movie
        all_movies = self.db.get_movies_by_name(movie['movie_name'])
        
        text = self.movie_utils.create_movie_caption(movie)
        text += "\n\n**Available Qualities:**"
        
        keyboard = []
        for mov in all_movies:
            keyboard.append([
                InlineKeyboardButton(
                    f"📹 {mov['quality']} ({mov['file_size']})", 
                    callback_data=f"quality_{mov['id']}_{mov['quality']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("📤 All Qualities", callback_data=f"all_{movie['movie_name']}")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Search", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def send_download_options(self, query, movie_id: int, quality: str):
        """Send download and streaming options"""
        movie = self.db.get_movie_by_id(movie_id)
        if not movie:
            await query.edit_message_text("❌ File not found!")
            return
        
        warning_text = "⚠️ **IMPORTANT** ⚠️\n\n"
        warning_text += "THIS MOVIE FILE/VIDEO WILL BE DELETED IN 10 MINUTES (DUE TO COPYRIGHT ISSUES).\n\n"
        warning_text += "PLEASE FORWARD THIS FILE TO SAVED MESSAGES AND START DOWNLOADING THERE\n\n"
        
        caption = f"**{movie['movie_name']}**\nQuality: {quality}\n\n{warning_text}"
        
        keyboard = [
            [InlineKeyboardButton("🚀 Fast Download", callback_data=f"dl_{movie['file_id']}")],
            [InlineKeyboardButton("🔙 Back", callback_data=f"select_{movie_id}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send the actual file
        try:
            await query.message.reply_document(
                document=movie['file_id'],
                caption=caption,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            await query.edit_message_text("✅ File sent! Check above message.")
        except Exception as e:
            logger.error(f"Error sending file: {e}")
            await query.edit_message_text("❌ Error sending file. File might be expired or deleted.")
    
    async def send_file(self, query, file_id: str):
        """Send file directly"""
        try:
            await query.message.reply_document(
                document=file_id,
                caption="🚀 **Fast Download**\n\nPlease save this file quickly!",
                parse_mode='Markdown'
            )
            await query.answer("File sent! ✅")
        except Exception as e:
            logger.error(f"Error sending file: {e}")
            await query.answer("❌ Error sending file. File might be expired.", show_alert=True)
    
    async def send_all_qualities(self, query, movie_name: str):
        """Send all available qualities for a movie"""
        movies = self.db.get_movies_by_name(movie_name)
        
        if not movies:
            await query.edit_message_text("❌ No qualities found for this movie!")
            return
        
        text = f"**🎬 {movie_name} - All Qualities**\n\n"
        
        for movie in movies:
            text += f"• **{movie['quality']}** - {movie['file_size']}\n"
        
        keyboard = []
        for movie in movies:
            keyboard.append([
                InlineKeyboardButton(
                    f"📥 Download {movie['quality']}", 
                    callback_data=f"quality_{movie['id']}_{movie['quality']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_more_results(self, query, search_query: str):
        """Show more search results"""
        results = self.db.search_movies(search_query, 20)
        
        if not results:
            await query.edit_message_text("❌ No more results found!")
            return
        
        text = f"**🔍 More Results for '{search_query}'**\n\n"
        
        for i, movie in enumerate(results, 1):
            text += f"**{i}.** {movie['movie_name']}"
            if movie.get('year'):
                text += f" ({movie['year']})"
            text += f"\n   📁 {movie.get('quality', '480p')} | 📊 {movie.get('file_size', 'N/A')}\n\n"
        
        keyboard = []
        for movie in results:
            keyboard.append([
                InlineKeyboardButton(
                    f"🎬 {movie['movie_name'][:25]}...", 
                    callback_data=f"select_{movie['id']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    def get_main_keyboard(self):
        """Get main menu keyboard"""
        bot_username = (self.config.BOT_TOKEN or 'bot').split(':')[0]
        keyboard = [
            [InlineKeyboardButton("🎬 Search Movies", switch_inline_query_current_chat="")],
            [InlineKeyboardButton("💎 Premium Plans", callback_data="buy_premium")],
            [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/your_admin")],
            [InlineKeyboardButton("🤖 Add to Group", url=f"https://t.me/{bot_username}?startgroup=true")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def setup_commands(self, application):
        """Setup bot commands"""
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("plan", "Premium plans"),
            BotCommand("help", "Get help"),
            BotCommand("request", "Request a movie")
        ]
        await application.bot.set_my_commands(commands)
    
    async def health_check(self, request):
        """Health check endpoint for Koyeb"""
        return web.Response(text="OK", status=200)
    
    async def start_web_server(self):
        """Start web server for health checks"""
        app = web.Application()
        app.router.add_get('/health', self.health_check)
        app.router.add_get('/', self.health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', self.config.PORT)
        await site.start()
        logger.info(f"Web server started on port {self.config.PORT}")
    
    async def run(self):
        """Run the bot"""
        try:
            # Validate configuration
            self.config.validate_config()
            
            # Create application
            self.application = ApplicationBuilder()\
                .token(self.config.BOT_TOKEN)\
                .build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(CommandHandler("plan", self.plan))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            self.application.add_handler(CallbackQueryHandler(self.button_handler))
            
            # Setup commands
            await self.setup_commands(self.application)
            
            # Start web server for health checks
            await self.start_web_server()
            
            logger.info("Filmzi Bot is starting...")
            
            # Start polling
            await self.application.run_polling()
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise

def main():
    """Main function to run the bot"""
    # Check if required environment variables are set
    required_vars = ['BOT_TOKEN', 'API_ID', 'API_HASH', 'CHANNEL_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your Koyeb environment settings.")
        return
    
    bot = FilmziBot()
    
    try:
        # Run the bot
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        bot.db.close_connection()
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        bot.db.close_connection()

if __name__ == '__main__':
    main()
