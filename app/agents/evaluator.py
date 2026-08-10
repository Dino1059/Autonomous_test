"""
Report & Evaluator Agent for analyzing test execution results & generating markdown reports
"""
import os
import logging
from typing import Dict, Any
from app.agents.base import BaseAgent
from app.schemas.agent_messages import AgentMessage, MessageType
from app.schemas.context import SharedExecutionContext


class ReportEvaluatorAgent(BaseAgent):
    """
    Report Evaluator Agent evaluates execution traces and produces formatted Markdown test reports.
    """
    def __init__(self, agent_id: str = "evaluator_1", name: str = "Evaluator", llm_config: Dict[str, Any] = None):
        super().__init__(agent_id, name, llm_config)

    async def process_message(
        self, message: AgentMessage, context: SharedExecutionContext
    ) -> AgentMessage:
        if message.message_type != MessageType.EVALUATION_REQUEST:
            raise ValueError(f"ReportEvaluatorAgent expects MessageType.EVALUATION_REQUEST, got {message.message_type}")

        self.logger.info(f"Evaluating execution results for task {context.task_id}...")

        evaluation_result = self._evaluate_context(context)
        context.final_evaluation = evaluation_result

        return AgentMessage(
            sender=self.name,
            recipient=message.sender,
            message_type=MessageType.FINAL_REPORT,
            payload=evaluation_result
        )

    def _evaluate_context(self, context: SharedExecutionContext) -> Dict[str, Any]:
        has_errors = any(
            log.get("status") == "failed" for log in context.execution_logs
        )
        status = "FAIL" if has_errors else "PASS"

        summary = {
            "task_id": context.task_id,
            "status": status,
            "total_steps": len(context.sub_goals),
            "executed_logs_count": len(context.execution_logs),
            "interactions_count": len(context.interaction_history),
            "report_folder": context.report_folder
        }
        return summary
