from flask import Flask, render_template_string, Response, request
import os
import hashlib
import time
from pyrogram import Client
import asyncio
from threading import Thread

app = Flask(__name__)

# Bot credentials
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))

# Initialize Pyrogram client for streaming
streaming_client = Client(
    "streaming_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# HTML template for Plyr player
PLAYER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ movie_name }} - Filmzi Streaming</title>
    
    <!-- Plyr CSS -->
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            width: 100%;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            text-align: center;
            color: white;
        }
        
        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 1.1em;
        }
        
        .player-wrapper {
            padding: 40px;
            background: #000;
        }
        
        video {
            width: 100%;
            border-radius: 10px;
        }
        
        .info-section {
            padding: 30px;
            background: #f8f9fa;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .info-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .info-card h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 0.9em;
            text-transform: uppercase;
        }
        
        .info-card p {
            color: #333;
            font-size: 1.1em;
            font-weight: 600;
        }
        
        .footer {
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
        }
        
        .footer a {
            color: #667eea;
            text-decoration: none;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.5em;
            }
            
            .player-wrapper {
                padding: 20px;
            }
            
            .info-section {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 {{ movie_name }}</h1>
            <p>Powered by Filmzi Streaming</p>
        </div>
        
        <div class="player-wrapper">
            <video 
                id="player" 
                playsinline 
                controls
                poster="{{ poster }}"
            >
                <source src="/stream/{{ file_id }}" type="video/mp4">
                Your browser doesn't support video playback.
            </video>
        </div>
        
        <div class="info-section">
            <h2>📊 Movie Information</h2>
            <div class="info-grid">
                <div class="info-card">
                    <h3>Quality</h3>
                    <p>{{ quality }}</p>
                </div>
                <div class="info-card">
                    <h3>Size</h3>
                    <p>{{ size }}</p>
                </div>
                <div class="info-card">
                    <h3>Format</h3>
                    <p>{{ format }}</p>
                </div>
                <div class="info-card">
                    <h3>Status</h3>
                    <p>✅ Available</p>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>⚡ Powered by <a href="https://t.me/filmzi_bot">Filmzi Movie Bot</a></p>
            <p style="margin-top: 10px; font-size: 0.9em; opacity: 0.8;">
                © 2025 BotzWala. All rights reserved.
            </p>
        </div>
    </div>
    
    <!-- Plyr JS -->
    <script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>
    
    <script>
        // Initialize Plyr
        const player = new Plyr('#player', {
            controls: [
                'play-large',
                'play',
                'progress',
                'current-time',
                'duration',
                'mute',
                'volume',
                'settings',
                'pip',
                'airplay',
                'fullscreen'
            ],
            settings: ['quality', 'speed'],
            quality: {
                default: 720,
                options: [1080, 720, 480, 360]
            },
            speed: {
                selected: 1,
                options: [0.5, 0.75, 1, 1.25, 1.5, 2]
            }
        });
        
        // Add event listeners
        player.on('ready', () => {
            console.log('Player is ready!');
        });
        
        player.on('play', () => {
            console.log('Video started playing');
        });
    </script>
</body>
</html>
"""

# Download page template
DOWNLOAD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Download - {{ movie_name }}</title>
    
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .download-card {
            background: white;
            border-radius: 20px;
            padding: 50px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            text-align: center;
        }
        
        .download-card h1 {
            color: #667eea;
            margin-bottom: 20px;
        }
        
        .movie-info {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 30px 0;
        }
        
        .movie-info p {
            margin: 10px 0;
            color: #555;
        }
        
        .download-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 50px;
            font-size: 1.2em;
            cursor: pointer;
            transition: transform 0.2s;
            text-decoration: none;
            display: inline-block;
            margin: 10px;
        }
        
        .download-btn:hover {
            transform: scale(1.05);
        }
        
        .warning {
            background: #fff3cd;
            border: 2px solid #ffc107;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            color: #856404;
        }
    </style>
</head>
<body>
    <div class="download-card">
        <h1>⚡ Fast Download</h1>
        
        <div class="movie-info">
            <h2>{{ movie_name }}</h2>
            <p><strong>Size:</strong> {{ size }}</p>
            <p><strong>Quality:</strong> {{ quality }}</p>
            <p><strong>Format:</strong> {{ format }}</p>
        </div>
        
        <a href="/download/{{ file_id }}" class="download-btn">
            🚀 Download Now
        </a>
        
        <a href="/watch/{{ file_id }}" class="download-btn" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            📺 Watch Online
        </a>
        
        <div class="warning">
            ⚠️ <strong>Note:</strong> This link expires in 24 hours. Download or save the file immediately.
        </div>
    </div>
</body>
</html>
"""

def format_bytes(bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"

def generate_token(file_id):
    """Generate a secure token for file access"""
    timestamp = str(int(time.time()))
    secret = os.environ.get("SECRET_KEY", "filmzi_secret_2025")
    token = hashlib.sha256(f"{file_id}{timestamp}{secret}".encode()).hexdigest()
    return token

@app.route('/')
def index():
    return """
    <html>
        <head>
            <title>Filmzi Streaming Server</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                    padding: 50px;
                }
                h1 { font-size: 3em; }
            </style>
        </head>
        <body>
            <h1>🎬 Filmzi Streaming Server</h1>
            <p>Server is running successfully!</p>
        </body>
    </html>
    """

@app.route('/watch/<file_id>')
def watch(file_id):
    """Serve the video player page"""
    # In production, fetch actual movie details from database
    movie_name = "Movie Name"
    quality = "1080p"
    size = "1.5 GB"
    format_type = "MKV"
    poster = "https://via.placeholder.com/1920x1080/667eea/ffffff?text=Filmzi+Movie"
    
    return render_template_string(
        PLAYER_TEMPLATE,
        movie_name=movie_name,
        file_id=file_id,
        quality=quality,
        size=size,
        format=format_type,
        poster=poster
    )

@app.route('/download-page/<file_id>')
def download_page(file_id):
    """Serve the download page"""
    movie_name = "Movie Name"
    quality = "1080p"
    size = "1.5 GB"
    format_type = "MKV"
    
    return render_template_string(
        DOWNLOAD_TEMPLATE,
        movie_name=movie_name,
        file_id=file_id,
        quality=quality,
        size=size,
        format=format_type
    )

@app.route('/stream/<file_id>')
async def stream_video(file_id):
    """Stream video content"""
    try:
        # This is a placeholder - implement actual streaming logic
        # You would fetch the file from Telegram and stream it
        return Response(
            "Video streaming endpoint - implement with Telegram file streaming",
            mimetype='video/mp4'
        )
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/download/<file_id>')
def download_file(file_id):
    """Direct download endpoint"""
    try:
        # Implement actual file download from Telegram
        return Response(
            "Download endpoint - implement with Telegram file download",
            mimetype='application/octet-stream'
        )
    except Exception as e:
        return f"Error: {str(e)}", 500

def run_flask():
    """Run Flask server"""
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Run Flask in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    print("Streaming server started on port 5000")
    print("Access at: http://localhost:5000")
    
    # Keep the main thread alive
    while True:
        time.sleep(1)
