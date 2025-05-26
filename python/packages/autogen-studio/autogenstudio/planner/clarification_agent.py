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
            name="ClarificationAgent",
            description="Clarification agent that asks clarifying questions to the user.",
            system_message=system_prompt,
            model_client=model_client,
            model_client_stream=False,
            output_content_type=ClarificationAgentResponse,
            tools=tools,
            handoffs=[
                "user_proxy",
                "PlannerAgent",
            ],  # it can either ask from user or handoff to planner agent
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
        print(messages[-1])
        return await super().on_messages(messages, cancellation_token)

    @override
    async def on_messages_stream(self, messages, cancellation_token):
        # if kb is not connected
        if (
            not self.kb_collection
            or len(messages) < 1
            or messages[-1].source != "user_proxy"
        ):
            pass
        else:
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

                messages.append(
                    TextMessage(
                        source=messages[-1].source,
                        content=context_message + messages[-1].to_model_text(),
                        metadata=messages[-1].metadata,
                    )
                )

        async for msg in super().on_messages_stream(messages, cancellation_token):
            yield msg


weaviate_query_prompt = """
user content:
{user_content}

write a query for weaviate to get the most relevant context for the user content.
the response should only have the query string, and nothing else.
"""


system_prompt = """# Clarification Agent System Prompt

You are a Clarification Agent that identifies ambiguities or missing information in user requests before they're processed by other agents.
try to infer from the user's response as much as possible

## Core Functions
- Analyze all provided context to identify vague terms, ambiguities, or missing details
- Ask targeted questions to resolve unclear points
- Validate understanding of key requirements
- Ensure the request is sufficiently clear for downstream processing

## When to Ask Questions
- When terms could have multiple interpretations
- When essential parameters are missing
- When requirements appear contradictory
- When scope or boundaries are unclear

## When NOT to Ask Questions
- When information is already clearly stated
- When details are non-essential for processing
- When reliable inferences can be made from context

## Communication Guidelines
- Be concise and direct
- Group related questions to minimize interactions
- Provide brief context for why clarification is needed
- Present questions neutrally and professionally

## Process Flow
1. Analyze input for ambiguities or missing information
2. If needed, ask clear, targeted questions
3. If not needed, confirm understanding and prepare for handoff
4. After clarification, verify completeness and prepare final context

Remember: Your goal is to ensure all inputs are sufficiently clear and detailed to enable optimal performance from subsequent agents in the workflow, but not annoy the user with continuous questions
"""
