from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
import logging

from app.config import MCPServerConfig
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mcp", tags=["MCP"])

# Dependency to get agent service
def get_agent_service() -> AgentService:
    return AgentService()

@router.get("/servers", response_model=Dict[str, Any])
async def get_mcp_servers(agent_service: AgentService = Depends(get_agent_service)):
    """Get all MCP servers and their status"""
    try:
        mcp_service = agent_service.get_mcp_service()
        servers = mcp_service.get_servers()
        
        return {
            "success": True,
            "servers": servers,
            "count": len(servers)
        }
    except Exception as e:
        logger.error(f"Error getting MCP servers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/servers/{server_name}", response_model=Dict[str, Any])
async def get_mcp_server(server_name: str, agent_service: AgentService = Depends(get_agent_service)):
    """Get information about a specific MCP server"""
    try:
        server_info = agent_service.get_mcp_server_info(server_name)
        
        if not server_info:
            raise HTTPException(status_code=404, detail=f"MCP server '{server_name}' not found")
        
        return {
            "success": True,
            "server": server_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting MCP server '{server_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/servers", response_model=Dict[str, Any])
async def add_mcp_server(config: MCPServerConfig, agent_service: AgentService = Depends(get_agent_service)):
    """Add or update an MCP server configuration"""
    try:
        mcp_service = agent_service.get_mcp_service()
        success = mcp_service.add_server(config)
        
        if success:
            return {
                "success": True,
                "message": f"MCP server '{config.name}' added successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to add MCP server '{config.name}'")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding MCP server: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/servers/{server_name}", response_model=Dict[str, Any])
async def delete_mcp_server(server_name: str, agent_service: AgentService = Depends(get_agent_service)):
    """Delete an MCP server configuration"""
    try:
        mcp_service = agent_service.get_mcp_service()
        success = mcp_service.delete_server(server_name)
        
        if success:
            return {
                "success": True,
                "message": f"MCP server '{server_name}' deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"MCP server '{server_name}' not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting MCP server '{server_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/servers/{server_name}/start", response_model=Dict[str, Any])
async def start_mcp_server(server_name: str, agent_service: AgentService = Depends(get_agent_service)):
    """Start an MCP server"""
    try:
        mcp_service = agent_service.get_mcp_service()
        success = await mcp_service.start_server(server_name)
        
        if success:
            return {
                "success": True,
                "message": f"MCP server '{server_name}' started successfully"
            }
        else:
            server_info = mcp_service.get_server(server_name)
            error_msg = server_info.error_message if server_info else "Unknown error"
            raise HTTPException(status_code=400, detail=f"Failed to start MCP server '{server_name}': {error_msg}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting MCP server '{server_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/servers/{server_name}/stop", response_model=Dict[str, Any])
async def stop_mcp_server(server_name: str, agent_service: AgentService = Depends(get_agent_service)):
    """Stop an MCP server"""
    try:
        mcp_service = agent_service.get_mcp_service()
        success = await mcp_service.stop_server(server_name)
        
        if success:
            return {
                "success": True,
                "message": f"MCP server '{server_name}' stopped successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to stop MCP server '{server_name}'")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping MCP server '{server_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/servers/{server_name}/health", response_model=Dict[str, Any])
async def health_check_mcp_server(server_name: str, agent_service: AgentService = Depends(get_agent_service)):
    """Check health of an MCP server"""
    try:
        mcp_service = agent_service.get_mcp_service()
        is_healthy = await mcp_service.health_check(server_name)
        
        return {
            "success": True,
            "healthy": is_healthy,
            "server": server_name
        }
    except Exception as e:
        logger.error(f"Error checking health of MCP server '{server_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/servers/{server_name}/discover", response_model=Dict[str, Any])
async def discover_mcp_server_capabilities(server_name: str, agent_service: AgentService = Depends(get_agent_service)):
    """Discover capabilities of an MCP server"""
    try:
        mcp_service = agent_service.get_mcp_service()
        await mcp_service.discover_capabilities(server_name)
        
        server_info = mcp_service.get_server(server_name)
        if not server_info:
            raise HTTPException(status_code=404, detail=f"MCP server '{server_name}' not found")
        
        return {
            "success": True,
            "tools": server_info.available_tools,
            "resources": server_info.available_resources
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error discovering capabilities for MCP server '{server_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/servers/{server_name}/tools/{tool_name}/call", response_model=Dict[str, Any])
async def call_mcp_tool(
    server_name: str, 
    tool_name: str, 
    arguments: Dict[str, Any],
    agent_service: AgentService = Depends(get_agent_service)
):
    """Call a tool on an MCP server"""
    try:
        mcp_service = agent_service.get_mcp_service()
        result = await mcp_service.call_tool(server_name, tool_name, arguments)
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error calling tool '{tool_name}' on MCP server '{server_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/servers/{server_name}/resources/{resource_uri:path}", response_model=Dict[str, Any])
async def get_mcp_resource(
    server_name: str, 
    resource_uri: str,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Get a resource from an MCP server"""
    try:
        mcp_service = agent_service.get_mcp_service()
        result = await mcp_service.get_resource(server_name, resource_uri)
        
        return {
            "success": True,
            "resource": result
        }
    except Exception as e:
        logger.error(f"Error getting resource '{resource_uri}' from MCP server '{server_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reload", response_model=Dict[str, Any])
async def reload_mcp_configurations(agent_service: AgentService = Depends(get_agent_service)):
    """Reload MCP server configurations from file"""
    try:
        mcp_service = agent_service.get_mcp_service()
        success = mcp_service.reload_configurations()
        
        if success:
            return {
                "success": True,
                "message": "MCP server configurations reloaded successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to reload MCP server configurations")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reloading MCP configurations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
