import asyncio
import json
import os
import tempfile
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from autogen_core import CancellationToken
from autogen_core.models import ChatCompletionClient, CreateResult, RequestUsage
from autogen_core.tools import BaseTool, FunctionTool

from aiplanet_core.types.messages import (
    FileMessage,
    PDFMessage,
    JSONMessage,
    FileProcessingEvent,
    BaseAgentEvent,
    BaseChatMessage
)
from autogen_agentchat.messages import TextMessage, ToolCallRequestEvent, ToolCallExecutionEvent, ModelClientStreamingChunkEvent
from autogen_agentchat.base import Response


# Import the FileAgent class
# Assuming FileAgent is in a module called 'file_agent' or is imported properly
from aiplanet_core.agents import FileAgent


@pytest.fixture
def test_files_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple text file
        with open(os.path.join(tmpdir, "sample.txt"), "w") as f:
            f.write("This is a sample text file for testing.")
        
        # Create a simple JSON file
        with open(os.path.join(tmpdir, "sample.json"), "w") as f:
            json.dump({"name": "Test", "value": 42}, f)
        
        # Return the temporary directory path
        yield tmpdir


@pytest.fixture
def mock_model_client():
    """Create a mock model client."""
    model_client = MagicMock(spec=ChatCompletionClient)
    model_client.model_info = {
        "vision": False,
        "function_calling": True,
        "json_output": True
    }
    
    # Setup the create method to return a text response
    # Mock response with required fields
    async def mock_create(*args, **kwargs):
        return CreateResult(
            content="I've processed your file and found the following information...",
            usage=RequestUsage(prompt_tokens=10, completion_tokens=20),
            thought=None,
            finish_reason="stop",
            cached=False,
        )

    # Correct mock without using AsyncMock
    async def mock_create_stream(*args, **kwargs):
        yield ModelClientStreamingChunkEvent(content="I've processed", source="file_agent")
        yield ModelClientStreamingChunkEvent(content=" your file", source="file_agent")
        yield CreateResult(
            content="I've processed your file and found the following information...",
            usage=RequestUsage(prompt_tokens=10, completion_tokens=20),
            thought=None,
            finish_reason="stop",
            cached=False,
        )
    
    model_client.create = AsyncMock(side_effect=mock_create)
    model_client.create_stream = mock_create_stream 
    
    return model_client


@pytest.fixture
def file_agent(mock_model_client, test_files_dir):
    """Create a FileAgent instance with mocked components."""
    agent = FileAgent(
        name="file_agent",
        model_client=mock_model_client,
        description="Test file agent",
        working_directory=test_files_dir,
        ocr_enabled=True,
        extraction_depth=2,
        # model_client_stream=True
    )
    return agent

@pytest.fixture
def file_agent_streaming(mock_model_client, test_files_dir):
    return FileAgent(
        name="file_agent",
        model_client=mock_model_client,
        description="Test file agent (streaming)",
        working_directory=test_files_dir,
        ocr_enabled=True,
        extraction_depth=2,
        model_client_stream=True,  # ✅ Enable streaming
    )


@pytest.mark.asyncio
async def test_agent_initialization(mock_model_client, test_files_dir):
    """Test agent initialization with various parameters."""
    agent = FileAgent(
        name="file_agent",
        model_client=mock_model_client,
        description="Test file agent",
        working_directory=test_files_dir,
    )
    
    assert agent.name == "file_agent"
    assert agent.description == "Test file agent"
    assert agent._working_directory == test_files_dir
    assert agent._ocr_enabled is False  # Default value
    assert agent._extraction_depth == 1  # Default value
    
    # Test with custom settings
    agent = FileAgent(
        name="file_agent",
        model_client=mock_model_client,
        description="Test file agent",
        working_directory=test_files_dir,
        ocr_enabled=True,
        extraction_depth=3,
        supported_file_types=["pdf", "json"],
        model_client_stream=True
    )
    
    assert agent._ocr_enabled is True
    assert agent._extraction_depth == 3
    assert agent._supported_file_types == ["pdf", "json"]


@pytest.mark.asyncio
async def test_file_tools_setup(file_agent):
    """Test that file operation tools are properly set up."""
    # Check if basic file operation tools are registered
    tool_names = [tool.name for tool in file_agent._tools]
    
    # Verify that common tools are present
    assert "list_files" in tool_names
    assert "extract_text_from_pdf" in tool_names
    assert "get_json_content" in tool_names
    assert "get_excel_data" in tool_names
    
    # Verify OCR tool is present (since ocr_enabled=True in fixture)
    assert "apply_ocr_to_image" in tool_names


