# MCP Integration Guide

This document explains how the Model Context Protocol (MCP) is integrated into the DSP AI Agent Builder project.

## Overview

The MCP integration allows agents to use external tools and services through a standardized protocol. This enables:

- **Modular tool architecture**: Tools can run as separate services
- **Scalability**: Tools can be distributed across different servers
- **Extensibility**: Easy to add new capabilities without changing agent code
- **Standardization**: Common interface for all external tools

## Architecture

```
Agent (LLM-powered)
    ↓
Agent Service
    ↓
MCP Service
    ↓
MCP Servers (Weather, Memory, Calculator, etc.)
    ↓
External APIs/Data Sources
```

## Components

### 1. MCP Service (`app/services/mcp_service.py`)
- Manages MCP server configurations
- Handles server lifecycle (start/stop)
- Provides tool calling interface
- Health monitoring and capability discovery

### 2. MCP Tools (`app/tools/mcp_tools.py`)
- LangChain-compatible tool wrappers
- Converts MCP calls to LangChain tool format
- Factory for creating tools from MCP servers

### 3. MCP Servers (`mcp_servers/`)
- **Weather Server** (`weather_server/`): Weather information and forecasts
- **Memory Server** (`memory_server/`): Persistent memory and knowledge storage
- **Calculator Server** (`calculator_server/`): Mathematical calculations and statistics

### 4. API Endpoints (`app/api/mcp_routes.py`)
- REST API for managing MCP servers
- Direct tool calling endpoints
- Server health and capability endpoints

## Configuration

### MCP Server Configuration (`storage/mcp_servers.json`)

```json
{
  "weather": {
    "name": "weather",
    "display_name": "Weather Server",
    "description": "Provides weather information",
    "transport": "http",
    "host": "localhost",
    "port": 8002,
    "enabled": true,
    "auto_start": false
  }
}
```

### Agent Configuration with MCP Tools

```json
{
  "name": "weather_agent",
  "tools": [
    {
      "name": "weather_get_weather",
      "type": "mcp",
      "description": "Get current weather information",
      "mcp_server": "weather",
      "mcp_tool_name": "get_weather"
    }
  ],
  "mcp_servers": ["weather"]
}
```

## Usage Examples

### 1. Starting MCP Servers

```bash
# Start all servers
python mcp_servers/start_all_servers.py

# Start individual servers
python mcp_servers/start_weather_server.py
python mcp_servers/start_memory_server.py
python mcp_servers/start_calculator_server.py
```

### 2. Using MCP Tools via API

```bash
# List MCP servers
curl http://localhost:3000/api/v1/mcp/servers

# Call a tool directly
curl -X POST http://localhost:3000/api/v1/mcp/servers/weather/tools/get_weather/call \
  -H "Content-Type: application/json" \
  -d '{"city": "New York"}'

# Use agent with MCP tools
curl -X POST http://localhost:3000/api/v1/agents/weather_agent/execute \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What is the weather in Paris?"}]}'
```

### 3. Programmatic Usage

```python
from app.services.agent_service import AgentService

# Initialize services
agent_service = AgentService()
mcp_service = agent_service.get_mcp_service()

# Start a server
await mcp_service.start_server("weather")

# Call a tool
result = await mcp_service.call_tool("weather", "get_weather", {"city": "London"})
print(result)

# Use with agent
config = agent_service.get_configuration("weather_agent")
# ... execute agent with MCP tools
```

## Available MCP Servers

### Weather Server (Port 8002)

**Tools:**
- `get_weather(city)`: Get current weather for a city
- `get_forecast(city, days)`: Get weather forecast

**Resources:**
- `weather://cities`: List of available cities

**Example:**
```python
result = await mcp_service.call_tool("weather", "get_weather", {"city": "Tokyo"})
# Returns: "Tokyo: sunny, 25°C, humidity 60%"
```

### Memory Server (Port 8003)

**Tools:**
- `store_memory(key, content, category)`: Store a memory
- `retrieve_memory(key)`: Retrieve a memory by key
- `search_memories(query, category, limit)`: Search memories
- `list_memories(category)`: List all memories
- `delete_memory(key)`: Delete a memory

**Resources:**
- `memory://stats`: Memory statistics
- `memory://categories`: List of categories

**Example:**
```python
# Store a memory
await mcp_service.call_tool("memory", "store_memory", {
    "key": "user_preference",
    "content": "User prefers metric units",
    "category": "preferences"
})

# Search memories
result = await mcp_service.call_tool("memory", "search_memories", {
    "query": "metric",
    "limit": 5
})
```

### Calculator Server (Port 8004)

**Tools:**
- `calculate(expression)`: Basic mathematical calculations
- `advanced_math(operation, value, base)`: Advanced math functions
- `statistics(numbers, measures)`: Statistical calculations
- `unit_conversion(value, from_unit, to_unit, category)`: Unit conversions

**Resources:**
- `calculator://constants`: Mathematical constants
- `calculator://functions`: Available functions

**Example:**
```python
# Basic calculation
result = await mcp_service.call_tool("calculator", "calculate", {
    "expression": "2 + 3 * 4"
})

# Advanced math
result = await mcp_service.call_tool("calculator", "advanced_math", {
    "operation": "sqrt",
    "value": 16
})

# Statistics
result = await mcp_service.call_tool("calculator", "statistics", {
    "numbers": [1, 2, 3, 4, 5],
    "measures": ["mean", "std"]
})
```

## Creating Custom MCP Servers

### 1. Basic Server Structure

