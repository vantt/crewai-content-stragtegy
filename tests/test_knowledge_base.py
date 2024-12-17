import pytest
from datetime import datetime
import uuid
import shutil
import time
import os
from pathlib import Path
from src.core.knowledge_base import KnowledgeBase
from src.models.knowledge_models import KnowledgeItem, DebateRecord, Template

def remove_readonly(func, path, excinfo):
    """Error handler for shutil.rmtree to handle readonly files."""
    os.chmod(path, 0o666)
    func(path)

@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """Create a temporary directory using pytest's tmp_path_factory."""
    temp_dir = tmp_path_factory.mktemp("knowledge_base")
    yield temp_dir
    # Cleanup after all tests
    try:
        time.sleep(1)  # Give time for connections to close
        shutil.rmtree(temp_dir, onerror=remove_readonly)
    except Exception as e:
        print(f"Warning: Failed to remove test directory: {e}")

@pytest.fixture
def knowledge_base(test_db_path):
    """Create a fresh knowledge base for each test."""
    kb = KnowledgeBase(test_db_path)
    kb.clear_database()  # Start with a clean database
    yield kb
    kb.cleanup()  # Ensure cleanup after each test

def test_add_and_get_knowledge_item(knowledge_base):
    # Create and add test item
    item = KnowledgeItem(
        item_id=str(uuid.uuid4()),
        category="test",
        content={"key": "value"},
        source="test",
        timestamp=datetime.now()
    )
    
    assert knowledge_base.add_knowledge_item(item)
    
    # Retrieve and verify
    retrieved = knowledge_base.get_knowledge_item(item.item_id)
    assert retrieved is not None
    assert retrieved.item_id == item.item_id
    assert retrieved.content == item.content

def test_search_knowledge(knowledge_base):
    # Verify empty database
    initial_results = knowledge_base.search_knowledge(category="test")
    assert len(initial_results) == 0
    
    # Add test items
    for i in range(3):
        item = KnowledgeItem(
            item_id=str(uuid.uuid4()),
            category="test",
            content={"index": i},
            source="test",
            timestamp=datetime.now()
        )
        knowledge_base.add_knowledge_item(item)
    
    # Search and verify
    results = knowledge_base.search_knowledge(category="test")
    assert len(results) == 3

def test_store_debate_record(knowledge_base):
    record = DebateRecord(
        debate_id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        primary_agent="agent1",
        adversary_agent="agent2",
        topic="test debate",
        proposal={"key": "value"},
        challenges=[],
        resolutions=[],
        final_consensus=None
    )
    
    assert knowledge_base.store_debate_record(record)

def test_add_template(knowledge_base):
    template = Template(
        template_id=str(uuid.uuid4()),
        category="test",
        content="Test content",
        parameters=["param1", "param2"],
        last_used=datetime.now()
    )
    
    assert knowledge_base.add_template(template)

def test_advanced_search(knowledge_base):
    # Add test items with different attributes
    items = [
        KnowledgeItem(
            item_id=str(uuid.uuid4()),
            category="marketing",
            content={"title": "Social Media Strategy"},
            source="internal",
            timestamp=datetime.now(),
            metadata={"platform": "twitter", "audience": "tech"}
        ),
        KnowledgeItem(
            item_id=str(uuid.uuid4()),
            category="marketing",
            content={"title": "Email Campaign"},
            source="external",
            timestamp=datetime.now(),
            metadata={"platform": "email", "audience": "business"}
        )
    ]
    
    for item in items:
        knowledge_base.add_knowledge_item(item)
    
    # Test different search criteria
    results = knowledge_base.search_knowledge_advanced(
        category="marketing",
        metadata_filters={"platform": "twitter"}
    )
    assert len(results) == 1
    assert results[0].metadata["platform"] == "twitter"

def test_backup_and_restore(knowledge_base):
    """Test backup and restore functionality."""
    # Add test data
    item = KnowledgeItem(
        item_id=str(uuid.uuid4()),
        category="test",
        content={"key": "value"},
        source="test",
        timestamp=datetime.now()
    )
    
    assert knowledge_base.add_knowledge_item(item)
    
    # Create backup
    backup_path = knowledge_base.create_backup(compression=True)
    assert backup_path is not None
    assert backup_path.exists()
    assert backup_path.suffix == '.zip'
    
    # Clear database
    knowledge_base.clear_database()
    results = knowledge_base.search_knowledge(category="test")
    assert len(results) == 0
    
    # Restore from backup
    assert knowledge_base.restore_from_backup(backup_path)
    
    # Verify data
    restored_items = knowledge_base.search_knowledge(category="test")
    assert len(restored_items) == 1
    assert restored_items[0].item_id == item.item_id
    
    # Cleanup backup
    try:
        if backup_path.exists():
            backup_path.unlink()
    except Exception as e:
        print(f"Warning: Failed to remove backup file: {e}")

def test_maintenance(knowledge_base):
    """Test maintenance operations."""
    # Add some test data
    for i in range(3):
        item = KnowledgeItem(
            item_id=str(uuid.uuid4()),
            category="test",
            content={"index": i},
            source="test",
            timestamp=datetime.now()
        )
        knowledge_base.add_knowledge_item(item)
    
    # Run maintenance
    result = knowledge_base.maintenance()
    
    assert result["status"] == "success"
    assert result["integrity_check"] == "ok"
    assert result["statistics"]["knowledge_items"]["row_count"] == 3