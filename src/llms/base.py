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
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
import base64
import requests
from io import BytesIO

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
                google_api_key=os.getenv('GOOGLE_API_KEY')
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
            ("human", "{input}"),
            ("placeholder", "{image}")
        ])

        # Configure chain with history management
        self.chain = RunnableWithMessageHistory(
            self.chat_prompt | self.llm,
            self.get_session_history,
            history_messages_key="history",
        )

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Get or create chat history for a session"""
        if session_id not in self.store:
            self.store[session_id] = InMemoryHistory()
        return self.store[session_id]

    def get_response(self, input_text: str, session_id: str, image_urls: List[str] = None) -> str:
        """Get response from LLM with history management, potentially including multiple images."""
        try:
            if image_urls and isinstance(image_urls, list) and len(image_urls) > 0:
                # For multimodal input, prepare a list of image content parts
                image_content_parts = []
                
                # Download and convert each image to base64
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                
                for image_url in image_urls:
                    response = requests.get(image_url, headers=headers)
                    response.raise_for_status()
                    image_data = response.content
                    base64_encoded_data = base64.b64encode(image_data).decode("UTF-8")
                    
                    # Add this image to the content parts
                    image_content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_encoded_data}"}
                    })
                
                # Construct the content parts with all images
                current_input_content = [
                    ("human", image_content_parts)
                ]

                response = self.chain.invoke(
                    {"input": input_text, "image": current_input_content},
                    config={"configurable": {"session_id": session_id}}
                )
                return response.content
            else:
                response = self.chain.invoke(
                   {"input": input_text},
                   config={"configurable": {"session_id": session_id}}
                )
                return response.content
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
        model="google/gemini-2.0-flash-exp:free",
        temperature=0.0,
        top_p=1.0,
        top_k=40,
        max_output_tokens=2048,
    )
    session_id = "test-session"
    # First message
    # try:
    #     response = base_llm_worker.get_response("Hello, how are you?", session_id)
    #     print("First response:", response)
        
    #     print('---------------------------------------------------------')
    # except Exception as e:
    #     print(f"Failed first message: {e}")

    # # Second message referencing history
    # try:
    #     response = base_llm_worker.get_response("What did you just say?", session_id)
    #     print("Second response:", response)
        
    #     print('---------------------------------------------------------')
    # except Exception as e:
    #     print(f"Failed second message: {e}")

    # Third message with image
    try:
        # Test with multiple images
        image_urls = [
            "https://upload.wikimedia.org/wikipedia/commons/b/b6/Image_created_with_a_mobile_phone.png",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"
        ]
        response = base_llm_worker.get_response(
            "Describe both images you see. What are the main differences between them?", 
            session_id, 
            image_urls
        )
        print("Multiple images response:", response)
        print('---------------------------------------------------------')
    except Exception as e:
        print(f"Failed multiple images test: {e}")

    # Fourth message - follow-up question
    try:    
        response = base_llm_worker.get_response("Which image showed a mobile phone?", session_id)
        print("Follow-up response:", response)
        print('---------------------------------------------------------')
    except Exception as e:
        print(f"Failed follow-up question: {e}") 

if __name__ == "__main__":
    print(os.getenv("OPENAI_API_KEY"))
    main()