```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="My MCP Server")

class ToolRequest(BaseModel):
    arguments: Dict[str, Any]

class ToolResponse(BaseModel):
    content: str
    success: bool = True

@app.get("/health")
async def health_check():
    return {"status": "healthy", "server": "my-mcp-server"}

@app.get("/tools")
async def get_tools():
    return {
        "tools": [
            {
                "name": "my_tool",
                "description": "My custom tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string", "description": "Input parameter"}
                    },
                    "required": ["input"]
                }
            }
        ]
    }

@app.post("/tools/my_tool")
async def my_tool(request: ToolRequest) -> ToolResponse:
    input_value = request.arguments.get("input")
    result = f"Processed: {input_value}"
    return ToolResponse(content=result)
```

### 2. Register the Server

Add to `storage/mcp_servers.json`:

```json
{
  "my_server": {
    "name": "my_server",
    "display_name": "My Custom Server",
    "description": "My custom MCP server",
    "transport": "http",
    "host": "localhost",
    "port": 8005,
    "enabled": true
  }
}
```

### 3. Use in Agent Configuration

```json
{
  "tools": [
    {
      "name": "my_custom_tool",
      "type": "mcp",
      "description": "My custom tool",
      "mcp_server": "my_server",
      "mcp_tool_name": "my_tool"
    }
  ],
  "mcp_servers": ["my_server"]
}
```

## API Reference

### MCP Management Endpoints

- `GET /api/v1/mcp/servers` - List all MCP servers
- `GET /api/v1/mcp/servers/{name}` - Get server details
- `POST /api/v1/mcp/servers` - Add/update server configuration
- `DELETE /api/v1/mcp/servers/{name}` - Delete server
- `POST /api/v1/mcp/servers/{name}/start` - Start server
- `POST /api/v1/mcp/servers/{name}/stop` - Stop server
- `GET /api/v1/mcp/servers/{name}/health` - Health check
- `POST /api/v1/mcp/servers/{name}/discover` - Discover capabilities

### Tool Calling Endpoints

- `POST /api/v1/mcp/servers/{server}/tools/{tool}/call` - Call a tool
- `GET /api/v1/mcp/servers/{server}/resources/{uri}` - Get a resource

## Troubleshooting

### Common Issues

1. **Server not starting**
   - Check if port is available
   - Verify server configuration
   - Check logs for error messages

2. **Tool calls failing**
   - Ensure server is running and healthy
   - Verify tool name and parameters
   - Check server logs

3. **Agent not using MCP tools**
   - Verify agent configuration includes MCP tools
   - Check if MCP servers are listed in agent config
   - Ensure tools are enabled

### Debugging

```python
# Check server status
servers = mcp_service.get_servers()
for name, info in servers.items():
    print(f"{name}: {info['status']}")

# Health check
is_healthy = await mcp_service.health_check("weather")
print(f"Weather server healthy: {is_healthy}")

# Discover capabilities
await mcp_service.discover_capabilities("weather")
server_info = mcp_service.get_server("weather")
print(f"Available tools: {server_info.available_tools}")
```

## RAG Integration

The RAG MCP server provides seamless integration with your existing RAG service for document retrieval and question answering.

### Prerequisites

1. **RAG Service**: Your RAG service must be running on `localhost:9000`
2. **Document Indexing**: Have documents indexed in your RAG configurations
3. **Environment Variables**: Set `RAG_SERVICE_URL` if using a different URL

### Starting the RAG MCP Server

```bash
# Start RAG MCP server individually
python mcp_servers/start_rag_server.py

# Or start all servers including RAG
python mcp_servers/start_all_servers.py
```

### Using RAG Tools in Agents

```python
# Example agent configuration with RAG tools
{
  "name": "research_agent",
  "mcp_servers": ["rag"],
  "tools": [
    {
      "name": "retrieve_documents",
      "type": "mcp",
      "config": {
        "server_name": "rag",
        "tool_name": "retrieve_documents"
      }
    },
    {
      "name": "query_with_generation",
      "type": "mcp",
      "config": {
        "server_name": "rag",
        "tool_name": "query_with_generation"
      }
    }
  ]
}
```

### RAG Tool Examples

```python
# Retrieve documents
result = await agent.invoke({
    "input": "Find documents about machine learning algorithms"
})

# Multi-configuration retrieval with fusion
result = await mcp_service.call_tool(
    "rag", 
    "retrieve_multi_config", 
    {
        "query": "artificial intelligence",
        "configuration_names": ["research_papers", "knowledge_base"],
        "fusion_method": "rrf",
        "k": 5
    }
)

# Generate comprehensive answers
result = await mcp_service.call_tool(
    "rag", 
    "query_with_generation", 
    {
        "query": "What are the latest developments in AI?",
        "configuration_name": "default",
        "k": 3
    }
)
```

### Testing RAG Integration

```bash
# Run the RAG MCP example
python examples/rag_mcp_example.py
```

This example will:
- Check RAG service and MCP server health
- Test document retrieval tools
- Demonstrate multi-configuration fusion
- Show agent integration patterns

## Best Practices

1. **Server Design**
   - Keep tools focused and atomic
   - Provide clear descriptions and parameter schemas
   - Handle errors gracefully
   - Include health check endpoints

2. **Configuration**
   - Use descriptive names and descriptions
   - Set appropriate timeouts
   - Configure proper error handling
   - Document tool parameters

3. **Security**
   - Validate all inputs
   - Use proper authentication if needed
   - Limit resource access
   - Monitor server health

4. **Performance**
   - Cache results when appropriate
   - Set reasonable timeouts
   - Monitor resource usage
   - Use async operations

## Example Workflow

1. **Development**: Create MCP server with tools
2. **Configuration**: Add server to `mcp_servers.json`
3. **Integration**: Create agent configuration with MCP tools
4. **Testing**: Use example script or API endpoints
5. **Deployment**: Start servers and main application
6. **Monitoring**: Check health and performance

This integration provides a powerful foundation for extending your agents with external capabilities while maintaining clean separation of concerns and scalability.
