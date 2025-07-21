import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Memory MCP Server", version="1.0.0")

class ToolRequest(BaseModel):
    arguments: Dict[str, Any]

class ToolResponse(BaseModel):
    content: str
    success: bool = True

# In-memory storage for demonstration (in production, use a proper database)
memory_store = {
    "memories": {},
    "conversations": {},
    "entities": {}
}

# Storage file for persistence
STORAGE_FILE = Path("memory_storage.json")

def load_memory():
    """Load memory from storage file"""
    global memory_store
    try:
        if STORAGE_FILE.exists():
            with open(STORAGE_FILE, 'r') as f:
                memory_store = json.load(f)
            logger.info("Loaded memory from storage")
    except Exception as e:
        logger.error(f"Error loading memory: {str(e)}")

def save_memory():
    """Save memory to storage file"""
    try:
        with open(STORAGE_FILE, 'w') as f:
            json.dump(memory_store, f, indent=2, default=str)
        logger.info("Saved memory to storage")
    except Exception as e:
        logger.error(f"Error saving memory: {str(e)}")

# Load memory on startup
load_memory()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "server": "memory-mcp"}

@app.get("/tools")
async def get_tools():
    """Get available tools"""
    return {
        "tools": [
            {
                "name": "store_memory",
                "description": "Store a memory with a key and content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Unique key for the memory"
                        },
                        "content": {
                            "type": "string", 
                            "description": "Content to store"
                        },
                        "category": {
                            "type": "string",
                            "description": "Category for the memory",
                            "default": "general"
                        }
                    },
                    "required": ["key", "content"]
                }
            },
            {
                "name": "retrieve_memory",
                "description": "Retrieve a memory by key",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Key of the memory to retrieve"
                        }
                    },
                    "required": ["key"]
                }
            },
            {
                "name": "search_memories",
                "description": "Search memories by content or category",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "category": {
                            "type": "string",
                            "description": "Category to search in"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10
                        }
                    }
                }
            },
            {
                "name": "list_memories",
                "description": "List all stored memories",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Filter by category"
                        }
                    }
                }
            },
            {
                "name": "delete_memory",
                "description": "Delete a memory by key",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Key of the memory to delete"
                        }
                    },
                    "required": ["key"]
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
                "uri": "memory://stats",
                "name": "Memory Statistics",
                "description": "Statistics about stored memories"
            },
            {
                "uri": "memory://categories",
                "name": "Memory Categories",
                "description": "List of memory categories"
            }
        ]
    }

@app.post("/tools/store_memory")
async def store_memory(request: ToolRequest) -> ToolResponse:
    """Store a memory"""
    try:
        key = request.arguments.get("key")
        content = request.arguments.get("content")
        category = request.arguments.get("category", "general")
        
        if not key or not content:
            raise HTTPException(status_code=400, detail="Key and content are required")
        
        memory_store["memories"][key] = {
            "content": content,
            "category": category,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        save_memory()
        
        result = f"Memory stored successfully with key: {key}"
        logger.info(f"Stored memory: {key}")
        return ToolResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error storing memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/retrieve_memory")
async def retrieve_memory(request: ToolRequest) -> ToolResponse:
    """Retrieve a memory by key"""
    try:
        key = request.arguments.get("key")
        
        if not key:
            raise HTTPException(status_code=400, detail="Key is required")
        
        memory = memory_store["memories"].get(key)
        
        if not memory:
            return ToolResponse(content=f"No memory found with key: {key}")
        
        result = f"Memory '{key}' (category: {memory['category']}):\n{memory['content']}\n\nCreated: {memory['created_at']}"
        
        logger.info(f"Retrieved memory: {key}")
        return ToolResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error retrieving memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/search_memories")
async def search_memories(request: ToolRequest) -> ToolResponse:
    """Search memories"""
    try:
        query = request.arguments.get("query", "").lower()
        category = request.arguments.get("category")
        limit = request.arguments.get("limit", 10)
        
        results = []
        
        for key, memory in memory_store["memories"].items():
            # Filter by category if specified
            if category and memory["category"] != category:
                continue
            
            # Search in content and key
            if query:
                if query in memory["content"].lower() or query in key.lower():
                    results.append((key, memory))
            else:
                results.append((key, memory))
        
        # Limit results
        results = results[:limit]
        
        if not results:
            return ToolResponse(content="No memories found matching the search criteria")
        
        result_lines = [f"Found {len(results)} memories:"]
        for key, memory in results:
            result_lines.append(f"- {key} ({memory['category']}): {memory['content'][:100]}...")
        
        result = "\n".join(result_lines)
        
        logger.info(f"Search returned {len(results)} results")
        return ToolResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error searching memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/list_memories")
async def list_memories(request: ToolRequest) -> ToolResponse:
    """List all memories"""
    try:
        category = request.arguments.get("category")
        
        memories = memory_store["memories"]
        
        if category:
            memories = {k: v for k, v in memories.items() if v["category"] == category}
        
        if not memories:
            return ToolResponse(content="No memories found")
        
        result_lines = [f"Found {len(memories)} memories:"]
        for key, memory in memories.items():
            result_lines.append(f"- {key} ({memory['category']}): {memory['content'][:100]}...")
        
        result = "\n".join(result_lines)
        
        logger.info(f"Listed {len(memories)} memories")
        return ToolResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error listing memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/delete_memory")
async def delete_memory(request: ToolRequest) -> ToolResponse:
    """Delete a memory"""
    try:
        key = request.arguments.get("key")
        
        if not key:
            raise HTTPException(status_code=400, detail="Key is required")
        
        if key not in memory_store["memories"]:
            return ToolResponse(content=f"No memory found with key: {key}")
        
        del memory_store["memories"][key]
        save_memory()
        
        result = f"Memory deleted successfully: {key}"
        logger.info(f"Deleted memory: {key}")
        return ToolResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error deleting memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/resources/memory://stats")
async def get_memory_stats():
    """Get memory statistics"""
    memories = memory_store["memories"]
    categories = {}
    
    for memory in memories.values():
        category = memory["category"]
        categories[category] = categories.get(category, 0) + 1
    
    stats = {
        "total_memories": len(memories),
        "categories": categories,
        "storage_file": str(STORAGE_FILE.absolute())
    }
    
    return {
        "content": json.dumps(stats, indent=2),
        "mimeType": "application/json"
    }

@app.get("/resources/memory://categories")
async def get_memory_categories():
    """Get list of memory categories"""
    memories = memory_store["memories"]
    categories = set(memory["category"] for memory in memories.values())
    
    return {
        "content": f"Memory categories: {', '.join(sorted(categories))}",
        "mimeType": "text/plain"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
