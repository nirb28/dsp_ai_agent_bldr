from fastapi import APIRouter
from .endpoints import router as main_router
from .mcp_routes import router as mcp_router

# Create main API router
router = APIRouter()

# Include all route modules
router.include_router(main_router)
router.include_router(mcp_router)
