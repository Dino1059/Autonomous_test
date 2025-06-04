async def wait_for_response(timeout_seconds: int = 15, browser: BrowserContext = None):
    """
    Wait for AI response generation with timeout.
    
    Args:
        timeout_seconds (int): Maximum time to wait for response
        browser (BrowserContext): Browser context (optional)
    
    Returns:
        ActionResult: Result indicating wait completion
    """
    import asyncio
    from datetime import datetime
    
    start_time = datetime.now()
    
    # Wait for the specified duration
    await asyncio.sleep(timeout_seconds)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    return ActionResult(
        extracted_content=f'Waited {duration:.1f} seconds for response generation',
        include_in_memory=True
    ) 