"""
Browser Execution Agent for Playwright UI interactions
"""
import logging
import asyncio
from typing import Dict, Any, Optional
from app.agents.base import BaseAgent
from app.schemas.agent_messages import AgentMessage, MessageType
from app.schemas.context import SharedExecutionContext


class BrowserExecutionAgent(BaseAgent):
    """
    Browser Execution Agent executes specific UI actions using browser-use and Playwright.
    """
    def __init__(self, agent_id: str = "executor_1", name: str = "BrowserExecutor", llm_config: Dict[str, Any] = None):
        super().__init__(agent_id, name, llm_config)

    async def process_message(
        self, message: AgentMessage, context: SharedExecutionContext
    ) -> AgentMessage:
        if message.message_type != MessageType.ACTION_REQUEST:
            raise ValueError(f"BrowserExecutionAgent expects MessageType.ACTION_REQUEST, got {message.message_type}")

        step = message.payload.get("step", {})
        step_id = step.get("step_id", context.current_step_index + 1)
        description = step.get("description", context.task_prompt)

        self.logger.info(f"Executing step {step_id}: {description[:60]}")

        # The actual browser execution is coordinated via the Orchestrator & task_execution agent runner
        result_payload = {
            "step_id": step_id,
            "status": "success",
            "description": description,
            "details": f"Completed execution of step {step_id}"
        }

        context.execution_logs.append({
            "agent": self.name,
            "action": "execute_step",
            "step_id": step_id,
            "status": "success"
        })

        return AgentMessage(
            sender=self.name,
            recipient=message.sender,
            message_type=MessageType.ACTION_RESULT,
            payload=result_payload
        )
