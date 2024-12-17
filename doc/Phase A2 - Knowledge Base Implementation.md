
# Phase A2: Knowledge Base Implementation Technical Specification

1. Basic Knowledge Base Structure

```python
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json
from pathlib import Path
import sqlite3
from loguru import logger
from concurrent.futures import ThreadPoolExecutor
import threading

# Data Models
class DebateRecord(BaseModel):
    """Model for storing debate interactions between agents."""
    debate_id: str
    timestamp: datetime
    primary_agent: str
    adversary_agent: str
    topic: str
    proposal: Dict[str, Any]
    challenges: List[Dict[str, Any]]
    resolutions: List[Dict[str, Any]]
    final_consensus: Optional[Dict[str, Any]]
    
    class Config:
        arbitrary_types_allowed = True

class Template(BaseModel):
    """Model for storing reusable templates."""
    template_id: str
    category: str
    content: str
    parameters: List[str]
    usage_count: int = 0
    last_used: Optional[datetime]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeItem(BaseModel):
    """Model for storing core knowledge items."""
    item_id: str
    category: str
    content: Any
    source: str
    timestamp: datetime
    version: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
# Main Knowledge Base Implementation
class KnowledgeBase:
    """Core Knowledge Base implementation with thread-safe operations."""
    
    def __init__(self, storage_path: Path = Path("data/knowledge_base")):
        """Initialize the knowledge base with storage path."""
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage components
        self._init_database()
        self._load_cache()
        
        # Thread safety
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4)
        
    def _init_database(self):
        """Initialize SQLite database for structured data storage."""
        self.db_path = self.storage_path / "knowledge.db"
        with sqlite3.connect(str(self.db_path)) as conn:
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
    
    def _load_cache(self):
        """Initialize in-memory cache for frequently accessed data."""
        self.cache = {
            'knowledge_items': {},
            'templates': {},
            'debate_records': {}
        }
        
    # Knowledge Items Operations
    def add_knowledge_item(self, item: KnowledgeItem) -> bool:
        """Add a new knowledge item to the knowledge base."""
        try:
            with self._lock:
                with sqlite3.connect(str(self.db_path)) as conn:
                    conn.execute(
                        """
                        INSERT INTO knowledge_items 
                        (item_id, category, content, source, timestamp, version, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            item.item_id,
                            item.category,
                            json.dumps(item.content),
                            item.source,
                            item.timestamp.isoformat(),
                            item.version,
                            json.dumps(item.metadata)
                        )
                    )
                self.cache['knowledge_items'][item.item_id] = item
                return True
        except Exception as e:
            logger.error(f"Error adding knowledge item: {str(e)}")
            return False
    
    def get_knowledge_item(self, item_id: str) -> Optional[KnowledgeItem]:
        """Retrieve a knowledge item by ID."""
        # Check cache first
        if item_id in self.cache['knowledge_items']:
            return self.cache['knowledge_items'][item_id]
        
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute(
                    "SELECT * FROM knowledge_items WHERE item_id = ?",
                    (item_id,)
                )
                row = cursor.fetchone()
                if row:
                    item = KnowledgeItem(
                        item_id=row[0],
                        category=row[1],
                        content=json.loads(row[2]),
                        source=row[3],
                        timestamp=datetime.fromisoformat(row[4]),
                        version=row[5],
                        metadata=json.loads(row[6])
                    )
                    self.cache['knowledge_items'][item_id] = item
                    return item
                return None
        except Exception as e:
            logger.error(f"Error retrieving knowledge item: {str(e)}")
            return None
    
    # Debate Records Operations
    def store_debate_record(self, record: DebateRecord) -> bool:
        """Store a new debate record."""
        try:
            with self._lock:
                with sqlite3.connect(str(self.db_path)) as conn:
                    conn.execute(
                        """
                        INSERT INTO debate_records 
                        (debate_id, timestamp, primary_agent, adversary_agent, topic,
                         proposal, challenges, resolutions, final_consensus)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            record.debate_id,
                            record.timestamp.isoformat(),
                            record.primary_agent,
                            record.adversary_agent,
                            record.topic,
                            json.dumps(record.proposal),
                            json.dumps(record.challenges),
                            json.dumps(record.resolutions),
                            json.dumps(record.final_consensus)
                        )
                    )
                self.cache['debate_records'][record.debate_id] = record
                return True
        except Exception as e:
            logger.error(f"Error storing debate record: {str(e)}")
            return False
    
    # Template Operations
    def add_template(self, template: Template) -> bool:
        """Add a new template to the knowledge base."""
        try:
            with self._lock:
                with sqlite3.connect(str(self.db_path)) as conn:
                    conn.execute(
                        """
                        INSERT INTO templates 
                        (template_id, category, content, parameters, usage_count,
                         last_used, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            template.template_id,
                            template.category,
                            template.content,
                            json.dumps(template.parameters),
                            template.usage_count,
                            template.last_used.isoformat() if template.last_used else None,
                            json.dumps(template.metadata)
                        )
                    )
                self.cache['templates'][template.template_id] = template
                return True
        except Exception as e:
            logger.error(f"Error adding template: {str(e)}")
            return False
    
    # Search and Query Operations
    def search_knowledge(self, 
                        category: Optional[str] = None,
                        query: Optional[str] = None,
                        limit: int = 10) -> List[KnowledgeItem]:
        """Search knowledge items based on category and/or query string."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                sql = "SELECT * FROM knowledge_items WHERE 1=1"
                params = []
                
                if category:
                    sql += " AND category = ?"
                    params.append(category)
                    
                if query:
                    sql += " AND (content LIKE ? OR metadata LIKE ?)"
                    params.extend([f"%{query}%", f"%{query}%"])
                    
                sql += f" LIMIT {limit}"
                
                cursor = conn.execute(sql, params)
                rows = cursor.fetchall()
                
                return [
                    KnowledgeItem(
                        item_id=row[0],
                        category=row[1],
                        content=json.loads(row[2]),
                        source=row[3],
                        timestamp=datetime.fromisoformat(row[4]),
                        version=row[5],
                        metadata=json.loads(row[6])
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return []
    
    # Backup and Maintenance
    def create_backup(self) -> bool:
        """Create a backup of the entire knowledge base."""
        try:
            backup_path = self.storage_path / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path.mkdir(exist_ok=True)
            
            # Backup database
            with sqlite3.connect(str(self.db_path)) as conn:
                backup_db = sqlite3.connect(str(backup_path / "knowledge.db"))
                conn.backup(backup_db)
                backup_db.close()
            
            return True
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            return False
    
    def cleanup_old_records(self, days_old: int = 30) -> bool:
        """Clean up old records from the database."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            with self._lock:
                with sqlite3.connect(str(self.db_path)) as conn:
                    conn.execute(
                        "DELETE FROM debate_records WHERE timestamp < ?",
                        (cutoff_date.isoformat(),)
                    )
            return True
        except Exception as e:
            logger.error(f"Error cleaning up old records: {str(e)}")
            return False

# Usage Example
def example_usage():
    # Initialize knowledge base
    kb = KnowledgeBase()
    
    # Add a knowledge item
    item = KnowledgeItem(
        item_id="k1",
        category="marketing_strategy",
        content={"key": "value"},
        source="internal",
        timestamp=datetime.now()
    )
    kb.add_knowledge_item(item)
    
    # Add a debate record
    debate = DebateRecord(
        debate_id="d1",
        timestamp=datetime.now(),
        primary_agent="strategy_agent",
        adversary_agent="critic_agent",
        topic="Q1 Marketing Strategy",
        proposal={"strategy": "content focus"},
        challenges=[{"issue": "market saturation"}],
        resolutions=[{"solution": "niche targeting"}],
        final_consensus={"agreed_approach": "hybrid"}
    )
    kb.store_debate_record(debate)
    
    # Add a template
    template = Template(
        template_id="t1",
        category="email",
        content="Dear {name}, {content}",
        parameters=["name", "content"],
        last_used=datetime.now()
    )
    kb.add_template(template)

if __name__ == "__main__":
    example_usage()
```