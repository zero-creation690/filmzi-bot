import sqlite3
import logging
import threading
from typing import List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self._local = threading.local()
        self.init_db()
    
    def get_connection(self):
        """Get database connection with thread safety"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
    
    def init_db(self):
        """Initialize database tables"""
        try:
            with self.get_cursor() as cursor:
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
                
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def add_movie(self, movie_data: Dict[str, Any]):
        """Add movie to database"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute('''
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
        except Exception as e:
            logger.error(f"Error adding movie: {e}")
    
    def search_movies(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search movies by name"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute('''
                    SELECT * FROM movies 
                    WHERE movie_name LIKE ? OR file_name LIKE ?
                    ORDER BY 
                        CASE WHEN movie_name LIKE ? THEN 1 ELSE 2 END,
                        year DESC
                    LIMIT ?
                ''', (f'%{query}%', f'%{query}%', f'{query}%', limit))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error searching movies: {e}")
            return []
    
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str = ""):
        """Add or update user"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute('''
                    INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, username, first_name, last_name))
        except Exception as e:
            logger.error(f"Error adding user: {e}")
    
    def get_movie_by_id(self, movie_id: int) -> Dict[str, Any]:
        """Get movie by ID"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute('''
                    SELECT * FROM movies WHERE id = ?
                ''', (movie_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting movie: {e}")
            return None
    
    def get_movies_by_name(self, movie_name: str) -> List[Dict[str, Any]]:
        """Get all movies with same name"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute('''
                    SELECT * FROM movies WHERE movie_name = ? ORDER BY quality
                ''', (movie_name,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting movies by name: {e}")
            return []
    
    def get_user(self, user_id: int) -> Dict[str, Any]:
        """Get user by ID"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def close_connection(self):
        """Close database connection"""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
            del self._local.conn
