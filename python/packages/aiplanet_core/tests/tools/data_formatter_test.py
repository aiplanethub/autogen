import os
import sys
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from aiplanet_core.tools.data_formatter.data_formatter import DataFormatterTool
from autogen_agentchat.agents import AssistantAgent
import asyncio

az_model_client = AzureOpenAIChatCompletionClient(
        azure_deployment=os.getenv("AZURE_DEPLOYMENT"),
        model=os.getenv("AZURE_MODEL"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
        api_key=os.getenv("AZURE_API_KEY"),
    )

async def data_formatter_example():
    tool = DataFormatterTool()
    agent = AssistantAgent(
        "assistant",
        model_client=az_model_client,  
        tools=[tool],
        system_message="""You are a helpful assistant that formats data.
When asked to format data, you should:
1. Extract the data and the specififed format from the user's message and pass it to tool
2. Use the DataFormatter tool with BOTH the data object and format_type parameters
3. Return the formatted result""",
        reflect_on_tool_use=True
    )
    
 
    input_string = """
    I have this data I want in json format:
    name: Alice
    age: 30
    skills:
        - python
        - ml

    """
    
    async for response in agent.run_stream(task=input_string):
        print(response)

# To run this example
if __name__ == "__main__":
    asyncio.run(data_formatter_example())