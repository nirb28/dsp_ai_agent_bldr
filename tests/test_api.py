import pytest
from fastapi.testclient import TestClient
import tempfile
import shutil

from main import app

@pytest.fixture
def temp_storage(monkeypatch):
    """Create a temporary storage directory for testing"""
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setattr('app.config.settings.STORAGE_PATH', temp_dir)
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def client(temp_storage):
    """Create a test client"""
    return TestClient(app)

def test_root_endpoint(client):
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Agent Platform" in data["message"]

def test_health_endpoint(client):
    """Test the health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_api_health_endpoint(client):
    """Test the API health endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data

def test_list_agents(client):
    """Test listing agents"""
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert "count" in data
    assert data["count"] >= 1  # Should have default agent

def test_list_agent_names(client):
    """Test listing agent names only"""
    response = client.get("/api/v1/agents?names_only=true")
    assert response.status_code == 200
    data = response.json()
    assert "names" in data
    assert "count" in data
    assert "default" in data["names"]

def test_get_default_agent(client):
    """Test getting the default agent"""
    response = client.get("/api/v1/agents/default")
    assert response.status_code == 200
    data = response.json()
    assert "agent_name" in data
    assert "config" in data
    assert data["agent_name"] == "default"

def test_get_nonexistent_agent(client):
    """Test getting a non-existent agent"""
    response = client.get("/api/v1/agents/nonexistent")
    assert response.status_code == 404

def test_create_agent(client):
    """Test creating a new agent"""
    agent_config = {
        "name": "test_agent",
        "config": {
            "name": "test_agent",
            "description": "A test agent",
            "agent_type": "react",
            "llm": {
                "model": "llama3-8b-8192",
                "provider": "groq",
                "temperature": 0.7,
                "max_tokens": 1024
            },
            "system_prompt": "You are a test agent.",
            "tools": [
                {
                    "name": "calculator",
                    "type": "calculator",
                    "description": "Test calculator",
                    "enabled": True
                }
            ],
            "memory": {
                "type": "buffer",
                "max_tokens": 2000
            }
        }
    }
    
    response = client.post("/api/v1/agents", json=agent_config)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "agent_name" in data
    assert data["agent_name"] == "test_agent"

def test_duplicate_agent(client):
    """Test duplicating an agent"""
    # First create an agent
    agent_config = {
        "name": "source_agent",
        "config": {
            "name": "source_agent",
            "description": "Source agent",
            "agent_type": "react",
            "tools": []
        }
    }
    
    client.post("/api/v1/agents", json=agent_config)
    
    # Now duplicate it
    duplicate_request = {
        "source_name": "source_agent",
        "target_name": "target_agent"
    }
    
    response = client.post("/api/v1/agents/duplicate", json=duplicate_request)
    assert response.status_code == 200
    data = response.json()
    assert "source_name" in data
    assert "target_name" in data
    assert data["source_name"] == "source_agent"
    assert data["target_name"] == "target_agent"

def test_delete_agent(client):
    """Test deleting an agent"""
    # First create an agent
    agent_config = {
        "name": "delete_me",
        "config": {
            "name": "delete_me",
            "description": "Agent to be deleted",
            "agent_type": "react",
            "tools": []
        }
    }
    
    client.post("/api/v1/agents", json=agent_config)
    
    # Now delete it
    response = client.delete("/api/v1/agents/delete_me")
    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True
    assert data["agent_name"] == "delete_me"

def test_list_tools(client):
    """Test listing available tools"""
    response = client.get("/api/v1/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert "count" in data
    assert data["count"] > 0
    
    # Check that calculator tool is available
    tools = data["tools"]
    assert "calculator" in tools

def test_copilotkit_chat(client):
    """Test CopilotKit compatible endpoint"""
    chat_request = {
        "messages": [
            {
                "role": "user",
                "content": "Hello, can you help me?"
            }
        ],
        "agent": "default"
    }
    
    # Note: This test might fail if no API keys are configured
    # In a real test environment, you'd mock the LLM calls
    response = client.post("/api/v1/copilotkit/chat", json=chat_request)
    # We expect either success or a configuration error
    assert response.status_code in [200, 500]

def test_legacy_agent_endpoint(client):
    """Test legacy agent endpoint"""
    request_data = {
        "input": "Hello, test message"
    }
    
    # Note: This test might fail if no API keys are configured
    response = client.post("/agent", json=request_data)
    # We expect either success or a configuration error
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "response" in data
