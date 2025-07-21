#!/usr/bin/env python3
"""
Start the Calculator MCP Server
"""
import sys
import os
from pathlib import Path

# Add the calculator server directory to Python path
calculator_server_dir = Path(__file__).parent / "calculator_server"
sys.path.insert(0, str(calculator_server_dir))

if __name__ == "__main__":
    from calculator_server.main import app
    import uvicorn
    
    print("Starting Calculator MCP Server on http://localhost:8004")
    uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")
