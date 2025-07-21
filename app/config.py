import os
import json
import logging
import re
from enum import Enum
from typing import Dict, Any, Optional, List, Union, TypeVar, Type
from pydantic import BaseModel, Field, model_validator, validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Type variable for generic model types
T = TypeVar('T', bound=BaseModel)

# Regular expression to match environment variable patterns like ${VAR_NAME}
ENV_VAR_PATTERN = re.compile(r'\${([A-Za-z0-9_]+)}')

def resolve_env_vars(value: str) -> str:
    """Replace environment variable references in a string with their values."""
    if not isinstance(value, str):
        return value
        
    def replace_env_var(match):
        var_name = match.group(1)
        env_value = os.getenv(var_name)
        if env_value is None:
            logging.warning(f"Environment variable '{var_name}' not found in .env file")
            return match.group(0)  # Return the original ${VAR_NAME} if not found
        return env_value
        
    return ENV_VAR_PATTERN.sub(replace_env_var, value)

def process_env_vars_in_model(model: T) -> T:
    """Process all string fields in a Pydantic model to substitute environment variables."""
    data = model.dict()
    
    # Process all string values in the model data
    for field_name, field_value in data.items():
        if isinstance(field_value, str):
            data[field_name] = resolve_env_vars(field_value)
        elif isinstance(field_value, dict):
            # Handle nested dictionaries
            for k, v in field_value.items():
                if isinstance(v, str):
                    field_value[k] = resolve_env_vars(v)
        elif isinstance(field_value, BaseModel):
            # Handle nested models
            data[field_name] = process_env_vars_in_model(field_value)
    
    # Create a new model instance with the processed data
    return model.__class__(**data)

class LLMProvider(str, Enum):
    """The provider of the LLM service"""
    GROQ = "groq"
    OPENAI = "openai"
    OPENAI_COMPATIBLE = "openai_compatible"
    TRITON = "triton"
    LOCAL = "local"

class AgentType(str, Enum):
    """Types of agents that can be created"""
    REACT = "react"  # ReAct (Reasoning and Acting) agent
    CONVERSATIONAL = "conversational"  # Simple conversational agent
    TOOL_CALLING = "tool_calling"  # Agent focused on tool usage
    PLANNING = "planning"  # Multi-step planning agent
    CUSTOM = "custom"  # Custom agent with user-defined graph

class ToolType(str, Enum):
    """Types of tools available to agents"""
    CALCULATOR = "calculator"
    WEB_SEARCH = "web_search"
    FILE_READER = "file_reader"
    CODE_EXECUTOR = "code_executor"
    API_CALLER = "api_caller"
    DATABASE_QUERY = "database_query"
    EMAIL_SENDER = "email_sender"
    MCP = "mcp"  # MCP server tool
    CUSTOM = "custom"

class MemoryType(str, Enum):
    """Types of memory systems for agents"""
    NONE = "none"
    BUFFER = "buffer"  # Simple conversation buffer
    SUMMARY = "summary"  # Summarized conversation history
    VECTOR = "vector"  # Vector-based memory
    ENTITY = "entity"  # Entity-based memory

class MCPTransport(str, Enum):
    """MCP transport protocols"""
    HTTP = "http"
    STREAMABLE_HTTP = "streamable-http"
    STDIO = "stdio"
    SSE = "sse"

