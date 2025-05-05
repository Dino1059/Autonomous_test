"""
Router for tasks endpoints
"""
from fastapi import APIRouter

from app.controllers import tasks

router = APIRouter()

router.include_router(tasks.router, tags=["Tasks"], prefix="/tasks") 