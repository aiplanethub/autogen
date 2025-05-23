from autogen_agentchat.agents import AssistantAgent
import asyncio
import os
import sys
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from aiplanet_core.tools.prompt_template import PromptTemplateTool

az_model_client = AzureOpenAIChatCompletionClient(
        azure_deployment=os.getenv("AZURE_DEPLOYMENT"),
        model=os.getenv("AZURE_MODEL"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
        api_key=os.getenv("AZURE_API_KEY"),
    )


async def prompt_template_example():
    tool = PromptTemplateTool()
    agent = AssistantAgent(
        "assistant",
        model_client=az_model_client,  
        tools=[tool],
        reflect_on_tool_use=True
    )
    async for response in agent.run_stream(
        task="Generate a system prompt for an AI assistant that helps users with travel planning."
    ):
        print(response)

# To run this example, uncomment the following lines:
if __name__ == "__main__":
    asyncio.run(prompt_template_example())
