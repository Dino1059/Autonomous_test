"""
Utility functions for browser actions and automation
"""
import os
import sys
import json
import asyncio
import logging
import pyperclip
from typing import Dict, Any, List, Optional

# Import from browser_use package
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from browser_use.agent.views import ActionResult
from browser_use.browser.context import BrowserContext
from playwright.sync_api import ElementHandle

def sanitize_response(text: str) -> str:
    """Remove excessive newlines or formatting that may trigger paste bugs"""
    sanitized = text.strip()
    sanitized = sanitized.replace('\r\n', '\n')  # Normalize newlines
    sanitized = '\n'.join(line.strip() for line in sanitized.splitlines())  # Strip each line
    # replace all \n with <line_break>
    sanitized = sanitized.replace('\n', '<line_break>')
    return sanitized

##work only for streamlit
async def go_down_the_page(temp_params: str, browser: BrowserContext):
    """Scroll down the page"""
    logger = logging.getLogger("GO DOWN THE PAGE")
    logger.info("Scrolling down the page")
    try:
        page = await browser.get_current_page()
        # For Playwright
        await page.evaluate("""
(() => {
    // Target the main Streamlit content container
    const mainContainer = document.querySelector('.stAppViewContainer');
    if (mainContainer) {
        mainContainer.scrollTo({
            top: 5000,
            behavior: 'smooth'
        });
    } else {
        // Fallback to main block container
        const blockContainer = document.querySelector('.stMainBlockContainer');
        if (blockContainer) {
            blockContainer.scrollTo({
                top: 5000,
                behavior: 'smooth'
            });
        }
    }
})()
""")

        return ActionResult(extracted_content="Done scrolling down the page.", include_in_memory=True)
    except Exception as e:
        logger.error(f"Error scrolling down the page: {str(e)}")
        return ActionResult(extracted_content=f"Failed to scroll down the page: {str(e)}", include_in_memory=True)


async def paste_from_clipboard(temp_params: str, browser: BrowserContext):
    """Paste text from clipboard to current input"""
    raw_text = pyperclip.paste()
    clean_text = sanitize_response(raw_text)

    # Send sanitized text to browser
    page = await browser.get_current_page()
    await page.keyboard.type(clean_text)

    logger = logging.getLogger("PASTE FROM CLIPBOARD")
    logger.info(f"Pasted: {clean_text}")
    ## implement go down the page
    await go_down_the_page(temp_params, browser)
    return ActionResult(
        extracted_content="Done pasting to input box. Please call `click_the_send_button` action to send the message.",
        include_in_memory=True
    )

async def call_user_simulator(temp_params: str) -> ActionResult:
    """Call user simulator to get a response"""
    import json_repair
    # Step 1: Get question from clipboard
    clipboard_text = pyperclip.paste().strip()
    
    from app.utils.globals import SETTINGS, USER_SIMULATOR_INTERACTIONS, get_or_initialize_llm_worker
    
    logger = logging.getLogger("CALL USER SIMULATOR")
    
    # Get or initialize the LLM worker
    llm_worker = get_or_initialize_llm_worker()
    
    if llm_worker is None:
        error_msg = "LLM worker could not be initialized. Please ensure simulator settings are configured."
        logger.error(error_msg)
        raise Exception(error_msg)
    
    session_id = SETTINGS["session_id"]
    
    # Initialize interactions list for this session if not exists
    if session_id not in USER_SIMULATOR_INTERACTIONS:
        USER_SIMULATOR_INTERACTIONS[session_id] = []
    
    # Try to parse as JSON
    try:
        # Try to repair JSON if needed
        try:
            data = json_repair.loads(clipboard_text)
        except:
            data = json.loads(clipboard_text)
        
        # Extract system message and images
        system_message = data.get("system_message", clipboard_text)
        image_urls = data.get("image_url", [])
        
        logger.info(f"Extracted system message: {system_message}")
        logger.info(f"Image URLs: {image_urls}")
        
        # Use customized prompt from settings if available
        user_simulator_task = SETTINGS.get("user_simulator_task", "")
        
        # Build the base prompt (fixed part)
        base_prompt = "You are a test user interacting with a marketing assistant. "
        base_prompt += "Your goal is to simulate realistic user responses to test the system. "
        #base_prompt += "PLease always respond in JSON format. {{'response': '....', 'feedback': '....'}}. But for the last response, please add a 'grade' field . The grade should be a number between 0 and 100."
        base_prompt += "Because you are testing the system, you need give the feedback at each step."
        
        # Add the flexible part if available
        if user_simulator_task:
            base_prompt += user_simulator_task + " "
        
        # Add the system message
        question = base_prompt
        question += f"\n\nMarketing Assistant: {system_message}"
        question += "\n\nPlease respond as a realistic user would. Keep responses short and concise. NO YAPPING!!!"
        
    except Exception as e:
        # If JSON parsing fails, use the clipboard text directly
        logger.warning(f"Failed to parse JSON: {e}")
        
        # Use customized prompt from settings if available
        user_simulator_task = SETTINGS.get("user_simulator_task", "")
        
        # Build the prompt
        base_prompt = "You are a test user interacting with a marketing assistant. "
        base_prompt += "Your goal is to simulate realistic user responses to test the system. "
        
        # Add the flexible part if available
        if user_simulator_task:
            base_prompt += user_simulator_task + " "
            
        question = base_prompt
        question += f"\n\nMarketing Assistant: {clipboard_text}"
        question += "\n\nPlease respond as a realistic user would. Keep responses short and concise. NO YAPPING!!!"
        
        # No images in this case
        image_urls = []
        system_message = clipboard_text

    # Step 2: Get response from the user simulator LLM
    # Handle potential images in the request - pass the list directly to get_response
    if image_urls and isinstance(image_urls, list) and len(image_urls) > 0:
        response = llm_worker.get_response(question, session_id, image_urls)
    else:
        response = llm_worker.get_response(question, session_id)
    
    # Our get_response now returns the content directly, not an object with content attribute
    json_tester_response = json_repair.loads(response)
    logger.info(f"JSON Response: {json_tester_response}")
    
    # Step 3: Sanitize response
    if isinstance(json_tester_response, dict):
        clean_response = sanitize_response(json_tester_response['response'])
        logger.info(f"Feedback: {json_tester_response['feedback']}")
        
        # Store the interaction
        interaction = {
            "system_message": sanitize_response(system_message),
            "image_url": image_urls,
            "user_response": clean_response,
            "feedback": sanitize_response(json_tester_response.get('feedback', '')),
            "grade": json_tester_response.get('grade', None)
        }
        USER_SIMULATOR_INTERACTIONS[session_id].append(interaction)
        
    else:
        logger.error(f"Invalid JSON response: {json_tester_response}")
        raise Exception("Invalid JSON response")

    # Step 4: Avoid re-copying same content to clipboard
    if pyperclip.paste().strip() != clean_response:
        pyperclip.copy(clean_response)
    ## Trick call `go_down_the_page` action
    return ActionResult(
        extracted_content="Done calling user simulator. Please call the `click_element_by_index` and `paste_from_clipboard` actions.",
        include_in_memory=True
    )

