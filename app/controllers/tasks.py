"""
Tasks controller for managing browser automation tasks
"""
import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict, Any, List

from app.serializers.models import RunTaskRequest, MessageResponse, DataResponse, RunTaskResponse
from app.utils.globals import BACKGROUND_TASKS, CANCELLATION_FLAGS
from app.utils.task_execution import run_tasks_background

router = APIRouter()

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
        request.use_own_browser
    )
    
    return DataResponse(data=MessageResponse(message=f"Task started with ID: {task_id}"))

@router.get("/{task_id}", response_model=DataResponse[Dict[str, Any]])
async def get_task_status(task_id: str):
    """Get the status and results of a task"""
    if task_id not in BACKGROUND_TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return DataResponse(data=BACKGROUND_TASKS[task_id])

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