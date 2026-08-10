"""
Planner Agent for breaking down test prompts into structured sub-goals
"""
import json
import logging
from typing import Dict, Any
from app.agents.base import BaseAgent
from app.schemas.agent_messages import AgentMessage, MessageType
from app.schemas.context import SharedExecutionContext
import json_repair


class PlannerAgent(BaseAgent):
    """
    Planner Agent analyzes high-level test scenarios and decomposes them
    into sub-goals with expected results and human approval flags.
    """
    def __init__(self, agent_id: str = "planner_1", name: str = "Planner", llm_config: Dict[str, Any] = None):
        super().__init__(agent_id, name, llm_config)

    async def process_message(
        self, message: AgentMessage, context: SharedExecutionContext
    ) -> AgentMessage:
        if message.message_type != MessageType.TASK_PLAN:
            raise ValueError(f"PlannerAgent expects MessageType.TASK_PLAN, got {message.message_type}")

        prompt = message.payload.get("prompt", context.task_prompt)
        self.logger.info(f"Planning sub-goals for task: {prompt[:80]}...")

        # Construct sub-goals either using LLM or structured step parsing
        steps = await self._generate_sub_goals(prompt)

        context.sub_goals = steps
        context.execution_logs.append({
            "agent": self.name,
            "action": "plan_generated",
            "step_count": len(steps)
        })

        return AgentMessage(
            sender=self.name,
            recipient=message.sender,
            message_type=MessageType.TASK_PLAN,
            payload={
                "task_prompt": prompt,
                "steps": steps,
                "status": "planned"
            }
        )

    async def _generate_sub_goals(self, prompt: str) -> list:
        """Decomposes the prompt into structured execution steps."""
        # Check if LLM instance is provided in llm_config
        llm_worker = self.llm_config.get("llm_worker")
        if llm_worker and hasattr(llm_worker, "get_response"):
            try:
                system_prompt = (
                    "You are an AI Test Planner. Given a test prompt, decompose it into a JSON list of steps. "
                    "Return strictly a JSON array of objects with keys: "
                    "'step_id', 'description', 'expected_result', 'requires_human_approval'."
                )
                raw_res = await llm_worker.get_response(f"{system_prompt}\nTest Prompt: {prompt}")
                parsed = json_repair.loads(raw_res)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed
            except Exception as e:
                self.logger.warning(f"Failed to generate steps via LLM worker: {e}. Falling back to default plan.")

        # Default fallback step list derived from the prompt
        return [
            {
                "step_id": 1,
                "description": f"Navigate and execute main test scenario: {prompt}",
                "expected_result": "Page loaded and target interaction completed successfully",
                "requires_human_approval": False
            }
        ]
