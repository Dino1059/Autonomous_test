import os
import sys
from pprint import pprint
import logging
from lmnr import Laminar
from dotenv import load_dotenv
import asyncio
from pydantic import BaseModel
import pyperclip

from typing import Optional
from playwright.sync_api import ElementHandle
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

from browser_use import Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig, BrowserContextConfig
from browser_use.browser.context import BrowserContext
from browser_use.agent.views import AgentHistoryList
from browser_use.agent.views import ActionResult

from src.llms.base import BaseLLMWorker


## --- SETUP ---
load_dotenv()




controller = Controller(
		exclude_actions=['search_google', 'go_back', 'input_text', 'save_pdf', 'switch_tab', 'close_tab', 'extract_content', 'send_keys', 'get_dropdown_options', 'select_dropdown_options', 'drag_drop', 'get_drag_elements', 'get_element_coordinates', 'execute_drag_operation']
)



@controller.registry.action("Extract the page content")
async def extract_page_content(
	temp_params: str, browser: BrowserContext,
	):

	page_extraction_llm = ChatGoogleGenerativeAI(
		model="gemini-2.0-flash",
		temperature=0.0,
		top_p=1.0,
		top_k=40,
		max_output_tokens=2048,
		google_api_key=os.getenv('GEMINI_API_KEY')
	)

	#logger = logging.getLogger("EXTRACT SYSTEM MESSAGE")
	page = await browser.get_current_page()
	import markdownify
	strip = []
	should_strip_link_urls=False
	if should_strip_link_urls:
		strip = ['a', 'img']
	content = markdownify.markdownify(await page.content(), strip=strip)
	##logger.info(f"Content: {content}")
	# manually append iframe text into the content so it's readable by the LLM (includes cross-origin iframes)
	for iframe in page.frames:
		if iframe.url != page.url and not iframe.url.startswith('data:'):
			content += f'\n\nIFRAME {iframe.url}:\n'
			content += markdownify.markdownify(await iframe.content())

	prompt = """
	Extract the first item sold in this page in JSON format.
	{{
		"name": str,
		"price": str,
		"description": str,
		"image_description": str,
	}}
	You have to look the image and generate the description for the image. Please give a detail image description.
	Page: {page}
	"""
	template = PromptTemplate(template=prompt, input_variables=['page'])
	logger = logging.getLogger("PAGE TEMPLATE")
	logger.info(f"Prompt: {template.format(page=content)}")
	try:
		output = await page_extraction_llm.ainvoke(template.format(page=content))
		msg = f'📄  Extracted from page\n: {output.content}\n'
		pyperclip.copy(msg)
		logger.info(msg)
		return ActionResult(extracted_content="Done extracting", include_in_memory=True)
	except Exception as e:
		logger.debug(f'Error extracting content: {e}')
		msg = f'📄  Extracted from page\n: {content}\n'
		logger.info(msg)
		return ActionResult(extracted_content=msg)


initial_actions = [
	{'open_tab': {'url': 'https://webscraper.io/test-sites/e-commerce/allinone'}},
]

## --- SETUP ---



async def main():
	model = ChatGoogleGenerativeAI(
		model="gemini-2.0-flash",
		temperature=0.0,
		top_p=1.0,
		top_k=40,
		max_output_tokens=2048,
		google_api_key=os.getenv('GEMINI_API_KEY')
	)

	browser = Browser(config=BrowserConfig(headless=False))
	
	agent =  Agent(
		task="Call `extract_page_content` action to extract the system's message from the page.",
		initial_actions=initial_actions,
		controller=controller,
		browser=browser,
		llm=model
	)
	
	await agent.run()
		
if __name__ == '__main__':
	asyncio.run(main())
