import asyncio
import logging
from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.services.mcp_service import MCPService

logger = logging.getLogger(__name__)

class MCPToolInput(BaseModel):
    """Input schema for MCP tools"""
    arguments: Dict[str, Any] = Field(description="Arguments to pass to the MCP tool")

class MCPTool(BaseTool):
    """A tool that calls an MCP server"""
    
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    server_name: str = Field(description="MCP server name")
    tool_name: str = Field(description="MCP tool name")
    mcp_service: MCPService = Field(description="MCP service instance")
    args_schema: type[BaseModel] = MCPToolInput
    
    def _run(self, arguments: Dict[str, Any]) -> str:
        """Run the tool synchronously"""
        try:
            # Run the async method in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.mcp_service.call_tool(self.server_name, self.tool_name, arguments)
                )
                return str(result.get("content", result))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error calling MCP tool '{self.tool_name}' on server '{self.server_name}': {str(e)}")
            return f"Error: {str(e)}"
    
    async def _arun(self, arguments: Dict[str, Any]) -> str:
        """Run the tool asynchronously"""
        try:
            result = await self.mcp_service.call_tool(self.server_name, self.tool_name, arguments)
            return str(result.get("content", result))
        except Exception as e:
            logger.error(f"Error calling MCP tool '{self.tool_name}' on server '{self.server_name}': {str(e)}")
            return f"Error: {str(e)}"

class MCPToolFactory:
    """Factory for creating MCP tools"""
    
    def __init__(self, mcp_service: MCPService):
        self.mcp_service = mcp_service
    
    async def create_tools_for_server(self, server_name: str) -> List[MCPTool]:
        """Create tools for all available tools on an MCP server"""
        tools = []
        
        try:
            server_info = self.mcp_service.get_server(server_name)
            if not server_info:
                logger.error(f"MCP server '{server_name}' not found")
                return tools
            
            # Ensure server is running and capabilities are discovered
            if server_info.status.value != "running":
                await self.mcp_service.start_server(server_name)
                await self.mcp_service.discover_capabilities(server_name)
            
            # Create tools for each available tool
            for tool_info in server_info.available_tools:
                tool_name = tool_info.get("name")
                tool_description = tool_info.get("description", f"Tool from MCP server {server_name}")
                
                if tool_name:
                    mcp_tool = MCPTool(
                        name=f"{server_name}_{tool_name}",
                        description=tool_description,
                        server_name=server_name,
                        tool_name=tool_name,
                        mcp_service=self.mcp_service
                    )
                    tools.append(mcp_tool)
                    logger.info(f"Created MCP tool: {mcp_tool.name}")
            
        except Exception as e:
            logger.error(f"Error creating tools for MCP server '{server_name}': {str(e)}")
        
        return tools
    
    async def create_tools_for_servers(self, server_names: List[str]) -> List[MCPTool]:
        """Create tools for multiple MCP servers"""
        all_tools = []
        
        for server_name in server_names:
            tools = await self.create_tools_for_server(server_name)
            all_tools.extend(tools)
        
        return all_tools
    
    def create_tool_from_config(self, server_name: str, tool_name: str, description: str) -> MCPTool:
        """Create a single MCP tool from configuration"""
        return MCPTool(
            name=f"{server_name}_{tool_name}",
            description=description,
            server_name=server_name,
            tool_name=tool_name,
            mcp_service=self.mcp_service
        )
