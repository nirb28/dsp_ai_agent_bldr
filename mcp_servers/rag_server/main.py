import os
import httpx
import logging
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Retrieval MCP Server", version="1.0.0")

class ToolRequest(BaseModel):
    arguments: Dict[str, Any]

class ToolResponse(BaseModel):
    content: str
    success: bool = True

# RAG service configuration
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:9000")
RAG_API_BASE = f"{RAG_SERVICE_URL}/api/v1"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if RAG service is available
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{RAG_API_BASE}/health")
            rag_healthy = response.status_code == 200
    except Exception:
        rag_healthy = False
    
    return {
        "status": "healthy",
        "server": "rag-mcp",
        "rag_service_healthy": rag_healthy,
        "rag_service_url": RAG_SERVICE_URL
    }

@app.get("/tools")
async def get_tools():
    """Get available tools"""
    return {
        "tools": [
            {
                "name": "retrieve_documents",
                "description": "Retrieve relevant documents from RAG configurations based on a query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant documents"
                        },
                        "configuration_name": {
                            "type": "string",
                            "description": "Name of the RAG configuration to search in",
                            "default": "default"
                        },
                        "k": {
                            "type": "integer",
                            "description": "Number of documents to retrieve (1-50)",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 50
                        },
                        "similarity_threshold": {
                            "type": "number",
                            "description": "Minimum similarity threshold (0.0-1.0)",
                            "default": 0.0,
                            "minimum": 0.0,
                            "maximum": 1.0
                        },
                        "use_reranking": {
                            "type": "boolean",
                            "description": "Whether to use reranking for better results",
                            "default": false
                        },
                        "include_metadata": {
                            "type": "boolean",
                            "description": "Whether to include document metadata",
                            "default": true
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "retrieve_multi_config",
                "description": "Retrieve documents from multiple RAG configurations with fusion",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant documents"
                        },
                        "configuration_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of RAG configuration names to search in"
                        },
                        "k": {
                            "type": "integer",
                            "description": "Number of documents to retrieve per configuration",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 50
                        },
                        "fusion_method": {
                            "type": "string",
                            "description": "Method for fusing results from multiple configurations",
                            "enum": ["rrf", "simple"],
                            "default": "rrf"
                        },
                        "rrf_k_constant": {
                            "type": "integer",
                            "description": "Constant for RRF calculation",
                            "default": 60,
                            "minimum": 1
                        },
                        "use_reranking": {
                            "type": "boolean",
                            "description": "Whether to use reranking for better results",
                            "default": false
                        }
                    },
                    "required": ["query", "configuration_names"]
                }
            },
            {
                "name": "list_configurations",
                "description": "List available RAG configurations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "names_only": {
                            "type": "boolean",
                            "description": "Return only configuration names without details",
                            "default": true
                        }
                    }
                }
            },
            {
                "name": "get_configuration",
                "description": "Get details of a specific RAG configuration",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "configuration_name": {
                            "type": "string",
                            "description": "Name of the configuration to retrieve"
                        }
                    },
                    "required": ["configuration_name"]
                }
            },
            {
                "name": "query_with_generation",
                "description": "Query documents and generate an answer using RAG",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The question or query to answer"
                        },
                        "configuration_name": {
                            "type": "string",
                            "description": "Name of the RAG configuration to use",
                            "default": "default"
                        },
                        "k": {
                            "type": "integer",
                            "description": "Number of documents to retrieve for context",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20
                        },
                        "similarity_threshold": {
                            "type": "number",
                            "description": "Minimum similarity threshold",
                            "default": 0.7,
                            "minimum": 0.0,
                            "maximum": 1.0
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    }

@app.get("/resources")
async def get_resources():
    """Get available resources"""
    return {
        "resources": [
            {
                "uri": "rag://configurations",
                "name": "RAG Configurations",
                "description": "List of available RAG configurations"
            },
            {
                "uri": "rag://health",
                "name": "RAG Service Health",
                "description": "Health status of the RAG service"
            }
        ]
    }

