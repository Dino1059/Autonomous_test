# AutoTester API Architecture Documentation

## Overview
The AutoTester API is a FastAPI-based service for browser automation testing. It provides endpoints for managing and executing browser automation tasks, templates, actions, and settings.

## Architecture Diagram
```
[Client] ──────────────────────────┐
                                   ▼
┌───────────────────────────────────────────────────┐
│                 FastAPI Server                    │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
│ │  /tasks     │ │ /templates  │ │  /actions   │  │
│ │  Endpoints  │ │  Endpoints  │ │  Endpoints  │  │
│ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘  │
│        │               │               │         │
│ ┌──────▼───────────────▼───────────────▼──────┐  │
│ │              Controller Layer              │  │
│ │  - Tasks Controller                        │  │
│ │  - Templates Controller                    │  │
│ │  - Actions Controller                      │  │
│ │  - Settings Controller                     │  │
│ └──────────────────────┬────────────────────┘  │
│                         │                       │
│ ┌───────────────────────▼─────────────────────┐ │
│ │           Background Task System            │ │
│ │  - Task Execution                           │ │
│ │  - Task Status Tracking                     │ │
│ │  - Cancellation Management                  │ │
│ └──────────────────────┬────────────────────┘  │
└─────────────────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
┌─────────────────┐ ┌────────────┐ ┌─────────────────┐
│   LLM Services  │ │  Laminar   │ │ User Simulator  │
│ (Google/OpenAI) │ │    API     │ │                 │
└─────────────────┘ └────────────┘ └─────────────────┘
```

## Core Components

### 1. API Structure
- **Base URL**: `/` - Welcome endpoint
- **Main Routes**:
  - `/tasks` - Browser automation task management
  - `/templates` - Test templates management
  - `/actions` - Custom actions management
  - `/settings` - System settings management

### 2. API Endpoints

#### Tasks
- `POST /tasks/run` - Run automation tasks in the background
- `GET /tasks/{task_id}` - Get status and results of a specific task
- `POST /tasks/{task_id}/cancel` - Cancel a running task
- `GET /tasks` - Get a list of all tasks and their statuses

#### Templates
- Endpoints for creating, retrieving, updating, and deleting test templates

#### Actions
- Endpoints for managing custom automation actions

#### Settings
- Endpoints for managing system settings including environment variables

### 3. Data Models

#### Request Models
- `RunTaskRequest` - Configuration for running automation tasks
- `TaskConfig` - Task configuration including name, prompt, and LLM settings
- `CustomAction` - Custom action definition with name and code
- `EnvironmentVariablesRequest` - Settings for API keys

#### Response Models
- `DataResponse<T>` - Generic wrapper for all API responses
- `MessageResponse` - Simple message response
- `RunTaskResponse` - Results and history of task execution

### 4. Background Task System
- Tasks run asynchronously in the background
- Task status tracking via unique task IDs
- Support for cancellation of running tasks

### 5. Integration Points
- LLM providers (Google, OpenAI, OpenRouter)
- Laminar API for browser interaction
- User simulation capabilities

## Technical Implementation
- Built with FastAPI framework
- Pydantic models for request/response validation
- Background task processing
- CORS middleware enabled for all origins
