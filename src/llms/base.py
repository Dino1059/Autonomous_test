"""
Worker LLMs - Lightweight models for simulating user and assistant behavior.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from dotenv import load_dotenv

load_dotenv()

settings = {
    # Server settings
    "laminar_project_api_key": "hcAzTvWi7Tyvpjnwpgcnd3liW35GX3tpPGiDFXtNwOaiBEkKhK6binwADLMAlaNa",
    "laminar_base_url": "http://localhost",
    "laminar_http_port": 9000,
    "laminar_grpc_port": 9001,
    "web_app_url": "http://localhost:8501/",
    
    # LLM settings
    "default_llm_model": "gemini-2.0-flash",
    "default_llm_provider": "google",  # options: google, openai, openrouter
    "openai_model": "gpt-4o-mini",
    "openrouter_model": "qwen/qwq-32b:free",
}

load_dotenv()

class InMemoryHistory(BaseChatMessageHistory, BaseModel):
    """In memory implementation of chat message history."""
    messages: List[BaseMessage] = Field(default_factory=list)

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Add a list of messages to the store"""
        self.messages.extend(messages)

    def clear(self) -> None:
        """Clear all messages from the store"""
        self.messages = []

class BaseLLMWorker:
    def __init__(
        self, 
        provider: str,
        model: str,
        **kwargs
    ):
        # Extract optional parameters with defaults
        temperature = kwargs.get("temperature", 0)
        top_p = kwargs.get("top_p", 1.0)
        top_k = kwargs.get("top_k", 40)
        max_output_tokens = kwargs.get("max_output_tokens", 2048)
        
        # Initialize appropriate LLM based on provider
        if provider == "google":
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                max_output_tokens=max_output_tokens,
                google_api_key=os.getenv('GEMINI_API_KEY')
            )
        elif provider == "openai":
            self.llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                openai_api_key=os.getenv('OPENAI_API_KEY')
            )
        elif provider == "openrouter":
            self.llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=os.getenv('OPENAI_API_KEY'),
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
            
        # Initialize store for message history
        self.store: Dict[str, BaseChatMessageHistory] = {}

        # Create chat prompt with system message and history
        self.chat_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}")
        ])

        # Configure chain with history management
        self.chain = RunnableWithMessageHistory(
            self.chat_prompt | self.llm,
            self.get_session_history,
            input_messages_key="question",
            history_messages_key="history",
        )

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Get or create chat history for a session"""
        if session_id not in self.store:
            self.store[session_id] = InMemoryHistory()
        return self.store[session_id]

    def get_response(self, input_text: str, session_id: str) -> str:
        """Get response from LLM with history management"""
        try:
            response = self.chain.invoke(
                {"question": input_text},
                config={"configurable": {"session_id": session_id}}
            )
            return response
        except Exception as e:
            logger.error(f"Error getting LLM response: {e}")
            raise

    def clear_history(self, session_id: str) -> None:
        """Clear history for a specific session"""
        if session_id in self.store:
            self.store[session_id].clear()

def main():
    """Main function for testing the LLM workers."""
    base_llm_worker = BaseLLMWorker(
        provider="openrouter",
        model="thudm/glm-z1-32b:free",
        temperature=0.0,
        top_p=1.0,
        top_k=40,
        max_output_tokens=2048,
    )
    session_id = settings["session_id"]

    # First message
    try:
        response = base_llm_worker.get_response("Hello, how are you?", session_id)
        print("First response:", response)
        
        # Print current history
        history = base_llm_worker.get_session_history(session_id)
        print(history)
        print('---------------------------------------------------------')
    except Exception as e:
        print(f"Failed first message: {e}")

    # Second message referencing history
    try:
        response = base_llm_worker.get_response("What did you just say?", session_id)
        print("Second response:", response)
        
        # Print updated history
        history = base_llm_worker.get_session_history(session_id)
        print(history)
        print(type(history))
        print('---------------------------------------------------------')
    except Exception as e:
        print(f"Failed second message: {e}")

if __name__ == "__main__":
    print(os.getenv("OPENAI_API_KEY"))
    main()

