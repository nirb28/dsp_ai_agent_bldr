import logging
import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
import json

from app.models.api_models import (
    HealthResponse, AgentConfigRequest, AgentConfigResponse, AgentConfigsResponse,
    AgentNamesResponse, DuplicateAgentRequest, DuplicateAgentResponse, DeleteAgentResponse,
    AgentExecuteRequest, AgentExecuteResponse, ToolExecuteRequest, ToolExecuteResponse,
    MemoryQueryRequest, MemoryQueryResponse, MemoryClearRequest, MemoryClearResponse,
    CopilotKitRequest, CopilotKitResponse, ErrorResponse, Message
)
from app.services.agent_service import AgentService
from app.services.execution_service import ExecutionService
from app.services.tool_service import ToolService
from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)

# Initialize services
agent_service = AgentService()
tool_service = ToolService()
memory_service = MemoryService()
execution_service = ExecutionService(tool_service, memory_service)

router = APIRouter()

# Health Check
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        services={
            "agent_service": "running",
            "execution_service": "running",
            "tool_service": "running",
            "memory_service": "running"
        }
    )

# Agent Configuration Endpoints
@router.post("/agents", response_model=AgentConfigResponse)
async def create_agent(request: AgentConfigRequest):
    """Create or update an agent configuration"""
    try:
        success = agent_service.add_configuration(request.name, request.config)
        
        if success:
            return AgentConfigResponse(
                message=f"Agent '{request.name}' created/updated successfully",
                agent_name=request.name,
                config=request.config
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to create/update agent")
            
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_name}")
async def get_agent(agent_name: str):
    """Get a specific agent configuration"""
    try:
        config = agent_service.get_configuration(agent_name)
        
        if not config:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        return {
            "agent_name": agent_name,
            "config": config.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents", response_model=AgentConfigsResponse)
async def list_agents(names_only: bool = Query(False, description="Return only agent names")):
    """List all agent configurations"""
    try:
        if names_only:
            names = agent_service.get_configuration_names()
            return AgentNamesResponse(names=names, count=len(names))
        else:
            configs = agent_service.get_configurations()
            return AgentConfigsResponse(agents=configs, count=len(configs))
            
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/agents/{agent_name}", response_model=DeleteAgentResponse)
async def delete_agent(agent_name: str):
    """Delete an agent configuration"""
    try:
        success = agent_service.delete_configuration(agent_name)
        
        if success:
            return DeleteAgentResponse(
                message=f"Agent '{agent_name}' deleted successfully",
                agent_name=agent_name,
                deleted=True
            )
        else:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/duplicate", response_model=DuplicateAgentResponse)
async def duplicate_agent(request: DuplicateAgentRequest):
    """Duplicate an agent configuration"""
    try:
        success = agent_service.duplicate_configuration(request.source_name, request.target_name)
        
        if success:
            config = agent_service.get_configuration(request.target_name)
            return DuplicateAgentResponse(
                message=f"Agent '{request.source_name}' duplicated to '{request.target_name}' successfully",
                source_name=request.source_name,
                target_name=request.target_name,
                config=config
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to duplicate agent")
            
    except Exception as e:
        logger.error(f"Error duplicating agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/reload")
async def reload_agents():
    """Reload agent configurations from file"""
    try:
        success = agent_service.reload_configurations()
        
        if success:
            return {"message": "Agent configurations reloaded successfully", "status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to reload configurations")
            
    except Exception as e:
        logger.error(f"Error reloading agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent Execution Endpoints
@router.post("/agents/{agent_name}/execute", response_model=AgentExecuteResponse)
async def execute_agent(agent_name: str, request: AgentExecuteRequest):
    """Execute an agent with given messages"""
    try:
        # Override agent name from URL
        request.agent_name = agent_name
        
        config = agent_service.get_configuration(agent_name)
        if not config:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        # Convert messages to dict format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        start_time = time.time()
        execution = await execution_service.execute_agent(
            agent_name, config, messages, request.context
        )
        execution_time = time.time() - start_time
        
        # Update metrics
        success = execution.status == "completed"
        agent_service.update_metrics(
            agent_name, execution_time, success, 
            execution.iterations, len(execution.tool_calls)
        )
        
        if execution.status == "completed":
            return AgentExecuteResponse(
                response=execution.final_response or "No response",
                agent_name=agent_name,
                execution_time=execution_time,
                iterations=execution.iterations,
                tool_calls=[tc.dict() for tc in execution.tool_calls]
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Agent execution failed: {execution.error}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{agent_name}/execute/stream")
async def execute_agent_stream(agent_name: str, request: AgentExecuteRequest):
    """Execute an agent with streaming response"""
    try:
        config = agent_service.get_configuration(agent_name)
        if not config:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        # Convert messages to dict format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        async def stream_generator():
            async for chunk_data in execution_service.execute_agent_stream(
                agent_name, config, messages, request.context
            ):
                yield f"data: {json.dumps(chunk_data)}\n\n"
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming agent execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Tool Endpoints
@router.post("/tools/{tool_name}/execute", response_model=ToolExecuteResponse)
async def execute_tool(tool_name: str, request: ToolExecuteRequest):
    """Execute a tool directly"""
    try:
        # Override tool name from URL
        request.tool_name = tool_name
        
        result = tool_service.execute_tool(
            tool_name, request.parameters, request.agent_name
        )
        
        return ToolExecuteResponse(**result)
        
    except Exception as e:
        logger.error(f"Error executing tool: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools")
async def list_tools():
    """List all available tools"""
    try:
        tools = tool_service.get_available_tools()
        return {"tools": tools, "count": len(tools)}
        
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Memory Endpoints
@router.post("/agents/{agent_name}/memory/query", response_model=MemoryQueryResponse)
async def query_agent_memory(agent_name: str, request: MemoryQueryRequest):
    """Query agent memory"""
    try:
        # Override agent name from URL
        request.agent_name = agent_name
        
        memories = await memory_service.query_memory(
            agent_name, request.query, request.limit
        )
        
        return MemoryQueryResponse(
            memories=memories,
            agent_name=agent_name,
            count=len(memories)
        )
        
    except Exception as e:
        logger.error(f"Error querying memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{agent_name}/memory/clear", response_model=MemoryClearResponse)
async def clear_agent_memory(agent_name: str, request: MemoryClearRequest):
    """Clear agent memory"""
    try:
        if not request.confirm:
            raise HTTPException(status_code=400, detail="Confirmation required to clear memory")
        
        success = await memory_service.clear_memory(agent_name)
        
        return MemoryClearResponse(
            message=f"Memory cleared for agent '{agent_name}'" if success else "Failed to clear memory",
            agent_name=agent_name,
            cleared=success
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_name}/memory/stats")
async def get_memory_stats(agent_name: str):
    """Get memory statistics for an agent"""
    try:
        stats = memory_service.get_memory_stats(agent_name)
        return {"agent_name": agent_name, "stats": stats}
        
    except Exception as e:
        logger.error(f"Error getting memory stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# CopilotKit Compatibility Endpoints
@router.post("/copilotkit/chat", response_model=CopilotKitResponse)
async def copilotkit_chat(request: CopilotKitRequest):
    """CopilotKit compatible chat endpoint"""
    try:
        agent_name = request.agent or "default"
        
        config = agent_service.get_configuration(agent_name)
        if not config:
            # Use default agent if specified agent not found
            agent_name = "default"
            config = agent_service.get_configuration(agent_name)
        
        if not config:
            raise HTTPException(status_code=404, detail="No agents available")
        
        # Convert CopilotKit messages to internal format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        execution = await execution_service.execute_agent(agent_name, config, messages)
        
        if execution.status == "completed":
            return CopilotKitResponse(
                response=execution.final_response or "No response",
                metadata={
                    "agent_name": agent_name,
                    "execution_time": (execution.end_time - execution.start_time).total_seconds(),
                    "iterations": execution.iterations
                }
            )
        else:
            raise HTTPException(status_code=500, detail=f"Execution failed: {execution.error}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in CopilotKit chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Legacy endpoint for compatibility
@router.post("/agent")
async def legacy_agent_endpoint(request: Request):
    """Legacy agent endpoint for compatibility with existing clients"""
    try:
        body = await request.json()
        
        # Extract input from various possible formats
        if "input" in body:
            user_input = body["input"]
        elif "messages" in body and isinstance(body["messages"], list) and body["messages"]:
            user_input = body["messages"][-1]["content"]
        else:
            for value in body.values():
                if isinstance(value, str):
                    user_input = value
                    break
            else:
                user_input = ""
        
        # Use default agent
        agent_name = "default"
        config = agent_service.get_configuration(agent_name)
        
        if not config:
            return {"response": "No default agent configured"}
        
        messages = [{"role": "user", "content": user_input}]
        execution = await execution_service.execute_agent(agent_name, config, messages)
        
        if execution.status == "completed":
            return {"response": execution.final_response or "No response"}
        else:
            return {"response": f"Error: {execution.error}"}
            
    except Exception as e:
        logger.error(f"Error in legacy endpoint: {str(e)}")
        return {"response": f"Error: {str(e)}"}
