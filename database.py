import sqlite3
import logging

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('movies.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Movies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                file_id TEXT NOT NULL,
                file_size TEXT,
                quality TEXT,
                year INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_premium BOOLEAN DEFAULT FALSE,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Search history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def add_movie(self, title, file_id, file_size, quality, year):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO movies (title, file_id, file_size, quality, year)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, file_id, file_size, quality, year))
        self.conn.commit()
    
    def search_movies(self, query):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM movies 
            WHERE title LIKE ? 
            ORDER BY 
                CASE WHEN title = ? THEN 1
                     WHEN title LIKE ? THEN 2
                     ELSE 3
                END,
                title
            LIMIT 10
        ''', (f'%{query}%', query, f'{query}%'))
        return cursor.fetchall()
    
    def add_user(self, user_id, username, first_name, last_name):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        self.conn.commit()
    
    def add_search_history(self, user_id, query):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO search_history (user_id, query)
            VALUES (?, ?)
        ''', (user_id, query))
        self.conn.commit()

db = Database()
