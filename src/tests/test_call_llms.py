import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.llms.base import BaseLLMWorker

def test_single_message():
    llm_worker = BaseLLMWorker("user_simulator")
    response = llm_worker.get_response("Hello, how are you?", "1")
    print("Response:", response)

def test_conversation():
    base_llm_worker = BaseLLMWorker("user_simulator")
    session_id = "test_session"

    # First message
    try:
        response = base_llm_worker.get_response("Hello, how are you?", session_id)
        print("First response:", response.content)
        
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
    # test_single_message()
    test_conversation()
