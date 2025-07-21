#!/usr/bin/env python3
"""
Startup script for the Agent Platform
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import langchain
        import langgraph
        import pydantic
        print("✓ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def setup_environment():
    """Set up environment variables and directories"""
    # Create storage directory
    storage_path = Path("./storage")
    storage_path.mkdir(exist_ok=True)
    print(f"✓ Storage directory created: {storage_path}")
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠ No .env file found. Copying from .env.example")
        example_file = Path(".env.example")
        if example_file.exists():
            import shutil
            shutil.copy(example_file, env_file)
            print("✓ Created .env file from example")
            print("Please edit .env file with your API keys before running the server")
        else:
            print("✗ No .env.example file found")
            return False
    else:
        print("✓ .env file exists")
    
    return True

def create_example_agents():
    """Create example agent configurations"""
    try:
        from examples.example_agents import create_example_agents
        create_example_agents()
        print("✓ Example agents created")
    except Exception as e:
        print(f"⚠ Could not create example agents: {e}")

def main():
    """Main startup function"""
    print("🚀 Starting Agent Platform")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Create example agents
    create_example_agents()
    
    print("\n" + "=" * 50)
    print("🎉 Setup complete!")
    print("\nTo start the server, run:")
    print("  python main.py")
    print("\nOr with uvicorn:")
    print("  uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
    print("\nAPI Documentation will be available at:")
    print("  http://localhost:8000/docs")
    print("\nHealth check:")
    print("  http://localhost:8000/health")

if __name__ == "__main__":
    main()
