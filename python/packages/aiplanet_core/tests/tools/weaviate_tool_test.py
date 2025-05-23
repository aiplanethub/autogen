from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from aiplanet_core.tools.weaviate import WeaviateSearchTool, WeaviateSearchInput
from aiplanet_core.tools.weaviate.weaviate_service import WeaviateService


az_model_client = AzureOpenAIChatCompletionClient(
        azure_deployment=os.getenv("AZURE_DEPLOYMENT"),
        model=os.getenv("AZURE_MODEL"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
        api_key=os.getenv("AZURE_API_KEY"),
    )


async def main():
    
    collection_name = "test_collections"
        
        # Sample documents to add to Weaviate
    documents = [
    {
        "content": (
            "In 2023, the city of Amsterdam implemented an AI-driven traffic management system to reduce congestion in the city center. "
            "Using real-time data from traffic cameras, GPS devices in public transport, and weather sensors, the system dynamically adjusted traffic lights and provided alternate routing to vehicles via a mobile app. "
            "A reinforcement learning algorithm was trained to optimize traffic flow patterns based on historical data and current conditions. "
            "Over the first six months, average commute times dropped by 18%, and carbon emissions in high-traffic zones decreased by 12%. "
            "However, the system faced challenges in adapting to large-scale public events and protests, where human intervention was still necessary. "
            "Despite these limitations, the project is now being studied by other cities looking to adopt smart traffic solutions."
        ),
        "title": "AI-Powered Traffic Management in Amsterdam"
    },
    {
        "content": (
            "During the COVID-19 pandemic, a mid-sized hospital in South Korea developed an NLP-based chatbot named 'MediTalk' to handle patient inquiries. "
            "The chatbot was integrated with the hospital’s EHR (Electronic Health Records) and could answer questions about symptoms, test results, and appointment schedules. "
            "Built using a fine-tuned BERT model trained on Korean medical datasets, MediTalk handled over 5,000 patient queries a day during peak outbreak periods. "
            "Patients reported high satisfaction, particularly older adults who found the voice interface easier to use than navigating the hospital’s website. "
            "However, MediTalk struggled with ambiguous or emotionally charged questions, such as those related to end-of-life care, leading to the inclusion of a fallback to human staff. "
            "The chatbot is now a permanent fixture of the hospital's digital ecosystem, with ongoing improvements based on feedback logs."
        ),
        "title": "MediTalk: A Medical NLP Chatbot During the Pandemic"
    },
    {
        "content": (
            "A vineyard in northern California began using drone-based computer vision to monitor grape ripeness and disease in real time. "
            "The drones captured high-resolution images across thousands of acres, which were then processed using a CNN trained on labeled grape cluster data. "
            "The system could identify subtle signs of mildew and differentiate between ripe, underripe, and overripe grapes based on color, texture, and cluster density. "
            "This allowed vineyard managers to make harvesting decisions with unprecedented precision. "
            "In one season, the system helped increase wine yield quality ratings by 22% while reducing pesticide use by 30%. "
            "However, extreme lighting conditions and unexpected foliage growth sometimes interfered with model accuracy, leading the team to explore multimodal sensor integration (e.g., infrared and thermal)."
        ),
        "title": "Computer Vision in Precision Viticulture"
    }
]

        
        # Add documents to Weaviate
    print(f"Adding documents to Weaviate collection '{collection_name}'...")
    async with WeaviateService() as weaviate_service:
        for doc in documents:
                weaviate_service.add(
                    collection_name=collection_name,
                    properties=doc
                )
        print(f"Successfully added {len(documents)} documents to collection")
    

    # Initialize the Weaviate search tool
    weaviate_tool = WeaviateSearchTool()

    # Create an agent with the tool
    agent = AssistantAgent(
        "assistant",
        model_client=az_model_client,
        tools=[weaviate_tool],
        reflect_on_tool_use=True
    )
    
    # Use the agent to perform a search
    async for response in agent.run_stream(
        task="What kind of data sources were used in Amsterdam’s AI-driven traffic system? Search in the 'test_collections' collection "
    ):
        print(response)

if __name__ == "__main__":
    asyncio.run(main())