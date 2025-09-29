import os
import logging
import sqlite3
import asyncio
import random
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, Message
)
from pyrogram.errors import FloodWait

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

# Bot instance
app = Client(
    "filmzi_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Database setup
def init_db():
    conn = sqlite3.connect('filmzi.db')
    c = conn.cursor()
    
    # Movies table
    c.execute('''CREATE TABLE IF NOT EXISTS movies
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  file_id TEXT NOT NULL,
                  file_name TEXT NOT NULL,
                  file_size INTEGER,
                  file_type TEXT,
                  message_id INTEGER,
                  UNIQUE(file_id))''')
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  first_name TEXT,
                  username TEXT,
                  joined_date TEXT)''')
    
    conn.commit()
    conn.close()

# Database functions
def add_movie(file_id, file_name, file_size, file_type, message_id):
    try:
        conn = sqlite3.connect('filmzi.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO movies VALUES (NULL, ?, ?, ?, ?, ?)",
                  (file_id, file_name, file_size, file_type, message_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False

def search_movies(query):
    conn = sqlite3.connect('filmzi.db')
    c = conn.cursor()
    search_term = f"%{query}%"
    c.execute("SELECT * FROM movies WHERE file_name LIKE ? LIMIT 50", (search_term,))
    results = c.fetchall()
    conn.close()
    return results

def get_total_movies():
    conn = sqlite3.connect('filmzi.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM movies")
    count = c.fetchone()[0]
    conn.close()
    return count

def add_user(user_id, first_name, username):
    try:
        from datetime import datetime
        conn = sqlite3.connect('filmzi.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)",
                  (user_id, first_name, username, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error adding user: {e}")

# Welcome messages
WELCOME_TEXT = """ʜᴇʏ {}, ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ 🌞

ɪ ᴀᴍ ᴛʜᴇ ᴍᴏsᴛ ᴘᴏᴡᴇʀғᴜʟ ᴀᴜᴛᴏ ғɪʟᴛᴇʀ ʙᴏᴛ ᴡɪᴛʜ ᴘʀᴇᴍɪᴜᴍ
I ᴄᴀɴ ᴘʀᴏᴠɪᴅᴇ ᴍᴏᴠɪᴇs ᴊᴜsᴛ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴏʀ sᴇɴᴅ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ᴀɴᴅ ᴇɴᴊᴏʏ

Nᴇᴇᴅ Pʀᴇᴍɪᴜᴍ 👉🏻 /plan"""

WELCOME_PHOTO = "https://ar-hosting.pages.dev/1759107724318.jpg"

# Reactions for messages
REACTIONS = ["👍", "❤️", "🔥", "🎉", "😍"]

# Start command
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    user = message.from_user
    add_user(user.id, user.first_name, user.username)
    
    # Get user's first name
    first_name = user.first_name
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ 🎬", 
                               url=f"https://t.me/{(await client.get_me()).username}?startgroup=true")
        ],
        [
            InlineKeyboardButton("⭐ ᴛᴏᴘ sᴇᴀʀᴄʜɪɴɢ", callback_data="top_searching"),
            InlineKeyboardButton("📢 ʜᴇʟᴘ", callback_data="help")
        ],
        [
            InlineKeyboardButton("📚 ᴀʙᴏᴜᴛ", callback_data="about"),
            InlineKeyboardButton("💰 ᴇᴀʀɴ ᴍᴏɴᴇʏ", callback_data="earn")
        ]
    ])
    
    try:
        await message.reply_photo(
            photo=WELCOME_PHOTO,
            caption=WELCOME_TEXT.format(first_name),
            reply_markup=buttons
        )
    except:
        await message.reply_text(
            text=WELCOME_TEXT.format(first_name),
            reply_markup=buttons
        )

# Auto-filter for private chat
@app.on_message(filters.private & filters.text & ~filters.command(['start', 'plan', 'help']))
async def auto_filter_private(client, message: Message):
    query = message.text
    user = message.from_user
    
    # Add user to database
    add_user(user.id, user.first_name, user.username)
    
    # Send searching message
    search_msg = await message.reply_text(f"🔍 sᴇᴀʀᴄʜɪɴɢ {query}")
    
    # Search in database
    results = search_movies(query)
    
    if not results:
        await search_msg.edit_text(
            f"❌ ɴᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ ғᴏʀ '{query}'\n\n"
            "ᴘʟᴇᴀsᴇ ᴛʀʏ:\n"
            "• ᴄʜᴇᴄᴋɪɴɢ ʏᴏᴜʀ sᴘᴇʟʟɪɴɢ\n"
            "• ᴜsɪɴɢ ᴅɪғғᴇʀᴇɴᴛ ᴋᴇʏᴡᴏʀᴅs"
        )
        return
    
    await search_msg.delete()
    
    # Prepare results display
    buttons = []
    for idx, movie in enumerate(results[:10], 1):
        file_name = movie[2]
        file_id = movie[1]
        buttons.append([InlineKeyboardButton(
            f"📁 {file_name}",
            callback_data=f"file_{file_id}"
        )])
    
    buttons.append([
        InlineKeyboardButton("🚫 ᴄʟᴏsᴇ 🚫", callback_data="close")
    ])
    
    total = len(results)
    await message.reply_text(
        f"🎯 ᴛɪᴛʟᴇ : {query}\n"
        f"📊 ᴛᴏᴛᴀʟ ғɪʟᴇs : {total}\n"
        f"📝 ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ : {user.mention}\n"
        f"⏱️ ʀᴇsᴜʟᴛ ɪɴ : 0.5 sᴇᴄᴏɴᴅs\n\n"
        f"🌳 ʀᴇǫᴜᴇsᴛᴇᴅ ғɪʟᴇs 👇",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Auto-filter for groups
@app.on_message(filters.group & filters.text & ~filters.command(['start']))
async def auto_filter_group(client, message: Message):
    query = message.text
    
    # Search in database
    results = search_movies(query)
    
    if not results:
        return
    
    # Send searching message
    search_msg = await message.reply_text(f"🔍 sᴇᴀʀᴄʜɪɴɢ {query}")
    
    await asyncio.sleep(0.5)
    await search_msg.delete()
    
    # Prepare results display
    buttons = []
    for idx, movie in enumerate(results[:10], 1):
        file_name = movie[2]
        file_id = movie[1]
        buttons.append([InlineKeyboardButton(
            f"📁 {file_name}",
            callback_data=f"file_{file_id}"
        )])
    
    buttons.append([
        InlineKeyboardButton("🚫 ᴄʟᴏsᴇ 🚫", callback_data="close")
    ])
    
    total = len(results)
    await message.reply_text(
        f"🎯 ᴛɪᴛʟᴇ : {query}\n"
        f"📊 ᴛᴏᴛᴀʟ ғɪʟᴇs : {total}\n"
        f"📝 ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ : {message.from_user.mention}\n"
        f"⏱️ ʀᴇsᴜʟᴛ ɪɴ : 0.5 sᴇᴄᴏɴᴅs\n\n"
        f"🌳 ʀᴇǫᴜᴇsᴛᴇᴅ ғɪʟᴇs 👇",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Handle file callback
@app.on_callback_query(filters.regex(r"^file_"))
async def send_file(client, callback_query: CallbackQuery):
    file_id = callback_query.data.split("_")[1]
    
    try:
        # Get file info
        conn = sqlite3.connect('filmzi.db')
        c = conn.cursor()
        c.execute("SELECT * FROM movies WHERE file_id = ?", (file_id,))
        movie = c.fetchone()
        conn.close()
        
        if not movie:
            await callback_query.answer("❌ ғɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ!", show_alert=True)
            return
        
        file_name = movie[2]
        message_id = movie[5]
        
        # Get the file from channel
        try:
            file_msg = await client.get_messages(CHANNEL_ID, message_id)
            
            # Create buttons
            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🚀 ғᴀsᴛ ᴅᴏᴡɴʟᴏᴀᴅ 🚀", callback_data=f"download_{file_id}"),
                    InlineKeyboardButton("📺 ᴡᴀᴛᴄʜ ᴏɴʟɪɴᴇ 📺", callback_data=f"stream_{file_id}")
                ],
                [
                    InlineKeyboardButton("📢 ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ 📢", url="https://t.me/your_channel")
                ]
            ])
            
            # Send file with caption
            caption = (
                f"📁 {file_name}\n\n"
                f"⚡ Pᴏᴡᴇʀᴇᴅ Bʏ : [BotzWala]\n\n"
                f"Iғ Yᴏᴜ Aʀᴇ Fᴀᴄɪɴɢ Aɴʏ Sᴏᴜɴᴅ Issᴜᴇ\n"
                f"Tʜᴇɴ ᴜsᴇ ᴀ VLC Mᴇᴅɪᴀ Pʟᴀʏᴇʀ"
            )
            
            if file_msg.video:
                await callback_query.message.reply_video(
                    video=file_msg.video.file_id,
                    caption=caption,
                    reply_markup=buttons
                )
            elif file_msg.document:
                await callback_query.message.reply_document(
                    document=file_msg.document.file_id,
                    caption=caption,
                    reply_markup=buttons
                )
            
            # Send auto-delete warning
            warning_msg = await callback_query.message.reply_text(
                "❗❗❗ IMPORTANT ❗❗❗\n\n"
                "THIS MOVIE FILE/VIDEO WILL BE DELETED IN 10 MINUTE 😬 "
                "(DUE TO COPYRIGHT ISSUES).\n\n"
                "PLEASE FORWARD THIS FILE TO SOMEWHERE ELSE AND START DOWNLOADING THERE"
            )
            
            # Delete warning after 2 minutes
            await asyncio.sleep(120)
            try:
                await warning_msg.delete()
            except:
                pass
            
            # React to the callback
            try:
                await callback_query.message.react(random.choice(REACTIONS))
            except:
                pass
            
            await callback_query.answer("✅ ғɪʟᴇ sᴇɴᴛ!")
            
        except Exception as e:
            logger.error(f"Error sending file: {e}")
            await callback_query.answer("❌ ᴇʀʀᴏʀ sᴇɴᴅɪɴɢ ғɪʟᴇ!", show_alert=True)
            
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await callback_query.answer("❌ sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ!", show_alert=True)

# Handle download callback
@app.on_callback_query(filters.regex(r"^download_"))
async def generate_download_link(client, callback_query: CallbackQuery):
    file_id = callback_query.data.split("_")[1]
    
    # Simulate link generation
    await callback_query.answer("🔗 ɢᴇɴᴇʀᴀᴛɪɴɢ ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ...", show_alert=True)
    
    # Send link generated message
    await callback_query.message.reply_text(
        "👁️ LINK GENERATED ☠️⚔️\n\n"
        "⚡ Fast Download Link: [Click Here](https://example.com/download)\n\n"
        "Note: Link expires in 24 hours"
    )

# Handle stream callback
@app.on_callback_query(filters.regex(r"^stream_"))
async def generate_stream_link(client, callback_query: CallbackQuery):
    file_id = callback_query.data.split("_")[1]
    
    await callback_query.answer("🎬 ɢᴇɴᴇʀᴀᴛɪɴɢ sᴛʀᴇᴀᴍ ʟɪɴᴋ...", show_alert=True)
    
    # Send stream link
    await callback_query.message.reply_text(
        "📺 STREAM LINK GENERATED\n\n"
        "🎥 Watch Online: [Click Here](https://example.com/stream)\n\n"
        "Powered by Plyr Player"
    )

# Other callbacks
@app.on_callback_query(filters.regex(r"^(close|help|about|earn|top_searching)$"))
async def handle_callbacks(client, callback_query: CallbackQuery):
    data = callback_query.data
    
    if data == "close":
        await callback_query.message.delete()
        await callback_query.answer("ᴄʟᴏsᴇᴅ!")
    
    elif data == "help":
        await callback_query.answer(
            "📢 Help\n\n"
            "Just send movie name and I'll send you the files!\n"
            "Add me to your group for auto-filter.",
            show_alert=True
        )
    
    elif data == "about":
        total_movies = get_total_movies()
        await callback_query.answer(
            f"ℹ️ About\n\n"
            f"Bot: Filmzi Movie Bot\n"
            f"Total Movies: {total_movies}\n"
            f"Developer: @BotzWala",
            show_alert=True
        )
    
    elif data == "earn":
        await callback_query.answer(
            "💰 Earn Money\n\n"
            "Refer friends and earn rewards!",
            show_alert=True
        )
    
    elif data == "top_searching":
        await callback_query.answer(
            "⭐ Top Searching Movies\n\n"
            "Coming Soon!",
            show_alert=True
        )

# Channel post handler (for indexing)
@app.on_message(filters.channel & (filters.video | filters.document))
async def index_files(client, message: Message):
    if message.chat.id != CHANNEL_ID:
        return
    
    try:
        if message.video:
            file_id = message.video.file_id
            file_name = message.video.file_name or "Unknown"
            file_size = message.video.file_size
            file_type = "video"
        elif message.document:
            file_id = message.document.file_id
            file_name = message.document.file_name or "Unknown"
            file_size = message.document.file_size
            file_type = "document"
        else:
            return
        
        message_id = message.id
        
        # Add to database
        if add_movie(file_id, file_name, file_size, file_type, message_id):
            logger.info(f"Indexed: {file_name}")
    
    except Exception as e:
        logger.error(f"Indexing error: {e}")

# Main function
if __name__ == "__main__":
    # Initialize database
    init_db()
    
    logger.info("Bot started successfully!")
    logger.info("Initializing Filmzi Bot...")
    
    # Run the bot
    app.run()
