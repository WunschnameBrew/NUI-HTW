# Backend/services/memory.py
import sqlite3
import asyncio
import logging
from typing import List, Dict, Optional
from Backend.config.settings import DB_PATH

logger = logging.getLogger("MEMORY")


class MemoryService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(DB_PATH)

    def _init_db(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL DEFAULT 'default',
                    role TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("PRAGMA table_info(conversations)")
            conversation_columns = {row[1] for row in cursor.fetchall()}
            if "session_id" not in conversation_columns:
                cursor.execute("ALTER TABLE conversations ADD COLUMN session_id TEXT NOT NULL DEFAULT 'default'")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE,
                    value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        except sqlite3.Error as error:
            logger.exception("Memory DB init failed: %s", error)
        finally:
            if conn:
                conn.close()

    async def start(self):
        await asyncio.to_thread(self._init_db)

    async def save_interaction(self, role: str, content: str, session_id: Optional[str] = None, enabled: bool = True):
        if not enabled:
            return
        session_id = session_id or "default"

        def _save():
            conn = None
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)",
                    (session_id, role, content),
                )
                conn.commit()
            except sqlite3.Error as error:
                logger.warning("Memory save failed for session '%s': %s", session_id, error)
            finally:
                if conn:
                    conn.close()

        await asyncio.to_thread(_save)

    async def get_recent_history(self, limit: int = 10, session_id: Optional[str] = None) -> List[Dict[str, str]]:
        session_id = session_id or "default"

        def _get():
            conn = None
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT role, content FROM (
                        SELECT role, content, id
                        FROM conversations
                        WHERE session_id = ?
                        ORDER BY id DESC
                        LIMIT ?
                    ) recent
                    ORDER BY id ASC
                    """,
                    (session_id, limit),
                )
                rows = cursor.fetchall()
                return [{"role": r[0], "content": r[1]} for r in rows]
            except sqlite3.Error as error:
                logger.warning("Memory read failed for session '%s': %s", session_id, error)
                return []
            finally:
                if conn:
                    conn.close()

        return await asyncio.to_thread(_get)

    async def clear_history(self, session_id: Optional[str] = None):
        session_id = session_id or "default"

        def _clear():
            conn = None
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
                conn.commit()
            except sqlite3.Error as error:
                logger.warning("Memory clear failed for session '%s': %s", session_id, error)
            finally:
                if conn:
                    conn.close()

        await asyncio.to_thread(_clear)


memory_service = MemoryService()
