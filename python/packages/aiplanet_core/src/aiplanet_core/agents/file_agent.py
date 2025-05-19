"""
FileAgent: An agent that specializes in processing file-based messages and performing operations on them.

This module provides a specialized agent for the AutoGen framework that can handle file-based
messages like PDFs, JSON files, images, and Excel files.
"""

import asyncio
import json
import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Mapping, Optional, Sequence, Union, cast

from autogen_core import CancellationToken, Component, ComponentModel, FunctionCall
from autogen_core.memory import Memory
from autogen_core.model_context import (
    ChatCompletionContext,
    UnboundedChatCompletionContext,
)
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    CreateResult,
    FunctionExecutionResult,
    FunctionExecutionResultMessage,
    LLMMessage,
    SystemMessage,
    UserMessage,
)
from autogen_core.tools import BaseTool, FunctionTool, StaticWorkbench, Workbench
from pydantic import BaseModel, Field

from autogen_agentchat.agents._base_chat_agent import BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import (
    BaseAgentEvent,
    BaseChatMessage,
    MemoryQueryEvent,
    MessageFactory,
    ModelClientStreamingChunkEvent,
    TextMessage,
    ThoughtEvent,
    ToolCallExecutionEvent,
    ToolCallRequestEvent,
    ToolCallSummaryMessage,
)
from autogen_agentchat.state import BaseState
from autogen_agentchat.utils import remove_images

# Import the file message types
# Assuming the modified message types from the previous artifact
from aiplanet_core.types.messages import (
    FileMessage,
    PDFMessage,
    PDFWithOCRMessage, 
    JSONMessage,
    ImageMessage,
    ExcelMessage,
    register_file_message_types
)

# Setup logging
logger = logging.getLogger(__name__)


class FileAgentState(BaseState):
    """State for a file agent."""

    llm_context: Mapping[str, Any] = Field(default_factory=lambda: dict([("messages", [])]))
    processed_files: List[str] = Field(default_factory=list)
    type: str = Field(default="FileAgentState")


class FileAgentConfig(BaseModel):
    """The declarative configuration for the FileAgent."""

    name: str
    model_client: ComponentModel
    tools: List[ComponentModel] | None = None
    workbench: ComponentModel | None = None
    model_context: ComponentModel | None = None
    memory: List[ComponentModel] | None = None
    description: str
    system_message: str | None = None
    model_client_stream: bool = False
    supported_file_types: List[str] | None = None  # File extensions to support
    ocr_enabled: bool = False
    extraction_depth: int = 1  # How deep to extract content from files
    file_handlers: Dict[str, str] | None = None  # Custom handlers for file types
    working_directory: str | None = None
    metadata: Dict[str, Any] | None = None
    reflect_on_tool_use: bool = True  # Default to True for file agent


