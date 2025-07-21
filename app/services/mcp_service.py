import json
import logging
import asyncio
import httpx
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.config import MCPServerConfig, MCPTransport, MCPServerStatus, settings, process_env_vars_in_model

logger = logging.getLogger(__name__)

class MCPServerInfo:
    """Runtime information about an MCP server"""
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.status = MCPServerStatus.STOPPED
        self.process: Optional[subprocess.Popen] = None
        self.last_health_check: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.available_tools: List[Dict[str, Any]] = []
        self.available_resources: List[Dict[str, Any]] = []

class MCPService:
    """Service for managing MCP servers"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServerInfo] = {}
        self._load_configurations()
        
    def _load_configurations(self):
        """Load MCP server configurations from storage"""
        config_file = Path(settings.STORAGE_PATH) / settings.MCP_SERVERS_FILE
        
        try:
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for server_name, config_data in data.items():
                    try:
                        config = MCPServerConfig(**config_data)
                        # Process environment variables
                        config = process_env_vars_in_model(config)
                        self.servers[server_name] = MCPServerInfo(config)
                    except Exception as e:
                        logger.error(f"Error loading MCP server configuration '{server_name}': {str(e)}")
                        continue
                        
                logger.info(f"Loaded {len(self.servers)} MCP server configurations")
            else:
                logger.info("No existing MCP server configurations found, creating defaults")
                self._create_default_configurations()
                
        except Exception as e:
            logger.error(f"Error loading MCP server configurations: {str(e)}")
            self._create_default_configurations()
    
    def _create_default_configurations(self):
        """Create default MCP server configurations"""
        default_servers = [
            MCPServerConfig(
                name="weather",
                display_name="Weather Server",
                description="Provides weather information for cities worldwide",
                transport=MCPTransport.HTTP,
                host="localhost",
                port=8002,
                enabled=True,
                auto_start=False
            ),
            MCPServerConfig(
                name="memory",
                display_name="Memory Server", 
                description="Provides persistent memory and knowledge graph capabilities",
                transport=MCPTransport.HTTP,
                host="localhost",
                port=8003,
                enabled=True,
                auto_start=False
            ),
            MCPServerConfig(
                name="calculator",
                display_name="Calculator Server",
                description="Advanced mathematical calculations and computations",
                transport=MCPTransport.HTTP,
                host="localhost", 
                port=8004,
                enabled=True,
                auto_start=False
            )
        ]
        
        for config in default_servers:
            self.servers[config.name] = MCPServerInfo(config)
            
        self._save_configurations()
    
    def _save_configurations(self):
        """Save MCP server configurations to storage"""
        try:
            config_file = Path(settings.STORAGE_PATH) / settings.MCP_SERVERS_FILE
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert configurations to dict for JSON serialization
            data = {}
            for server_name, server_info in self.servers.items():
                data[server_name] = server_info.config.dict()
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info("Saved MCP server configurations")
            
        except Exception as e:
            logger.error(f"Error saving MCP server configurations: {str(e)}")
    
    def add_server(self, config: MCPServerConfig) -> bool:
        """Add or update an MCP server configuration"""
        try:
            if config.name in self.servers:
                logger.info(f"Updating existing MCP server configuration: {config.name}")
            else:
                logger.info(f"Adding new MCP server configuration: {config.name}")
            
            self.servers[config.name] = MCPServerInfo(config)
            self._save_configurations()
            return True
            
        except Exception as e:
            logger.error(f"Error adding MCP server configuration '{config.name}': {str(e)}")
            return False
    
    def get_server(self, server_name: str) -> Optional[MCPServerInfo]:
        """Get MCP server information"""
        return self.servers.get(server_name)
    
    def get_server_names(self) -> List[str]:
        """Get list of all MCP server names"""
        return list(self.servers.keys())
    
    def get_servers(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all MCP servers"""
        result = {}
        for server_name, server_info in self.servers.items():
            result[server_name] = {
                "config": server_info.config.dict(),
                "status": server_info.status.value,
                "last_health_check": server_info.last_health_check.isoformat() if server_info.last_health_check else None,
                "error_message": server_info.error_message,
                "available_tools": server_info.available_tools,
                "available_resources": server_info.available_resources
            }
        return result
    
    def delete_server(self, server_name: str) -> bool:
        """Delete an MCP server configuration"""
        try:
            if server_name not in self.servers:
                logger.error(f"MCP server '{server_name}' not found")
                return False
            
            # Stop server if running
            server_info = self.servers[server_name]
            if server_info.status == MCPServerStatus.RUNNING:
                self.stop_server(server_name)
            
            # Remove configuration
            del self.servers[server_name]
            self._save_configurations()
            
            logger.info(f"Deleted MCP server configuration: {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting MCP server configuration '{server_name}': {str(e)}")
            return False
    
    async def start_server(self, server_name: str) -> bool:
        """Start an MCP server"""
        try:
            if server_name not in self.servers:
                logger.error(f"MCP server '{server_name}' not found")
                return False
            
            server_info = self.servers[server_name]
            config = server_info.config
            
            if not config.enabled:
                logger.error(f"MCP server '{server_name}' is disabled")
                return False
            
            if server_info.status == MCPServerStatus.RUNNING:
                logger.info(f"MCP server '{server_name}' is already running")
                return True
            
            server_info.status = MCPServerStatus.STARTING
            server_info.error_message = None
            
            if config.transport == MCPTransport.STDIO and config.command:
                # Start server as subprocess for STDIO transport
                cmd = [config.command] + config.args
                env = {**os.environ, **config.env}
                
                server_info.process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Give it a moment to start
                await asyncio.sleep(1)
                
                if server_info.process.poll() is None:
                    server_info.status = MCPServerStatus.RUNNING
                    logger.info(f"Started MCP server '{server_name}' via STDIO")
                else:
                    server_info.status = MCPServerStatus.ERROR
                    server_info.error_message = "Process exited immediately"
                    logger.error(f"Failed to start MCP server '{server_name}': Process exited")
                    return False
            
            elif config.transport in [MCPTransport.HTTP, MCPTransport.STREAMABLE_HTTP]:
                # For HTTP-based transports, we assume the server is externally managed
                # Just check if it's reachable
                is_healthy = await self.health_check(server_name)
                if is_healthy:
                    server_info.status = MCPServerStatus.RUNNING
                    logger.info(f"MCP server '{server_name}' is reachable via HTTP")
                else:
                    server_info.status = MCPServerStatus.ERROR
                    server_info.error_message = "Server not reachable"
                    logger.error(f"MCP server '{server_name}' is not reachable")
                    return False
            
            # Discover available tools and resources
            await self.discover_capabilities(server_name)
            
            return server_info.status == MCPServerStatus.RUNNING
            
        except Exception as e:
            logger.error(f"Error starting MCP server '{server_name}': {str(e)}")
            if server_name in self.servers:
                self.servers[server_name].status = MCPServerStatus.ERROR
                self.servers[server_name].error_message = str(e)
            return False
    
    async def stop_server(self, server_name: str) -> bool:
        """Stop an MCP server"""
        try:
            if server_name not in self.servers:
                logger.error(f"MCP server '{server_name}' not found")
                return False
            
            server_info = self.servers[server_name]
            
            if server_info.status == MCPServerStatus.STOPPED:
                logger.info(f"MCP server '{server_name}' is already stopped")
                return True
            
            if server_info.process:
                server_info.process.terminate()
                try:
                    server_info.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_info.process.kill()
                    server_info.process.wait()
                server_info.process = None
            
            server_info.status = MCPServerStatus.STOPPED
            server_info.error_message = None
            server_info.available_tools = []
            server_info.available_resources = []
            
            logger.info(f"Stopped MCP server '{server_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping MCP server '{server_name}': {str(e)}")
            return False
    
    async def health_check(self, server_name: str) -> bool:
        """Check if an MCP server is healthy"""
        try:
            if server_name not in self.servers:
                return False
            
            server_info = self.servers[server_name]
            config = server_info.config
            
            if config.transport in [MCPTransport.HTTP, MCPTransport.STREAMABLE_HTTP]:
                async with httpx.AsyncClient(timeout=config.timeout) as client:
                    # Try to get server capabilities
                    response = await client.get(f"{config.url}/health")
                    server_info.last_health_check = datetime.now()
                    return response.status_code == 200
            
            elif config.transport == MCPTransport.STDIO:
                # For STDIO, check if process is still running
                if server_info.process:
                    server_info.last_health_check = datetime.now()
                    return server_info.process.poll() is None
            
            return False
            
        except Exception as e:
            logger.error(f"Health check failed for MCP server '{server_name}': {str(e)}")
            return False
    
    async def discover_capabilities(self, server_name: str):
        """Discover available tools and resources from an MCP server"""
        try:
            if server_name not in self.servers:
                return
            
            server_info = self.servers[server_name]
            config = server_info.config
            
            if config.transport in [MCPTransport.HTTP, MCPTransport.STREAMABLE_HTTP]:
                async with httpx.AsyncClient(timeout=config.timeout) as client:
                    # Get available tools
                    try:
                        tools_response = await client.get(f"{config.url}/tools")
                        if tools_response.status_code == 200:
                            server_info.available_tools = tools_response.json().get("tools", [])
                    except Exception as e:
                        logger.warning(f"Could not fetch tools from '{server_name}': {str(e)}")
                    
                    # Get available resources
                    try:
                        resources_response = await client.get(f"{config.url}/resources")
                        if resources_response.status_code == 200:
                            server_info.available_resources = resources_response.json().get("resources", [])
                    except Exception as e:
                        logger.warning(f"Could not fetch resources from '{server_name}': {str(e)}")
            
            logger.info(f"Discovered {len(server_info.available_tools)} tools and {len(server_info.available_resources)} resources from '{server_name}'")
            
        except Exception as e:
            logger.error(f"Error discovering capabilities for MCP server '{server_name}': {str(e)}")
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on an MCP server"""
        try:
            if server_name not in self.servers:
                raise ValueError(f"MCP server '{server_name}' not found")
            
            server_info = self.servers[server_name]
            config = server_info.config
            
            if server_info.status != MCPServerStatus.RUNNING:
                raise ValueError(f"MCP server '{server_name}' is not running")
            
            if config.transport in [MCPTransport.HTTP, MCPTransport.STREAMABLE_HTTP]:
                async with httpx.AsyncClient(timeout=config.timeout) as client:
                    response = await client.post(
                        f"{config.url}/tools/{tool_name}",
                        json={"arguments": arguments}
                    )
                    response.raise_for_status()
                    return response.json()
            
            else:
                raise ValueError(f"Tool calling not implemented for transport: {config.transport}")
            
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}' on MCP server '{server_name}': {str(e)}")
            raise
    
    async def get_resource(self, server_name: str, resource_uri: str) -> Dict[str, Any]:
        """Get a resource from an MCP server"""
        try:
            if server_name not in self.servers:
                raise ValueError(f"MCP server '{server_name}' not found")
            
            server_info = self.servers[server_name]
            config = server_info.config
            
            if server_info.status != MCPServerStatus.RUNNING:
                raise ValueError(f"MCP server '{server_name}' is not running")
            
            if config.transport in [MCPTransport.HTTP, MCPTransport.STREAMABLE_HTTP]:
                async with httpx.AsyncClient(timeout=config.timeout) as client:
                    response = await client.get(
                        f"{config.url}/resources",
                        params={"uri": resource_uri}
                    )
                    response.raise_for_status()
                    return response.json()
            
            else:
                raise ValueError(f"Resource access not implemented for transport: {config.transport}")
            
        except Exception as e:
            logger.error(f"Error getting resource '{resource_uri}' from MCP server '{server_name}': {str(e)}")
            raise
    
    def reload_configurations(self) -> bool:
        """Reload configurations from file"""
        try:
            # Stop all running servers
            for server_name, server_info in self.servers.items():
                if server_info.status == MCPServerStatus.RUNNING:
                    asyncio.create_task(self.stop_server(server_name))
            
            # Clear existing configurations
            self.servers = {}
            
            # Reload from file
            self._load_configurations()
            
            logger.info(f"Reloaded MCP server configurations. Found {len(self.servers)} servers.")
            return True
            
        except Exception as e:
            logger.error(f"Error reloading MCP server configurations: {str(e)}")
            return False
