#!/usr/bin/env python3
"""
Start the Weather MCP Server
"""
import sys
import os
from pathlib import Path

# Add the weather server directory to Python path
weather_server_dir = Path(__file__).parent / "weather_server"
sys.path.insert(0, str(weather_server_dir))

if __name__ == "__main__":
    from weather_server.main import app
    import uvicorn
    
    print("Starting Weather MCP Server on http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
