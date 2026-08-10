"""
Shared execution context schema for Multi-Agent AutoTester
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class SharedExecutionContext(BaseModel):
    task_id: str
    status: str = "running"                            # running, waiting_human_input, waiting_human_approval, paused, completed, failed, cancelled
    sub_goals: List[Dict[str, Any]] = Field(default_factory=list)
    current_step_index: int = 0
    browser_snapshots: List[Dict[str, Any]] = Field(default_factory=list) # [{url, screenshot_base64, html}]
    interaction_history: List[Dict[str, Any]] = Field(default_factory=list) # User simulator & human answers
    execution_logs: List[Dict[str, Any]] = Field(default_factory=list)
    final_evaluation: Optional[Dict[str, Any]] = None
    report_folder: Optional[str] = None
    task_prompt: str = ""
    control_mode: str = "autonomous"                   # autonomous, semi_autonomous, human_takeover

    class Config:
        arbitrary_types_allowed = True
