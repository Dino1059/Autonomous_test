import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pprint import pprint
import logging
from lmnr import Laminar
from dotenv import load_dotenv
import asyncio
from pydantic import BaseModel, Field
from typing import List, Optional
import pyperclip

from playwright.sync_api import ElementHandle
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from browser_use import Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig, BrowserContextConfig
from browser_use.browser.context import BrowserContext
from browser_use.agent.views import AgentHistoryList
from browser_use.agent.views import ActionResult

from src.llms.base import BaseLLMWorker


## --- SETUP ---
load_dotenv()

llm_worker = BaseLLMWorker("user_simulator")
session_id = "test_session"

Laminar.initialize(
    project_api_key="hcAzTvWi7Tyvpjnwpgcnd3liW35GX3tpPGiDFXtNwOaiBEkKhK6binwADLMAlaNa",
    base_url="http://localhost",
    http_port=9000,
    grpc_port=9001,
    
)

class MetadataCampaign(BaseModel):
	campaign_name: str
	campaign_id: str
	thread_id: str


initial_actions = [
	{'open_tab': {'url': 'http://localhost:8501/'}},
]

SYSTEM_PROMPT = """
a
"""


controller = Controller(
		exclude_actions=['search_google', 'go_back', 'input_text', 'save_pdf', 'switch_tab', 'close_tab', 'extract_content', 'send_keys', 'get_dropdown_options', 'select_dropdown_options', 'drag_drop', 'get_drag_elements', 'get_element_coordinates', 'execute_drag_operation']
)

controller_setup = Controller(
	output_model=MetadataCampaign, 
	exclude_actions=['search_google', 'go_back', 'input_text', 'save_pdf', 'switch_tab', 'close_tab', 'extract_content', 'send_keys'])


# @controller.registry.action('Function to Copy text to clipboard')
# def copy_to_clipboard(text_to_copy: str):
# 	pyperclip.copy(text_to_copy)
# 	return ActionResult(extracted_content="Has copied to clipboard")

def sanitize_response(text: str) -> str:
    # Remove excessive newlines or formatting that may trigger paste bugs
    sanitized = text.strip()
    sanitized = sanitized.replace('\r\n', '\n')  # Normalize newlines
    sanitized = '\n'.join(line.strip() for line in sanitized.splitlines())  # Strip each line
	## replace all \n with <line_break>
    sanitized = sanitized.replace('\n', '<line_break>')
    return sanitized


@controller.registry.action('Always use this action everytime you see something like Paste text...')
async def paste_from_clipboard(temp_params: str, browser: BrowserContext):
    raw_text = pyperclip.paste()
    clean_text = sanitize_response(raw_text)

    # Send sanitized text to browser
    page = await browser.get_current_page()
    await page.keyboard.type(clean_text)

    logger = logging.getLogger("PASTE FROM CLIPBOARD")
    logger.info(f"Pasted: {clean_text}")

    return ActionResult(
        extracted_content="Done pasting to input box",
        include_in_memory=True
    )


@controller.registry.action('Call user simulator')
## ALways pass at least one parameter to this function
## https://github.com/browser-use/browser-use/issues/733
def call_user_simulator(temp_params: str) -> str:
    import pyperclip
    from json_repair import repair_json
    # Step 1: Get question from clipboard
    clipboard_text = pyperclip.paste().strip()
    ## load in json format
    json_text = repair_json(clipboard_text)
    question = "You are chatting with a marketing assistant."
    question += "\n\nMarketing Assistant: " + clipboard_text
    question += "\n\nPlease answer for the marketing assistant in short and concise. NO YAPPING!!!"

    # Step 2: Get response
    response = llm_worker.get_response(question, session_id)
    logger = logging.getLogger("CALL USER SIMULATOR")
    logger.info(f"Raw Response: {response.content}")

    # Step 3: Sanitize response
    clean_response = sanitize_response(response.content)

    # Step 4: Avoid re-copying same content to clipboard
    if pyperclip.paste().strip() != clean_response:
        pyperclip.copy(clean_response)

    return ActionResult(
        extracted_content="Done calling user simulator",
        include_in_memory=True
    )

# @controller.registry.action('Get image description')
# def get_image_description(image_description: str):
# 	return ActionResult(extracted_content=image_description)