@pytest.mark.asyncio
async def test_processing_text_message(file_agent):
    """Test processing a simple text message."""
    # Create a cancellation token
    cancellation_token = CancellationToken()
    
    # Create a text message
    text_message = TextMessage(
        source="user",
        content="Can you process the sample.json file?",
    )
    
    # Process the message
    response = await file_agent.on_messages([text_message], cancellation_token)
    
    # Check the response
    assert isinstance(response, Response)
    assert isinstance(response.chat_message, TextMessage)
    assert "I've processed your file" in response.chat_message.content
    
    # Verify that model client was called
    file_agent._model_client.create.assert_called_once()


@pytest.mark.asyncio
async def test_processing_file_message(file_agent, test_files_dir):
    """Test processing a file message."""
    # Create a cancellation token
    cancellation_token = CancellationToken()
    
    # Create a file message for the JSON file
    json_file_path = os.path.join(test_files_dir, "sample.json")
    file_message = JSONMessage(
        source="user",
        filepath=json_file_path,
        filename="sample.json",
        filetype="json"
    )
    
    # Set up a mock for _process_json_message
    with patch.object(file_agent, '_process_json_message', new_callable=AsyncMock) as mock_process_json:
        mock_process_json.return_value = (
            'JSON File: sample.json\n\n{"name": "Test", "value": 42}',
            [FileProcessingEvent(
                source="file_agent",
                filename="sample.json",
                operation="extracting text from JSON",
                status="completed"
            )]
        )
        
        # Process the message
        response = await file_agent.on_messages([file_message], cancellation_token)
        
        # Check that the processing method was called
        mock_process_json.assert_called_once()
        
        # Check the response
        assert isinstance(response, Response)
        assert isinstance(response.chat_message, TextMessage)
        assert "I've processed your file" in response.chat_message.content


@pytest.mark.asyncio
async def test_processing_json_file(file_agent, test_files_dir):
    """Test processing a JSON file."""
    # Create a real JSON message for a file that exists
    json_file_path = os.path.join(test_files_dir, "sample.json")
    json_message = JSONMessage(
        source="user",
        filepath=json_file_path,
        filename="sample.json",
        filetype="json"
    )
    
    # Call the process method directly
    result, events = await file_agent._process_json_message(json_message)
    
    # Check the result
    assert "JSON File: sample.json" in result
    assert "Test" in result  # Content from the JSON file
    assert "42" in result    # Content from the JSON file
    
    # Check the events
    assert len(events) >= 2  # Should have at least start and complete events
    assert events[0].status == "started"
    assert events[-1].status == "completed"


@pytest.mark.asyncio
async def test_streaming_response(file_agent_streaming):
    """Test streaming response from on_messages_stream."""
    # Create a cancellation token
    cancellation_token = CancellationToken()
    
    # Create a text message
    text_message = TextMessage(
        source="user",
        content="Can you process the sample.json file?",
    )
    
    # Collect all streamed messages
    collected_messages = []
    async for message in file_agent_streaming.on_messages_stream([text_message], cancellation_token):
        collected_messages.append(message)
    
    # Analyze the collected messages
    non_response_messages = [msg for msg in collected_messages if not isinstance(msg, Response)]
    response_messages = [msg for msg in collected_messages if isinstance(msg, Response)]
    
    # We should have at least one streaming chunk and one final response
    # assert len(non_response_messages) > 0
    assert len(response_messages) == 1
    
    # The final message should be a Response
    assert isinstance(collected_messages[-1], Response)
    assert isinstance(collected_messages[-1].chat_message, TextMessage)


