"""
Simple demonstration of the CDP feature.

To test this locally, follow these steps:
1. Create a shortcut for the executable Chrome file.
2. Add the following argument to the shortcut:
   - On Windows: `--remote-debugging-port=9222`
3. Open a web browser and navigate to `http://localhost:9222/json/version` to verify that the Remote Debugging Protocol (CDP) is running.
4. Launch this example.

@dev You need to set the `GOOGLE_API_KEY` environment variable before proceeding.
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from browser_use import Agent, Controller
from browser_use.browser import BrowserSession

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
	raise ValueError('OPENAI_API_KEY is not set')

browser_session = BrowserSession(
	headless=False,
	#user_data_dir="C:/Users/anpro/.config/browseruse/profiles/Andeptrai",
)
controller = Controller()


async def main():
	task = 'Go to google. Done task'
	model = ChatOpenAI(model='gpt-4o-mini', api_key=SecretStr(api_key))
	agent = Agent(
		task=task,
		llm=model,
		controller=controller,
		browser_session=browser_session,
	)

	await agent.run()
	#await browser_session.close()



if __name__ == '__main__':
	asyncio.run(main())