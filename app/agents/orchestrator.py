"""
Orchestrator Manager Agent for Multi-Agent coordination & Human-in-the-Loop control
"""
import asyncio
import logging
from typing import Dict, Any, Optional

from app.schemas.agent_messages import AgentMessage, MessageType
from app.schemas.context import SharedExecutionContext
from app.agents.event_bus import AgentEventBus
from app.agents.planner import PlannerAgent
from app.agents.browser_executor import BrowserExecutionAgent
from app.agents.user_simulator import UserSimulatorAgent
from app.agents.evaluator import ReportEvaluatorAgent


class Orchestrator:
    """
    Manager Orchestrator Agent coordinating multi-agent execution,
    state propagation, event bus routing, and human-in-the-loop interventions.
    """
    def __init__(self, task_id: str, config: Optional[Dict[str, Any]] = None):
        self.task_id = task_id
        self.config = config or {}
        self.logger = logging.getLogger(f"ORCHESTRATOR.{task_id}")
        self.context = SharedExecutionContext(
            task_id=task_id,
            control_mode=self.config.get("control_mode", "autonomous")
        )
        self.event_bus = AgentEventBus()

        # Human intervention event & data holder
        self.human_input_event = asyncio.Event()
        self.pending_human_input: Optional[Dict[str, Any]] = None

        # Instantiate specialized agents
        self.planner = PlannerAgent("planner_1", "Planner", self.config.get("planner_llm_config"))
        self.browser_executor = BrowserExecutionAgent("executor_1", "BrowserExecutor", self.config.get("executor_llm_config"))
        self.user_simulator = UserSimulatorAgent("simulator_1", "UserSimulator", self.config.get("simulator_llm_config"))
        self.evaluator = ReportEvaluatorAgent("evaluator_1", "Evaluator", self.config.get("evaluator_llm_config"))

    async def initialize(self, prompt: str):
        """Set task prompt and subscribe agents to event bus."""
        self.context.task_prompt = prompt
        self.logger.info(f"Initialized Orchestrator for task {self.task_id}")

    async def provide_human_input(self, input_payload: Dict[str, Any]):
        """Callback invoked when user submits input or approval via API/Gradio UI."""
        self.logger.info(f"Received human input for task {self.task_id}: {input_payload}")
        self.pending_human_input = input_payload
        self.context.status = "running"
        self.human_input_event.set()

    async def pause_task(self):
        """Pause execution."""
        self.context.status = "paused"
        self.logger.info(f"Task {self.task_id} paused")

    async def resume_task(self):
        """Resume execution."""
        self.context.status = "running"
        self.human_input_event.set()
        self.logger.info(f"Task {self.task_id} resumed")

    async def run(self) -> Dict[str, Any]:
        """
        Execute full multi-agent orchestration workflow:
        1. Planner decomposes prompt -> Sub-goals
        2. Iterative execution of steps with optional Human / Simulator approval
        3. Evaluator generates final report summary
        """
        self.logger.info(f"Starting Multi-Agent Orchestration for task {self.task_id}...")
        self.context.status = "running"

        # 1. PLANNER STAGE
        plan_req = AgentMessage(
            sender="Orchestrator",
            recipient="Planner",
            message_type=MessageType.TASK_PLAN,
            payload={"prompt": self.context.task_prompt}
        )
        plan_response = await self.planner.process_message(plan_req, self.context)
        steps = plan_response.payload.get("steps", [])

        # 2. BROWSER EXECUTION LOOP
        for idx, step in enumerate(steps):
            self.context.current_step_index = idx

            # Check for Human-in-the-Loop approval gate
            if step.get("requires_human_approval") or self.context.control_mode == "semi_autonomous":
                self.logger.info(f"Step {idx+1} requires human approval. Waiting for UI signal...")
                self.context.status = "waiting_human_approval"
                self.human_input_event.clear()
                await self.human_input_event.wait()

            # Execute Step via Browser Execution Agent
            exec_req = AgentMessage(
                sender="Orchestrator",
                recipient="BrowserExecutor",
                message_type=MessageType.ACTION_REQUEST,
                payload={"step": step}
            )
            exec_res = await self.browser_executor.process_message(exec_req, self.context)

            # Check if simulation query is triggered
            if exec_res.payload.get("needs_user_simulation"):
                sim_req = AgentMessage(
                    sender="Orchestrator",
                    recipient="UserSimulator",
                    message_type=MessageType.SIMULATION_QUERY,
                    payload={"query": exec_res.payload.get("query", "")}
                )
                sim_res = await self.user_simulator.process_message(sim_req, self.context)
                self.logger.info(f"User Simulator provided response: {sim_res.payload.get('response')}")

        # 3. EVALUATION STAGE
        eval_req = AgentMessage(
            sender="Orchestrator",
            recipient="Evaluator",
            message_type=MessageType.EVALUATION_REQUEST,
            payload={}
        )
        eval_res = await self.evaluator.process_message(eval_req, self.context)

        self.context.status = "completed"
        self.logger.info(f"Multi-Agent Orchestration completed for task {self.task_id}")
        return eval_res.payload
