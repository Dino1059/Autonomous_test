async def gather_evidence(description: str, screenshot_name: str, browser: BrowserContext):
    """
    Capture a screenshot of the current page and save it to the reports/images folder.

    Args:
        description (str): A description of the screenshot.
        screenshot_name (str): The name of the screenshot file without extension.
    
    Returns:
        ActionResult: Result containing screenshot path and description
    """
    import os
    import json
    from datetime import datetime
    from pathlib import Path
    import re
    
    # Setup base paths
    base_path = Path("E:/official_DopikAI/ai-agent-tester/gradio_ui/reports")
    base_path.mkdir(parents=True, exist_ok=True)

    images_path = base_path / "images"
    images_path.mkdir(parents=True, exist_ok=True)

    # Get current page
    page = await browser.get_current_page()
    
    # Clean screenshot name (remove extension if provided)
    screenshot_name = re.sub(r'\.[^.]+$', '', screenshot_name)
    screenshot_path = images_path / f"{screenshot_name}.png"

    # Take screenshot
    await page.screenshot(
        path=str(screenshot_path),
        full_page=True,
        animations='disabled'
    )

    # Return relative path for reports
    short_screenshot_path = f"../images/{screenshot_name}.png"
    
    return ActionResult(
        extracted_content=f'Has gathered the evidence with description: {description}, screenshot_path: {short_screenshot_path}',
        include_in_memory=True
    ) 