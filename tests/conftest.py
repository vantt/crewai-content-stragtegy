# tests/conftest.py
import pytest
from unittest.mock import MagicMock

from src.agents.base import BaseAgent


@pytest.fixture
def mock_crew_agent():
    return MagicMock()

@pytest.fixture(scope="session")
def mock_knowledge_base():
    return MagicMock()

@pytest.fixture(autouse=True)
def env_setup():
    """Setup environment variables for testing"""
    import os
    os.environ["OPENAI_API_KEY"] = "test_key"
    os.environ["ANTHROPIC_API_KEY"] = "test_key"