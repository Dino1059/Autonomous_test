"""
Tasks controller for managing browser automation tasks
"""
import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict, Any, List

from app.serializers.models import RunTaskRequest, MessageResponse, DataResponse, RunTaskResponse, GeneratePlanRequest, GeneratePlanResponse
from app.utils.globals import BACKGROUND_TASKS, CANCELLATION_FLAGS
from app.utils.task_execution import run_tasks_background

router = APIRouter()

@router.post("/generate-plan", response_model=DataResponse[GeneratePlanResponse])
async def generate_plan_endpoint(request: GeneratePlanRequest):
    """Generate a structured test plan from natural language prompt"""
    prompt = request.prompt
    
    # Infer target URL from prompt or use standard fallback
    target_url = "https://test.com/forgot-password"
    import re
    urls = re.findall(r'https?://[^\s]+', prompt)
    if urls:
        target_url = urls[0]
    elif "github" in prompt.lower():
        target_url = "https://github.com/login"
    elif "login" in prompt.lower():
        target_url = "https://app.example.com/login"
        
    steps = [
        {"id": 1, "action": "Open Target URL", "selector": target_url, "expected": "Page loads with 200 OK status code"},
        {"id": 2, "action": "Inspect Input Fields", "selector": "form input", "expected": "Input fields identified by DOM agent"},
        {"id": 3, "action": "Fill Form Credentials", "selector": "#email-input, #password-input", "expected": "Test payload injected into input elements"},
        {"id": 4, "action": "Trigger Submit Button", "selector": "button[type='submit']", "expected": "HTTP request sent and 200 OK payload returned"},
        {"id": 5, "action": "Verify UI Response Toast", "selector": ".toast, .alert-success", "expected": "Success visual state verified"},
        {"id": 6, "action": "Validate API Network Log", "selector": "POST /api/auth/verify", "expected": "JSON schema and response latency verified"}
    ]
    
    plan = GeneratePlanResponse(
        title=f"Autonomous E2E Test - {prompt[:30]}...",
        objective=f"Execute end-to-end multi-agent verification for: '{prompt}'",
        target_url=target_url,
        preconditions=["Environment service health verified", "Headless browser session ready"],
        test_data={"user": "demo_tester@test.com", "session": "active_token"},
        steps=steps
    )
    return DataResponse(data=plan, message="Generated test plan successfully")

@router.post("/run", response_model=DataResponse[MessageResponse])
async def run_tasks_endpoint(request: RunTaskRequest, background_tasks: BackgroundTasks):
    """Run tasks in the background and return a task ID"""
    # Generate a unique task ID
    task_id = str(uuid.uuid4())
    
    # Initialize task status in global storage
    BACKGROUND_TASKS[task_id] = {"status": "running"}
    
    # Convert CustomAction objects to dictionaries
    custom_actions_dict = [action.model_dump() for action in request.custom_actions]
    
    # Start the task in the background
    background_tasks.add_task(
        run_tasks_background,
        task_id,
        [task.model_dump() for task in request.tasks],
        request.laminar_api_key,
        request.laminar_base_url,
        request.laminar_http_port,
        request.laminar_grpc_port,
        request.session_id,
        request.simulator_provider,
        request.simulator_model,
        request.simulator_temperature,
        request.simulator_task,
        custom_actions_dict,
        request.browser_config
    )
    
    return DataResponse(data=MessageResponse(message=f"Task started with ID: {task_id}"))

@router.get("/{task_id}", response_model=DataResponse[Dict[str, Any]])
async def get_task_status(task_id: str):
    """Get the status and real-time results of a task"""
    if task_id not in BACKGROUND_TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    
    response_data = dict(BACKGROUND_TASKS[task_id])
    
    # Merge active orchestrator context if running
    from app.utils.globals import ACTIVE_ORCHESTRATORS
    orchestrator = ACTIVE_ORCHESTRATORS.get(task_id)
    if orchestrator and hasattr(orchestrator, "context"):
        ctx = orchestrator.context
        response_data["status"] = ctx.status
        response_data["current_step_index"] = ctx.current_step_index
        response_data["sub_goals"] = ctx.sub_goals
        response_data["execution_logs"] = ctx.execution_logs
        response_data["browser_snapshots"] = ctx.browser_snapshots
        response_data["active_agent"] = "BrowserExecutor" if ctx.status == "running" else ("UserSimulator" if "waiting" in ctx.status else "Planner")

    return DataResponse(data=response_data)


