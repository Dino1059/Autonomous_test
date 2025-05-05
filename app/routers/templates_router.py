"""
Router for templates endpoints
"""
from fastapi import APIRouter

from app.controllers import templates

router = APIRouter()

router.include_router(templates.router, tags=["Templates"], prefix="/templates") 