#!/usr/bin/env python3
"""
Start all MCP servers
"""
import subprocess
import sys
import time
from pathlib import Path

def start_server(script_name, server_name):
    """Start an MCP server"""
    script_path = Path(__file__).parent / script_name
    
    print(f"Starting {server_name}...")
    process = subprocess.Popen([sys.executable, str(script_path)])
    
    # Give it a moment to start
    time.sleep(2)
    
    if process.poll() is None:
        print(f"✓ {server_name} started successfully (PID: {process.pid})")
        return process
    else:
        print(f"✗ Failed to start {server_name}")
        return None

if __name__ == "__main__":
    print("Starting all MCP servers...")
    print("=" * 50)
    
    servers = [
        ("start_weather_server.py", "Weather Server"),
        ("start_memory_server.py", "Memory Server"),
        ("start_calculator_server.py", "Calculator Server")
    ]
    
    processes = []
    
    for script, name in servers:
        process = start_server(script, name)
        if process:
            processes.append((process, name))
    
    print("\n" + "=" * 50)
    print(f"Started {len(processes)} MCP servers")
    print("\nServer URLs:")
    print("- Weather Server: http://localhost:8002")
    print("- Memory Server: http://localhost:8003")
    print("- Calculator Server: http://localhost:8004")
    
    print("\nPress Ctrl+C to stop all servers...")
    
    try:
        # Wait for user interrupt
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping all servers...")
        
        for process, name in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✓ Stopped {name}")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"✓ Force stopped {name}")
            except Exception as e:
                print(f"✗ Error stopping {name}: {e}")
        
        print("All servers stopped.")
