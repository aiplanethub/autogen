from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from aiplanet_core.tools.Google_search.google_search import GoogleSearchTool
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
import asyncio


az_model_client = AzureOpenAIChatCompletionClient(
        azure_deployment=os.getenv("AZURE_DEPLOYMENT"),
        model=os.getenv("AZURE_MODEL"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
        api_key=os.getenv("AZURE_API_KEY"),
    )


async def main():
    # Initialize the tool
    search_tool = GoogleSearchTool()
    
    model_client = az_model_client

    # Create an agent with the tool
    agent = AssistantAgent(
        "assistant",
        model_client=model_client,
        tools=[search_tool],
        reflect_on_tool_use=True
    )
    
    async for response in agent.run_stream(
        task="Search for the latest developments in AI and summarize them"
    ):
        print(response)

if __name__ == "__main__":
    asyncio.run(main())