@router.post("/{task_id}/cancel", response_model=DataResponse[MessageResponse])
async def cancel_task(task_id: str):
    """Cancel a running task"""
    import logging
    logger = logging.getLogger("CANCEL_TASK")
    
    if task_id not in BACKGROUND_TASKS:
        logger.warning(f"Cancellation requested for non-existent task {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_status = BACKGROUND_TASKS[task_id].get("status", "unknown")
    logger.info(f"Cancellation requested for task {task_id} with current status: {task_status}")
    
    if task_status == "completed":
        logger.warning(f"Cannot cancel completed task {task_id}")
        raise HTTPException(status_code=400, detail="Task is already completed and cannot be cancelled")
    
    if task_status == "failed":
        logger.warning(f"Cannot cancel failed task {task_id}")
        raise HTTPException(status_code=400, detail="Task already failed and cannot be cancelled")
    
    if task_status == "cancelled":
        logger.info(f"Task {task_id} was already cancelled")
        return DataResponse(data=MessageResponse(message=f"Task {task_id} was already cancelled"))
    
    if task_status != "running" and task_status != "cancelling":
        logger.warning(f"Cannot cancel task {task_id} with status {task_status}")
        raise HTTPException(status_code=400, detail=f"Task is in state '{task_status}' and cannot be cancelled")
    
    # Set cancellation flag to signal the task to stop
    CANCELLATION_FLAGS[task_id] = True
    logger.info(f"Set cancellation flag for task {task_id} to True")
    
    # Set task status to cancelling
    BACKGROUND_TASKS[task_id]["status"] = "cancelling"
    BACKGROUND_TASKS[task_id]["message"] = "Cancellation requested by user"
    logger.info(f"Updated task {task_id} status to 'cancelling'")
    
    return DataResponse(data=MessageResponse(message=f"Task {task_id} cancellation requested, please check status endpoint for updates"))

@router.get("", response_model=DataResponse[Dict[str, Any]])
async def get_all_tasks():
    """Get a list of all tasks and their statuses"""
    task_list = {}
    
    for task_id, task_data in BACKGROUND_TASKS.items():
        # Extract just the status and some basic info
        status = task_data.get("status", "unknown")
        
        task_summary = {
            "status": status,
            "message": task_data.get("message", ""),
        }
        
        # Add some details based on the status
        if status == "completed":
            # Get count of results if available
            results = task_data.get("results", [])
            task_summary["result_count"] = len(results)
        elif status == "failed":
            # Add error message but not full traceback
            task_summary["error"] = task_data.get("error", "Unknown error")
        
        task_list[task_id] = task_summary
    
    return DataResponse(data={
        "tasks": task_list,
        "count": len(task_list)
    })

@router.post("/{task_id}/human-input", response_model=DataResponse[MessageResponse])
async def submit_human_input(task_id: str, payload: Dict[str, Any]):
    """Submit human input / approval to a waiting multi-agent task"""
    from app.utils.globals import ACTIVE_ORCHESTRATORS
    if task_id not in BACKGROUND_TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
        
    orchestrator = ACTIVE_ORCHESTRATORS.get(task_id)
    if not orchestrator:
        raise HTTPException(status_code=400, detail="Active orchestrator not found for task")
        
    await orchestrator.provide_human_input(payload)
    return DataResponse(data=MessageResponse(message=f"Human input submitted successfully for task {task_id}"))

@router.post("/{task_id}/pause", response_model=DataResponse[MessageResponse])
async def pause_task_endpoint(task_id: str):
    """Pause a running multi-agent task"""
    from app.utils.globals import ACTIVE_ORCHESTRATORS
    orchestrator = ACTIVE_ORCHESTRATORS.get(task_id)
    if not orchestrator:
        raise HTTPException(status_code=400, detail="Active orchestrator not found for task")
        
    await orchestrator.pause_task()
    BACKGROUND_TASKS[task_id]["status"] = "paused"
    return DataResponse(data=MessageResponse(message=f"Task {task_id} paused"))

@router.post("/{task_id}/resume", response_model=DataResponse[MessageResponse])
async def resume_task_endpoint(task_id: str):
    """Resume a paused multi-agent task"""
    from app.utils.globals import ACTIVE_ORCHESTRATORS
    orchestrator = ACTIVE_ORCHESTRATORS.get(task_id)
    if not orchestrator:
        raise HTTPException(status_code=400, detail="Active orchestrator not found for task")
        
    await orchestrator.resume_task()
    BACKGROUND_TASKS[task_id]["status"] = "running"
    return DataResponse(data=MessageResponse(message=f"Task {task_id} resumed"))

@router.get("/history/runs", response_model=DataResponse[List[Dict[str, Any]]])
async def get_test_runs_history():
    """Get persistent test runs history from SQLite database"""
    from app.db.database import get_all_test_runs
    runs = get_all_test_runs(limit=50)
    return DataResponse(data=runs, message="Retrieved test runs history")

@router.get("/history/runs/{run_id}", response_model=DataResponse[Dict[str, Any]])
async def get_test_run_detail(run_id: str):
    """Get persistent test run detail from SQLite database"""
    from app.db.database import get_test_run_by_id
    run = get_test_run_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found in database")
    return DataResponse(data=run, message="Retrieved test run details")


# ── Task 1.1: Alias /run-steps → logic của /run (FE compatibility) ─────────
@router.post("/run-steps", response_model=DataResponse[MessageResponse])
async def run_steps_alias(request: RunTaskRequest, background_tasks: BackgroundTasks):
    """Alias endpoint cho FE gọi /tasks/run-steps — delegates sang run_tasks_endpoint"""
    return await run_tasks_endpoint(request, background_tasks)


# ── Task 1.2: Stream task đang chạy gần nhất (FE gọi /tasks/stream/latest) ─
@router.get("/stream/latest")
async def stream_latest_task_events():
    """Stream SSE events của task đang running gần nhất — FE compatibility"""
    from fastapi.responses import StreamingResponse
    import json
    import asyncio

    # Tìm task đang running
    running = [
        (tid, td) for tid, td in BACKGROUND_TASKS.items()
        if td.get("status") == "running"
    ]

    async def empty_stream():
        yield 'data: {"status": "no_active_task"}\n\n'

    if not running:
        return StreamingResponse(empty_stream(), media_type="text/event-stream")

    # Lấy task mới nhất theo thứ tự xuất hiện cuối cùng
    latest_task_id = running[-1][0]

    async def event_generator(task_id: str):
        for _ in range(120):  # timeout 120 giây
            await asyncio.sleep(1)
            task_data = BACKGROUND_TASKS.get(task_id, {})
            status = task_data.get("status", "unknown")
            payload = {"task_id": task_id, "status": status}
            yield f"data: {json.dumps(payload)}\n\n"
            if status in ("completed", "failed", "cancelled"):
                break

    return StreamingResponse(
        event_generator(latest_task_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )