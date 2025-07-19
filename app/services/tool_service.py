import logging
import time
import json
import httpx
from typing import Dict, List, Any, Optional, Callable
from langchain.tools import tool

from app.config import AgentConfig, ToolType

logger = logging.getLogger(__name__)

class ToolService:
    """Service for managing and executing agent tools"""
    
    def __init__(self):
        self.custom_tools: Dict[str, Callable] = {}
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """Register built-in tools"""
        
        @tool
        def calculator(expression: str) -> str:
            """Evaluates a mathematical expression safely."""
            try:
                # Safe evaluation with limited builtins
                allowed_names = {
                    k: v for k, v in __builtins__.items()
                    if k in ['abs', 'round', 'min', 'max', 'sum', 'pow']
                }
                allowed_names.update({
                    'pi': 3.14159265359,
                    'e': 2.71828182846
                })
                
                result = eval(expression, {"__builtins__": {}}, allowed_names)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        @tool
        def web_search(query: str, num_results: int = 5) -> str:
            """Search the web for information (placeholder implementation)."""
            # This is a placeholder - in a real implementation, you'd integrate with a search API
            return f"Search results for '{query}': [This is a placeholder. Integrate with actual search API]"
        
        @tool
        def file_reader(file_path: str) -> str:
            """Read the contents of a text file."""
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content[:2000]  # Limit content length
            except Exception as e:
                return f"Error reading file: {str(e)}"
        
        @tool
        def code_executor(code: str, language: str = "python") -> str:
            """Execute code safely (placeholder implementation)."""
            # This is a placeholder - in a real implementation, you'd use a sandboxed environment
            return f"Code execution not implemented yet. Code: {code[:100]}..."
        
        @tool
        def api_caller(url: str, method: str = "GET", headers: Optional[Dict] = None, data: Optional[Dict] = None) -> str:
            """Make HTTP API calls."""
            try:
                with httpx.Client(timeout=10.0) as client:
                    if method.upper() == "GET":
                        response = client.get(url, headers=headers or {})
                    elif method.upper() == "POST":
                        response = client.post(url, headers=headers or {}, json=data)
                    elif method.upper() == "PUT":
                        response = client.put(url, headers=headers or {}, json=data)
                    elif method.upper() == "DELETE":
                        response = client.delete(url, headers=headers or {})
                    else:
                        return f"Unsupported HTTP method: {method}"
                    
                    return f"Status: {response.status_code}\nResponse: {response.text[:1000]}"
            except Exception as e:
                return f"API call failed: {str(e)}"
        
        # Register tools
        self.builtin_tools = {
            "calculator": calculator,
            "web_search": web_search,
            "file_reader": file_reader,
            "code_executor": code_executor,
            "api_caller": api_caller
        }
    
    def get_tools_for_agent(self, agent_name: str) -> List[Callable]:
        """Get all enabled tools for an agent"""
        from app.services.agent_service import AgentService
        
        # This would normally be injected, but for simplicity we'll create an instance
        # In a real application, you'd use dependency injection
        agent_service = AgentService()
        config = agent_service.get_configuration(agent_name)
        
        if not config:
            return []
        
        tools = []
        for tool_config in config.tools:
            if not tool_config.enabled:
                continue
                
            tool_func = self._get_tool_function(tool_config)
            if tool_func:
                tools.append(tool_func)
        
        return tools
    
    def _get_tool_function(self, tool_config) -> Optional[Callable]:
        """Get the function for a tool configuration"""
        tool_name = tool_config.name
        tool_type = tool_config.type
        
        # Check built-in tools first
        if tool_type == ToolType.CALCULATOR and "calculator" in self.builtin_tools:
            return self.builtin_tools["calculator"]
        elif tool_type == ToolType.WEB_SEARCH and "web_search" in self.builtin_tools:
            return self.builtin_tools["web_search"]
        elif tool_type == ToolType.FILE_READER and "file_reader" in self.builtin_tools:
            return self.builtin_tools["file_reader"]
        elif tool_type == ToolType.CODE_EXECUTOR and "code_executor" in self.builtin_tools:
            return self.builtin_tools["code_executor"]
        elif tool_type == ToolType.API_CALLER and "api_caller" in self.builtin_tools:
            return self.builtin_tools["api_caller"]
        elif tool_type == ToolType.CUSTOM and tool_name in self.custom_tools:
            return self.custom_tools[tool_name]
        
        logger.warning(f"Tool not found: {tool_name} (type: {tool_type})")
        return None
    
    def register_custom_tool(self, name: str, func: Callable):
        """Register a custom tool function"""
        self.custom_tools[name] = func
        logger.info(f"Registered custom tool: {name}")
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any], agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Execute a tool directly"""
        start_time = time.time()
        
        try:
            # Find the tool
            tool_func = None
            
            # Check built-in tools
            if tool_name in self.builtin_tools:
                tool_func = self.builtin_tools[tool_name]
            elif tool_name in self.custom_tools:
                tool_func = self.custom_tools[tool_name]
            
            if not tool_func:
                return {
                    "result": None,
                    "tool_name": tool_name,
                    "execution_time": time.time() - start_time,
                    "success": False,
                    "error": f"Tool '{tool_name}' not found"
                }
            
            # Execute the tool
            if hasattr(tool_func, 'func'):
                # This is a LangChain tool, call the underlying function
                result = tool_func.func(**parameters)
            else:
                # Direct function call
                result = tool_func(**parameters)
            
            return {
                "result": result,
                "tool_name": tool_name,
                "execution_time": time.time() - start_time,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            return {
                "result": None,
                "tool_name": tool_name,
                "execution_time": time.time() - start_time,
                "success": False,
                "error": str(e)
            }
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available tools"""
        tools_info = {}
        
        # Built-in tools
        for name, func in self.builtin_tools.items():
            tools_info[name] = {
                "name": name,
                "type": "builtin",
                "description": func.__doc__ or "No description available",
                "parameters": self._extract_parameters(func)
            }
        
        # Custom tools
        for name, func in self.custom_tools.items():
            tools_info[name] = {
                "name": name,
                "type": "custom",
                "description": func.__doc__ or "No description available",
                "parameters": self._extract_parameters(func)
            }
        
        return tools_info
    
    def _extract_parameters(self, func: Callable) -> List[Dict[str, Any]]:
        """Extract parameter information from a function"""
        import inspect
        
        try:
            sig = inspect.signature(func)
            parameters = []
            
            for param_name, param in sig.parameters.items():
                param_info = {
                    "name": param_name,
                    "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                    "required": param.default == inspect.Parameter.empty,
                    "default": param.default if param.default != inspect.Parameter.empty else None
                }
                parameters.append(param_info)
            
            return parameters
            
        except Exception as e:
            logger.warning(f"Could not extract parameters for function: {str(e)}")
            return []
