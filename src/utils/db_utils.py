# utils/db_utils.py
import sqlite3
from pathlib import Path
from typing import Optional

def init_database(db_path: Path) -> None:
    """Initialize SQLite database with required tables."""
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_items (
                item_id TEXT PRIMARY KEY,
                category TEXT,
                content TEXT,
                source TEXT,
                timestamp TEXT,
                version INTEGER,
                metadata TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS debate_records (
                debate_id TEXT PRIMARY KEY,
                timestamp TEXT,
                primary_agent TEXT,
                adversary_agent TEXT,
                topic TEXT,
                proposal TEXT,
                challenges TEXT,
                resolutions TEXT,
                final_consensus TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                template_id TEXT PRIMARY KEY,
                category TEXT,
                content TEXT,
                parameters TEXT,
                usage_count INTEGER,
                last_used TEXT,
                metadata TEXT
            )
        """)