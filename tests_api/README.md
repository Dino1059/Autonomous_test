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
        {
          "open_tab": {
            "url": "https://example.com"
          }
        }
      ],
      "use_vision_for_planner": True,
      "planner_interval": 1,
      "is_planner_reasoning": True,
      "planner_llm": {
        "provider": "openai",
        "model": "gpt-4.1",
        "temperature": 0.0
      },
      "report_config": {
        "provider": "google",
        "model": "gemini-2.0-flash",
        "temperature": 0.2,
        "is_report_reasoning": False,
        "extend_report_system_message": "Include code samples when relevant.",
        "use_vision_for_report": False,
        "report_folder": "E:/official_DopikAI/ai-agent-tester/tests_api/demo_simple"
      }
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
  "custom_actions": [],
  "use_own_browser": True
}

```

**Field Descriptions**:

*Task Object Fields:*
| Field                    | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                   | **(String)** A descriptive name for the task.                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `prompt`                 | **(String)** Instructions for the AI agent to follow when executing the task.                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `max_steps`              | **(Integer)** Maximum number of steps the AI can take to complete the task.                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `output_model_fields`    | **(Object)** Optional JSON schema defining the structure of the desired output.                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `exclude_actions`        | **(Array)** Array of action types to disable for this task.                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `llm_provider`           | **(String)** Provider of the language model (e.g., `"google"`, `"openai"`).                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `llm_model`              | **(String)** Specific model to use (e.g., `"gemini-2.0-flash"`).                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `llm_temperature`        | **(Float)** Controls randomness of AI outputs (`0.0` = deterministic).                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `enable_memory`          | **(Boolean)** Whether to enable persistent memory across steps.                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `memory_interval`        | **(Integer)** Number of steps between memory snapshots.                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `initial_actions`        | **(Array)** Actions to perform before starting the task (e.g., opening URLs).                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `use_vision_for_planner` | **(Boolean)** Whether the planner can use vision-based inputs like screenshots during planning.                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `planner_interval`       | **(Integer)** Frequency (in steps) at which the planner LLM is invoked (e.g., `1` = every step).                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `is_planner_reasoning`   | **(Boolean)** Enables explicit reasoning by the planner when deciding the next action.                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `planner_llm`            | **(Object)** Configuration for the planner language model:<br> • `provider`: LLM provider (e.g., `"openai"`)<br> • `model`: Planner model (e.g., `"gpt-4.1"`)<br> • `temperature`: Controls planner output randomness.                                                                                                                                                                                                                                                                                               |
| `report_config`          | **(Object)** Configuration for the task report generation:<br> • `provider`: LLM provider for report (e.g., `"google"`)<br> • `model`: LLM used to generate the report<br> • `temperature`: Creativity of the report output<br> • `is_report_reasoning`: Whether to include reasoning in the report<br> • `extend_report_system_message`: Custom prompt to enrich report content<br> • `use_vision_for_report`: Whether to use visual inputs in the report<br> • `report_folder`: Filesystem path to save the report |




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
- `use_own_browser`: Use your browser with cookies and profile.

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