# AutoTester API Tests

This directory contains test scripts for the AutoTester API.

## Setting Up

1. Create a `.env` file in this directory with the following variables:

```
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Target URL for testing (required)
TARGET_URL=http://localhost:8501

# Laminar settings (optional)
LAMINAR_API_KEY=your_laminar_api_key_here
LAMINAR_BASE_URL=http://localhost:8000
LAMINAR_HTTP_PORT=8000
LAMINAR_GRPC_PORT=50051
```

2. Install required packages:

```
pip install requests python-dotenv
```

## Available Tests

The tests directory includes the following test files:

- `basic_tasks.py`: Tests basic task execution and multiple tasks in a sequence
- `task_cancellation.py`: Tests the ability to cancel running tasks
- `user_simulator.py`: Tests the user simulator functionality
- `custom_actions.py`: Tests the ability to register and use custom actions
- `custom_outputmodel.py`: Tests the custom output model functionality


## Note on Test Environment

Make sure the AutoTester API is running at `http://localhost:8081` before running these tests. 
If your API is running on a different URL, update the `API_BASE_URL` variable in each test file.

The `TARGET_URL` in your `.env` file should point to an appropriate application for testing the AutoTester functionality. 
For testing chat functionality, use a URL that has a chat interface. 