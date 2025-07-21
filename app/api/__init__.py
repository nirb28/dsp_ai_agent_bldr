from fastapi import APIRouter
from .endpoints import router as main_router
from .mcp_routes import router as mcp_router

# Create main API router
router = APIRouter()

# Include all route modules
router.include_router(main_router)

# Make sure MCP router is included
router.include_router(mcp_router)

# Debug routes
import logging
logger = logging.getLogger(__name__)
logger.info(f"Available routes: {[route for route in mcp_router.routes]}")
