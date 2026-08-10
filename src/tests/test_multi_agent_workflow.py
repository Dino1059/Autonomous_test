"""
Unit and Integration tests for Multi-Agent AutoTester Framework
"""
import unittest
import asyncio
from app.schemas.agent_messages import AgentMessage, MessageType
from app.schemas.context import SharedExecutionContext
from app.agents.event_bus import AgentEventBus
from app.agents.planner import PlannerAgent
from app.agents.browser_executor import BrowserExecutionAgent
from app.agents.user_simulator import UserSimulatorAgent
from app.agents.evaluator import ReportEvaluatorAgent
from app.agents.orchestrator import Orchestrator


class TestMultiAgentFramework(unittest.TestCase):

    def test_agent_message_protocol(self):
        msg = AgentMessage(
            sender="Planner",
            recipient="Orchestrator",
            message_type=MessageType.TASK_PLAN,
            payload={"prompt": "Test navigation"}
        )
        self.assertEqual(msg.sender, "Planner")
        self.assertEqual(msg.recipient, "Orchestrator")
        self.assertEqual(msg.message_type, MessageType.TASK_PLAN)
        self.assertEqual(msg.payload["prompt"], "Test navigation")

    def test_planner_agent(self):
        async def run_test():
            planner = PlannerAgent()
            context = SharedExecutionContext(task_id="test_1", task_prompt="Check login page")
            msg = AgentMessage(
                sender="Orchestrator",
                recipient="Planner",
                message_type=MessageType.TASK_PLAN,
                payload={"prompt": context.task_prompt}
            )
            res = await planner.process_message(msg, context)
            self.assertEqual(res.message_type, MessageType.TASK_PLAN)
            self.assertTrue(len(context.sub_goals) > 0)
        asyncio.run(run_test())

    def test_user_simulator_agent(self):
        async def run_test():
            simulator = UserSimulatorAgent()
            context = SharedExecutionContext(task_id="test_2")
            msg = AgentMessage(
                sender="Orchestrator",
                recipient="UserSimulator",
                message_type=MessageType.SIMULATION_QUERY,
                payload={"query": "Please provide confirmation email"}
            )
            res = await simulator.process_message(msg, context)
            self.assertEqual(res.message_type, MessageType.SIMULATION_RESPONSE)
            self.assertEqual(len(context.interaction_history), 1)
        asyncio.run(run_test())

    def test_orchestrator_full_workflow(self):
        async def run_test():
            orchestrator = Orchestrator(task_id="test_orchestrator_1")
            await orchestrator.initialize("Run test suite for user authentication")
            result = await orchestrator.run()
            self.assertEqual(result["task_id"], "test_orchestrator_1")
            self.assertIn(result["status"], ["PASS", "FAIL"])
        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
