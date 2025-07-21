#!/usr/bin/env python3
"""
Example script demonstrating MCP server integration with the DSP AI Agent Builder.

This script shows how to:
1. Start MCP servers
2. Configure agents to use MCP tools
3. Execute agents with MCP capabilities
4. Manage MCP server lifecycle
"""

import asyncio
import json
import time
from pathlib import Path
import sys

# Add the parent directory to the path so we can import from app
sys.path.append(str(Path(__file__).parent.parent))

from app.services.agent_service import AgentService
from app.services.mcp_service import MCPService
from app.config import AgentConfig, MCPServerConfig, MCPTransport

async def main():
    """Main example function"""
    print("🚀 MCP Integration Example for DSP AI Agent Builder")
    print("=" * 60)
    
    # Initialize services
    agent_service = AgentService()
    mcp_service = agent_service.get_mcp_service()
    
    print("\n📋 Step 1: Check available MCP servers")
    servers = mcp_service.get_servers()
    print(f"Found {len(servers)} configured MCP servers:")
    for name, info in servers.items():
        print(f"  - {name}: {info['config']['display_name']} ({info['status']})")
    
    print("\n🔧 Step 2: Start MCP servers")
    server_names = ["weather", "memory", "calculator"]
    
    for server_name in server_names:
        print(f"Starting {server_name} server...")
        try:
            success = await mcp_service.start_server(server_name)
            if success:
                print(f"  ✅ {server_name} server started successfully")
            else:
                print(f"  ❌ Failed to start {server_name} server")
        except Exception as e:
            print(f"  ❌ Error starting {server_name}: {e}")
    
    # Wait a moment for servers to fully start
    print("\n⏳ Waiting for servers to initialize...")
    await asyncio.sleep(3)
    
    print("\n🔍 Step 3: Discover server capabilities")
    for server_name in server_names:
        try:
            await mcp_service.discover_capabilities(server_name)
            server_info = mcp_service.get_server(server_name)
            if server_info:
                print(f"\n{server_name.title()} Server Capabilities:")
                print(f"  Tools: {len(server_info.available_tools)}")
                for tool in server_info.available_tools:
                    print(f"    - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
                print(f"  Resources: {len(server_info.available_resources)}")
                for resource in server_info.available_resources:
                    print(f"    - {resource.get('name', 'Unknown')}: {resource.get('description', 'No description')}")
        except Exception as e:
            print(f"  ❌ Error discovering capabilities for {server_name}: {e}")
    
    print("\n🧪 Step 4: Test MCP tools directly")
    
    # Test weather tool
    print("\n🌤️  Testing Weather Tool:")
    try:
        result = await mcp_service.call_tool("weather", "get_weather", {"city": "New York"})
        print(f"  Weather result: {result.get('content', result)}")
    except Exception as e:
        print(f"  ❌ Weather tool error: {e}")
    
    # Test calculator tool
    print("\n🧮 Testing Calculator Tool:")
    try:
        result = await mcp_service.call_tool("calculator", "calculate", {"expression": "2 + 3 * 4"})
        print(f"  Calculator result: {result.get('content', result)}")
    except Exception as e:
        print(f"  ❌ Calculator tool error: {e}")
    
    # Test memory tool
    print("\n🧠 Testing Memory Tool:")
    try:
        # Store a memory
        store_result = await mcp_service.call_tool("memory", "store_memory", {
            "key": "example_memory",
            "content": "This is a test memory from the MCP example script",
            "category": "examples"
        })
        print(f"  Memory store result: {store_result.get('content', store_result)}")
        
        # Retrieve the memory
        retrieve_result = await mcp_service.call_tool("memory", "retrieve_memory", {
            "key": "example_memory"
        })
        print(f"  Memory retrieve result: {retrieve_result.get('content', retrieve_result)}")
    except Exception as e:
        print(f"  ❌ Memory tool error: {e}")
    
    print("\n🤖 Step 5: Load and test MCP-enabled agents")
    
    # Load MCP agent configurations
    mcp_config_file = Path(__file__).parent.parent / "storage" / "agent_configurations_mcp.json"
    if mcp_config_file.exists():
        print(f"Loading MCP agent configurations from {mcp_config_file}")
        
        with open(mcp_config_file, 'r') as f:
            mcp_configs = json.load(f)
        
        # Add a weather agent configuration
        if "weather_agent" in mcp_configs:
            config_data = mcp_configs["weather_agent"]
            try:
                weather_config = AgentConfig(**config_data)
                agent_service.add_configuration("weather_agent", weather_config)
                print("  ✅ Weather agent configuration loaded")
            except Exception as e:
                print(f"  ❌ Error loading weather agent: {e}")
        
        # Add a calculator agent configuration  
        if "calculator_agent" in mcp_configs:
            config_data = mcp_configs["calculator_agent"]
            try:
                calc_config = AgentConfig(**config_data)
                agent_service.add_configuration("calculator_agent", calc_config)
                print("  ✅ Calculator agent configuration loaded")
            except Exception as e:
                print(f"  ❌ Error loading calculator agent: {e}")
    
    print("\n📊 Step 6: Server health check")
    for server_name in server_names:
        try:
            is_healthy = await mcp_service.health_check(server_name)
            status = "✅ Healthy" if is_healthy else "❌ Unhealthy"
            print(f"  {server_name}: {status}")
        except Exception as e:
            print(f"  {server_name}: ❌ Error - {e}")
    
    print("\n🎯 Step 7: Example usage scenarios")
    print("\nYou can now use the MCP-enabled agents in several ways:")
    print("\n1. Via API endpoints:")
    print("   POST /api/v1/agents/weather_agent/execute")
    print("   Body: {\"messages\": [{\"role\": \"user\", \"content\": \"What's the weather in Paris?\"}]}")
    
    print("\n2. Via MCP API endpoints:")
    print("   GET /api/v1/mcp/servers - List all MCP servers")
    print("   POST /api/v1/mcp/servers/weather/tools/get_weather/call")
    print("   Body: {\"city\": \"London\"}")
    
    print("\n3. Direct tool calls:")
    print("   Use the mcp_service.call_tool() method as shown above")
    
    print("\n📝 Step 8: Available agent configurations")
    agent_names = agent_service.get_configuration_names()
    print(f"Available agents: {', '.join(agent_names)}")
    
    print("\n✨ MCP Integration Example Complete!")
    print("\nNext steps:")
    print("1. Start the main application: python main.py")
    print("2. Visit http://localhost:3000/docs for API documentation")
    print("3. Test the MCP-enabled agents via the API")
    print("4. Create your own MCP servers and integrate them")
    
    print("\n🛑 Stopping MCP servers...")
    for server_name in server_names:
        try:
            await mcp_service.stop_server(server_name)
            print(f"  ✅ Stopped {server_name}")
        except Exception as e:
            print(f"  ❌ Error stopping {server_name}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
