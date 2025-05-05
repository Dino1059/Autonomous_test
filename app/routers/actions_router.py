"""
Router for actions endpoints
"""
from fastapi import APIRouter

from app.controllers import actions

router = APIRouter()

router.include_router(actions.router, tags=["Actions"], prefix="/actions") 