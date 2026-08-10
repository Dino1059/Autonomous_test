"""
Asynchronous Event Bus for inter-agent communication
"""
import asyncio
import logging
from typing import Dict, List, Callable, Awaitable
from app.schemas.agent_messages import AgentMessage


class AgentEventBus:
    """
    Decoupled async event message bus for dispatching AgentMessages to registered agents.
    """
    def __init__(self):
        self.listeners: Dict[str, List[Callable[[AgentMessage], Awaitable[None]]]] = {}
        self.queue: asyncio.Queue[AgentMessage] = asyncio.Queue()
        self.logger = logging.getLogger("EVENT_BUS")

    def subscribe(self, recipient: str, callback: Callable[[AgentMessage], Awaitable[None]]):
        """Subscribe a handler callback to messages directed at 'recipient' or broadcast '*'."""
        if recipient not in self.listeners:
            self.listeners[recipient] = []
        self.listeners[recipient].append(callback)
        self.logger.info(f"Subscribed handler for recipient: {recipient}")

    async def publish(self, message: AgentMessage):
        """Publish a message onto the queue."""
        await self.queue.put(message)
        self.logger.debug(f"Message {message.message_id} queued from {message.sender} to {message.recipient}")

    async def dispatch_next(self):
        """Dispatch a single message from queue to its subscribers."""
        message = await self.queue.get()
        recipients = [message.recipient]
        if "*" in self.listeners:
            recipients.append("*")

        for r in recipients:
            if r in self.listeners:
                for callback in self.listeners[r]:
                    try:
                        await callback(message)
                    except Exception as e:
                        self.logger.error(f"Error in listener callback for {r}: {e}")
        self.queue.task_done()
