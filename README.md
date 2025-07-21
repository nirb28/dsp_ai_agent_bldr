# Agent Platform

A comprehensive platform for creating, managing, and executing AI agents using LangGraph, FastAPI, and CopilotKit. This platform provides a flexible architecture for building intelligent agents with various capabilities, memory systems, and tool integrations.

## Features

### 🤖 Agent Management
- **Multiple Agent Types**: ReAct, Conversational, Tool-calling, Planning, and Custom agents
- **Flexible Configuration**: JSON-based agent configurations with environment variable support
- **Dynamic Loading**: Hot-reload agent configurations without restarting the service
- **Agent Metrics**: Track performance, success rates, and usage statistics

### 🛠️ Tool System
- **Built-in Tools**: Calculator, Web Search, File Reader, Code Executor, API Caller
- **Custom Tools**: Easy integration of custom tools and functions
- **Tool Management**: Enable/disable tools per agent, configure tool parameters
- **Direct Tool Execution**: Execute tools independently for testing and debugging

### 🧠 Memory Systems
- **Multiple Memory Types**: Buffer, Summary, Vector, and Entity-based memory
- **Persistent Storage**: Conversation history and context preservation
- **Memory Limits**: Configurable token limits and automatic cleanup
- **Memory Querying**: Search and retrieve specific memories

### 🚀 Execution Engine
- **LangGraph Integration**: Powered by LangGraph for complex agent workflows
- **Multiple LLM Providers**: Support for Groq, OpenAI, and OpenAI-compatible APIs
- **Streaming Support**: Real-time streaming responses
- **Async Execution**: Non-blocking agent execution with timeout handling

### 🔌 API & Integration
- **RESTful API**: Comprehensive REST API for all operations
- **CopilotKit Compatible**: Direct integration with CopilotKit applications
- **Legacy Support**: Backward compatibility with existing agent endpoints
- **OpenAPI Documentation**: Auto-generated API documentation

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd dsp_ai_agent_bldr

## Environment Variable Substitution in Configuration

You can reference environment variables in `agent_configurations.json` using the syntax `${ENV_VAR_NAME}`. At runtime, these will be replaced by the value from your `.env` file or system environment.

**Example:**
```json
"api_key": "${GROQ_API_KEY}"
```
This will use the value of `GROQ_API_KEY` from your environment.

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### 2. Configuration

Edit `.env` file with your API keys:

```env
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run the Platform

```bash
# Start the server
python main.py

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access the API

- **API Documentation**: http://localhost:3000/docs
- **Health Check**: http://localhost:3000/health
- **Agent List**: http://localhost:3000/api/v1/agents

## Agent Configuration

### Basic Agent Structure

```json
{
  "name": "my_agent",
  "description": "A helpful assistant",
  "agent_type": "react",
  "llm": {
    "model": "llama3-8b-8192",
    "provider": "groq",
    "temperature": 0.7,
    "max_tokens": 1024
  },
  "system_prompt": "You are a helpful AI assistant.",
  "tools": [
    {
      "name": "calculator",
      "type": "calculator",
      "description": "Perform calculations",
      "enabled": true
    }
  ],
  "memory": {
    "type": "buffer",
    "max_tokens": 2000
  }
}
```

### Agent Types

1. **ReAct**: Reasoning and Acting agents for complex problem-solving
2. **Conversational**: Simple chat-based agents
3. **Tool-calling**: Specialized for tool usage and API integration
4. **Planning**: Multi-step planning and execution
5. **Custom**: User-defined agent workflows

### Memory Types

1. **Buffer**: Simple conversation buffer with token limits
2. **Summary**: Summarized conversation history
3. **Vector**: Vector-based similarity search (future)
4. **Entity**: Entity-based memory tracking (future)

## API Usage

### Create an Agent

```bash
curl -X POST "http://localhost:3000/api/v1/agents" -H "Content-Type: application/json" -d '{
    "name": "calculator_bot1",
    "config": {
      "name": "calculator_bot1",
      "description": "A calculator agent",
      "agent_type": "react",
      "tools": [
        {
          "name": "calculator",
          "type": "calculator",
          "description": "Perform calculations",
          "enabled": true
        }
      ]
    }
  }'
```

### Execute an Agent

```bash
curl -X POST "http://localhost:3000/api/v1/agents/calculator_bot/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "calculator_bot",
    "messages": [
      {
        "role": "user",
        "content": "What is 15 * 23 + 47?"
      }
    ]
  }'
```

### CopilotKit Integration

```bash
curl -X POST "http://localhost:3000/api/v1/copilotkit/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Hello, can you help me with math?"
      }
    ],
    "agent": "calculator_bot"
  }'
```

## Example Agents

The platform includes several pre-configured example agents:

1. **Calculator Agent**: Mathematical problem solving
2. **Research Assistant**: Web search and file analysis
3. **API Integration Agent**: HTTP API interactions
4. **Conversational Assistant**: General chat and assistance
5. **Code Assistant**: Programming help and code execution

Run the examples:

```bash
python examples/example_agents.py
```

## Tool Development

### Creating Custom Tools

```python
from langchain.tools import tool
from app.services.tool_service import ToolService

@tool
def my_custom_tool(parameter: str) -> str:
    """Description of what the tool does."""
    # Tool implementation
    return f"Result: {parameter}"

# Register the tool
tool_service = ToolService()
tool_service.register_custom_tool("my_tool", my_custom_tool)
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Agent Service  │    │ Execution Svc   │
│                 │────│                 │────│                 │
│  • REST API     │    │ • Config Mgmt   │    │ • LangGraph     │
│  • CopilotKit   │    │ • Persistence   │    │ • LLM Providers │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Tool Service  │    │ Memory Service  │    │   Storage       │
│                 │    │                 │    │                 │
│ • Built-in      │    │ • Buffer        │    │ • JSON Files    │
│ • Custom        │    │ • Summary       │    │ • Persistence   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Configuration Management

The platform uses a similar configuration management approach to the DSP AI RAG system:

- **JSON-based storage**: Configurations stored in JSON files
- **Environment variables**: Support for `${VAR_NAME}` substitution
- **Hot reloading**: Configurations can be reloaded without restart
- **Validation**: Pydantic models ensure configuration validity

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Project Structure

```
dsp_ai_agent_bldr/
├── app/
│   ├── api/
│   │   └── endpoints.py      # API endpoints
│   ├── models/
│   │   ├── api_models.py     # API request/response models
│   │   └── agent_models.py   # Agent execution models
│   ├── services/
│   │   ├── agent_service.py  # Agent configuration management
│   │   ├── execution_service.py # Agent execution engine
│   │   ├── tool_service.py   # Tool management
│   │   └── memory_service.py # Memory management
│   └── config.py            # Configuration models
├── examples/
│   └── example_agents.py    # Example agent configurations
├── tests/                   # Test files
├── storage/                 # Data storage directory
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

