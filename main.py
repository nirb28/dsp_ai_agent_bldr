import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.api import router

# Set up logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Agent Platform")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Storage path: {settings.STORAGE_PATH}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Agent Platform")

# Create FastAPI app
app = FastAPI(
    title="Agent Platform",
    description="A platform for creating, managing, and executing AI agents using LangGraph, FastAPI, and CopilotKit",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API routes
app.include_router(router, prefix="/api/v1")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Agent Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "agents": "/api/v1/agents",
        "tools": "/api/v1/tools"
    }

# Health check endpoint (also available at root level)
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "platform": "Agent Platform"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )
