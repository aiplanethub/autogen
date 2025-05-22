"""
Example demonstrating how to use the FileAgent with AutoGen.

This script shows how to instantiate a FileAgent, send file-based messages to it,
and handle the responses appropriately.
"""

import asyncio
import os
import tempfile
from typing import List

# Import our custom modules
from aiplanet_core.agents.file_agent import FileAgent
from autogen_agentchat.agents import AssistantAgent
from aiplanet_core.types.messages import (
    ExcelMessage,
    FileMessage,
    ImageMessage,
    JSONMessage,
    PDFMessage,
    PDFWithOCRMessage,
    register_file_message_types,
)
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.messages import MessageFactory, TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient


async def create_test_files() -> List[str]:
    """Create sample test files for the example."""

    # Create a temporary directory for the test files
    temp_dir = tempfile.mkdtemp()
    files = []

    # Create a simple JSON file
    json_file = os.path.join(temp_dir, "data.json")
    with open(json_file, "w") as f:
        f.write("""
        {
            "people": [
                {"name": "John", "age": 30, "city": "New York"},
                {"name": "Jane", "age": 25, "city": "San Francisco"},
                {"name": "Bob", "age": 40, "city": "Chicago"}
            ],
            "company": {
                "name": "Acme Corp",
                "founded": 1985,
                "active": true
            }
        }
        """)
    files.append(json_file)

    # Create a simple text file that we'll treat as a "PDF"
    # (For a real example, you would use an actual PDF)
    pdf_file = os.path.join(temp_dir, "document.pdf")
    with open(pdf_file, "w") as f:
        f.write("""
        This is a sample document that simulates a PDF.

        It contains multiple paragraphs of text that the FileAgent
        will process and extract information from. In a real-world
        scenario, this would be an actual PDF file with multiple
        pages, formatting, and possibly images.

        The FileAgent should be able to:
        1. Extract the text content
        2. Identify key information
        3. Answer questions about the document

        This is just a simple test file for demonstration purposes.
        """)
    files.append(pdf_file)

    # Create a simple CSV file that we'll treat as an Excel file
    excel_file = os.path.join(temp_dir, "spreadsheet.csv")
    with open(excel_file, "w") as f:
        f.write("""Name,Age,Department,Salary
John Doe,32,Engineering,85000
Jane Smith,28,Marketing,76000
Bob Johnson,45,Finance,120000
Alice Williams,36,Human Resources,82000
        """)
    files.append(excel_file)

    print(f"Created test files in {temp_dir}")
    return files


async def file_agent_example():
    """Run the FileAgent example."""

    # Create the OpenAI model client
    model_client = AzureOpenAIChatCompletionClient(
        azure_deployment="",
        api_key="",
        api_version="",
        azure_endpoint="",
        model="gpt-4o-mini"
    )

    # Create the file agent with proper configuration
    file_agent = FileAgent(
        name="file_assistant",
        model_client=model_client,
        description="An agent that processes and analyzes various file types",
        system_message="You are a helpful assistant that analyzes files. When given file content, analyze it and answer questions about it.",
        model_client_stream=False,  # Disable streaming to avoid issues
        ocr_enabled=False,  # Disable OCR since we're using text files
        extraction_depth=2,  # Medium extraction depth
        working_directory=os.getcwd(),  # Use current directory for file operations
    )

    try:
        # Create test files
        test_files = await create_test_files()
        
        # Create proper message types for each file
        messages = []
        
        for file_path in test_files:
            file_extension = os.path.splitext(file_path)[1].lower()
            filename = os.path.basename(file_path)
            
            print(f"Processing file: {filename}")
            
            if file_extension == ".json":
                messages.append(
                    JSONMessage(
                        source="user",
                        filepath=file_path,
                        filename=filename,
                        filetype="json"
                    )
                )
            elif file_extension == ".pdf":
                # For the text file that simulates a PDF
                messages.append(
                    PDFMessage(
                        source="user",
                        filepath="/Users/gourabsinha/Downloads/1/1106.4577v1.pdf",
                        filename="1106.4577v1.pdf",
                        filetype="application/pdf"
                    )
                )
            elif file_extension == ".csv":
                messages.append(
                    ExcelMessage(
                        source="user",
                        filepath=file_path,
                        filename=filename,
                        filetype="csv"
                    )
                )
            else:
                messages.append(
                    FileMessage(
                        source="user",
                        filepath=file_path,
                        filename=filename,
                        filetype=file_extension.lstrip(".")
                    )
                )
        
        # Create a question message
        question = TextMessage(
            source="user",
            content="Please analyze the files I've shared and tell me what information they contain. "
            "Then answer the following questions: "
            "1. How many people are in the JSON file and what are their names? "
            "2. What is the main topic of the text document? "
            "3. Who has the highest salary in the spreadsheet?",
        )
        
        # Add the question to the messages
        messages.append(question)
        
        # Run the file agent with all messages
        print("Running the file agent...")
        response = await file_agent.run(task=messages)
        
        # Print the response
        if response and response.messages:
            for msg in response.messages:
                print(f"---------- {msg.__class__.__name__} ({msg.source}) ----------")
                print(msg.content if hasattr(msg, 'content') else "No content")
        else:
            print("No response received from the file agent")

    except Exception as e:
        print(f"Error in file_agent_example: {str(e)}")
        import traceback
        traceback.print_exc()


