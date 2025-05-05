"""
Main router that includes all sub-routers
"""
from fastapi import APIRouter

# Import all routers
from app.routers.tasks_router import router as tasks_router
from app.routers.templates_router import router as templates_router
from app.routers.actions_router import router as actions_router

# Create main router
router = APIRouter()

# Include all sub-routers
router.include_router(tasks_router)
router.include_router(templates_router)
router.include_router(actions_router) 