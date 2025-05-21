import asyncio
import pytest
from typing import Dict

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage

from aiplanet_core.model_context.summarizing_chat_context import SummarizingChatCompletionContext


@pytest.mark.skipif(not pytest.importorskip("azure"), reason="Azure OpenAI not installed")
@pytest.mark.integration
class TestSummarizingChatCompletionContextIntegration:
    """Integration tests for SummarizingChatCompletionContext with real API"""

    @pytest.fixture(scope="class")
    def azure_credentials(self) -> Dict[str, str]:
        """Fixture to provide Azure OpenAI credentials.

        For this to work, you need to set the following environment variables:
        - AZURE_ENDPOINT
        - AZURE_API_KEY
        - AZURE_DEPLOYMENT
        - AZURE_API_VERSION
        """
        import os

        env_vars = {
            "endpoint":  os.getenv("AZURE_ENDPOINT"),
            "api_key": os.getenv("AZURE_API_KEY"),
            "deployment": os.getenv("AZURE_DEPLOYMENT"),
            "api_version": os.getenv("AZURE_API_VERSION", "2023-07-01-preview"),
            "model": os.getenv("AZURE_OPEN_MODEL", "gpt-4o-mini"),
        }

        missing_vars = [k for k, v in env_vars.items() if not v]
        if missing_vars:
            pytest.skip(f"Missing environment variables: {', '.join(missing_vars)}")

        return env_vars

    @pytest.fixture
    def azure_model_client(self, azure_credentials):
        from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

        return AzureOpenAIChatCompletionClient(
            azure_endpoint=azure_credentials["endpoint"],
            api_key=azure_credentials["api_key"],
            azure_deployment=azure_credentials["deployment"],
            api_version=azure_credentials["api_version"],
            model=azure_credentials["model"]
        )

    @pytest.fixture
    def agent_with_summarizing_context(self, azure_model_client):
        context = SummarizingChatCompletionContext(
            recent_capacity=3,
            old_capacity=5,
            model_client=azure_model_client
        )

        return AssistantAgent(
            name="test_agent",
            model_client=azure_model_client,
            model_context=context,
            system_message="You are a helpful assistant with excellent memory."
        )

    @pytest.mark.asyncio
    async def test_conversation_with_summarization(self, agent_with_summarizing_context):
        agent = agent_with_summarizing_context
        context = agent.model_context

        questions = [
            "What is machine learning?",
            "What are neural networks?",
            "What are transformers in deep learning?",
            "What is BERT?",
            "What is GPT?",
            "What is reinforcement learning?",
            "What is transfer learning?",
            "What is fine-tuning?",
            "What is zero-shot learning?",
            "What is few-shot learning?",
        ]

        for question in questions:
            response = await agent.on_messages([TextMessage(content=question, source="user")], None)
            assert response.chat_message.content.strip(), "Empty response received"

            messages = await context.get_messages()
            recent_count = len(context._recent_messages)
            old_count = len(context._old_messages)

        messages = await context.get_messages()
        assert len(messages) < (len(questions) * 2 + 1)

        memory_question = "Earlier we discussed machine learning. What is it and how does it relate to neural networks?"
        response = await agent.on_messages([TextMessage(content=memory_question, source="user")], None)

        content = response.chat_message.content.lower()
        assert "machine learning" in content and "neural network" in content

    @pytest.mark.asyncio
    async def test_topic_switch_memory(self, agent_with_summarizing_context):
        agent = agent_with_summarizing_context
        context = agent.model_context

        await agent.on_messages([TextMessage(content="Pluto was reclassified as a dwarf planet in 2006.", source="user")], None)

        astronomy_questions = [
            "What is a black hole?",
            "What is a neutron star?",
            "What is dark matter?",
            "What is dark energy?",
            "What is the Big Bang theory?",
            "What are exoplanets?",
        ]

        for question in astronomy_questions:
            await agent.on_messages([TextMessage(content=question, source="user")], None)

        history_questions = [
            "Who was Alexander the Great?",
            "What was the Byzantine Empire?",
            "Who was Napoleon Bonaparte?",
            "What was the Renaissance?",
            "What was the Industrial Revolution?",
        ]

        for question in history_questions:
            await agent.on_messages([TextMessage(content=question, source="user")], None)

        messages = await context.get_messages()
        assert len(messages) < (len(astronomy_questions) + len(history_questions) + 3)

        pluto_question = "What happened to Pluto's classification and when?"
        response = await agent.on_messages([TextMessage(content=pluto_question, source="user")], None)
        content = response.chat_message.content.lower()
        assert "2006" in content and "dwarf planet" in content

# Entry point for CLI-based test execution
if __name__ == "__main__":
    import pytest
    import sys

    sys.exit(pytest.main([
        "-xvs",
        __file__
    ]))
