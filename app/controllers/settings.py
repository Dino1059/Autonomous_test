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