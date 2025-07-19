from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from app.config import AgentConfig

# Health Check Models
class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, str]

# Agent Configuration Models
class AgentConfigRequest(BaseModel):
    """Request model for creating/updating agent configurations"""
    name: str = Field(description="Agent configuration name")
    config: AgentConfig = Field(description="Agent configuration")

class AgentConfigResponse(BaseModel):
    """Response model for agent configuration operations"""
    message: str
    agent_name: str
    config: AgentConfig

class AgentInfo(BaseModel):
    """Information about an agent configuration"""
    name: str
    description: str
    agent_type: str
    llm_provider: str
    llm_model: str
    tools_count: int
    memory_type: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class AgentConfigsResponse(BaseModel):
    """Response model for listing agent configurations"""
    agents: List[AgentInfo]
    count: int

class AgentNamesResponse(BaseModel):
    """Response model for listing agent names only"""
    names: List[str]
    count: int

class DuplicateAgentRequest(BaseModel):
    """Request model for duplicating an agent configuration"""
    source_name: str = Field(description="Source agent configuration name")
    target_name: str = Field(description="Target agent configuration name")
    include_memory: bool = Field(default=False, description="Whether to include memory state")

class DuplicateAgentResponse(BaseModel):
    """Response model for agent duplication"""
    message: str
    source_name: str
    target_name: str
    config: AgentConfig

class DeleteAgentResponse(BaseModel):
    """Response model for agent deletion"""
    message: str
    agent_name: str
    deleted: bool

# Agent Execution Models
class Message(BaseModel):
    """Chat message model"""
    role: str = Field(description="Message role (user, assistant, system)")
    content: str = Field(description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class AgentExecuteRequest(BaseModel):
    """Request model for agent execution"""
    agent_name: str = Field(description="Name of the agent to execute")
    messages: List[Message] = Field(description="Conversation messages")
    stream: bool = Field(default=False, description="Whether to stream the response")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

class AgentExecuteResponse(BaseModel):
    """Response model for agent execution"""
    response: str = Field(description="Agent response")
    agent_name: str = Field(description="Name of the executed agent")
    execution_time: float = Field(description="Execution time in seconds")
    iterations: int = Field(description="Number of iterations used")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Tools called during execution")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class AgentStreamResponse(BaseModel):
    """Response model for streaming agent execution"""
    chunk: str = Field(description="Response chunk")
    agent_name: str = Field(description="Name of the executed agent")
    is_final: bool = Field(default=False, description="Whether this is the final chunk")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

# Tool Models
class ToolExecuteRequest(BaseModel):
    """Request model for direct tool execution"""
    tool_name: str = Field(description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(description="Tool parameters")
    agent_name: Optional[str] = Field(default=None, description="Agent context for the tool")

class ToolExecuteResponse(BaseModel):
    """Response model for tool execution"""
    result: Any = Field(description="Tool execution result")
    tool_name: str = Field(description="Name of the executed tool")
    execution_time: float = Field(description="Execution time in seconds")
    success: bool = Field(description="Whether execution was successful")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")

# Memory Models
class MemoryQueryRequest(BaseModel):
    """Request model for querying agent memory"""
    agent_name: str = Field(description="Name of the agent")
    query: Optional[str] = Field(default=None, description="Memory query (for vector memory)")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of memories to return")

class MemoryQueryResponse(BaseModel):
    """Response model for memory queries"""
    memories: List[Dict[str, Any]] = Field(description="Retrieved memories")
    agent_name: str = Field(description="Name of the agent")
    count: int = Field(description="Number of memories returned")

class MemoryClearRequest(BaseModel):
    """Request model for clearing agent memory"""
    agent_name: str = Field(description="Name of the agent")
    confirm: bool = Field(description="Confirmation flag")

class MemoryClearResponse(BaseModel):
    """Response model for memory clearing"""
    message: str
    agent_name: str
    cleared: bool

# Error Models
class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

# CopilotKit Compatibility Models
class CopilotKitMessage(BaseModel):
    """CopilotKit compatible message model"""
    role: str
    content: str

class CopilotKitRequest(BaseModel):
    """CopilotKit compatible request model"""
    messages: List[CopilotKitMessage]
    agent: Optional[str] = Field(default="default", description="Agent to use")

class CopilotKitResponse(BaseModel):
    """CopilotKit compatible response model"""
    response: str
    metadata: Optional[Dict[str, Any]] = None