@controller.registry.action("Extract the system's message")
async def get_system_message(
	temp_params: str, browser: BrowserContext,
	):

    class SystemMessage(BaseModel):
        system_message: str = Field(description="system message")
        image_url: List[str] = Field(description="list of url of the image")
	

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
	# manually append iframe text into the content so it's readable by the LLM (includes cross-origin iframes)
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
    template = PromptTemplate(template=prompt, input_variables=['page'], partial_variables={"format_instructions": parser.get_format_instructions()},)
	#logger.info(f"TEMPLATE: {template.format(page=content)}")
    try:
        output = await page_extraction_llm.ainvoke(template.format(page=content))
        msg = f'📄  Extracted from page\n: {output.content}\n'
        pyperclip.copy(msg)
        logger.info(msg)
        return ActionResult(extracted_content="Done extracting system message", include_in_memory=True)
    except Exception as e:
        logger.debug(f'Error extracting content: {e}')
        msg = f'📄  Extracted from page\n: {content}\n'
        logger.info(msg)
        return ActionResult(extracted_content=msg)


@controller.registry.action("Click the send button")
async def click_the_send_button(temp_params: str, browser: BrowserContext):
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
        msg = '🖱️  Clicked the send button'
        logger.info(msg)

        return ActionResult(extracted_content=msg, include_in_memory=True)

    except Exception as e:
        logger.warning('Failed to click the send button', exc_info=True)
        return ActionResult(error=str(e))

		
	
task_description = f"""
**Task Description:**
You are the Operator of a web app used to simulate user interaction for testing automated game campaign planning.

Your job is to simulate the user's message flow — NOT to generate any content or alter any text. You must copy and paste assistant responses *exactly word-by-word*, simulating how a user would reply via automation.

---

**Please do step by step:**
1. Call `extract_content` with temp_params=None to get the system's message.
2. Call `call_user_simulator` with temp_params=None to get the user's simulated reply.
3. Call `click_element_by_index` to click on the input box.
4. Call `paste_from_clipboard` with temp_params=None.
5. Call `click_the_send_button` with temp_params=None to click on the send button.
6. Wait for the assistant to generate the next message. You maybe need to call `wait` function more than once.
7. Only move to the next step after the assistant has generated the next message else continue call `wait` function.
**If any step fails, terminate the task and return the error message.**
**Repeat the steps above until the assistant provides a completed campaign plan or content.**

MAKE SURE FOLLOW THE RULES, NO YAPPING!!!.
"""



## --- SETUP ---



async def main():
	
	browser = Browser()
	async with await browser.new_context() as context:
		model = ChatGoogleGenerativeAI(
		    model="gemini-2.0-flash",  # Use an actual Gemini model name
		    temperature=0.0,
		    top_p=1.0,
		    top_k=40,
		    max_output_tokens=2048,
		    google_api_key=os.getenv('GEMINI_API_KEY')
		)

		# model = ChatOpenAI(
		# 	model="openai/gpt-4o-mini-2024-07-18",
		# 	temperature=0.0,
        #     openai_api_key=os.getenv('OPENAI_API_KEY'),
        #     base_url="https://openrouter.ai/api/v1"
		# )
		
		agent_setup = Agent(
			task="""
			1. Select the campaign named "2: new".
			2. Open the thread dropdown and select the thread ID : 5ec09a9e-ea37-439b-ab6b-260ae2983c64 from the list.
            3. Click on the input box.
			4. Return the following fields in JSON format: campaign_name, campaign_id, and thread_id.
			Task complete!
			""",
			llm=model,
			controller=controller_setup,
			browser_context=context,
			initial_actions=initial_actions,
		)

		agent_chat = Agent(
			task=task_description,
			llm=model,
			controller=controller,
			browser_context=context,
			enable_memory=True,
			memory_interval=3,
			# initial_actions=initial_actions,
			# extend_system_message=SYSTEM_PROMPT
		)
		history_1 = await agent_setup.run(max_steps=7)
		result_1 = history_1.final_result()
		if result_1:
			parsed: MetadataCampaign = MetadataCampaign.model_validate_json(result_1)
			print(parsed.campaign_name)
			print(parsed.campaign_id)
			print(parsed.thread_id)
			print("--------------------------------")

		history_2 = await agent_chat.run()
if __name__ == '__main__':
	asyncio.run(main())
