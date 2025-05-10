# AutoTester API Tests

This directory contains test scripts for the AutoTester API.

## API Format

### Starting Tasks
- **Endpoint**: `POST /tasks/run`
- **Description**: Initiates one or more tasks to be executed sequentially

**Request Body**:
```json
{
  "tasks": [
    {
      "name": "Task Name",
      "prompt": "Instructions for the AI to execute",
      "max_steps": 20,
      "output_model_fields": {
        // Optional JSON schema for structured output
      },
      "exclude_actions": [],
      "llm_provider": "google",
      "llm_model": "gemini-2.0-flash",
      "llm_temperature": 0.0,
      "enable_memory": false,
      "memory_interval": 10,
      "initial_actions": [
        {"open_tab": {"url": "https://example.com"}}
      ]
    }
  ],
  "laminar_api_key": "your_laminar_api_key",
  "laminar_base_url": "http://localhost:8000",
  "laminar_http_port": 8000,
  "laminar_grpc_port": 50051,
  "session_id": "unique_session_identifier",
  "simulator_provider": "google",
  "simulator_model": "gemini-2.0-flash",
  "simulator_temperature": 0.0,
  "simulator_task": "",
  "custom_actions": []
}
```

**Field Descriptions**:

*Task Object Fields:*
- `name` - A descriptive name for the task
- `prompt` - Instructions for the AI agent to follow when executing the task
- `max_steps` - Maximum number of steps the AI can take to complete the task
- `output_model_fields` - Optional JSON schema defining the structure of the desired output
- `exclude_actions` - Array of action types to disable for this task
- `llm_provider` - Provider of the language model (e.g., "google", "openai")
- `llm_model` - Specific model to use (e.g., "gemini-2.0-flash")
- `llm_temperature` - Controls randomness of AI outputs (0.0 = deterministic)
- `enable_memory` - Whether to enable persistent memory across steps
- `memory_interval` - Number of steps between memory snapshots
- `initial_actions` - Actions to perform before starting the task (e.g., opening URLs)

*Top-level Fields:*
- `tasks` - Array of task objects to be executed sequentially
- `laminar_api_key` - API key for accessing Laminar browser automation service
- `laminar_base_url` - Base URL of the Laminar service
- `laminar_http_port` - HTTP port for Laminar service
- `laminar_grpc_port` - gRPC port for Laminar service
- `session_id` - Unique identifier for the browser session
- `simulator_provider` - Provider for the user simulator LLM
- `simulator_model` - Model to use for user simulation
- `simulator_temperature` - Temperature setting for simulator responses
- `simulator_task` - Instructions for the user simulator (if enabled)
- `custom_actions` - Array of custom actions available to the AI agent

**Response**:
```json
{
  "data": {
    "message": "Task started: task_id_here"
  }
}
```

### Checking Task Status
- **Endpoint**: `GET /tasks/{task_id}`
- **Description**: Retrieves the current status and results of a task

**Response**:
```json
{
  "data": {
    "status": "completed|running|failed|cancelled",
    "results": {
      // Task output data (if completed)
    },
    "error": "Error message (if failed)"
  }
}
```

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

Make sure the AutoTester API is running at `http://localhost:8000` before running these tests. 
If your API is running on a different URL, update the `API_BASE_URL` variable in each test file.

The `TARGET_URL` in your `.env` file should point to an appropriate application for testing the AutoTester functionality. 
For testing chat functionality, use a URL that has a chat interface. 