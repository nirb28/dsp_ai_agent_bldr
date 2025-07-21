#!/usr/bin/env python3
"""
Start the RAG Retrieval MCP Server
"""
import uvicorn
import sys
import os

# Add the server directory to the path
server_dir = os.path.join(os.path.dirname(__file__), "rag_server")
sys.path.insert(0, server_dir)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info"
    )
