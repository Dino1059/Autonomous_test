# AutoTester WebUI - Key Features

AutoTester WebUI simplifies LLM-powered browser automation testing.

## Core features

### 1. Agent/Tester Creator

Define reusable test logic templates:

*   **Create/Manage:** Build, save, edit, delete, import/export agents/testers.
*   **Prompt Templates:** Craft agent/tester instructions using text and `{placeholder_N}` variables for data injection.
*   **LLM Config:** Select provider (Google, OpenAI, etc.), model, temperature, and max steps.
*   **Control:** Optionally use structured output models or exclude specific browser actions.
*   **Filter & View:** Easily find saved agents by type.

### 2. CSV Test Runner

Run data-driven tests using agents/testers and CSV files:

*   **Upload & Preview:** Load test data from `.csv` files (comma/tab separated) and preview content.
*   **Select Workflow:** Choose pre-defined agents and testers.
*   **Map Data:** Link `{placeholder_N}` variables in agent/tester prompts to columns in your CSV.
*   **Configure:** Set the target URL and session ID for the test run.
*   **Preview & Run:** Validate setup and execute the agent workflow row-by-row from the CSV.
*   **Track & Analyze:** Monitor progress, view status per test case, inspect detailed results (including tester interactions and errors) in a modal, and export all results to JSON.

### 3. Settings

Configure necessary credentials and connection details:

*   **API Keys:** Enter and save keys for OpenAI and Google Gemini.
*   **Laminar:** Configure the API key, base URL, HTTP port, and gRPC port for tracking browser automation service.

## Installation

Only Browser-Use is needed. See the installation instructions at https://github.com/browser-use/browser-use.
