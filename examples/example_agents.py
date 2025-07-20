"""
Example agent configurations for the Agent as a Service Platform
"""

import os
import sys
# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import AgentConfig, LLMConfig, ToolConfig, MemoryConfig, AgentType, ToolType, MemoryType, LLMProvider

# Example 1: Simple Calculator Agent
calculator_agent = AgentConfig(
    name="calculator_agent",
    description="A specialized agent for mathematical calculations and problem solving",
    agent_type=AgentType.REACT,
    llm=LLMConfig(
        model="llama3-8b-8192",
        provider=LLMProvider.GROQ,
        temperature=0.1,  # Low temperature for precise calculations
        max_tokens=1024
    ),
    system_prompt="""You are a mathematical assistant specialized in solving calculations and math problems. 
    Always use the calculator tool for any mathematical operations. Provide step-by-step explanations for complex problems.""",
    tools=[
        ToolConfig(
            name="calculator",
            type=ToolType.CALCULATOR,
            description="Perform mathematical calculations",
            enabled=True
        )
    ],
    memory=MemoryConfig(type=MemoryType.BUFFER, max_tokens=1000)
)

# Example 2: Research Assistant Agent
research_agent = AgentConfig(
    name="research_assistant",
    description="An agent that can search the web and read files for research tasks",
    agent_type=AgentType.REACT,
    llm=LLMConfig(
        model="llama3-70b-8192",
        provider=LLMProvider.GROQ,
        temperature=0.7,
        max_tokens=2048
    ),
    system_prompt="""You are a research assistant that helps users find and analyze information. 
    Use web search to find current information and file reading capabilities to analyze documents. 
    Always cite your sources and provide comprehensive, well-structured responses.""",
    tools=[
        ToolConfig(
            name="web_search",
            type=ToolType.WEB_SEARCH,
            description="Search the web for information",
            enabled=True,
            config={"max_results": 5}
        ),
        ToolConfig(
            name="file_reader",
            type=ToolType.FILE_READER,
            description="Read and analyze text files",
            enabled=True
        ),
        ToolConfig(
            name="calculator",
            type=ToolType.CALCULATOR,
            description="Perform calculations if needed",
            enabled=True
        )
    ],
    memory=MemoryConfig(type=MemoryType.SUMMARY, max_tokens=3000)
)

# Example 3: API Integration Agent
api_agent = AgentConfig(
    name="api_integration_agent",
    description="An agent specialized in making API calls and integrating with external services",
    agent_type=AgentType.TOOL_CALLING,
    llm=LLMConfig(
        model="gpt-4",
        provider=LLMProvider.OPENAI,
        temperature=0.3,
        max_tokens=1500
    ),
    system_prompt="""You are an API integration specialist. You can make HTTP requests to various APIs 
    and help users integrate with external services. Always validate API responses and handle errors gracefully. 
    Provide clear explanations of API interactions and results.""",
    tools=[
        ToolConfig(
            name="api_caller",
            type=ToolType.API_CALLER,
            description="Make HTTP API calls",
            enabled=True,
            config={"timeout": 30, "max_retries": 3}
        ),
        ToolConfig(
            name="calculator",
            type=ToolType.CALCULATOR,
            description="Calculate values for API parameters",
            enabled=True
        )
    ],
    memory=MemoryConfig(type=MemoryType.BUFFER, max_tokens=2000)
)

# Example 4: Conversational Assistant
conversational_agent = AgentConfig(
    name="conversational_assistant",
    description="A friendly conversational agent for general assistance and chat",
    agent_type=AgentType.CONVERSATIONAL,
    llm=LLMConfig(
        model="mixtral-8x7b-32768",
        provider=LLMProvider.GROQ,
        temperature=0.8,
        max_tokens=1024
    ),
    system_prompt="""You are a helpful and friendly AI assistant. You can engage in natural conversation 
    and help with a variety of tasks. Be personable, empathetic, and provide helpful responses. 
    Use tools when necessary to provide accurate information.""",
    tools=[
        ToolConfig(
            name="calculator",
            type=ToolType.CALCULATOR,
            description="Help with calculations",
            enabled=True
        ),
        ToolConfig(
            name="web_search",
            type=ToolType.WEB_SEARCH,
            description="Search for current information",
            enabled=False  # Disabled by default for simple conversation
        )
    ],
    memory=MemoryConfig(type=MemoryType.BUFFER, max_tokens=2500)
)

# Example 5: Code Assistant Agent
code_agent = AgentConfig(
    name="code_assistant",
    description="An agent specialized in code analysis, execution, and programming help",
    agent_type=AgentType.PLANNING,
    llm=LLMConfig(
        model="llama3-70b-8192",
        provider=LLMProvider.GROQ,
        temperature=0.2,
        max_tokens=3000
    ),
    system_prompt="""You are a programming assistant that can help with code analysis, debugging, 
    and execution. You can read code files, execute code safely, and provide programming guidance. 
    Always explain your code suggestions and follow best practices.""",
    tools=[
        ToolConfig(
            name="code_executor",
            type=ToolType.CODE_EXECUTOR,
            description="Execute code safely",
            enabled=True,
            config={"allowed_languages": ["python", "javascript"], "timeout": 10}
        ),
        ToolConfig(
            name="file_reader",
            type=ToolType.FILE_READER,
            description="Read code files",
            enabled=True
        ),
        ToolConfig(
            name="calculator",
            type=ToolType.CALCULATOR,
            description="Calculate algorithmic complexity or numerical results",
            enabled=True
        )
    ],
    memory=MemoryConfig(type=MemoryType.VECTOR, max_tokens=4000)
)

# Dictionary of all example agents
EXAMPLE_AGENTS = {
    "calculator_agent": calculator_agent,
    "research_assistant": research_agent,
    "api_integration_agent": api_agent,
    "conversational_assistant": conversational_agent,
    "code_assistant": code_agent
}

def create_example_agents():
    """Create example agents in the system"""
    from app.services.agent_service import AgentService
    
    agent_service = AgentService()
    
    for agent_name, agent_config in EXAMPLE_AGENTS.items():
        success = agent_service.add_configuration(agent_name, agent_config)
        if success:
            print(f"Created example agent: {agent_name}")
        else:
            print(f"Failed to create example agent: {agent_name}")

if __name__ == "__main__":
    create_example_agents()
