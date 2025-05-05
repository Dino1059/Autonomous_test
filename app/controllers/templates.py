"""
Templates controller for action templates and helpers
"""
from fastapi import APIRouter
from typing import Dict

from app.serializers.models import DataResponse

# Sample action templates
DEFAULT_ACTION_TEMPLATE = """async def custom_action(temp_params: str, browser: BrowserContext):
    # Get the current page
    page = await browser.get_current_page()
    
    # Your custom action logic here
    
    # Return result
    return ActionResult(
        extracted_content="Custom action executed",
        include_in_memory=True
    )
"""

CLICK_ELEMENT_TEMPLATE = """async def click_custom_element(temp_params: str, browser: BrowserContext):
    # Get the current page
    page = await browser.get_current_page()
    
    # Locate element by selector
    selector = 'button.your-class'  # Replace with your selector
    element = await browser.get_locate_element_by_css_selector(selector)
    
    if not element:
        return ActionResult(
            error=f"Element with selector '{selector}' not found",
            include_in_memory=True
        )
    
    # Click the element
    await element.click()
    
    return ActionResult(
        extracted_content=f"Clicked element with selector '{selector}'",
        include_in_memory=True
    )
"""

DATA_EXTRACTION_TEMPLATE = """async def extract_data(temp_params: str, browser: BrowserContext):
    # Get the current page
    page = await browser.get_current_page()
    
    # Extract data from page
    data = await page.evaluate('''() => {
        // JavaScript to run in the browser
        const elements = document.querySelectorAll('.data-item');
        return Array.from(elements).map(el => el.textContent);
    }''')
    
    return ActionResult(
        extracted_content=f"Extracted data: {data}",
        include_in_memory=True
    )
"""

router = APIRouter()

@router.get("/actions", response_model=DataResponse[Dict[str, str]])
async def get_action_templates():
    """Get action templates"""
    return DataResponse(data={
        "default": DEFAULT_ACTION_TEMPLATE,
        "click_element": CLICK_ELEMENT_TEMPLATE,
        "data_extraction": DATA_EXTRACTION_TEMPLATE
    }) 