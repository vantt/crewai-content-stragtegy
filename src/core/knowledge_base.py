# core/knowledge_base.py
from pathlib import Path
import sqlite3
import json
import threading
import zipfile
import shutil
import atexit
import contextlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from loguru import logger

from ..models.knowledge_models import KnowledgeItem, DebateRecord, Template
from ..utils.db_utils import init_database


class KnowledgeBase:
    """Core Knowledge Base implementation with thread-safe operations."""
    
    _instances = set()

    def __init__(self, storage_path: Path = Path("data/knowledge_base")):
        """Initialize the knowledge base with storage path."""
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage components
        self.db_path = self.storage_path / "knowledge.db"
        self._conn = None
        self._init_database()
        self._load_cache()
        
        # Thread safety
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Register instance for cleanup
        KnowledgeBase._instances.add(self)
    
    @contextlib.contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database with required tables."""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    item_id TEXT PRIMARY KEY,
                    category TEXT,
                    content TEXT,
                    source TEXT,
                    timestamp TEXT,
                    version INTEGER,
                    metadata TEXT,
                    created_at TEXT,
                    updated_at TEXT
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
                    final_consensus TEXT,
                    created_at TEXT
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
                    metadata TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

    
    def get_connection(self):
        """Get a database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
        return self._conn
    
    def close(self):
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
    
    def clear_database(self):
        """Clear all data from the database."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM knowledge_items")
            conn.execute("DELETE FROM debate_records")
            conn.execute("DELETE FROM templates")
    
    def cleanup(self):
        """Cleanup resources."""
        if self in KnowledgeBase._instances:
            KnowledgeBase._instances.remove(self)

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
    
    def _load_cache(self):
        """Initialize in-memory cache for frequently accessed data."""
        self.cache = {
            'knowledge_items': {},
            'templates': {},
            'debate_records': {}
        }

    def add_knowledge_item(self, item: KnowledgeItem) -> bool:
        """Add a new knowledge item to the knowledge base."""
        try:
            with self._lock:
                with self.get_connection() as conn:
                    now = datetime.now().isoformat()
                    conn.execute(
                        """
                        INSERT INTO knowledge_items 
                        (item_id, category, content, source, timestamp, version, 
                        metadata, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            item.item_id,
                            item.category,
                            json.dumps(item.content),
                            item.source,
                            item.timestamp.isoformat(),
                            item.version,
                            json.dumps(item.metadata),
                            now,
                            now
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

    def search_knowledge_advanced(
        self,
        category: Optional[str] = None,
        query: Optional[str] = None,
        date_range: Optional[tuple[datetime, datetime]] = None,
        source: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        limit: int = 10
    ) -> List[KnowledgeItem]:
        """Advanced search with multiple filters and sorting."""
        try:
            with self.get_connection() as conn:
                sql = "SELECT * FROM knowledge_items WHERE 1=1"
                params = []
                
                # Apply filters
                if category:
                    sql += " AND category = ?"
                    params.append(category)
                
                if query:
                    sql += " AND (content LIKE ? OR metadata LIKE ?)"
                    params.extend([f"%{query}%", f"%{query}%"])
                
                if date_range:
                    sql += " AND timestamp BETWEEN ? AND ?"
                    params.extend([d.isoformat() for d in date_range])
                
                if source:
                    sql += " AND source = ?"
                    params.append(source)
                
                if metadata_filters:
                    for key, value in metadata_filters.items():
                        sql += f" AND json_extract(metadata, '$.{key}') = ?"
                        params.append(str(value))
                
                # Apply sorting
                if sort_by:
                    sql += f" ORDER BY {sort_by}"
                
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
            logger.error(f"Error in advanced search: {str(e)}")
            return []

    def create_backup(
        self,
        backup_type: str = "full",
        compression: bool = True
    ) -> Optional[Path]:
        """Create a backup of the knowledge base."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = self.storage_path / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Consistent filename for database backup
            db_filename = "backup.db"
            manifest_filename = "manifest.json"
            backup_path = backup_dir / db_filename
            
            # Create backup
            with self.get_connection() as source_conn:
                backup_conn = sqlite3.connect(str(backup_path))
                source_conn.backup(backup_conn)
                backup_conn.close()
            
            # Create manifest
            manifest = {
                "timestamp": timestamp,
                "type": backup_type,
                "compressed": compression,
                "database_size": backup_path.stat().st_size,
                "tables": self._get_table_stats()
            }
            
            manifest_path = backup_dir / manifest_filename
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)
            
            if compression:
                zip_path = backup_dir / f"backup_{timestamp}.zip"
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Use consistent filenames in the zip
                    zipf.write(backup_path, db_filename)
                    zipf.write(manifest_path, manifest_filename)
                
                # Clean up uncompressed files
                backup_path.unlink()
                manifest_path.unlink()
                
                return zip_path
            
            return backup_path
                
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            return None
        

    def restore_from_backup(self, backup_path: Path) -> bool:
        """Restore the knowledge base from a backup."""
        try:
            # Handle compressed backups
            if backup_path.suffix == '.zip':
                import tempfile
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_dir_path = Path(temp_dir)
                    
                    # Extract with consistent filename expectations
                    with zipfile.ZipFile(backup_path, 'r') as zipf:
                        # List contents for debugging
                        logger.debug(f"Zip contents: {zipf.namelist()}")
                        
                        # Extract database file
                        try:
                            zipf.extract("backup.db", temp_dir_path)
                            db_path = temp_dir_path / "backup.db"
                        except KeyError:
                            logger.error("Database file 'backup.db' not found in zip")
                            return False
                        
                        if not db_path.exists():
                            logger.error(f"Extracted database file not found at {db_path}")
                            return False
                            
                        return self._perform_restore(db_path)
            else:
                # Direct database file
                if not backup_path.exists():
                    logger.error(f"Backup file not found: {backup_path}")
                    return False
                return self._perform_restore(backup_path)
                
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            return False

    def _perform_restore(self, backup_db_path: Path) -> bool:
        """Perform the actual database restore."""
        try:
            logger.debug(f"Performing restore from {backup_db_path}")
            
            # Close existing connection
            self.cleanup()
            
            # Verify backup file exists and is readable
            if not backup_db_path.exists():
                logger.error(f"Backup database not found at {backup_db_path}")
                return False
                
            try:
                # Test backup file integrity
                test_conn = sqlite3.connect(str(backup_db_path))
                test_conn.execute("SELECT COUNT(*) FROM sqlite_master")
                test_conn.close()
            except sqlite3.Error as e:
                logger.error(f"Backup database integrity check failed: {str(e)}")
                return False
            
            # Replace current database with backup
            try:
                shutil.copy2(backup_db_path, self.db_path)
            except PermissionError:
                logger.error("Permission error during restore, attempting to close all connections")
                self.close()
                shutil.copy2(backup_db_path, self.db_path)
            
            # Reinitialize connection and cache
            self._init_database()
            self._load_cache()
            
            logger.info("Database restore completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database restore failed: {str(e)}")
            return False

    def maintenance(self) -> Dict[str, Any]:
        """Perform maintenance operations on the database."""
        try:
            with self.get_connection() as conn:
                # Vacuum database
                conn.execute("VACUUM")
                
                # Analyze tables
                conn.execute("ANALYZE")
                
                # Clean up old backups
                self._cleanup_old_backups()
                
                # Verify database integrity
                cursor = conn.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                
                # Get database stats
                stats = self._get_table_stats()
                
                return {
                    "status": "success",
                    "integrity_check": integrity_result,
                    "statistics": stats,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Maintenance failed: {str(e)}")
            return {"status": "failed", "error": str(e)}

    def _get_table_stats(self) -> Dict[str, Any]:
        """Get statistics for all tables."""
        stats = {}
        table_timestamp_columns = {
            'knowledge_items': 'created_at',
            'debate_records': 'created_at',
            'templates': 'last_used'
        }
        
        with self.get_connection() as conn:
            for table, timestamp_col in table_timestamp_columns.items():
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = {
                    "row_count": count,
                    "last_updated": self._get_last_updated(conn, table, timestamp_col)
                }
        return stats

    def _get_last_updated(
        self, 
        conn: sqlite3.Connection, 
        table: str, 
        timestamp_col: str
    ) -> Optional[str]:
        """Get the last updated timestamp for a table."""
        try:
            cursor = conn.execute(f"SELECT MAX({timestamp_col}) FROM {table}")
            result = cursor.fetchone()[0]
            return result if result else None
        except sqlite3.OperationalError:
            return None

    def _cleanup_old_backups(self, max_age_days: int = 30):
        """Clean up old backup files."""
        backup_dir = self.storage_path / "backups"
        if not backup_dir.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        for backup in backup_dir.iterdir():
            try:
                # Parse backup timestamp from directory name
                backup_date = datetime.strptime(backup.name, '%Y%m%d_%H%M%S')
                if backup_date < cutoff_date:
                    if backup.is_file() and backup.suffix == '.zip':
                        backup.unlink()
                    elif backup.is_dir():
                        shutil.rmtree(backup)
            except (ValueError, OSError) as e:
                logger.warning(f"Error cleaning up backup {backup}: {str(e)}")

# Register cleanup for all instances
@atexit.register
def cleanup_all_instances():
    """Clean up all KnowledgeBase instances at exit."""
    for instance in list(KnowledgeBase._instances):
        instance.cleanup()