@app.post("/tools/retrieve_documents")
async def retrieve_documents(request: ToolRequest) -> ToolResponse:
    """Retrieve relevant documents from a RAG configuration"""
    try:
        args = request.arguments
        query = args.get("query")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        # Prepare request for RAG service
        rag_request = {
            "query": query,
            "configuration_name": args.get("configuration_name", "default"),
            "k": args.get("k", 5),
            "similarity_threshold": args.get("similarity_threshold", 0.0),
            "use_reranking": args.get("use_reranking", False),
            "include_metadata": args.get("include_metadata", True),
            "include_vectors": False  # Don't include vectors in MCP response
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{RAG_API_BASE}/retrieve",
                json=rag_request
            )
            response.raise_for_status()
            result = response.json()
        
        # Format the response for MCP
        documents = result.get("documents", [])
        total_found = result.get("total_found", 0)
        processing_time = result.get("processing_time", 0)
        
        if not documents:
            content = f"No relevant documents found for query: '{query}'"
        else:
            content_lines = [
                f"Found {total_found} relevant documents for query: '{query}'",
                f"Configuration: {result.get('configuration_name', 'unknown')}",
                f"Processing time: {processing_time:.3f}s",
                "",
                "Documents:"
            ]
            
            for i, doc in enumerate(documents, 1):
                content_lines.append(f"\n{i}. Score: {doc.get('similarity_score', 'N/A')}")
                content_lines.append(f"   Content: {doc.get('content', '')[:200]}...")
                
                if doc.get('metadata'):
                    metadata = doc['metadata']
                    if metadata.get('source'):
                        content_lines.append(f"   Source: {metadata['source']}")
                    if metadata.get('page'):
                        content_lines.append(f"   Page: {metadata['page']}")
        
        content = "\n".join(content_lines)
        
        logger.info(f"Retrieved {total_found} documents for query: {query}")
        return ToolResponse(content=content)
        
    except httpx.HTTPStatusError as e:
        logger.error(f"RAG service error: {e}")
        error_msg = f"RAG service error: {e.response.status_code}"
        if e.response.status_code == 404:
            error_msg = f"Configuration '{args.get('configuration_name', 'default')}' not found"
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        logger.error(f"Error retrieving documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/retrieve_multi_config")
async def retrieve_multi_config(request: ToolRequest) -> ToolResponse:
    """Retrieve documents from multiple configurations with fusion"""
    try:
        args = request.arguments
        query = args.get("query")
        configuration_names = args.get("configuration_names")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")
        if not configuration_names:
            raise HTTPException(status_code=400, detail="Configuration names are required")
        
        # Prepare request for RAG service
        rag_request = {
            "query": query,
            "configuration_names": configuration_names,
            "k": args.get("k", 5),
            "fusion_method": args.get("fusion_method", "rrf"),
            "rrf_k_constant": args.get("rrf_k_constant", 60),
            "use_reranking": args.get("use_reranking", False),
            "include_metadata": True,
            "include_vectors": False
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{RAG_API_BASE}/retrieve",
                json=rag_request
            )
            response.raise_for_status()
            result = response.json()
        
        # Format the response
        documents = result.get("documents", [])
        total_found = result.get("total_found", 0)
        processing_time = result.get("processing_time", 0)
        fusion_method = result.get("fusion_method", "unknown")
        
        if not documents:
            content = f"No relevant documents found for query: '{query}'"
        else:
            content_lines = [
                f"Found {total_found} relevant documents for query: '{query}'",
                f"Configurations: {', '.join(configuration_names)}",
                f"Fusion method: {fusion_method}",
                f"Processing time: {processing_time:.3f}s",
                "",
                "Documents:"
            ]
            
            for i, doc in enumerate(documents, 1):
                content_lines.append(f"\n{i}. Score: {doc.get('similarity_score', 'N/A')}")
                if doc.get('rrf_score'):
                    content_lines.append(f"   RRF Score: {doc.get('rrf_score', 'N/A')}")
                if doc.get('source_configuration'):
                    content_lines.append(f"   Source Config: {doc['source_configuration']}")
                content_lines.append(f"   Content: {doc.get('content', '')[:200]}...")
        
        content = "\n".join(content_lines)
        
        logger.info(f"Retrieved {total_found} documents from {len(configuration_names)} configurations")
        return ToolResponse(content=content)
        
    except Exception as e:
        logger.error(f"Error in multi-config retrieval: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/list_configurations")
async def list_configurations(request: ToolRequest) -> ToolResponse:
    """List available RAG configurations"""
    try:
        args = request.arguments
        names_only = args.get("names_only", True)
        
        params = {"names_only": names_only}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{RAG_API_BASE}/configurations",
                params=params
            )
            response.raise_for_status()
            result = response.json()
        
        if names_only:
            names = result.get("names", [])
            total_count = result.get("total_count", 0)
            content = f"Available RAG configurations ({total_count}):\n" + "\n".join(f"- {name}" for name in names)
        else:
            configurations = result.get("configurations", [])
            total_count = result.get("total_count", 0)
            content_lines = [f"Available RAG configurations ({total_count}):"]
            
            for config in configurations:
                content_lines.append(f"\n- {config['configuration_name']}")
                content_lines.append(f"  Documents: {config['document_count']}")
                if config.get('last_updated'):
                    content_lines.append(f"  Last updated: {config['last_updated']}")
            
            content = "\n".join(content_lines)
        
        logger.info(f"Listed {result.get('total_count', 0)} configurations")
        return ToolResponse(content=content)
        
    except Exception as e:
        logger.error(f"Error listing configurations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/get_configuration")
