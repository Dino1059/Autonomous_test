"""
Settings controller for managing application environment settings
"""
import os
from fastapi import APIRouter, HTTPException

from app.serializers.models import EnvironmentVariablesRequest, MessageResponse, DataResponse

router = APIRouter()

@router.post("", response_model=DataResponse[MessageResponse])
async def update_environment(request: EnvironmentVariablesRequest):
    """Update environment variables"""
    try:
        # Update .env file
        with open(".env", "w") as f:
            f.write(f"OPENAI_API_KEY={request.openai_api_key}\n")
            f.write(f"GEMINI_API_KEY={request.gemini_api_key}\n")
            f.write(f"HUB1_API_KEY={request.hub1_api_key}\n")
            f.write(f"HUB1_API_BASE_URL={request.hub1_api_base_url}\n")
        
        # Also set in current environment
        os.environ["OPENAI_API_KEY"] = request.openai_api_key
        os.environ["GEMINI_API_KEY"] = request.gemini_api_key
        os.environ["HUB1_API_KEY"] = request.hub1_api_key
        os.environ["HUB1_API_BASE_URL"] = request.hub1_api_base_url
        
        return DataResponse(data=MessageResponse(message="Environment variables updated successfully"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update environment variables: {str(e)}")


# ── Task 1.3: GET current settings — FE gọi GET /settings ──────────────────
@router.get("", response_model=DataResponse[dict])
async def get_current_settings():
    """Trả về settings hiện tại (các API keys đã mask) — alias cho FE"""
    SENSITIVE_KEYS = {"OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
                      "HUB1_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY"}
    settings = {}
    for key in SENSITIVE_KEYS | {"HUB1_API_BASE_URL", "PORT", "HOST", "REPORT_FOLDER"}:
        val = os.environ.get(key, "")
        # Mask: chỉ hiện 8 ký tự đầu nếu là key
        if val and key in SENSITIVE_KEYS:
            settings[key] = val[:8] + "****" if len(val) > 8 else "****"
        else:
            settings[key] = val
    return DataResponse(data=settings, message="Current settings")