async def get_system_message(temp_params: str, browser: BrowserContext):
    """Extract the system's message from the page"""
    from pydantic import Field
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    from app.serializers.models import BaseModel

    page = await browser.get_current_page()
    await page.evaluate("window.scrollBy(0, 5000);")
    
    class SystemMessage(BaseModel):
        system_message: str = Field(description="system message")
        image_url: List[str] = Field(description="list of url of the image, end with .png/.jpg/.jpeg/.gif/.webp")

    page_extraction_llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.0,
        top_p=1.0,
        top_k=40,
        max_output_tokens=2048,
        google_api_key=os.getenv('GEMINI_API_KEY')
    )

    logger = logging.getLogger("EXTRACT SYSTEM MESSAGE")
    page = await browser.get_current_page()
    import markdownify
    strip = []
    should_strip_link_urls=False
    if should_strip_link_urls:
        strip = ['a', 'img']
    content = markdownify.markdownify(await page.content(), strip=strip)
    
    # Manually append iframe text into the content so it's readable by the LLM
    for iframe in page.frames:
        if iframe.url != page.url and not iframe.url.startswith('data:'):
            content += f'\n\nIFRAME {iframe.url}:\n'
            content += markdownify.markdownify(await iframe.content())

    prompt = """
    Extract the lastest system's message from the system. Don't include user's message. If the system also send image. Please attach the url of the image in the <image_url> tag.
    The system_message don't include the image url. If there are multiple image, please place a placeholder <image_index> in system_message.
    Example:
    system_message: Here is three cat images, <image_1>, <image_2>, <image_3>
    The image_url should be a list of url like this:
    [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg",
        "https://example.com/image3.jpg"
    ]
    
    You should return in JSON FORMAT:
    {format_instructions}
    Page: {page}
    """
    
    parser = JsonOutputParser(pydantic_object=SystemMessage)
    template = PromptTemplate(
        template=prompt, 
        input_variables=['page'], 
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    try:
        output = await page_extraction_llm.ainvoke(template.format(page=content))
        msg = f'📄  Extracted from page\n: {output.content}\n'
        pyperclip.copy(msg)
        logger.info(msg)
        return ActionResult(
            extracted_content="Done extracting system message. Please call `call_user_simulator` action.", 
            include_in_memory=True
        )
    except Exception as e:
        logger.debug(f'Error extracting content: {e}')
        msg = f'📄  Extracted from page\n: {content}\n'
        logger.info(msg)
        return ActionResult(extracted_content=msg)

async def click_the_send_button(temp_params: str, browser: BrowserContext):
    """Click the send button in the chat interface"""
    session = await browser.get_session()
    initial_pages = len(session.context.pages)

    # Locate the send button via the provided CSS selector helper
    element_handle: Optional[ElementHandle] = await browser.get_locate_element_by_css_selector(
        'button[data-testid="stChatInputSubmitButton"]'
    )
    if not element_handle:
        raise Exception('Send button not found on the page')

    logger = logging.getLogger("CLICK THE SEND BUTTON")
    try:
        # Click the button directly
        await element_handle.click()
        msg = '🖱️  Clicked the send button. Please call `wait` action to wait for the response.'
        logger.info(msg)

        return ActionResult(extracted_content=msg, include_in_memory=True)
    except Exception as e:
        logger.warning('Failed to click the send button', exc_info=True)
        return ActionResult(error=str(e)) 