class FileAgent(BaseChatAgent, Component[FileAgentConfig]):
    """An agent that specializes in processing files and answering questions about them.

    The agent can handle various file types including PDFs, images, JSON, and Excel files.
    It automatically extracts content from these files and includes it in responses to user queries.

    Args:
        name (str): The name of the agent.
        model_client (ChatCompletionClient): The model client to use for inference.
        tools (List[BaseTool[Any, Any]] | None, optional): 
            Additional tools to register with the agent.
        workbench (Workbench | None, optional): The workbench to use for the agent.
        model_context (ChatCompletionContext | None, optional): The model context for storing and retrieving messages.
        memory (Sequence[Memory] | None, optional): The memory store to use for the agent.
        description (str, optional): The description of the agent.
        system_message (str, optional): The system message for the model.
        model_client_stream (bool, optional): Whether to use streaming for model responses.
        supported_file_types (List[str] | None, optional): List of file extensions to support (e.g., ["pdf", "json"]).
            If None, all supported file types are enabled.
        ocr_enabled (bool, optional): Whether to enable OCR for images and PDFs.
        extraction_depth (int, optional): How deeply to extract content from files (1-3).
        file_handlers (Dict[str, str] | None, optional): Custom handlers for specific file types.
        working_directory (str | None, optional): Directory for file operations. Defaults to current directory.
        reflect_on_tool_use (bool, optional): If True, the agent will make another model inference using the tool call
            results to generate a response. Defaults to True.
        metadata (Dict[str, Any] | None, optional): Additional metadata for the agent.
    """

    component_config_schema = FileAgentConfig
    component_provider_override = "autogen_agentchat.agents.FileAgent"

    DEFAULT_SYSTEM_MESSAGE = """You are a File Processing Assistant that specializes in extracting and analyzing information from various file types.
You can work with PDFs, images, JSON files, Excel spreadsheets, and more. 
When provided with files, you'll automatically extract their contents and help answer questions about them.
For images and PDFs, you can extract text using OCR if needed.
Always be specific about what you find in the files and cite the source when answering questions."""

    def __init__(
        self,
        name: str,
        model_client: ChatCompletionClient,
        *,
        tools: List[BaseTool[Any, Any]] | None = None,
        workbench: Workbench | None = None,
        model_context: ChatCompletionContext | None = None,
        memory: Sequence[Memory] | None = None,
        description: str = "An agent that specializes in processing and analyzing files",
        system_message: str | None = DEFAULT_SYSTEM_MESSAGE,
        model_client_stream: bool = False,
        supported_file_types: List[str] | None = None,
        ocr_enabled: bool = False,
        extraction_depth: int = 1,
        file_handlers: Dict[str, str] | None = None,
        working_directory: str | None = None,
        reflect_on_tool_use: bool = True,
        metadata: Dict[str, Any] | None = None,
    ):
        super().__init__(name=name, description=description)
        self._metadata = metadata or {}
        self._model_client = model_client
        self._model_client_stream = model_client_stream
        self._supported_file_types = supported_file_types
        self._ocr_enabled = ocr_enabled
        self._extraction_depth = max(1, min(extraction_depth, 3))  # Clamp between 1 and 3
        self._file_handlers = file_handlers or {}
        self._working_directory = working_directory or os.getcwd()
        self._processed_files: List[str] = []
        self._reflect_on_tool_use = reflect_on_tool_use

        # Initialize memory
        self._memory = None
        if memory is not None:
            if isinstance(memory, list):
                self._memory = memory
            else:
                raise TypeError(f"Expected Memory, List[Memory], or None, got {type(memory)}")

        # Initialize the message factory with file message types
        self._message_factory = MessageFactory()
        register_file_message_types(self._message_factory)

        # Set up system messages
        self._system_messages: List[SystemMessage] = []
        if system_message is not None:
            self._system_messages = [SystemMessage(content=system_message)]

        # Set up tools
        self._tools: List[BaseTool[Any, Any]] = []
        if tools is not None:
            for tool in tools:
                if isinstance(tool, BaseTool):
                    self._tools.append(tool)
                else:
                    raise ValueError(f"Unsupported tool type: {type(tool)}")
            
            # Check if tool names are unique
            tool_names = [tool.name for tool in self._tools]
            if len(tool_names) != len(set(tool_names)):
                raise ValueError(f"Tool names must be unique: {tool_names}")

        # Set up file operation tools
        self._setup_file_tools()

        # Set up workbench with tools
        if workbench is not None:
            if self._tools:
                raise ValueError("Tools cannot be used with a workbench.")
            self._workbench = workbench
        else:
            self._workbench = StaticWorkbench(self._tools)

        # Set up model context
        if model_context is not None:
            self._model_context = model_context
        else:
            self._model_context = UnboundedChatCompletionContext()

    def _setup_file_tools(self):
        """Set up tools for file operations."""
        
        async def list_files(directory: str = "") -> str:
            """List files in the specified directory or the working directory."""
            target_dir = os.path.join(self._working_directory, directory) if directory else self._working_directory
            if not os.path.exists(target_dir):
                return f"Error: Directory {target_dir} does not exist."
            
            files = os.listdir(target_dir)
            return json.dumps({"files": files})
        
        async def extract_text_from_pdf(filepath: str) -> str:
            """Extract text from a PDF file."""
            full_path = os.path.join(self._working_directory, filepath)
            if not os.path.exists(full_path):
                return f"Error: File {filepath} does not exist."
            
            try:
                # Create a PDF message and extract text
                pdf_msg = PDFMessage(
                    source=self.name, 
                    filepath=full_path, 
                    filename=os.path.basename(full_path),
                    filetype="pdf"
                )
                text = await pdf_msg.extract_text()
                return text
            except Exception as e:
                return f"Error extracting text from PDF: {str(e)}"
                
        async def apply_ocr_to_image(filepath: str, language: str = "") -> str:
            """Apply OCR to an image or PDF file."""
            if not self._ocr_enabled:
                return "Error: OCR is not enabled for this agent."
                
            full_path = os.path.join(self._working_directory, filepath)
            if not os.path.exists(full_path):
                return f"Error: File {filepath} does not exist."
                
            try:
                # Determine file type
                ext = os.path.splitext(filepath)[1].lower()
                if ext == '.pdf':
                    # Use PDFWithOCRMessage for PDFs
                    msg = PDFWithOCRMessage(
                        source=self.name,
                        filepath=full_path,
                        filename=os.path.basename(full_path),
                        filetype="pdf",
                        ocr_language=language if language else None
                    )
                    text = await msg.extract_text()
                else:
                    # Assume it's an image
                    msg = ImageMessage(
                        source=self.name,
                        filepath=full_path,
                        filename=os.path.basename(full_path),
                        filetype=ext.lstrip('.')
                    )
                    text = await msg.ocr_extract_text(language if language else None)
                
                return text
            except Exception as e:
                return f"Error applying OCR: {str(e)}"
                
        async def get_json_content(filepath: str) -> str:
            """Get the content of a JSON file."""
            full_path = os.path.join(self._working_directory, filepath)
            if not os.path.exists(full_path):
                return f"Error: File {filepath} does not exist."
                
            try:
                msg = JSONMessage(
                    source=self.name,
                    filepath=full_path,
                    filename=os.path.basename(full_path),
                    filetype="json"
                )
                content = await msg.get_content()
                return json.dumps(content, indent=2)
            except Exception as e:
                return f"Error getting JSON content: {str(e)}"
                
        async def get_excel_data(filepath: str, sheet_name: str = "") -> str:
            """Get data from an Excel file, optionally specifying a sheet name."""
            full_path = os.path.join(self._working_directory, filepath)
            if not os.path.exists(full_path):
                return f"Error: File {filepath} does not exist."
                
            try:
                msg = ExcelMessage(
                    source=self.name,
                    filepath=full_path,
                    filename=os.path.basename(full_path),
                    filetype="xlsx"
                )
                
                data_dict = await msg.to_dict()
                if sheet_name and sheet_name in data_dict:
                    return json.dumps(data_dict[sheet_name], indent=2)
                else:
                    return json.dumps(data_dict, indent=2)
            except Exception as e:
                return f"Error getting Excel data: {str(e)}"
        
        # Add file operation tools
        self._tools.extend([
            FunctionTool(list_files, description="List files in a directory"),
            FunctionTool(extract_text_from_pdf, description="Extract text from a PDF file"),
            FunctionTool(get_json_content, description="Get content from a JSON file"),
            FunctionTool(get_excel_data, description="Get data from an Excel file"),
        ])
        
        # Add OCR tool if enabled
        if self._ocr_enabled:
            self._tools.append(FunctionTool(apply_ocr_to_image, description="Apply OCR to an image or PDF file"))

    @property
    def produced_message_types(self) -> Sequence[type[BaseChatMessage]]:
        """The types of messages that the agent produces."""
        message_types = [
            TextMessage,
            FileMessage,
            PDFMessage,
            PDFWithOCRMessage,
            JSONMessage,
            ImageMessage,
            ExcelMessage,
        ]
        
        if self._tools:
            message_types.append(ToolCallSummaryMessage)
            
        return tuple(message_types)

    @property
    def model_context(self) -> ChatCompletionContext:
        """The model context in use by the agent."""
        return self._model_context

    async def on_messages(self, messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken) -> Response:
        """Handle incoming messages and return a response."""
        async for message in self.on_messages_stream(messages, cancellation_token):
            if isinstance(message, Response):
                return message
        raise AssertionError("The stream should have returned the final result.")

    async def on_messages_stream(
        self, messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken
    ) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | Response, None]:
        """Process incoming messages and yield events/responses as they happen."""
        
        # Gather all relevant state
        agent_name = self.name
        model_context = self._model_context
        memory = self._memory
        system_messages = self._system_messages
        workbench = self._workbench
        model_client = self._model_client
        model_client_stream = self._model_client_stream
        reflect_on_tool_use = self._reflect_on_tool_use
        
        # STEP 1: Add new messages to the model context
        await self._add_messages_to_context(
            model_context=model_context,
            messages=messages,
        )

        # STEP 2: Update model context with any relevant memory
        inner_messages: List[BaseAgentEvent | BaseChatMessage] = []
        for event_msg in await self._update_model_context_with_memory(
            memory=memory,
            model_context=model_context,
            agent_name=agent_name,
        ):
            inner_messages.append(event_msg)
            yield event_msg
        
        # STEP 3: Process and extract information from any file messages
        extracted_content: List[str] = []
        
        for msg in messages:
            # Process file messages
            if isinstance(msg, (FileMessage, PDFMessage, PDFWithOCRMessage, JSONMessage, ImageMessage, ExcelMessage)):
                extracted_info = await self._process_file_message(msg)
                if extracted_info:
                    extracted_content.append(extracted_info)
                    # Add the file to processed files list if not already there
                    if hasattr(msg, 'filepath') and msg.filepath not in self._processed_files:
                        self._processed_files.append(msg.filepath)
        
        # If content was extracted, add it to the model context
        if extracted_content:
            file_content_msg = UserMessage(
                content=f"File content:\n\n" + "\n\n".join(extracted_content),
                source="file_extractor"
            )
            await model_context.add_message(file_content_msg)
        
        # STEP 4: Run the model inference
        model_result = None
        try:
            async for inference_output in self._call_llm(
                model_client=model_client,
                model_client_stream=model_client_stream,
                system_messages=system_messages,
                model_context=model_context,
                workbench=workbench,
                agent_name=agent_name,
                cancellation_token=cancellation_token,
            ):
                if isinstance(inference_output, CreateResult):
                    model_result = inference_output
                else:
                    # Streaming chunk event
                    yield inference_output
        except Exception as e:
            # Handle any exceptions during model inference
            error_msg = f"Error during model inference: {str(e)}"
            yield Response(
                chat_message=TextMessage(
                    content=error_msg,
                    source=agent_name,
                ),
                inner_messages=inner_messages,
            )
            return

        # Ensure we have a model result
        if model_result is None:
            yield Response(
                chat_message=TextMessage(
                    content="No response was generated by the model.",
                    source=agent_name,
                ),
                inner_messages=inner_messages,
            )
            return

        # If the model produced a thought, yield it as an event
        if model_result.thought:
            thought_event = ThoughtEvent(content=model_result.thought, source=agent_name)
            yield thought_event
            inner_messages.append(thought_event)

        # Add the assistant message to the model context
        await model_context.add_message(
            AssistantMessage(
                content=model_result.content,
                source=agent_name,
                thought=getattr(model_result, "thought", None),
            )
        )

        # STEP 5: Process the model output - either direct response or function calls
        if isinstance(model_result.content, str):
            # Direct text response
            yield Response(
                chat_message=TextMessage(
                    content=model_result.content,
                    source=agent_name,
                    models_usage=model_result.usage,
                ),
                inner_messages=inner_messages,
            )
        elif isinstance(model_result.content, list) and all(isinstance(item, FunctionCall) for item in model_result.content):
            # Function call processing
            
            # STEP 5A: Yield ToolCallRequestEvent
            tool_call_msg = ToolCallRequestEvent(
                content=model_result.content,
                source=agent_name,
                models_usage=model_result.usage,
            )
            inner_messages.append(tool_call_msg)
            yield tool_call_msg

            # STEP 5B: Execute tool calls
            executed_calls_and_results = await asyncio.gather(
                *[
                    self._execute_tool_call(
                        tool_call=call,
                        workbench=workbench,
                        agent_name=agent_name,
                        cancellation_token=cancellation_token,
                    )
                    for call in model_result.content
                ]
            )
            exec_results = [result for _, result in executed_calls_and_results]

            # Yield ToolCallExecutionEvent
            tool_call_result_msg = ToolCallExecutionEvent(
                content=exec_results,
                source=agent_name,
            )
            await model_context.add_message(FunctionExecutionResultMessage(content=exec_results))
            inner_messages.append(tool_call_result_msg)
            yield tool_call_result_msg

            # STEP 5C: Reflect or summarize tool results
            if reflect_on_tool_use:
                async for reflection_response in self._reflect_on_tool_use_flow(
                    system_messages=system_messages,
                    model_client=model_client,
                    model_client_stream=model_client_stream,
                    model_context=model_context,
                    agent_name=agent_name,
                    inner_messages=inner_messages,
                ):
                    yield reflection_response
            else:
                yield self._summarize_tool_use(
                    executed_calls_and_results=executed_calls_and_results,
                    inner_messages=inner_messages,
                    agent_name=agent_name,
                )
        else:
            # Unexpected content type
            yield Response(
                chat_message=TextMessage(
                    content=f"Unexpected model response format: {type(model_result.content)}",
                    source=agent_name,
                ),
                inner_messages=inner_messages,
            )

    @staticmethod
    async def _add_messages_to_context(
        model_context: ChatCompletionContext,
        messages: Sequence[BaseChatMessage],
    ) -> None:
        """Add incoming messages to the model context."""
        for msg in messages:
            await model_context.add_message(msg.to_model_message())

    @staticmethod
    async def _update_model_context_with_memory(
        memory: Optional[Sequence[Memory]],
        model_context: ChatCompletionContext,
        agent_name: str,
    ) -> List[MemoryQueryEvent]:
        """If memory modules are present, update the model context and return the events produced."""
        events: List[MemoryQueryEvent] = []
        if memory:
            for mem in memory:
                update_context_result = await mem.update_context(model_context)
                if update_context_result and len(update_context_result.memories.results) > 0:
                    memory_query_event_msg = MemoryQueryEvent(
                        content=update_context_result.memories.results,
                        source=agent_name,
                    )
                    events.append(memory_query_event_msg)
        return events

    async def _process_file_message(self, msg: BaseChatMessage) -> str:
        """Process a file message and extract its content."""
        # Check if the message has a content property using the new consistent interface
        if hasattr(msg, 'content'):
            if isinstance(msg, PDFMessage):
                return await self._process_pdf_message(msg)
            elif isinstance(msg, PDFWithOCRMessage):
                return await self._process_pdf_ocr_message(msg)
            elif isinstance(msg, JSONMessage):
                return await self._process_json_message(msg)
            elif isinstance(msg, ImageMessage):
                return await self._process_image_message(msg)
            elif isinstance(msg, ExcelMessage):
                return await self._process_excel_message(msg)
            elif isinstance(msg, FileMessage):
                return f"File received: {msg.filename} (type: {msg.filetype})"
            
        return ""

    async def _process_pdf_message(self, msg: PDFMessage) -> str:
        """Process a PDF message."""
        try:
            # Use the get_content method to ensure we have text content
            text = await msg.get_content()
            
            meta_info = f"PDF: {msg.filename}"
            if msg.page_count:
                meta_info += f" ({msg.page_count} pages)"
            if msg.title:
                meta_info += f", Title: {msg.title}"
            if msg.author:
                meta_info += f", Author: {msg.author}"
                
            # For long PDFs, we might want to truncate or summarize
            if isinstance(text, str) and len(text) > 8000 and self._extraction_depth < 3:
                text = text[:8000] + "...[truncated]"
                
            return f"{meta_info}\n\n{text}"
        except Exception as e:
            return f"Error processing PDF {msg.filename}: {str(e)}"

    async def _process_pdf_ocr_message(self, msg: PDFWithOCRMessage) -> str:
        """Process a PDF with OCR message."""
        try:
            # Use get_content which will prioritize OCR text if available
            text = await msg.get_content()
                
            meta_info = f"PDF with OCR: {msg.filename}"
            if msg.page_count:
                meta_info += f" ({msg.page_count} pages)"
                
            # For long PDFs, truncate if needed
            if isinstance(text, str) and len(text) > 8000 and self._extraction_depth < 3:
                text = text[:8000] + "...[truncated]"
                
            return f"{meta_info}\n\n{text}"
        except Exception as e:
            return f"Error processing PDF with OCR {msg.filename}: {str(e)}"

    async def _process_json_message(self, msg: JSONMessage) -> str:
        """Process a JSON message."""
        try:
            # Use get_content which returns the parsed JSON data
            content = await msg.get_content()
            
            # Format JSON content as a string
            formatted_content = json.dumps(content, indent=2)
            
            # For large JSON files, truncate based on extraction depth
            if len(formatted_content) > 5000 and self._extraction_depth < 2:
                formatted_content = formatted_content[:5000] + "...[truncated]"
                
            return f"JSON File: {msg.filename}\n\n{formatted_content}"
        except Exception as e:
            return f"Error processing JSON {msg.filename}: {str(e)}"

    async def _process_image_message(self, msg: ImageMessage) -> str:
        """Process an image message."""
        try:
            # Use get_content which will return OCR text if available
            content = await msg.get_content()
            
            meta_info = f"Image: {msg.filename}"
            if msg.width and msg.height:
                meta_info += f" ({msg.width}x{msg.height})"
                
            # If content is a string (OCR text)
            if isinstance(content, str) and content and not content.startswith("Error") and not content.startswith("Required"):
                return f"{meta_info}\n\nText content:\n{content}"
            elif isinstance(content, dict):
                # If content is a dictionary (image metadata)
                return f"{meta_info}"
                    
            return meta_info
        except Exception as e:
            return f"Error processing image {msg.filename}: {str(e)}"

    async def _process_excel_message(self, msg: ExcelMessage) -> str:
        """Process an Excel message."""
        try:
            # Use get_content to get the Excel data as a dictionary
            content = await msg.get_content()
            
            # Get sheet information
            sheet_info = []
            if msg.sheet_names:
                for sheet in msg.sheet_names:
                    info = f"'{sheet}'"
                    if msg.row_count and msg.column_count:
                        rows = msg.row_count.get(sheet, "?")
                        cols = msg.column_count.get(sheet, "?")
                        info += f" ({rows}x{cols})"
                    sheet_info.append(info)
                    
            meta_info = f"Excel File: {msg.filename}"
            if sheet_info:
                meta_info += f" (Sheets: {', '.join(sheet_info)})"
                
            # Extract data based on extraction depth
            if content and self._extraction_depth >= 2:
                # Format as JSON
                formatted_data = json.dumps(content, indent=2)
                
                # Truncate for very large Excel files
                if len(formatted_data) > 6000 and self._extraction_depth < 3:
                    formatted_data = formatted_data[:6000] + "...[truncated]"
                    
                return f"{meta_info}\n\n{formatted_data}"
            
            return meta_info
        except Exception as e:
            return f"Error processing Excel file {msg.filename}: {str(e)}"

    @classmethod
    async def _call_llm(
        cls,
        model_client: ChatCompletionClient,
        model_client_stream: bool,
        system_messages: List[SystemMessage],
        model_context: ChatCompletionContext,
        workbench: Workbench,
        agent_name: str,
        cancellation_token: CancellationToken,
    ) -> AsyncGenerator[Union[CreateResult, ModelClientStreamingChunkEvent], None]:
        """Perform a model inference and yield streaming chunks or final result."""
        all_messages = await model_context.get_messages()
        llm_messages = cls._get_compatible_context(model_client=model_client, messages=system_messages + all_messages)
        
        tools = await workbench.list_tools()
        
        if model_client_stream:
            model_result: Optional[CreateResult] = None
            async for chunk in model_client.create_stream(
                llm_messages,
                tools=tools,
                cancellation_token=cancellation_token,
            ):
                if isinstance(chunk, CreateResult):
                    model_result = chunk
                elif isinstance(chunk, str):
                    yield ModelClientStreamingChunkEvent(content=chunk, source=agent_name)
                else:
                    raise RuntimeError(f"Invalid chunk type: {type(chunk)}")
            if model_result is None:
                raise RuntimeError("No final model result in streaming mode.")
            yield model_result
        else:
            model_result = await model_client.create(
                llm_messages,
                tools=tools,
                cancellation_token=cancellation_token,
            )
            yield model_result

    @staticmethod
    async def _execute_tool_call(
        tool_call: FunctionCall,
        workbench: Workbench,
        agent_name: str,
        cancellation_token: CancellationToken,
    ) -> tuple[FunctionCall, FunctionExecutionResult]:
        """Execute a single tool call and return the result."""
        # Load the arguments from the tool call.
        try:
            arguments = json.loads(tool_call.arguments)
        except json.JSONDecodeError as e:
            return (
                tool_call,
                FunctionExecutionResult(
                    content=f"Error: {e}",
                    call_id=tool_call.id,
                    is_error=True,
                    name=tool_call.name,
                ),
            )

        # Handle tool call using workbench
        result = await workbench.call_tool(
            name=tool_call.name,
            arguments=arguments,
            cancellation_token=cancellation_token,
        )
        return (
            tool_call,
            FunctionExecutionResult(
                content=result.to_text(),
                call_id=tool_call.id,
                is_error=result.is_error,
                name=tool_call.name,
            ),
        )

    @classmethod
    async def _reflect_on_tool_use_flow(
        cls,
        system_messages: List[SystemMessage],
        model_client: ChatCompletionClient,
        model_client_stream: bool,
        model_context: ChatCompletionContext,
        agent_name: str,
        inner_messages: List[BaseAgentEvent | BaseChatMessage],
    ) -> AsyncGenerator[Response | ModelClientStreamingChunkEvent | ThoughtEvent, None]:
        """Run another inference based on tool results and yield the final text response."""
        all_messages = system_messages + await model_context.get_messages()
        llm_messages = cls._get_compatible_context(model_client=model_client, messages=all_messages)

        reflection_result: Optional[CreateResult] = None

        if model_client_stream:
            async for chunk in model_client.create_stream(llm_messages):
                if isinstance(chunk, CreateResult):
                    reflection_result = chunk
                elif isinstance(chunk, str):
                    yield ModelClientStreamingChunkEvent(content=chunk, source=agent_name)
                else:
                    raise RuntimeError(f"Invalid chunk type: {type(chunk)}")
        else:
            reflection_result = await model_client.create(llm_messages)

        if not reflection_result or not isinstance(reflection_result.content, str):
            raise RuntimeError("Reflect on tool use produced no valid text response.")

        # If the reflection produced a thought, yield it
        if reflection_result.thought:
            thought_event = ThoughtEvent(content=reflection_result.thought, source=agent_name)
            yield thought_event
            inner_messages.append(thought_event)

        # Add to context (including thought if present)
        await model_context.add_message(
            AssistantMessage(
                content=reflection_result.content,
                source=agent_name,
                thought=getattr(reflection_result, "thought", None),
            )
        )

        yield Response(
            chat_message=TextMessage(
                content=reflection_result.content,
                source=agent_name,
                models_usage=reflection_result.usage,
            ),
            inner_messages=inner_messages,
        )

    @staticmethod
    def _summarize_tool_use(
        executed_calls_and_results: List[tuple[FunctionCall, FunctionExecutionResult]],
        inner_messages: List[BaseAgentEvent | BaseChatMessage],
        agent_name: str,
    ) -> Response:
        """Create a summary message of all tool calls when not using reflection."""
        tool_call_summaries: List[str] = []
        for tool_call, tool_call_result in executed_calls_and_results:
            tool_call_summaries.append(
                f"{tool_call.name}: {tool_call_result.content}"
            )
        tool_call_summary = "\n\n".join(tool_call_summaries)
        return Response(
            chat_message=ToolCallSummaryMessage(
                content=tool_call_summary,
                source=agent_name,
            ),
            inner_messages=inner_messages,
        )

    @staticmethod
    def _get_compatible_context(model_client: ChatCompletionClient, messages: List[LLMMessage]) -> Sequence[LLMMessage]:
        """Ensure the messages are compatible with the model client."""
        if model_client.model_info["vision"]:
            return messages
        else:
            return remove_images(messages)

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        """Reset the agent to its initialization state."""
        await self._model_context.clear()
        self._processed_files = []

    async def on_pause(self, cancellation_token: CancellationToken) -> None:
        """Called when the agent is paused."""
        pass  # No specific pause behavior needed

    async def on_resume(self, cancellation_token: CancellationToken) -> None:
        """Called when the agent is resumed."""
        pass  # No specific resume behavior needed

    async def save_state(self) -> Mapping[str, Any]:
        """Save the current state of the file agent."""
        model_context_state = await self._model_context.save_state()
        return FileAgentState(
            llm_context=model_context_state,
            processed_files=self._processed_files,
        ).model_dump()

    async def load_state(self, state: Mapping[str, Any]) -> None:
        """Load the state of the file agent."""
        file_agent_state = FileAgentState.model_validate(state)
        # Load the model context state
        await self._model_context.load_state(file_agent_state.llm_context)
        self._processed_files = file_agent_state.processed_files

    async def close(self) -> None:
        """Release any resources held by the agent."""
        pass  # No specific resources to release

    def _to_config(self) -> FileAgentConfig:
        """Convert the file agent to a declarative config."""
        return FileAgentConfig(
            name=self.name,
            model_client=self._model_client.dump_component(),
            tools=None,  # Tools are not serialized as they're part of the workbench
            workbench=self._workbench.dump_component() if self._workbench else None,
            model_context=self._model_context.dump_component(),
            memory=[memory.dump_component() for memory in self._memory] if self._memory else None,
            description=self.description,
            system_message=self._system_messages[0].content
            if self._system_messages and isinstance(self._system_messages[0].content, str)
            else None,
            model_client_stream=self._model_client_stream,
            supported_file_types=self._supported_file_types,
            ocr_enabled=self._ocr_enabled,
            extraction_depth=self._extraction_depth,
            file_handlers=self._file_handlers,
            working_directory=self._working_directory,
            reflect_on_tool_use=self._reflect_on_tool_use,
            metadata=self._metadata,
        )

    @classmethod
    def _from_config(cls, config: FileAgentConfig) -> "FileAgent":
        """Create a file agent from a declarative config."""
        return cls(
            name=config.name,
            model_client=ChatCompletionClient.load_component(config.model_client),
            workbench=Workbench.load_component(config.workbench) if config.workbench else None,
            model_context=ChatCompletionContext.load_component(config.model_context) if config.model_context else None,
            memory=[Memory.load_component(memory) for memory in config.memory] if config.memory else None,
            tools=[BaseTool.load_component(tool) for tool in config.tools] if config.tools else None,
            description=config.description,
            system_message=config.system_message,
            model_client_stream=config.model_client_stream,
            supported_file_types=config.supported_file_types,
            ocr_enabled=config.ocr_enabled,
            extraction_depth=config.extraction_depth,
            file_handlers=config.file_handlers,
            working_directory=config.working_directory,
            reflect_on_tool_use=config.reflect_on_tool_use,
            metadata=config.metadata,
        )