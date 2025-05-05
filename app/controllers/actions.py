"""
Actions controller for managing available browser actions
"""
from fastapi import APIRouter
from typing import List

from app.serializers.models import DataResponse

router = APIRouter()

@router.get("", response_model=DataResponse[List[str]])
async def get_available_actions():
    """Get list of available actions"""
    return DataResponse(data=[
        'search_google', 'go_back', 'input_text', 'save_pdf', 'switch_tab', 
        'close_tab', 'extract_content', 'send_keys', 'get_dropdown_options', 
        'select_dropdown_options', 'drag_drop', 'get_drag_elements', 
        'get_element_coordinates', 'execute_drag_operation',
        'click_element', 'click_element_by_text', 'click_element_by_index',
        'wait', 'scroll', 'paste_from_clipboard', 'call_user_simulator', 
        'get_system_message', 'click_the_send_button'
    ]) 