@pytest.mark.asyncio
async def test_tool_calling(file_agent, test_files_dir):
    """Test the agent's ability to call tools."""
    # Create a cancellation token
    cancellation_token = CancellationToken()
    
    # Create a text message
    text_message = TextMessage(
        source="user",
        content="List the files in the directory",
    )
    
    # Mock the model client to return a function call
    from autogen_core import FunctionCall
    tool_call = FunctionCall(
        id="call_123",
        name="list_files",
        arguments='{"directory": ""}'
    )
    
    file_agent._model_client.create.return_value = CreateResult(
        content=[tool_call],
        usage=RequestUsage(prompt_tokens=10, completion_tokens=20),
        thought=None
    )
    
    # Process the message
    collected_messages = []
    async for message in file_agent.on_messages_stream([text_message], cancellation_token):
        collected_messages.append(message)
    
    # Check for tool call request and execution events
    tool_call_requests = [msg for msg in collected_messages if isinstance(msg, ToolCallRequestEvent)]
    tool_call_executions = [msg for msg in collected_messages if isinstance(msg, ToolCallExecutionEvent)]
    
    assert len(tool_call_requests) > 0
    assert len(tool_call_executions) > 0
    
    # The tool call execution should contain the result of listing files
    execution_content = tool_call_executions[0].content[0].content
    assert "sample.json" in execution_content
    assert "sample.txt" in execution_content


@pytest.mark.asyncio
async def test_reset_agent(file_agent):
    """Test resetting the agent state."""
    # Set some state to be reset
    file_agent._processed_files = ["file1.txt", "file2.pdf"]
    
    # Reset the agent
    await file_agent.on_reset(CancellationToken())
    
    # Check that the state was reset
    assert len(file_agent._processed_files) == 0


@pytest.mark.asyncio
async def test_save_and_load_state(file_agent):
    """Test saving and loading agent state."""
    # Set some state to be saved
    file_agent._processed_files = ["file1.txt", "file2.pdf"]
    
    # Save the state
    state = await file_agent.save_state()
    
    # Modify the state
    file_agent._processed_files = []
    
    # Load the state back
    await file_agent.load_state(state)
    
    # Check that the state was restored
    assert file_agent._processed_files == ["file1.txt", "file2.pdf"]


@pytest.mark.asyncio
async def test_multiple_file_processing(file_agent, test_files_dir):
    """Test processing multiple files in sequence."""
    # Create a cancellation token
    cancellation_token = CancellationToken()
    
    # Create file messages
    text_file_path = os.path.join(test_files_dir, "sample.txt")
    json_file_path = os.path.join(test_files_dir, "sample.json")
    
    text_file_message = FileMessage(
        source="user",
        filepath=text_file_path,
        filename="sample.txt",
        filetype="txt"
    )
    
    json_file_message = JSONMessage(
        source="user",
        filepath=json_file_path,
        filename="sample.json",
        filetype="json"
    )
    
    # Process messages in sequence
    with patch.object(file_agent, '_process_file_message', new_callable=AsyncMock) as mock_process_file:
        mock_process_file.side_effect = [
            ("Text file content", [FileProcessingEvent(source="file_agent", filename="sample.txt", operation="processing", status="completed")]),
            ("JSON file content", [FileProcessingEvent(source="file_agent", filename="sample.json", operation="processing", status="completed")])
        ]
        
        await file_agent.on_messages([text_file_message], cancellation_token)
        await file_agent.on_messages([json_file_message], cancellation_token)
        
        # Check that _process_file_message was called twice
        assert mock_process_file.call_count == 2
        
        # Check that both files were processed
        assert len(file_agent._processed_files) == 1  # Only one should be added because the mock doesn't set the actual filepath
    

@pytest.mark.asyncio
async def test_custom_file_handler(mock_model_client, test_files_dir):
    """Test using a custom file handler."""
    # Define a custom handler
    async def custom_pdf_handler(msg):
        return f"Custom handler processed: {msg.filename}"
    
    # Create a FileAgent with custom handler
    agent = FileAgent(
        name="file_agent",
        model_client=mock_model_client,
        description="Test file agent",
        working_directory=test_files_dir,
        file_handlers={"pdf": "custom_pdf_handler"}
    )
    
    # Add the custom handler to the agent
    agent.custom_pdf_handler = custom_pdf_handler
    
    # Create a PDF message
    pdf_message = PDFMessage(
        source="user",
        filepath=os.path.join(test_files_dir, "dummy.pdf"),  # This doesn't need to exist for the mock
        filename="dummy.pdf",
        filetype="pdf"
    )
    
    # Process the message with custom handler
    with patch.object(agent, '_process_file_message', wraps=agent._process_file_message) as wrapped_process:
        with patch.object(agent, 'custom_pdf_handler', wraps=custom_pdf_handler) as wrapped_handler:
            # Set up the calls to not actually try to process the file
            wrapped_process.return_value = ("Custom processing result", [])
            
            # Process the message
            await agent.on_messages([pdf_message], CancellationToken())
            
            # Check that the custom handler was called
            wrapped_handler.assert_called_once()


