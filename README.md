# Core API for AutoTesterWebUI

## Features

- **Browser Automation**: Execute complex web testing tasks with Browser-use
- **Task Management**: Run, monitor, and cancel automation tasks via API
- **Action Templates**: Predefined templates for common browser interactions 
- **Custom Actions**: Create and execute custom browser automation scripts
- **User Simulation**: Simulate user behavior for interactive testing
- **REST API**: FastAPI-based endpoints with comprehensive documentation

## Playround
See the `test_api` for examples how to use API.

## Installation Guide

```bash
# Clone the repository
git clone https://github.com/DopikAI-Labs/ai-agent-tester/tree/dev/core-api
cd ai-agent-tester

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```
### Run API
```bash
cd app
python main.py --port 8000
```

## Project Structure

```
app/
├── controllers/       # Business logic for handling API requests
│   ├── actions.py     # Available browser automation actions
│   ├── tasks.py       # Task execution and management
│   └── templates.py   # Template management for custom actions
├── routers/           # API route definitions
│   ├── actions_router.py
│   ├── tasks_router.py
│   └── templates_router.py
├── serializers/       # Data models and schemas
│   └── models.py      # Pydantic models for request/response validation
├── utils/             # Helper functions and utilities
│   ├── browser_actions.py  # Browser interaction implementations
│   ├── globals.py          # Global variables and state management
│   ├── llm_utils.py        # LLM integration utilities
│   └── task_execution.py   # Background task execution logic
└── main.py            # FastAPI application entry point
```

### Key Components

- **main.py**: Initializes the FastAPI application, configures middleware, and includes routers
- **controllers/**: Contains the business logic for the application
  - **actions.py**: Defines available browser automation actions like clicking, scrolling, etc.
  - **tasks.py**: Manages the execution of automation tasks with background processing
  - **templates.py**: Provides reusable code templates for custom automation actions
- **routers/**: Defines API endpoints and routes requests to appropriate controllers
- **serializers/models.py**: Contains Pydantic models for request/response validation and type safety
- **utils/**: Helper functions and utilities
  - **browser_actions.py**: Core implementation of browser automation capabilities
  - **globals.py**: Manages global state and shared resources
  - **llm_utils.py**: Integration with language models for simulation
  - **task_execution.py**: Background task processing logic
