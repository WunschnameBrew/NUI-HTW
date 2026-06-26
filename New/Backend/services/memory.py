# Backend/services/memory.py
import sqlite3
import asyncio
import json
from datetime import datetime
from Backend.config.settings import DB_PATH

class MemoryService:
    def __init__(self):
        self.db_path = DB_PATH

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    async def start(self):
        await asyncio.to_thread(self._init_db)

    async def save_interaction(self, role: str, content: str):
        def _save():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO conversations (role, content) VALUES (?, ?)", (role, content))
            conn.commit()
            conn.close()
        await asyncio.to_thread(_save)

    async def get_recent_history(self, limit=10):
        def _get():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT role, content FROM conversations ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            return [{"role": r[0], "content": r[1]} for r in reversed(rows)]
        return await asyncio.to_thread(_get)

    async def clear_history(self):
        def _clear():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversations")
            conn.commit()
            conn.close()
        await asyncio.to_thread(_clear)

memory_service = MemoryService()
