import pytest
import tempfile
import shutil
from pathlib import Path

from app.config import AgentConfig, LLMConfig, ToolConfig, MemoryConfig, AgentType, ToolType, MemoryType
from app.services.agent_service import AgentService

@pytest.fixture
def temp_storage():
    """Create a temporary storage directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def agent_service(temp_storage, monkeypatch):
    """Create an AgentService instance with temporary storage"""
    monkeypatch.setattr('app.config.settings.STORAGE_PATH', temp_storage)
    return AgentService()

@pytest.fixture
def sample_agent_config():
    """Create a sample agent configuration for testing"""
    return AgentConfig(
        name="test_agent",
        description="A test agent",
        agent_type=AgentType.REACT,
        llm=LLMConfig(
            model="llama3-8b-8192",
            temperature=0.7
        ),
        tools=[
            ToolConfig(
                name="calculator",
                type=ToolType.CALCULATOR,
                description="Test calculator",
                enabled=True
            )
        ],
        memory=MemoryConfig(type=MemoryType.BUFFER)
    )

def test_agent_service_initialization(agent_service):
    """Test that AgentService initializes correctly"""
    assert isinstance(agent_service, AgentService)
    assert isinstance(agent_service.configurations, dict)
    assert "default" in agent_service.configurations

def test_add_configuration(agent_service, sample_agent_config):
    """Test adding an agent configuration"""
    success = agent_service.add_configuration("test_agent", sample_agent_config)
    assert success is True
    
    # Verify the configuration was added
    config = agent_service.get_configuration("test_agent")
    assert config is not None
    assert config.name == "test_agent"
    assert config.description == "A test agent"

def test_get_configuration(agent_service, sample_agent_config):
    """Test getting an agent configuration"""
    agent_service.add_configuration("test_agent", sample_agent_config)
    
    config = agent_service.get_configuration("test_agent")
    assert config is not None
    assert config.name == "test_agent"
    
    # Test getting non-existent configuration
    config = agent_service.get_configuration("non_existent")
    assert config is None

def test_get_configuration_names(agent_service, sample_agent_config):
    """Test getting configuration names"""
    # Should have default configuration
    names = agent_service.get_configuration_names()
    assert "default" in names
    
    # Add test configuration
    agent_service.add_configuration("test_agent", sample_agent_config)
    names = agent_service.get_configuration_names()
    assert "test_agent" in names
    assert len(names) >= 2

def test_delete_configuration(agent_service, sample_agent_config):
    """Test deleting an agent configuration"""
    # Add configuration first
    agent_service.add_configuration("test_agent", sample_agent_config)
    assert agent_service.get_configuration("test_agent") is not None
    
    # Delete configuration
    success = agent_service.delete_configuration("test_agent")
    assert success is True
    assert agent_service.get_configuration("test_agent") is None
    
    # Test deleting non-existent configuration
    success = agent_service.delete_configuration("non_existent")
    assert success is False
    
    # Test that default configuration cannot be deleted
    success = agent_service.delete_configuration("default")
    assert success is False

def test_duplicate_configuration(agent_service, sample_agent_config):
    """Test duplicating an agent configuration"""
    # Add source configuration
    agent_service.add_configuration("source_agent", sample_agent_config)
    
    # Duplicate configuration
    success = agent_service.duplicate_configuration("source_agent", "target_agent")
    assert success is True
    
    # Verify both configurations exist
    source_config = agent_service.get_configuration("source_agent")
    target_config = agent_service.get_configuration("target_agent")
    
    assert source_config is not None
    assert target_config is not None
    assert target_config.name == "target_agent"
    assert "Copy of" in target_config.description
    
    # Test duplicating non-existent configuration
    success = agent_service.duplicate_configuration("non_existent", "target2")
    assert success is False
    
    # Test duplicating to existing name
    success = agent_service.duplicate_configuration("source_agent", "target_agent")
    assert success is False

def test_get_configurations(agent_service, sample_agent_config):
    """Test getting all configurations info"""
    configs = agent_service.get_configurations()
    assert isinstance(configs, list)
    assert len(configs) >= 1  # Should have default
    
    # Add test configuration
    agent_service.add_configuration("test_agent", sample_agent_config)
    configs = agent_service.get_configurations()
    
    # Find the test agent in configs
    test_config = next((c for c in configs if c["name"] == "test_agent"), None)
    assert test_config is not None
    assert test_config["description"] == "A test agent"
    assert test_config["agent_type"] == "react"
    assert test_config["tools_count"] == 1

def test_update_metrics(agent_service):
    """Test updating agent metrics"""
    # Update metrics for default agent
    agent_service.update_metrics("default", 1.5, True, 3, 2)
    
    metrics = agent_service.get_metrics("default")
    assert metrics is not None
    assert metrics.total_executions == 1
    assert metrics.successful_executions == 1
    assert metrics.failed_executions == 0
    assert metrics.average_execution_time == 1.5
    assert metrics.average_iterations == 3.0
    assert metrics.total_tool_calls == 2

def test_reload_configurations(agent_service, sample_agent_config):
    """Test reloading configurations"""
    # Add a configuration
    agent_service.add_configuration("test_agent", sample_agent_config)
    assert "test_agent" in agent_service.configurations
    
    # Reload configurations
    success = agent_service.reload_configurations()
    assert success is True
    
    # Configuration should still be there (it was saved)
    assert "test_agent" in agent_service.configurations
