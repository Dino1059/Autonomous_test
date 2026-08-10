"""
Base abstract agent for Multi-Agent AutoTester
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.schemas.agent_messages import AgentMessage
from app.schemas.context import SharedExecutionContext


class BaseAgent(ABC):
    """
    Abstract Base Class for all specialized agents in the system.
    """
    def __init__(self, agent_id: str, name: str, llm_config: Optional[Dict[str, Any]] = None):
        self.agent_id = agent_id
        self.name = name
        self.llm_config = llm_config or {}
        self.logger = logging.getLogger(f"AGENT.{name.upper()}")

    @abstractmethod
    async def process_message(
        self, message: AgentMessage, context: SharedExecutionContext
    ) -> AgentMessage:
        """
        Process an incoming AgentMessage within the shared context and return a response AgentMessage.
        """
        pass
