import asyncio
from typing import List

from autogen_core import CancellationToken
from autogen_core.models import (
    UserMessage, 
    SystemMessage, 
    AssistantMessage,
    LLMMessage
)
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

# Import your model client
# For example:
# from autogen_ext.models.openai import OpenAIChatCompletionClient
# Or use an in-process model when available:
# from autogen_ext.models.fastembed import FastEmbedClient

# Import our new context class
from aiplanet_core.model_context.summarizing_chat_context import SummarizingChatCompletionContext

async def main():
    """Example of using SummarizingChatCompletionContext."""
    
    # Set up a model client for summarization
    # If you're using OpenAI:
    model_client = AzureOpenAIChatCompletionClient(
        azure_deployment="",
        api_key="",
        api_version="",
        azure_endpoint="",
        model="gpt-4o-mini"
    )
    
    # Create context with relatively small capacities for demonstration
    context = SummarizingChatCompletionContext(
        recent_capacity=5,  # Keep only 5 recent messages
        old_capacity=10,    # Keep 10 old messages before summarizing
        model_client=model_client  # Uncomment to enable summarization
    )
    
    # Add system message
    await context.add_message(SystemMessage(
        content="You are a helpful assistant that provides concise answers."
    ))
    
    # Simulate a conversation
    conversation_pairs = [
        ("What is machine learning?", "Machine learning is a field of artificial intelligence that uses statistical techniques to give computer systems the ability to 'learn' from data, without being explicitly programmed."),
        ("How does supervised learning work?", "Supervised learning works by training a model on labeled data, where the correct outputs are provided. The model learns to map inputs to outputs by minimizing the error between its predictions and the true labels."),
        ("What's the difference between classification and regression?", "Classification predicts discrete class labels or categories, while regression predicts continuous values. For example, predicting if an email is spam (classification) versus predicting a house price (regression)."),
        ("What is overfitting?", "Overfitting occurs when a model learns the training data too well, including its noise and outliers. This results in poor generalization to new, unseen data. It's like memorizing answers instead of understanding concepts."),
        ("How can I prevent overfitting?", "You can prevent overfitting by: 1) Using more training data, 2) Applying regularization techniques, 3) Using simpler models, 4) Early stopping during training, 5) Using techniques like cross-validation, and 6) Implementing dropout in neural networks."),
        ("What is cross-validation?", "Cross-validation is a technique to evaluate a model's performance by partitioning the data into multiple subsets. The most common form is k-fold cross-validation, where data is split into k folds, training on k-1 folds and validating on the remaining fold, repeating k times with different validation folds."),
        ("What are decision trees?", "Decision trees are tree-like models where internal nodes represent feature tests, branches represent outcomes of tests, and leaf nodes represent class labels or continuous values. They make decisions by following a path from root to leaf based on feature values."),
        ("What is ensemble learning?", "Ensemble learning combines multiple models to improve performance beyond what any individual model could achieve. Common methods include bagging (e.g., Random Forest), boosting (e.g., XGBoost), and stacking, which use different strategies to create and combine diverse models."),
        ("What is deep learning?", "Deep learning is a subset of machine learning that uses neural networks with multiple layers (deep neural networks) to progressively extract higher-level features from raw input. It's particularly powerful for complex tasks like image recognition, natural language processing, and speech recognition."),
        ("Explain convolutional neural networks", "Convolutional Neural Networks (CNNs) are specialized neural networks designed primarily for processing grid-like data such as images. They use convolutional layers to detect spatial patterns, pooling layers to reduce dimensionality, and fully connected layers for final predictions. CNNs have revolutionized computer vision tasks."),
        ("What is reinforcement learning?", "Reinforcement learning is a type of machine learning where an agent learns to make decisions by taking actions in an environment to maximize cumulative rewards. It's based on trial and error, with the agent receiving feedback through rewards or penalties and learning optimal strategies over time."),
        ("What is transfer learning?", "Transfer learning involves taking a pre-trained model developed for one task and repurposing it for a related task. This approach leverages knowledge gained from solving one problem to improve generalization in another, reducing training time and data requirements."),
        ("What are GANs?", "Generative Adversarial Networks (GANs) consist of two neural networks—a generator and a discriminator—that compete against each other. The generator creates fake data samples trying to fool the discriminator, while the discriminator tries to distinguish real data from fake. Through this adversarial process, GANs learn to generate increasingly realistic data."),
        ("Explain LSTM networks", "Long Short-Term Memory (LSTM) networks are a specialized form of recurrent neural networks designed to remember long-term dependencies in sequence data. They use a cell state and various gates (input, forget, output) to regulate the flow of information, making them effective for tasks involving sequential data like text, speech, and time series."),
        ("What is NLP?", "Natural Language Processing (NLP) is a field at the intersection of linguistics, computer science, and AI focused on enabling computers to understand, interpret, and generate human language. NLP powers applications like machine translation, sentiment analysis, chatbots, and voice assistants."),
    ]
    
    # Add messages to the context
    for i, (user_question, assistant_response) in enumerate(conversation_pairs):
        print(f"Adding conversation pair {i+1}/{len(conversation_pairs)}")
        
        # Add user message
        await context.add_message(UserMessage(
            content=user_question,
            source="user"
        ))
        
        # Add assistant response
        await context.add_message(AssistantMessage(
            content=assistant_response,
            source="assistant"
        ))
        
        # Print current state after each pair
        messages = await context.get_messages()
        print(f"Current context has {len(messages)} messages:")
        for j, msg in enumerate(messages):
            # Truncate content for display
            content = str(msg.content)
            if len(content) > 50:
                content = content[:47] + "..."
            print(f"  {j+1}. {msg.__class__.__name__}: {content}")
        print()
    
    print("Final context:")
    final_messages = await context.get_messages()
    print(f"The context contains {len(final_messages)} messages in total")
    print(f"- Old bucket: {len(context._old_messages)} messages")
    print(f"- Recent bucket: {len(context._recent_messages)} messages")
    
    # Show all messages in detail
    print("\nComplete context content:")
    for i, msg in enumerate(final_messages):
        print(f"\nMessage {i+1} ({msg.__class__.__name__}):")
        print(f"{msg.content}")

if __name__ == "__main__":
    asyncio.run(main())