import asyncio
import time
from typing import List

from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.ui import Console

from aiplanet_core.model_context.summarizing_chat_context import SummarizingChatCompletionContext


async def generate_conversation(
    agent: AssistantAgent, 
    questions: List[str],
    pause_seconds: float = 1.0,
    show_context_size: bool = True
) -> None:
    """Generate a conversation with the agent by asking a series of questions.
    
    Args:
        agent: The agent to converse with
        questions: List of questions to ask
        pause_seconds: Time to pause between questions
        show_context_size: Whether to show the context size after each question
    """
    for i, question in enumerate(questions):
        print(f"\n\n---------- Question {i+1}/{len(questions)} ----------")
        print(f"User: {question}")
        
        # Send the question to the agent
        response = await agent.on_messages([TextMessage(content=question, source="user")], None)
        print(f"Agent: {response.chat_message.content}")
        
        # Optionally show context size
        if show_context_size and hasattr(agent, "model_context"):
            messages = await agent.model_context.get_messages()
            recent_count = len(agent.model_context._recent_messages) if hasattr(agent.model_context, "_recent_messages") else 0
            old_count = len(agent.model_context._old_messages) if hasattr(agent.model_context, "_old_messages") else 0
            print(f"\nContext stats - Total: {len(messages)}, Recent: {recent_count}, Old: {old_count}")
        
        # Pause between questions
        if i < len(questions) - 1:
            time.sleep(pause_seconds)


async def main() -> None:
    # Create a model client for both agent responses and summarization
    model_client = AzureOpenAIChatCompletionClient(
        azure_deployment="",
        api_key="",
        api_version="",
        azure_endpoint="",
        model="gpt-4o-mini"
    )
    
    # Create a summarizing context with small capacities to demonstrate summarization
    # In real applications, you'd likely use larger values (e.g., recent_capacity=20, old_capacity=50)
    summarizing_context = SummarizingChatCompletionContext(
        recent_capacity=3,  # Keep only 3 most recent messages before moving to old bucket
        old_capacity=5,     # Summarize after 5 messages in the old bucket
        model_client=model_client,  # Use the same model client for summarization
        summarize_prompt=(
            "Summarize the following conversation snippets concisely while preserving key information "
            "about the topics discussed. Focus on facts and information that may be needed later."
        )
    )
    
    # Create the assistant agent with our summarizing context
    agent = AssistantAgent(
        name="Knowledge_Assistant",
        model_client=model_client,
        model_context=summarizing_context,
        system_message=(
            "You are a knowledgeable assistant who provides helpful, accurate, and concise information "
            "on a variety of topics. Maintain a friendly tone and build upon previously discussed topics "
            "when relevant."
        )
    )
    
    # List of questions for a conversation that builds knowledge incrementally
    questions = [
        "What are the main features of Python?",
        "How does Python handle memory management?",
        "Tell me about list comprehensions in Python.",
        "What are some common Python design patterns?",
        "How does Python's Global Interpreter Lock work?",
        "What are some alternatives to the GIL?",
        "How do Python decorators work?",
        "Can you explain context managers in Python?",
        "What's the difference between __new__ and __init__ in Python classes?",
        "What are metaclasses in Python?",
        "Now, let's switch topics. Tell me about black holes.",
        "What is Hawking radiation?",
        "How do black holes evaporate?",
        "What happens when two black holes merge?",
        "Actually, let's go back to Python. Can you remind me how decorators work?",
    ]
    
    # Run the conversation
    await generate_conversation(agent, questions)
    
    # Now demonstrate a follow-up question that requires summarized context
    print("\n\n---------- Testing Memory ----------")
    memory_question = "What topics have we discussed so far in our conversation?"
    print(f"User: {memory_question}")
    
    response = await agent.on_messages([TextMessage(content=memory_question, source="user")], None)
    print(f"Agent: {response.chat_message.content}")


if __name__ == "__main__":
    asyncio.run(main())