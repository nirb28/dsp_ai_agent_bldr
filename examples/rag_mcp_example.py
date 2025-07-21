#!/usr/bin/env python3
"""
RAG MCP Integration Example

This example demonstrates how to use the RAG MCP server for document retrieval
and question answering within the DSP AI Agent Builder framework.

Prerequisites:
1. RAG service running on localhost:9000
2. RAG MCP server running on localhost:8005
3. Some documents indexed in the RAG service

Usage:
    python examples/rag_mcp_example.py
"""

import asyncio
import json
import logging
import os
import sys
import httpx
from typing import Dict, Any

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app.services.agent_service import AgentService
from app.services.mcp_service import MCPService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_rag_service_health():
    """Check if the RAG service is running and healthy"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:9000/api/v1/health")
            if response.status_code == 200:
                logger.info("✅ RAG service is healthy")
                return True
            else:
                logger.error(f"❌ RAG service returned status {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ RAG service is not accessible: {e}")
        return False

async def check_rag_mcp_server():
    """Check if the RAG MCP server is running"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8005/health")
            if response.status_code == 200:
                health_data = response.json()
                logger.info("✅ RAG MCP server is healthy")
                logger.info(f"   RAG service connection: {'✅' if health_data.get('rag_service_healthy') else '❌'}")
                return True
            else:
                logger.error(f"❌ RAG MCP server returned status {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ RAG MCP server is not accessible: {e}")
        return False

async def test_rag_mcp_tools():
    """Test RAG MCP tools directly"""
    logger.info("\n🔧 Testing RAG MCP Tools")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test list configurations
            logger.info("Testing list_configurations...")
            response = await client.post(
                "http://localhost:8005/tools/list_configurations",
                json={"arguments": {"names_only": True}}
            )
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Configurations: {result['content']}")
            else:
                logger.error(f"❌ List configurations failed: {response.status_code}")
                return False
            
            # Test document retrieval
            logger.info("Testing retrieve_documents...")
            response = await client.post(
                "http://localhost:8005/tools/retrieve_documents",
                json={
                    "arguments": {
                        "query": "What is artificial intelligence?",
                        "configuration_name": "default",
                        "k": 3
                    }
                }
            )
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ Document retrieval successful")
                logger.info(f"   Result preview: {result['content'][:200]}...")
            else:
                logger.error(f"❌ Document retrieval failed: {response.status_code}")
                logger.error(f"   Error: {response.text}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error testing RAG MCP tools: {e}")
        return False

async def test_rag_agent():
    """Test the RAG agent with MCP tools"""
    logger.info("\n🤖 Testing RAG Agent")
    
    try:
        # Initialize services
        agent_service = AgentService()
        mcp_service = MCPService()
        
        # Load RAG agent configuration
        rag_config_path = os.path.join(project_root, "storage", "rag_agent_config.json")
        if not os.path.exists(rag_config_path):
            logger.error(f"❌ RAG agent config not found: {rag_config_path}")
            return False
        
        with open(rag_config_path, 'r') as f:
            rag_config = json.load(f)
        
        # Add RAG server to MCP service
        await mcp_service.add_server({
            "name": "rag",
            "description": "RAG retrieval server",
            "transport": "http",
            "url": "http://localhost:8005",
            "enabled": True,
            "timeout": 30
        })
        
        # Start RAG MCP server
        await mcp_service.start_server("rag")
        
        # Create agent with RAG configuration
        agent_config = rag_config["rag_agent"]
        agent = await agent_service.create_agent_from_config(agent_config, mcp_service)
        
        # Test queries
        test_queries = [
            "List available RAG configurations",
            "What documents are available about artificial intelligence?",
            "Search for information about machine learning"
        ]
        
        for query in test_queries:
            logger.info(f"\n📝 Query: {query}")
            try:
                response = await agent.ainvoke({"input": query})
                logger.info(f"✅ Response: {response.get('output', 'No output')[:300]}...")
            except Exception as e:
                logger.error(f"❌ Query failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing RAG agent: {e}")
        return False

async def demonstrate_multi_config_retrieval():
    """Demonstrate multi-configuration retrieval with fusion"""
    logger.info("\n🔀 Testing Multi-Configuration Retrieval")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First, list available configurations
            response = await client.post(
                "http://localhost:8005/tools/list_configurations",
                json={"arguments": {"names_only": True}}
            )
            
            if response.status_code != 200:
                logger.error("❌ Could not list configurations")
                return False
            
            # For demo, assume we have at least one config
            response = await client.post(
                "http://localhost:8005/tools/retrieve_multi_config",
                json={
                    "arguments": {
                        "query": "machine learning algorithms",
                        "configuration_names": ["default"],  # Use available configs
                        "k": 3,
                        "fusion_method": "rrf"
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ Multi-config retrieval successful")
                logger.info(f"   Result: {result['content'][:300]}...")
            else:
                logger.error(f"❌ Multi-config retrieval failed: {response.status_code}")
                logger.error(f"   Error: {response.text}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in multi-config retrieval: {e}")
        return False

async def main():
    """Main example function"""
    print("=" * 60)
    print("RAG MCP Integration Example")
    print("=" * 60)
    
    # Check prerequisites
    logger.info("🔍 Checking prerequisites...")
    
    rag_healthy = await check_rag_service_health()
    mcp_healthy = await check_rag_mcp_server()
    
    if not rag_healthy:
        logger.error("❌ RAG service is not running. Please start it first:")
        logger.error("   cd path/to/rag/project && python app/main.py")
        return
    
    if not mcp_healthy:
        logger.error("❌ RAG MCP server is not running. Please start it first:")
        logger.error("   python mcp_servers/start_rag_server.py")
        return
    
    # Test MCP tools directly
    tools_ok = await test_rag_mcp_tools()
    if not tools_ok:
        logger.error("❌ MCP tools testing failed")
        return
    
    # Test multi-config retrieval
    await demonstrate_multi_config_retrieval()
    
    # Test RAG agent (optional, requires proper setup)
    logger.info("\n⚠️  RAG agent testing requires proper environment setup")
    logger.info("   Make sure NVIDIA_* environment variables are set")
    
    # Uncomment to test RAG agent
    # await test_rag_agent()
    
    print("\n" + "=" * 60)
    print("RAG MCP Integration Example Complete!")
    print("=" * 60)
    
    print("\n📚 Next Steps:")
    print("1. Index some documents in your RAG service")
    print("2. Set up environment variables for LLM access")
    print("3. Use the RAG agent in your applications")
    print("4. Explore multi-configuration retrieval for complex queries")

if __name__ == "__main__":
    asyncio.run(main())
