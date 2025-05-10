"""
Router for environment and settings endpoints
"""
from fastapi import APIRouter

from app.controllers import settings

router = APIRouter()

router.include_router(settings.router, tags=["Settings"], prefix="/environment") 