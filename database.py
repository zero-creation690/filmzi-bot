import sqlite3
import logging
import aiosqlite
from typing import List, Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.init_db_sync()
    
    def init_db_sync(self):
        """Initialize database tables synchronously"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Movies table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT UNIQUE,
                    file_name TEXT,
                    file_size TEXT,
                    movie_name TEXT,
                    year INTEGER,
                    quality TEXT,
                    language TEXT,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_premium BOOLEAN DEFAULT FALSE,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Requests table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    movie_name TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_movies_name ON movies(movie_name)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_movies_quality ON movies(quality)
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    async def add_movie(self, movie_data: Dict[str, Any]):
        """Add movie to database asynchronously"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO movies 
                    (file_id, file_name, file_size, movie_name, year, quality, language, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    movie_data['file_id'],
                    movie_data['file_name'],
                    movie_data['file_size'],
                    movie_data['movie_name'],
                    movie_data.get('year'),
                    movie_data.get('quality'),
                    movie_data.get('language'),
                    movie_data.get('category', 'movie')
                ))
                await db.commit()
        except Exception as e:
            logger.error(f"Error adding movie: {e}")
    
    async def search_movies(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search movies by name asynchronously"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT * FROM movies 
                    WHERE movie_name LIKE ? OR file_name LIKE ?
                    ORDER BY 
                        CASE WHEN movie_name LIKE ? THEN 1 ELSE 2 END,
                        year DESC
                    LIMIT ?
                ''', (f'%{query}%', f'%{query}%', f'{query}%', limit))
                
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error searching movies: {e}")
            return []
    
    async def add_user(self, user_id: int, username: str, first_name: str, last_name: str = ""):
        """Add or update user asynchronously"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, username, first_name, last_name))
                await db.commit()
        except Exception as e:
            logger.error(f"Error adding user: {e}")
    
    async def get_movie_by_id(self, movie_id: int) -> Dict[str, Any]:
        """Get movie by ID"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT * FROM movies WHERE id = ?
                ''', (movie_id,))
                row = await cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting movie: {e}")
            return None
    
    async def get_movies_by_name(self, movie_name: str) -> List[Dict[str, Any]]:
        """Get all movies with same name"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT * FROM movies WHERE movie_name = ? ORDER BY quality
                ''', (movie_name,))
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting movies by name: {e}")
            return []
