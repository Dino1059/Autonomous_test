import asyncio
import os
import json
import base64
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent
from app.utils.llm_utils import generate_report

load_dotenv()

# Initialize the model
llm = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash',
    temperature=0.0,
    google_api_key=os.getenv('GOOGLE_API_KEY')
)

report_config = {
    "report_folder": "E:/official_DopikAI/ai-agent-tester/tests_api/demo_simple",
    "is_report_reasoning": False,
    "extend_report_system_message": "Include code samples when relevant.",
    "use_vision_for_report": False,
    "reporter": llm,
    "state": None
}


task = "Search openai"


agent = Agent(
    task=task,
    llm=llm,
    use_vision=True,
)

async def main():
    await agent.run()
    print(agent.state)
    report_config["state"] = agent.state
    await generate_report(
        task=task,
        **report_config
    )
    

if __name__ == '__main__':
    asyncio.run(main())
