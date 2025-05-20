## Improvements (To-Do) 🛠️

* [ ] `actions.py` and `templates.py` can be merged into a single module.
* [ ] The `/routers` files can be merged or optimized.
* [ ] `TaskConfig`, `RunTaskRequest`, `CustomAction`, `DataResponse` contain some repeated code across files; this needs to be cleaned up for consistency.
* [ ] The cleaned serializers need to be updated in all files within `/utils`.
* [ ] There should be an optional flag for using `record_api.py`.
* [ ] The logger needs to be designed carefully to help collect insights.

---

## AI Agent Tester Architecture Documentation

### Overview
The application is a **FastAPI-based web service** designed for browser automation testing with AI agents. It allows users to run automated browser tests with different AI models and configurations. 🧪

---

### Directory Structure

#### Root Files
* `.env`: Environment configuration file with API keys and settings 🔑
* `init.py`: Package initialization file
* `main.py`: Application entry point that configures FastAPI, CORS, and routes 🚀
* `record_api.py`: API for recording agent interactions during testing 🎬

#### Core Directories

##### Controllers (`/controllers`)
Controllers handle the business logic of the application:
* `actions.py`: Manages browser actions and user interactions 🖱️
* `settings.py`: Handles configuration settings for the application ⚙️
* `tasks.py`: Core controller for managing browser automation tasks ✅
* `templates.py`: Manages test templates 📄

##### Routers (`/routers`)
Routers define the API endpoints:
* `init.py`: Main router that includes all sub-routers
* `tasks_router.py`: Routes for task management
* `templates_router.py`: Routes for template management
* `actions_router.py`: Routes for browser actions
* `settings_router.py`: Routes for application settings

##### Serializers (`/serializers`)
Serializers define the data models using Pydantic:
* `models.py`: Contains Pydantic models for all API requests and responses:
    * `TaskConfig`: Configuration for running automation tasks
    * `RunTaskRequest`: Request model for running tasks
    * `CustomAction`: Model for defining custom browser actions
    * `DataResponse`: Generic response wrapper

##### Utils (`/utils`)
Utility functions to support the application:
* `browser_actions.py`: Implements browser interaction functions 🌐
* `globals.py`: Global variables and state management 🌍
* `llm_utils.py`: Utilities for working with LLM providers 🤖
* `prompts.py`: Prompt templates for LLM interactions 📝
* `task_execution.py`: Core logic for executing browser automation tasks 🛠️

##### Templates (`/templates`)
Contains HTML templates for the application UI. 🖼️

##### Recordings (`/recordings`)
Stores test execution recordings and results. 📼

---

### Key Components

#### Task Execution Flow
1.  User submits a task via `/tasks/run` endpoint.
2.  Task is assigned a unique ID and executed in the background.
3.  Browser automation is performed using the `browser_use` library.
4.  Results are stored in memory and can be retrieved via the `/tasks/{task_id}` endpoint.

#### LLM Integration
* The application supports multiple LLM providers (**Google, OpenAI, OpenRouter**).
* LLM models are used for:
    * User simulation during testing
    * Task execution and decision making
    * Result analysis and reporting

#### Browser Automation
* Browser interaction is handled through a **custom automation framework**.
* **Custom actions** can be registered and executed during tests.
* Screenshots and HTML content are captured during test execution. 📸

#### Data Flow
* Task configurations are defined using the `TaskConfig` model.
* Controllers process these configurations and initialize the necessary components.
* The task execution engine runs the tests in a background process.
* Results are stored in the `BACKGROUND_TASKS` global dictionary.
* API endpoints provide access to task status and results.