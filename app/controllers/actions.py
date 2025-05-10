"""
Actions controller for managing available browser actions
"""
from fastapi import APIRouter
from typing import List, Dict
import json
import os
from pathlib import Path

from app.serializers.models import DataResponse

router = APIRouter()

def load_actions_from_json():
    """Load actions from JSON file"""
    actions_path = Path(__file__).parent.parent / "templates" / "actions" / "actions.json"
    try:
        with open(actions_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading actions file: {e}")
        return []

@router.get("", response_model=DataResponse[List[Dict]])
async def get_available_actions():
    """Get list of available actions"""
    actions = load_actions_from_json()
    return DataResponse(data=actions)