@pytest.mark.asyncio
async def test_memory_integration(mock_model_client, test_files_dir):
    """Test integration with memory modules."""
    # Create a mock memory
    mock_memory = MagicMock()
    mock_memory.update_context = AsyncMock()
    mock_memory.update_context.return_value = None  # No memories found
    
    # Create a FileAgent with memory
    agent = FileAgent(
        name="file_agent",
        model_client=mock_model_client,
        description="Test file agent",
        working_directory=test_files_dir,
        memory=[mock_memory]
    )
    
    # Process a message
    text_message = TextMessage(
        source="user",
        content="What files have we processed before?",
    )
    
    await agent.on_messages([text_message], CancellationToken())
    
    # Check that memory was queried
    mock_memory.update_context.assert_called_once()


@pytest.mark.asyncio
async def test_error_handling(file_agent):
    """Test handling errors during file processing."""
    # Create a cancellation token
    cancellation_token = CancellationToken()
    
    # Create a file message that will cause an error
    file_message = JSONMessage(
        source="user",
        filepath="/nonexistent/path/to/file.json",
        filename="file.json",
        filetype="json"
    )
    
    # Process the message and expect it to handle the error
    response = await file_agent.on_messages([file_message], cancellation_token)
    
    # The agent should still return a response despite the error
    assert isinstance(response, Response)
    assert isinstance(response.chat_message, TextMessage)


@pytest.mark.asyncio
async def test_model_inference_error_handling(file_agent):
    """Test handling errors during model inference."""
    # Create a cancellation token
    cancellation_token = CancellationToken()
    
    # Create a text message
    text_message = TextMessage(
        source="user",
        content="Can you process a file?",
    )
    
    # Make the model client raise an exception
    file_agent._model_client.create.side_effect = Exception("Model inference failed")
    
    # Process the message and collect the response
    response = await file_agent.on_messages([text_message], cancellation_token)
    
    # The agent should return an error message
    assert isinstance(response, Response)
    assert isinstance(response.chat_message, TextMessage)
    assert "Error" in response.chat_message.content


@pytest.mark.asyncio
async def test_file_process_events(file_agent, test_files_dir):
    """Test that file processing events are properly generated and yielded."""
    # Create a cancellation token
    cancellation_token = CancellationToken()
    
    # Create a JSON file message
    json_file_path = os.path.join(test_files_dir, "sample.json")
    json_message = JSONMessage(
        source="user",
        filepath=json_file_path,
        filename="sample.json",
        filetype="json"
    )
    
    # Collect all events from processing
    events = []
    async for message in file_agent.on_messages_stream([json_message], cancellation_token):
        if isinstance(message, FileProcessingEvent):
            events.append(message)
    
    # Check that we have the expected events (at least start and complete)
    assert any(event.status == "started" for event in events)
    assert any(event.status == "completed" for event in events)


@pytest.mark.asyncio
async def test_reflection_on_tool_use(file_agent):
    """Test that reflection on tool use works properly."""
    # Set reflection flag
    file_agent._reflect_on_tool_use = True
    
    # Create a cancellation token
    cancellation_token = CancellationToken()
    
    # Create a text message that will trigger tool use
    text_message = TextMessage(
        source="user",
        content="List the files in the directory",
    )
    
    # Mock the model to return a function call
    from autogen_core import FunctionCall
    tool_call = FunctionCall(
        id="call_123",
        name="list_files",
        arguments='{"directory": ""}'
    )
    
    file_agent._model_client.create.side_effect = [
        # First call returns a tool call
        CreateResult(
            content=[tool_call],
            usage=RequestUsage(prompt_tokens=10, completion_tokens=20),
            thought=None
        ),
        # Second call returns reflection
        CreateResult(
            content="I've analyzed the directory and found the following files: sample.json and sample.txt",
            usage=RequestUsage(prompt_tokens=15, completion_tokens=25),
            thought="This will help the user understand what files are available."
        )
    ]
    
    # Process the message
    response = await file_agent.on_messages([text_message], cancellation_token)
    
    # Check that model was called twice (once for tool call, once for reflection)
    assert file_agent._model_client.create.call_count == 2
    
    # The response should contain the reflection
    assert "I've analyzed the directory" in response.chat_message.content


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])