async def file_agent_with_team_example():
    """Run an example with the FileAgent in a team."""

    # Create the OpenAI model client
    model_client = AzureOpenAIChatCompletionClient(
        azure_deployment="",
        api_key="",
        api_version="",
        azure_endpoint="",
        model="gpt-4o-mini"
    )

    # Create the file agent
    file_agent = FileAgent(
        name="file_processor",
        model_client=model_client,
        description="An agent that processes and extracts content from files",
        ocr_enabled=False,
        extraction_depth=2,
    )


    assistant_agent = AssistantAgent(
        name="analyst",
        model_client=model_client,
        description="An agent that analyzes and interprets information extracted from files",
        system_message="You analyze information extracted from files by the file_processor agent. "
        "Focus on providing insights, patterns, and answering user questions about the content.",
    )

    # Create a team
    termination = MaxMessageTermination(6)  # Limit to 6 messages
    # IMPORTANT: Include the custom message types when creating the team
    custom_message_types = [
        FileMessage,
        PDFMessage,
        PDFWithOCRMessage,
        JSONMessage,
        ImageMessage,
        ExcelMessage
    ]
    team = RoundRobinGroupChat(
        participants=[file_agent, assistant_agent],
        termination_condition=termination,
        custom_message_types=custom_message_types,
    )

    # Create test files
    test_files = await create_test_files()

    # Create file messages for the first file only (to keep the example simpler)
    json_file = [f for f in test_files if f.endswith(".json")][0]
    json_message = JSONMessage(
        source="user",
        filepath=json_file,
        filename=os.path.basename(json_file),
        filetype="json",
    )

    # Create a question message
    question = TextMessage(
        source="user",
        content="Here's a JSON file with information about people and a company. "
        "I'd like you to analyze it and provide insights about the data. "
        "What's the average age of the people? What city has the most people? "
        "When was the company founded?",
    )

    # Run the team
    print("Running the team with file agent and analyst...")
    response = await team.run(task=[json_message, question])
    
    # Print the response
    if response and response.messages:
        for msg in response.messages:
            print(f"---------- {msg.__class__.__name__} ({msg.source}) ----------")
            print(msg.content if hasattr(msg, 'content') else "No content")
    else:
        print("No response received from the team")


async def main():
    """Run the main example."""

    # Register file message types with the message factory
    message_factory = MessageFactory()
    register_file_message_types(message_factory)

    # Run the single agent example
    await file_agent_example()

    # Run the team example
    # await file_agent_with_team_example()


if __name__ == "__main__":
    asyncio.run(main())