async def get_configuration(request: ToolRequest) -> ToolResponse:
    """Get details of a specific RAG configuration"""
    try:
        args = request.arguments
        configuration_name = args.get("configuration_name")
        
        if not configuration_name:
            raise HTTPException(status_code=400, detail="Configuration name is required")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{RAG_API_BASE}/configurations/{configuration_name}"
            )
            response.raise_for_status()
            result = response.json()
        
        config = result.get("config", {})
        content_lines = [
            f"Configuration: {configuration_name}",
            "",
            "Settings:"
        ]
        
        # Format key configuration settings
        if config.get("chunking"):
            chunking = config["chunking"]
            content_lines.append(f"- Chunking: {chunking.get('strategy', 'unknown')} (size: {chunking.get('chunk_size', 'N/A')})")
        
        if config.get("embedding"):
            embedding = config["embedding"]
            content_lines.append(f"- Embedding: {embedding.get('model', 'unknown')}")
        
        if config.get("vector_store"):
            vector_store = config["vector_store"]
            content_lines.append(f"- Vector Store: {vector_store.get('type', 'unknown')}")
        
        if config.get("generation"):
            generation = config["generation"]
            content_lines.append(f"- Generation: {generation.get('model', 'unknown')}")
        
        content = "\n".join(content_lines)
        
        logger.info(f"Retrieved configuration: {configuration_name}")
        return ToolResponse(content=content)
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Configuration '{configuration_name}' not found")
        raise HTTPException(status_code=500, detail=f"RAG service error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Error getting configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/query_with_generation")
async def query_with_generation(request: ToolRequest) -> ToolResponse:
    """Query documents and generate an answer using RAG"""
    try:
        args = request.arguments
        query = args.get("query")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        # Prepare request for RAG service
        rag_request = {
            "query": query,
            "configuration_name": args.get("configuration_name", "default"),
            "k": args.get("k", 5),
            "similarity_threshold": args.get("similarity_threshold", 0.7),
            "include_metadata": True
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for generation
            response = await client.post(
                f"{RAG_API_BASE}/query",
                json=rag_request
            )
            response.raise_for_status()
            result = response.json()
        
        # Format the response
        answer = result.get("answer", "No answer generated")
        sources = result.get("sources", [])
        processing_time = result.get("processing_time", 0)
        
        content_lines = [
            f"Query: {query}",
            f"Configuration: {result.get('configuration_name', 'unknown')}",
            f"Processing time: {processing_time:.3f}s",
            "",
            f"Answer: {answer}",
            "",
            f"Sources ({len(sources)}):"
        ]
        
        for i, source in enumerate(sources, 1):
            content_lines.append(f"\n{i}. Score: {source.get('similarity_score', 'N/A')}")
            content_lines.append(f"   Content: {source.get('content', '')[:150]}...")
            if source.get('metadata', {}).get('source'):
                content_lines.append(f"   Source: {source['metadata']['source']}")
        
        content = "\n".join(content_lines)
        
        logger.info(f"Generated answer for query: {query}")
        return ToolResponse(content=content)
        
    except Exception as e:
        logger.error(f"Error in query with generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/resources/rag://configurations")
async def get_configurations_resource():
    """Get list of RAG configurations as a resource"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{RAG_API_BASE}/configurations?names_only=true")
            response.raise_for_status()
            result = response.json()
        
        names = result.get("names", [])
        return {
            "content": f"Available RAG configurations: {', '.join(names)}",
            "mimeType": "text/plain"
        }
    except Exception as e:
        return {
            "content": f"Error retrieving configurations: {str(e)}",
            "mimeType": "text/plain"
        }

@app.get("/resources/rag://health")
async def get_health_resource():
    """Get RAG service health as a resource"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{RAG_API_BASE}/health")
            response.raise_for_status()
            result = response.json()
        
        return {
            "content": json.dumps(result, indent=2),
            "mimeType": "application/json"
        }
    except Exception as e:
        return {
            "content": f"RAG service unavailable: {str(e)}",
            "mimeType": "text/plain"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005, log_level="info")
