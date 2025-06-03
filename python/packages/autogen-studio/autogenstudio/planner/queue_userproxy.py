import asyncio
from typing import Any, List, Optional
from autogen_agentchat.agents import UserProxyAgent
from typing_extensions import override
from autogen_core.models import ChatCompletionClient
from autogen_core.models import AssistantMessage, SystemMessage


class QueueUserProxyAgent(UserProxyAgent):
    def __init__(
        self,
        name: str,
        model_client: ChatCompletionClient,
        queue: asyncio.Queue,
        **kwargs
    ):
        super().__init__(name, description="standin agent for user input", **kwargs)

        self.message_queue = queue
        self.model_client = model_client

    @override
    async def _get_input(
        self, prompt: str, cancellation_token: Optional[Any] = None
    ) -> str:
        user_input = await self.message_queue.get()
        return user_input

    async def receive_message(self, messages: List):
        return {"name": self.name, "response": await self.message_queue.get()}

    @property
    def is_full(self):
        return self.message_queue.full()
