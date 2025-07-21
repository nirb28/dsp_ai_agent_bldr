#!/usr/bin/env python3
"""
Start the Memory MCP Server
"""
import sys
import os
from pathlib import Path

# Add the memory server directory to Python path
memory_server_dir = Path(__file__).parent / "memory-server"
sys.path.insert(0, str(memory_server_dir))

if __name__ == "__main__":
    from memory_server.main import app
    import uvicorn
    
    print("Starting Memory MCP Server on http://localhost:8003")
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
