import pytest
from src.core.initialization import SystemInitializer
from src.config.settings import Settings

@pytest.fixture
def system_initializer():
    return SystemInitializer()

def test_environment_validation(system_initializer):
    """Test environment validation."""
    assert system_initializer.validate_environment() is True

def test_system_initialization(system_initializer):
    """Test complete system initialization."""
    assert system_initializer.initialize_system() is True