class MCPServerStatus(str, Enum):
    """MCP server status"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    UNKNOWN = "unknown"

# Common model names for reference
COMMON_MODELS = {
    "groq": ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768", "gemma-7b-it"],
    "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"],
    "openai_compatible": ["llama3", "mistral", "mixtral", "codellama"],
    "triton": ["Llama-3.1-70B-Instruct", "llama3-vllm"],
    "local": ["custom-model"]
}

class LLMConfig(BaseModel):
    """Configuration for the Language Model"""
    model: str = Field(default="llama3-8b-8192", description="Model name")
    provider: LLMProvider = Field(default=LLMProvider.GROQ, description="LLM provider")
    api_key: Optional[str] = Field(default=None, description="API key for the provider")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=None, ge=1, le=100)
    server_url: Optional[str] = Field(default="http://localhost:8000", description="URL for custom server")
    
    @model_validator(mode='after')
    def validate_provider(self):
        """Ensure provider is valid"""
        if self.provider not in [p.value for p in LLMProvider]:
            raise ValueError(f"Invalid provider: {self.provider}")
        return self

class MCPServerConfig(BaseModel):
    """Configuration for an MCP server"""
    name: str = Field(description="Server name (unique identifier)")
    display_name: str = Field(description="Human-readable server name")
    description: str = Field(description="Description of what the server provides")
    transport: MCPTransport = Field(default=MCPTransport.HTTP, description="Transport protocol")
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    base_url: Optional[str] = Field(default=None, description="Base URL for HTTP transport")
    command: Optional[str] = Field(default=None, description="Command to start server (for stdio)")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    enabled: bool = Field(default=True, description="Whether the server is enabled")
    auto_start: bool = Field(default=False, description="Whether to auto-start the server")
    timeout: int = Field(default=30, ge=5, le=300, description="Connection timeout in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @property
    def url(self) -> str:
        """Get the full URL for HTTP-based transports"""
        if self.base_url:
            return self.base_url
        return f"http://{self.host}:{self.port}"

class ToolConfig(BaseModel):
    """Configuration for a tool"""
    name: str = Field(description="Tool name")
    type: ToolType = Field(description="Type of tool")
    description: str = Field(description="Description of what the tool does")
    enabled: bool = Field(default=True, description="Whether the tool is enabled")
    config: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific configuration")
    # MCP-specific fields
    mcp_server: Optional[str] = Field(default=None, description="MCP server name (for MCP tools)")
    mcp_tool_name: Optional[str] = Field(default=None, description="MCP tool name (for MCP tools)")
    
class MemoryConfig(BaseModel):
    """Configuration for agent memory"""
    type: MemoryType = Field(default=MemoryType.BUFFER, description="Type of memory system")
    max_tokens: int = Field(default=2000, ge=100, le=10000, description="Maximum tokens to store")
    summary_prompt: Optional[str] = Field(default=None, description="Custom summary prompt")
    vector_store_config: Optional[Dict[str, Any]] = Field(default=None, description="Vector store configuration")

class AgentConfig(BaseModel):
    """Main configuration for an agent"""
    name: str = Field(description="Agent name")
    description: str = Field(description="Agent description")
    agent_type: AgentType = Field(default=AgentType.REACT, description="Type of agent")
    llm: LLMConfig = Field(default_factory=LLMConfig, description="LLM configuration")
    system_prompt: str = Field(
        default="You are a helpful AI assistant. Use the available tools to help the user.",
        description="System prompt for the agent"
    )
    tools: List[ToolConfig] = Field(default_factory=list, description="Available tools")
    mcp_servers: List[str] = Field(default_factory=list, description="MCP server names to use")
    memory: MemoryConfig = Field(default_factory=MemoryConfig, description="Memory configuration")
    max_iterations: int = Field(default=10, ge=1, le=50, description="Maximum iterations for agent execution")
    timeout: int = Field(default=300, ge=30, le=1800, description="Timeout in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @model_validator(mode='after')
    def validate_config(self):
        """Validate the agent configuration"""
        # Ensure tool names are unique
        tool_names = [tool.name for tool in self.tools]
        if len(tool_names) != len(set(tool_names)):
            raise ValueError("Tool names must be unique")
        
        # Validate system prompt
        if not self.system_prompt.strip():
            raise ValueError("System prompt cannot be empty")
            
        return self

class Settings:
    """Application settings"""
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "3000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "./storage")
    AGENT_CONFIGS_FILE: str = os.getenv("AGENT_CONFIGS_FILE", "agent_configurations.json")
    MCP_SERVERS_FILE: str = os.getenv("MCP_SERVERS_FILE", "mcp_servers.json")
    MODEL_SERVER_URL: str = os.getenv("MODEL_SERVER_URL", "http://localhost:9001")
    TRITON_SERVER_URL: str = os.getenv("TRITON_SERVER_URL", "http://localhost:8001")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    DEFAULT_MAX_TOKENS: int = int(os.getenv("DEFAULT_MAX_TOKENS", "1024"))
    DEFAULT_TOP_P: float = float(os.getenv("DEFAULT_TOP_P", "0.9"))
    # MCP settings
    MCP_SERVERS_DIR: str = os.getenv("MCP_SERVERS_DIR", "./mcp_servers")
    MCP_DEFAULT_TIMEOUT: int = int(os.getenv("MCP_DEFAULT_TIMEOUT", "30"))

settings = Settings()
