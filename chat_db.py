import sqlite3
from datetime import datetime
from typing import List, Dict
import json
import os

class ChatDatabase:
    def __init__(self, db_path="chat_history.db"):
        self.db_path = db_path
        # Initialize database if it doesn't exist or if tables need to be created
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_active DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Create conversations table with user_id
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    task TEXT,
                    plan TEXT,
                    draft TEXT,
                    critique TEXT,
                    content TEXT,
                    revision_number INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            # Create conversation summaries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    conversation_id INTEGER,
                    summary TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            ''')
            conn.commit()

    def create_or_get_user(self, user_id: str, username: str) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username)
                VALUES (?, ?)
            ''', (user_id, username))
            
            cursor.execute('''
                UPDATE users 
                SET last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            conn.commit()
            
            if user:
                return {
                    'user_id': user[0],
                    'username': user[1],
                    'created_at': user[2],
                    'last_active': user[3]
                }
            return None

    def save_conversation(self, user_id: str, state: Dict):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversations 
                (user_id, task, plan, draft, critique, content, revision_number)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                state.get('task', ''),
                state.get('plan', ''),
                state.get('draft', ''),
                state.get('critique', ''),
                '\n'.join(state.get('content', [])),
                state.get('revision_number', 1)
            ))
            conversation_id = cursor.lastrowid
            
            # Generate and save summary
            summary = f"Essay about: {state.get('task', '')} (Revision {state.get('revision_number', 1)})"
            cursor.execute('''
                INSERT INTO conversation_summaries 
                (user_id, conversation_id, summary)
                VALUES (?, ?, ?)
            ''', (user_id, conversation_id, summary))
            
            conn.commit()
            return conversation_id

    def get_recent_conversations(self, user_id: str, limit=5):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, s.summary 
                FROM conversations c
                LEFT JOIN conversation_summaries s ON c.id = s.conversation_id
                WHERE c.user_id = ?
                ORDER BY c.timestamp DESC 
                LIMIT ?
            ''', (user_id, limit))
            return cursor.fetchall()

    def get_last_conversation_summary(self, user_id: str) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.task, c.plan, c.draft, s.summary
                FROM conversations c
                LEFT JOIN conversation_summaries s ON c.id = s.conversation_id
                WHERE c.user_id = ?
                ORDER BY c.timestamp DESC
                LIMIT 1
            ''', (user_id,))
            result = cursor.fetchone()
            if result:
                return {
                    'task': result[0],
                    'plan': result[1],
                    'draft': result[2],
                    'summary': result[3]
                }
            return None
