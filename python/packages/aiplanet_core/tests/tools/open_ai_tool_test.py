from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from aiplanet_core.tools.OpenAI import OpenAITool

az_model_client = AzureOpenAIChatCompletionClient(
        azure_deployment=os.getenv("AZURE_DEPLOYMENT"),
        model=os.getenv("AZURE_MODEL"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
        api_key=os.getenv("AZURE_API_KEY"),
    )

async def main():
    # Initialize the tool
    openai_tool = OpenAITool()
    
    
    model_client=az_model_client
    # Create an agent with the tool
    agent = AssistantAgent(
        "assistant",
        model_client=az_model_client,
        tools=[openai_tool],
        reflect_on_tool_use=True
    )
    
    # Use the agent
    async for response in agent.run_stream(
        task="Explain quantum computing in simple terms"
    ):
        print(response)

if __name__ == "__main__":
    asyncio.run(main())