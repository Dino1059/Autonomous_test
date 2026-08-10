"""
User Simulator Agent for simulating real human user interactions & responses
"""
import logging
from typing import Dict, Any
from app.agents.base import BaseAgent
from app.schemas.agent_messages import AgentMessage, MessageType
from app.schemas.context import SharedExecutionContext
import json_repair


class UserSimulatorAgent(BaseAgent):
    """
    User Simulator Agent acts as a persona answering queries, security challenges,
    and generating contextually appropriate input for form elements.
    """
    def __init__(self, agent_id: str = "simulator_1", name: str = "UserSimulator", llm_config: Dict[str, Any] = None):
        super().__init__(agent_id, name, llm_config)

    async def process_message(
        self, message: AgentMessage, context: SharedExecutionContext
    ) -> AgentMessage:
        if message.message_type != MessageType.SIMULATION_QUERY:
            raise ValueError(f"UserSimulatorAgent expects MessageType.SIMULATION_QUERY, got {message.message_type}")

        query = message.payload.get("query", "")
        system_msg = message.payload.get("system_message", "")
        self.logger.info(f"Simulating user response for query: {query[:60]}")

        response_text = await self._simulate_response(query, system_msg)

        interaction_record = {
            "query": query,
            "system_message": system_msg,
            "simulated_response": response_text
        }
        context.interaction_history.append(interaction_record)

        return AgentMessage(
            sender=self.name,
            recipient=message.sender,
            message_type=MessageType.SIMULATION_RESPONSE,
            payload={
                "query": query,
                "response": response_text
            }
        )

    async def _simulate_response(self, query: str, system_msg: str) -> str:
        llm_worker = self.llm_config.get("llm_worker")
        if llm_worker and hasattr(llm_worker, "get_response"):
            try:
                prompt = (
                    f"You are simulating a user answering a test query.\n"
                    f"System context: {system_msg}\n"
                    f"User question: {query}\n"
                    f"Provide a concise JSON answer object."
                )
                res = await llm_worker.get_response(prompt)
                return res
            except Exception as e:
                self.logger.warning(f"Error getting response from LLM worker in UserSimulatorAgent: {e}")

        return "Confirmed. Proceed with test step."
