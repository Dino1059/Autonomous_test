"""
Router for reports endpoints
"""
from fastapi import APIRouter
from app.controllers import reports

router = APIRouter()

router.include_router(reports.router, tags=["Reports"], prefix="/reports")
