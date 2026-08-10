"""
Message protocol definitions for Inter-Agent communication
"""
import uuid
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    TASK_PLAN = "TASK_PLAN"                             # Planner -> Orchestrator
    ACTION_REQUEST = "ACTION_REQUEST"                   # Orchestrator -> BrowserExecutor
    ACTION_RESULT = "ACTION_RESULT"                     # BrowserExecutor -> Orchestrator
    SIMULATION_QUERY = "SIMULATION_QUERY"               # Executor/Orchestrator -> UserSimulator
    SIMULATION_RESPONSE = "SIMULATION_RESPONSE"         # UserSimulator -> Orchestrator
    HUMAN_INTERVENTION_NEEDED = "HUMAN_INTERVENTION_NEEDED"  # Agent -> Human/UI
    HUMAN_INPUT_PROVIDED = "HUMAN_INPUT_PROVIDED"       # Human/UI -> Orchestrator
    EVALUATION_REQUEST = "EVALUATION_REQUEST"           # Orchestrator -> Evaluator
    FINAL_REPORT = "FINAL_REPORT"                       # Evaluator -> Orchestrator


class AgentMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    sender: str                                         # e.g., "Planner", "BrowserExecutor", "UserSimulator", "Evaluator", "Orchestrator", "Human"
    recipient: str                                      # e.g., "Orchestrator", "BrowserExecutor", "UserSimulator", etc.
    message_type: MessageType
    payload: Dict[str, Any] = Field(default_factory=dict) # Structured message content

    class Config:
        arbitrary_types_allowed = True
