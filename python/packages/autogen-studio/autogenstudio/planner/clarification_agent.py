from typing import Optional

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core.models import ChatCompletionClient, UserMessage
from autogen_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing_extensions import override
from weaviate import WeaviateClient

from autogenstudio.services.weaviate_service import WeaviateService


class ClarificationAgentResponse(BaseModel):
    """Output model for the agent."""

    questions: list[str] = Field(..., description="List of questions to ask the user.")
    is_clarification_needed: bool = Field(
        ..., description="Flag indicating if clarification is needed."
    )


class ClarificationAgent(AssistantAgent):
    """Create a clarification agent."""

    def __init__(
        self,
        model_client: ChatCompletionClient,
        tools: list[BaseTool] = [],
        kb_collection_name: Optional[str] = None,
    ):

        self.kb_collection = kb_collection_name

        super().__init__(
            name="clarify",
            description="Clarification agent that asks clarifying questions to the user.",
            system_message=system_prompt,
            model_client=model_client,
            model_client_stream=False,
            output_content_type=ClarificationAgentResponse,
            tools=tools,
            handoffs=["user_proxy", "planner"],
        )

    @override
    async def on_messages(self, messages, cancellation_token):

        # if kb is not connected
        if not self.kb_collection or len(messages) < 1:
            return await super().on_messages(messages, cancellation_token)

        # the mose recent user message
        message = messages[-1]
        kb_context = None

        query = await self._model_client.create(
            [
                UserMessage(
                    content=weaviate_query_prompt.format(
                        user_content=message.to_model_text()
                    ),
                    type="UserMessage",
                    source=message.source,
                )
            ],
            cancellation_token=cancellation_token,
        )

        assert isinstance(query.content, str), "Query should be a string"

        if message:
            async with WeaviateService() as service:
                collection = self.kb_collection
                kb_results = await service.query_weaviate(query.content, collection)

                if kb_results:
                    kb_context = "\n".join(str(item) for item in kb_results)

        if kb_context:
            context_message = f"[Knoledge Base Context]\n{kb_context}\n\n"
            messages = list(messages)

            messages[-1] = TextMessage(
                source=messages[-1].source,
                content=context_message + messages[-1].to_model_text(),
                metadata=messages[-1].metadata,
            )
        return await super().on_messages(messages, cancellation_token)

    @override
    async def on_messages_stream(self, messages, cancellation_token):
        # if kb is not connected
        if not self.kb_collection or len(messages) < 1:
            pass
        else:
            # the most recent user message
            message = messages[-1]
            kb_context = None

            query = await self._model_client.create(
                [
                    UserMessage(
                        content=weaviate_query_prompt.format(
                            user_content=message.to_model_text()
                        ),
                        source=message.source,
                    )
                ],
                cancellation_token=cancellation_token,
            )

            assert isinstance(query.content, str), "Query should be a string"

            if message:
                async with WeaviateService() as service:
                    collection = self.kb_collection
                    kb_results = await service.query_weaviate(query.content, collection)

                    if kb_results:
                        kb_context = "\n".join(str(item) for item in kb_results)

            if kb_context:
                context_message = f"[Knoledge Base Context]\n{kb_context}\n\n"
                messages = list(messages)

                messages.append(
                    TextMessage(
                        source=messages[-1].source,
                        content=context_message + messages[-1].to_model_text(),
                        metadata=messages[-1].metadata,
                    )
                )
        print("running clarification agent")

        async for msg in super().on_messages_stream(messages, cancellation_token):
            yield msg


weaviate_query_prompt = """user content:
{user_content}

write a query for weaviate to get the most relevant context for the user content.
the response should only have the query string, and nothing else."""


system_prompt = """Clarification Agent Prompt
You ensure user requests are clear and complete before they are processed. Focus on workflow structure, data flow, and functional goals, not code or implementation details.

Your Role
Spot vague terms, missing steps, or unclear goals

Ask brief, targeted questions to clarify pipeline intent, inputs/outputs, or expected behavior

Avoid questions about programming languages, frameworks, or algorithms

Ask Questions When:
Steps or data connections are unclear

Inputs, outputs, or expected outcomes are missing

Terms like “analyze” or “process” are ambiguous

Don’t Ask When:
Only implementation details are missing
If user tells to decide yourself

Non-critical choices should be inferred or deferred

Style
just return whether the clarification is needed or not, and the questions to ask the user

Focus on making pipeline requests UI-ready — not implementation-ready.

Handoffs
if you have questions, handoff to user_proxy
if you have no questions, handoff to planner
"""
