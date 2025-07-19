from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class AgentState(BaseModel):
    """State model for agent execution"""
    messages: List[Dict[str, str]] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    iteration: int = Field(default=0)
    max_iterations: int = Field(default=10)
    is_complete: bool = Field(default=False)
    error: Optional[str] = Field(default=None)

class ToolCall(BaseModel):
    """Model for tool call information"""
    tool_name: str
    parameters: Dict[str, Any]
    result: Any
    execution_time: float
    success: bool
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class AgentExecution(BaseModel):
    """Model for tracking agent execution"""
    agent_name: str
    execution_id: str
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = Field(default="running")  # running, completed, failed, timeout
    iterations: int = Field(default=0)
    tool_calls: List[ToolCall] = Field(default_factory=list)
    final_response: Optional[str] = None
    error: Optional[str] = None

class MemoryEntry(BaseModel):
    """Model for memory entries"""
    id: str
    agent_name: str
    content: str
    role: str  # user, assistant, system
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None  # For vector memory

class AgentMetrics(BaseModel):
    """Model for agent performance metrics"""
    agent_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0.0
    average_iterations: float = 0.0
    total_tool_calls: int = 0
    last_execution: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
