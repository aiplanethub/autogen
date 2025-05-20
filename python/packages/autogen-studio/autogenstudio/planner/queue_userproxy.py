import asyncio
from typing import Any, List, Optional


class QueueUserProxyAgent:
    def __init__(self, name: str, builder_id: int, builder_queues: dict):
        self.name = name
        self.builder_id = builder_id
        self.builder_queues = builder_queues
        if builder_id not in self.builder_queues:
            self.builder_queues[builder_id] = asyncio.Queue(maxsize=1)
        self.message_queue = self.builder_queues[builder_id]

    async def get_input(
        self, prompt: str, cancellation_token: Optional[Any] = None
    ) -> str:
        return await self.message_queue.get()

    async def receive_message(self, messages: List):
        return {"name": self.name, "response": await self.message_queue.get()}

    @property
    def is_full(self):
        return self.message_queue.full()
