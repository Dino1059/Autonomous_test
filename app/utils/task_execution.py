"""
Utility functions for task execution and management
"""
import os
import sys
import json
import asyncio
import logging
import traceback
import inspect
from typing import Dict, Any, List, Tuple, Optional

from browser_use import Agent, Controller
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext
from browser_use.agent.views import ActionResult
from playwright.sync_api import ElementHandle
import pyperclip
from src.llms.base import BaseLLMWorker

from app.utils.globals import SETTINGS, BACKGROUND_TASKS, USER_SIMULATOR_INTERACTIONS, CANCELLATION_FLAGS, get_or_initialize_llm_worker
from app.utils.browser_actions import paste_from_clipboard, call_user_simulator, get_system_message, click_the_send_button, sanitize_response
from app.utils.llm_utils import create_llm_for_task, create_model_from_schema
from app.serializers.models import MetadataCampaign, TaskConfig

import json_repair


async def run_tasks(
    tasks: List[Dict[str, Any]],
    laminar_api_key: str,
    laminar_base_url: str,
    laminar_http_port: int,
    laminar_grpc_port: int,
    session_id: str,
    sim_provider: str,
    sim_model: str,
    sim_temperature: float,
    simulator_task: str,
    custom_actions: List[Dict[str, str]] = [],
    task_id: str = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Run multiple browser automation tasks with specified settings in the same browser context"""
    
    # Set up logging for LLM initialization
    logger = logging.getLogger("RUN_TASKS")
    logger.info(f"Initializing LLM worker with provider: {sim_provider}, model: {sim_model}, temperature: {sim_temperature}, task: {simulator_task}")
    
    # Update settings with API values
    SETTINGS.update({
        "laminar_project_api_key": laminar_api_key,
        "laminar_base_url": laminar_base_url,
        "laminar_http_port": laminar_http_port,
        "laminar_grpc_port": laminar_grpc_port,
        "session_id": session_id,
        "user_simulator_task": simulator_task,
        "simulator_provider": sim_provider,
        "simulator_model": sim_model,
        "simulator_temperature": sim_temperature
    })
    
    # Initialize the LLM worker with the specified provider
    try:
        llm_worker = get_or_initialize_llm_worker(
            provider=sim_provider,
            model=sim_model,
            temperature=sim_temperature
        )
        
        if llm_worker is None:
            raise Exception(f"Failed to initialize LLM worker with provider: {sim_provider}, model: {sim_model}")
            
        logger.info("LLM worker initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing LLM worker: {str(e)}")
        return [{"status": "failed", "message": f"Failed to initialize LLM worker: {str(e)}"}], []
    
    # Initialize Laminar
    if SETTINGS["laminar_project_api_key"] and SETTINGS["laminar_base_url"]:
        from lmnr import Laminar
        Laminar.initialize(
            project_api_key=SETTINGS["laminar_project_api_key"],
            base_url=SETTINGS["laminar_base_url"],
            http_port=SETTINGS["laminar_http_port"],
            grpc_port=SETTINGS["laminar_grpc_port"],
        )
        logger.info("Laminar initialized successfully")
    else:
        logger.info("Laminar initialization skipped - API key or base URL not provided")
    
    
    try:
        all_results = []
        all_history = []
        
        # Initialize cancellation check
        if task_id:
            # Ensure cancellation flag is initialized properly
            if task_id not in CANCELLATION_FLAGS:
                CANCELLATION_FLAGS[task_id] = False
            # Add early check for cancellation before starting
            if CANCELLATION_FLAGS.get(task_id, False):
                logger.info(f"Task {task_id} was cancelled before execution. Aborting.")
                return [{"status": "cancelled", "message": "Task cancelled before execution"}], []
                
        # Initialize browser
        browser = Browser()
        async with await browser.new_context() as context:
            # Loop through tasks and execute them in the same context
            for i, task in enumerate(tasks):
                # Check if the task has been cancelled
                if task_id and CANCELLATION_FLAGS.get(task_id, False):
                    logger.info(f"Task {task_id} has been cancelled. Stopping execution.")
                    return [{"status": "cancelled", "message": "Task cancelled during execution"}], []
                
                from app.serializers.models import TaskConfig
                task_config = TaskConfig.model_validate(task)
                
                # Create a new controller for this task
                output_model = None
                if task_config.output_model_fields:
                    output_model = create_model_from_schema(task_config.output_model_fields)
                else:
                    output_model = None
                
                controller = Controller(
                    output_model=output_model, 
                    exclude_actions=task_config.exclude_actions
                )
                
                # Register built-in actions with this controller
                register_controller_actions(controller)
                
                # Register custom actions if any
                for action in custom_actions:
                    try:
                        register_custom_action(controller, action)
                    except Exception as e:
                        print(f"Error registering custom action: {e}")

                # Create the LLM for this specific task
                llm = create_llm_for_task(task_config)
                
                # Create agent with task
                agent = Agent(
                    task=task_config.prompt,
                    llm=llm,
                    controller=controller,
                    browser_context=context,
                    enable_memory=task_config.enable_memory if task_config.enable_memory is not None else True,
                    memory_interval=task_config.memory_interval if task_config.memory_interval else 10,
                    initial_actions=task_config.initial_actions if task_config.initial_actions else None,
                )
                
                # Define a cancellation check callback
                async def check_cancellation():
                    if task_id and CANCELLATION_FLAGS.get(task_id, False):
                        logger.info(f"Task {task_id} has been cancelled during execution. Forcing agent to stop.")
                        return True
                    return False
                
                # Add cancellation check to agent
                agent.cancellation_check = check_cancellation
                
                # Run agent
                try:
                    # Create task for agent run so we can monitor cancellation separately
                    agent_run_task = asyncio.create_task(agent.run(max_steps=task_config.max_steps))
                    
                    # Monitor the agent task and check for cancellation
                    while not agent_run_task.done():
                        # Check for cancellation every 0.5 seconds
                        if task_id and CANCELLATION_FLAGS.get(task_id, False):
                            logger.info(f"Cancellation detected for task {task_id}, aborting agent run.")
                            # Call agent.stop() first to properly stop the agent
                            agent.stop()
                            logger.info(f"Called agent.stop() for task {task_id}")
                            # Wait a moment for the stop to take effect
                            await asyncio.sleep(1.0)
                            # If the task is still not done, cancel it
                            if not agent_run_task.done():
                                agent_run_task.cancel()
                                logger.info(f"Cancelled agent task for {task_id} after calling stop()")
                            # Return early with cancellation status
                            return [{"status": "cancelled", "message": "Task cancelled during agent execution"}], []
                        
                        # Wait a short time before checking again
                        await asyncio.sleep(0.5)
                    
                    # Get the result if task completed successfully
                    history = await agent_run_task
                    
                    # Get results
                    final_result = history.final_result()
                    final_result = json_repair.loads(final_result)
                    
                    # Simply convert the history to a string
                    history_info = {
                        "history_type": str(type(history)),
                        "history_dir": str(dir(history)),
                        "history_methods": {name: str(method) for name, method in inspect.getmembers(history, predicate=inspect.ismethod)},
                    }
                    
                    # Try to get history as a dictionary
                    try:
                        if hasattr(history, "__dict__"):
                            history_dict = history.__dict__
                        elif hasattr(history, "model_dump"):
                            history_dict = history.model_dump()
                        else:
                            history_dict = {"info": "Could not convert history to dictionary"}
                        
                        # Convert to JSON-serializable format
                        history_json = json.loads(json.dumps(history_dict['history'], default=str))
                    except Exception as e:
                        history_json = {"history_error": str(e)}
                    
                    # Add to results
                    all_results.append({
                        "task_name": task_config.name,
                        "result": final_result
                    })
                    
                    all_history.append({
                        "history": history_json
                    })
                except asyncio.CancelledError:
                    logger.info(f"Agent task for {task_config.name} was cancelled.")
                    # Task was cancelled, check if we should continue with next task
                    if task_id and CANCELLATION_FLAGS.get(task_id, False):
                        logger.info(f"Task {task_id} was cancelled during execution, stopping all tasks.")
                        # Ensure agent is properly stopped
                        agent.stop()
                        return [{"status": "cancelled", "message": f"Task cancelled during '{task_config.name}' execution"}], []
                except Exception as e:
                    if task_id and CANCELLATION_FLAGS.get(task_id, False):
                        logger.info(f"Task {task_id} was cancelled during execution.")
                        # Ensure agent is properly stopped even on exception
                        agent.stop()
                        return [{"status": "cancelled", "message": f"Task cancelled during error handling for '{task_config.name}'"}], []
                    else:
                        logger.error(f"Error running task: {e}")
                        raise
            
            return all_results, all_history
    except Exception as e:
        traceback_str = traceback.format_exc()
        logger.error(f"Error in run_tasks: {traceback_str}")
        return [{"error": str(e), "traceback": traceback_str}], []
    finally:
        # Clean up cancellation flag if task is complete
        if task_id and task_id in CANCELLATION_FLAGS:
            CANCELLATION_FLAGS.pop(task_id)

def register_controller_actions(controller):
    """Register actions with the controller"""
    # Get the registry object
    registry = controller.registry
    
    # Register built-in actions by attaching the registry decorator
    registry.action('Always use this action everytime you see something like Paste text...')(paste_from_clipboard)
    registry.action('Call user simulator')(call_user_simulator)
    registry.action("Extract the system's message")(get_system_message)
    registry.action("Click the send button")(click_the_send_button)

def register_custom_action(controller, action_config):
    """Register a custom action from the API"""
    registry = controller.registry
    
    action_name = action_config.get("name", "")
    action_code = action_config.get("code", "")
    
    if not action_name or not action_code:
        raise ValueError("Action name and code are required")
    
    # Create the function from the code string
    # This is potentially dangerous but necessary for dynamic function creation
    try:
        # Create a context with necessary imports
        context = {
            "ActionResult": ActionResult,
            "BrowserContext": BrowserContext,
            "logging": logging,
            "pyperclip": pyperclip,
            "sanitize_response": sanitize_response,
            "ElementHandle": ElementHandle,
            "Optional": Optional,
            "asyncio": asyncio,
            "json": json,
            "os": os,
        }
        
        # Execute the function definition in the context
        exec(action_code, context)
        
        # Get the function from the context
        # We assume the last defined function in the code is the one we want
        func_name = None
        for name, obj in context.items():
            if callable(obj) and not name.startswith("__"):
                func_name = name
        
        if not func_name:
            raise ValueError("No function defined in the provided code")
        
        function = context[func_name]
        
        # Register the function with the controller
        registry.action(action_name)(function)
        
        return True
    except Exception as e:
        raise ValueError(f"Failed to create function: {str(e)}")

async def run_tasks_background(
    task_id: str,
    tasks: List[Dict[str, Any]],
    laminar_api_key: str,
    laminar_base_url: str,
    laminar_http_port: int,
    laminar_grpc_port: int,
    session_id: str,
    simulator_provider: str,
    simulator_model: str,
    simulator_temperature: float,
    simulator_task: str,
    custom_actions: List[Dict[str, str]]
):
    """Run tasks in the background and store the results"""
    try:
        # Initialize cancellation flag for this task
        CANCELLATION_FLAGS[task_id] = False
        
        # Update task status to running
        BACKGROUND_TASKS[task_id] = {"status": "running"}
        
        results, history = await run_tasks(
            tasks,
            laminar_api_key,
            laminar_base_url,
            laminar_http_port,
            laminar_grpc_port,
            session_id,
            simulator_provider,
            simulator_model,
            simulator_temperature,
            simulator_task,
            custom_actions,
            task_id  # Pass task_id to run_tasks for cancellation check
        )
        
        # Check if task was cancelled from results
        if results and len(results) > 0 and "status" in results[0] and results[0]["status"] == "cancelled":
            BACKGROUND_TASKS[task_id] = {
                "status": "cancelled",
                "message": results[0].get("message", "Task was cancelled by user")
            }
            return
        
        # Add user simulator interactions to the results if available
        if session_id in USER_SIMULATOR_INTERACTIONS:
            simulator_interactions = USER_SIMULATOR_INTERACTIONS[session_id]
            
            # Store the results in global storage with interactions
            BACKGROUND_TASKS[task_id] = {
                "status": "completed",
                "results": results,
                "history": history,
                "simulator_interactions": simulator_interactions
            }
        else:
            # Store the results in global storage without interactions
            BACKGROUND_TASKS[task_id] = {
                "status": "completed",
                "results": results,
                "history": history,
                "simulator_interactions": []
            }
    except Exception as e:
        traceback_str = traceback.format_exc()
        
        # Check if task was cancelled during the exception
        if CANCELLATION_FLAGS.get(task_id, False):
            BACKGROUND_TASKS[task_id] = {
                "status": "cancelled",
                "message": "Task was cancelled during execution",
                "error": str(e),
                "traceback": traceback_str
            }
        else:
            # Store the error in global storage
            BACKGROUND_TASKS[task_id] = {
                "status": "failed",
                "error": str(e),
                "traceback": traceback_str
            }
    finally:
        # Clean up cancellation flag
        if task_id in CANCELLATION_FLAGS:
            CANCELLATION_FLAGS.pop(task_id) 