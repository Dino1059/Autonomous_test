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
import requests
from typing import Dict, Any, List, Tuple, Optional
import base64
from pathlib import Path
from dotenv import load_dotenv
from inspect import signature

from browser_use import Agent, Controller
from browser_use.browser import BrowserProfile, BrowserSession
from browser_use.agent.views import ActionResult
from browser_use.agent.memory import MemoryConfig
from playwright.sync_api import ElementHandle
import pyperclip
from src.llms.base import BaseLLMWorker
from pyobjtojson import obj_to_json

from app.utils.globals import SETTINGS, BACKGROUND_TASKS, USER_SIMULATOR_INTERACTIONS, CANCELLATION_FLAGS, get_or_initialize_llm_worker
from app.utils.browser_actions import paste_from_clipboard, call_user_simulator, get_system_message, sanitize_response
from app.utils.llm_utils import create_llm_for_task, create_model_from_schema, generate_report
from app.serializers.models import TaskConfig, BrowserConfig
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()


import json_repair

## Current not used
async def record_activity(agent_obj):
    """Hook function that captures and records agent activity at each step"""
    logger = logging.getLogger("RECORD_ACTIVITY")
    logger.info("Recording agent activity")
    
    website_html = None
    website_screenshot = None
    urls_json_last_elem = None
    model_thoughts_last_elem = None
    model_outputs_json_last_elem = None
    model_actions_json_last_elem = None
    extracted_content_json_last_elem = None
    
    # Get task_id from agent_obj if available
    task_id = "default"
    if hasattr(agent_obj, "task_id"):
        task_id = agent_obj.task_id

    try:
        # Capture current page state
        website_html = await agent_obj.browser_context.get_page_html()
        website_screenshot = await agent_obj.browser_context.take_screenshot()

        # Make sure we have state history
        if hasattr(agent_obj, "state"):
            history = agent_obj.state.history
        else:
            history = None
            logger.warning("Warning: Agent has no state history")
            return

        # Process model thoughts
        model_thoughts = obj_to_json(
            obj=history.model_thoughts(),
            check_circular=False
        )
        if len(model_thoughts) > 0:
            model_thoughts_last_elem = model_thoughts[-1]

        # Process model outputs
        model_outputs = agent_obj.state.history.model_outputs()
        model_outputs_json = obj_to_json(
            obj=model_outputs,
            check_circular=False
        )
        if len(model_outputs_json) > 0:
            model_outputs_json_last_elem = model_outputs_json[-1]

        # Process model actions
        model_actions = agent_obj.state.history.model_actions()
        model_actions_json = obj_to_json(
            obj=model_actions,
            check_circular=False
        )
        if len(model_actions_json) > 0:
            model_actions_json_last_elem = model_actions_json[-1]

        # Process extracted content
        extracted_content = agent_obj.state.history.extracted_content()
        extracted_content_json = obj_to_json(
            obj=extracted_content,
            check_circular=False
        )
        if len(extracted_content_json) > 0:
            extracted_content_json_last_elem = extracted_content_json[-1]

        # Process URLs
        urls = agent_obj.state.history.urls()
        urls_json = obj_to_json(
            obj=urls,
            check_circular=False
        )
        if len(urls_json) > 0:
            urls_json_last_elem = urls_json[-1]

        # Create a summary of all data for this step
        model_step_summary = {
            "website_html": website_html,
            "website_screenshot": website_screenshot,
            "url": urls_json_last_elem,
            "model_thoughts": model_thoughts_last_elem,
            "model_outputs": model_outputs_json_last_elem,
            "model_actions": model_actions_json_last_elem,
            "extracted_content": extracted_content_json_last_elem
        }

        logger.info(f"Recording step for URL: {urls_json_last_elem}")
        
        # Send data to the recording API with task_id as query parameter
        url = f"http://127.0.0.1:9091/post_agent_history_step?task_id={task_id}"
        response = requests.post(url, json=model_step_summary)
        logger.info(f"Recording API response: {response.json()}")
    
    except Exception as e:
        logger.error(f"Error in record_activity: {str(e)}")


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
    task_id: str = None,
    browser_config: Optional[BrowserConfig] = None
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
        "simulator_temperature": sim_temperature,
        "browser_config": browser_config
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
                

        # Load environment variables
        load_dotenv()
        
        # Initialize browser configuration
        final_browser_config = {}
        
        # Start with browser_config if provided
        if browser_config:
            final_browser_config = browser_config.model_dump(exclude_none=True)
            logger.info(f"Using provided browser_config: {final_browser_config}")
            # browser_profile = BrowserProfile(
            #     **final_browser_config
            # )
            browser_session = BrowserSession(**final_browser_config)
            logger.info(f"Browser session: {browser_session}")
        else:
            browser_profile = None
            browser_session = BrowserSession()
    

        await browser_session.start()
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
            
            # Prepare kwargs for Agent constructor
            kwargs = task_config.model_dump()
            report_config = kwargs.pop("report_config", None)
            # Remove task-specific fields that shouldn't be passed to Agent
            fields_to_remove = ["name", "max_steps", "output_model_fields", "exclude_actions", 
                               "llm_provider", "llm_model", "llm_temperature", "prompt", "report_config"]
            for field in fields_to_remove:
                if field in kwargs:
                    kwargs.pop(field)
            # agent_params = signature(Agent).parameters.keys()
            # agent_kwargs = {k: v for k, v in kwargs.items() if k in agent_params}
            
            # Handle memory configuration
            if "enable_memory" in kwargs and kwargs["enable_memory"]:
                memory_interval = kwargs.pop("memory_interval", 7)
                agent_id = f"agent_{task_id}" if task_id else f"agent_{i+1}"
                
                # Create MemoryConfig
                memory_config = MemoryConfig(
                    agent_id=agent_id,
                    memory_interval=memory_interval
                )
                
                # Replace individual memory params with memory_config
                kwargs.pop("enable_memory")
                kwargs["memory_config"] = memory_config
            elif "enable_memory" in kwargs:
                # If enable_memory is False, just remove it and memory_interval
                kwargs.pop("enable_memory")
                if "memory_interval" in kwargs:
                    kwargs.pop("memory_interval")
            
            # Set required parameters
            kwargs["task"] = task_config.prompt
            kwargs["llm"] = llm
            kwargs["controller"] = controller
            kwargs["browser_session"] = browser_session
            
            # Debug log all parameters being passed to Agent
            #logging.getLogger("RUN_TASKS").info("Agent signature: %s", inspect.signature(Agent))
            #logging.getLogger("RUN_TASKS").info("Final kwargs keys: %r", list(kwargs.keys()))
            
            # Handle planner_llm parameter if specified
            if "planner_llm" in kwargs:
                if kwargs["planner_llm"] is True:
                    # If planner_llm is set to True, use the same LLM
                    kwargs["planner_llm"] = llm
                elif isinstance(kwargs["planner_llm"], dict):
                    # If planner_llm is a dictionary with configuration, create a new LLM instance
                    try:
                        from app.utils.llm_utils import create_custom_llm
                        planner_config = kwargs["planner_llm"]
                        # Create custom LLM for planner
                        kwargs["planner_llm"] = create_custom_llm(
                            provider=planner_config.get("provider", task_config.llm_provider),
                            model=planner_config.get("model", task_config.llm_model),
                            temperature=planner_config.get("temperature", task_config.llm_temperature)
                        )
                        logger.info(f"Created custom planner LLM with provider={planner_config.get('provider')}, model={planner_config.get('model')}")
                    except Exception as e:
                        logger.error(f"Error creating custom planner LLM: {str(e)}")
                        # Fall back to using the main LLM
                        kwargs["planner_llm"] = llm
                        logger.info("Falling back to using the main LLM for planning")
            if report_config:
                if isinstance(report_config, dict):
                    try:
                        from app.utils.llm_utils import create_custom_llm
                        report_config['reporter'] = create_custom_llm(
                            provider=report_config.get("provider", task_config.llm_provider),
                            model=report_config.get("model", task_config.llm_model),
                            temperature=report_config.get("temperature", task_config.llm_temperature)
                        )
                        logger.info(f"Created custom report LLM with provider={report_config.get('provider')}, model={report_config.get('model')}")
                    except Exception as e:
                        logger.error(f"Error creating custom report LLM: {str(e)}")
                else:
                    raise ValueError("report_config must be a dictionary")
            
            try:
                agent = Agent(**kwargs)
                
                # Add task_id as attribute for recording hook
                if task_id:
                    agent.task_id = task_id
                else:
                    agent.task_id = f"task_{i+1}"
                    
            except TypeError as e:
                logger.error(f"Error creating Agent: {str(e)}")
                # If we get a TypeError, it might be due to unexpected parameters
                # Try to extract the problematic parameter name from the error message
                error_msg = str(e)
                if "got an unexpected keyword argument" in error_msg:
                    param_name = error_msg.split("'")[-2]
                    logger.error(f"Removing unsupported parameter: {param_name}")
                    if param_name in kwargs:
                        kwargs.pop(param_name)
                        # Try again with the problematic parameter removed
                        agent = Agent(**kwargs)
                else:
                    # Re-raise if it's not a parameter issue or couldn't be fixed
                    raise
            
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
                agent_run_task = asyncio.create_task(agent.run(
                    max_steps=task_config.max_steps,
                    #on_step_start=record_activity  # Add recording hook
                ))
                
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
                # Update report_config with the correct state (history)
                if report_config:
                    report_config['state'] = agent.state
                    ## report generation
                    await generate_report(
                        task=task_config.prompt,
                        **report_config
                    )
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
                    "result": final_result,
                    "report_folder": report_config['report_folder'] if report_config else None
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
        await browser_session.close()
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
            "BrowserContext": BrowserSession,
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
    custom_actions: List[Dict[str, str]],
    browser_config: Optional[BrowserConfig] = None
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
            task_id,  # Pass task_id to run_tasks for cancellation check
            browser_config  # Pass browser_config parameter
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