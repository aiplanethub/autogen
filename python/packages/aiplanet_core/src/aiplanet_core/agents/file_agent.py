"""
FileAgent: An agent that specializes in processing file-based messages and performing operations on them.

This module provides a specialized agent for the AutoGen framework that can handle file-based
messages like PDFs, JSON files, images, and Excel files.
"""

import asyncio
import json
import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Mapping, Optional, Sequence, Tuple, Union, cast

from autogen_agentchat.agents._base_chat_agent import BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import (
    BaseAgentEvent,
    BaseChatMessage,
    MessageFactory,
    ModelClientStreamingChunkEvent,
    TextMessage,
    ThoughtEvent,
)
from autogen_agentchat.state import BaseState
from autogen_agentchat.utils import remove_images
from autogen_core import CancellationToken, Component, ComponentModel
from autogen_core.model_context import (
    ChatCompletionContext,
    UnboundedChatCompletionContext,
)
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    CreateResult,
    LLMMessage,
    SystemMessage,
    UserMessage,
)
from autogen_core.tools import BaseTool, FunctionTool, StaticWorkbench, Workbench
from pydantic import BaseModel, Field

# Import the file message types
from ..types.messages import (
    ExcelMessage,
    FileMessage,
    ImageMessage,
    JSONMessage,
    PDFMessage,
    PDFWithOCRMessage,
    register_file_message_types,
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
    description: str
    system_message: str | None = None
    model_client_stream: bool = False
    supported_file_types: List[str] | None = None  # File extensions to support
    ocr_enabled: bool = False
    extraction_depth: int = 1  # How deep to extract content from files
    file_handlers: Dict[str, str] | None = None  # Custom handlers for file types
    working_directory: str | None = None
    metadata: Dict[str, Any] | None = None


class FileAgent(BaseChatAgent, Component[FileAgentConfig]):
    """An agent that specializes in processing files and answering questions about them.

    The agent can handle various file types including PDFs, images, JSON, and Excel files.
    It automatically extracts content from these files and includes it in responses to user queries.

    Args:
        name (str): The name of the agent.
        model_client (ChatCompletionClient): The model client to use for inference.
        tools (List[BaseTool[Any, Any] | Callable[..., Any] | Callable[..., Awaitable[Any]]] | None, optional):
            Additional tools to register with the agent.
        workbench (Workbench | None, optional): The workbench to use for the agent.
        model_context (ChatCompletionContext | None, optional): The model context for storing and retrieving messages.
        description (str, optional): The description of the agent.
        system_message (str, optional): The system message for the model.
        model_client_stream (bool, optional): Whether to use streaming for model responses.
        supported_file_types (List[str] | None, optional): List of file extensions to support (e.g., ["pdf", "json"]).
            If None, all supported file types are enabled.
        ocr_enabled (bool, optional): Whether to enable OCR for images and PDFs.
        extraction_depth (int, optional): How deeply to extract content from files (1-3).
        file_handlers (Dict[str, str] | None, optional): Custom handlers for specific file types.
        working_directory (str | None, optional): Directory for file operations. Defaults to current directory.
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
        description: str = "An agent that specializes in processing and analyzing files",
        system_message: str | None = DEFAULT_SYSTEM_MESSAGE,
        model_client_stream: bool = False,
        supported_file_types: List[str] | None = None,
        ocr_enabled: bool = False,
        extraction_depth: int = 1,
        file_handlers: Dict[str, str] | None = None,
        working_directory: str | None = None,
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
                    source=self.name, filepath=full_path, filename=os.path.basename(full_path), filetype="pdf"
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
                if ext == ".pdf":
                    # Use PDFWithOCRMessage for PDFs
                    msg = PDFWithOCRMessage(
                        source=self.name,
                        filepath=full_path,
                        filename=os.path.basename(full_path),
                        filetype="pdf",
                        ocr_language=language if language else None,
                    )
                    text = await msg.extract_text()
                else:
                    # Assume it's an image
                    msg = ImageMessage(
                        source=self.name,
                        filepath=full_path,
                        filename=os.path.basename(full_path),
                        filetype=ext.lstrip("."),
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
                    source=self.name, filepath=full_path, filename=os.path.basename(full_path), filetype="json"
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
                    source=self.name, filepath=full_path, filename=os.path.basename(full_path), filetype="xlsx"
                )

                data_dict = await msg.to_dict()
                if sheet_name and sheet_name in data_dict:
                    return json.dumps(data_dict[sheet_name], indent=2)
                else:
                    return json.dumps(data_dict, indent=2)
            except Exception as e:
                return f"Error getting Excel data: {str(e)}"

        # Add file operation tools
        self._tools.extend(
            [
                FunctionTool(list_files, description="List files in a directory"),
                FunctionTool(extract_text_from_pdf, description="Extract text from a PDF file"),
                FunctionTool(get_json_content, description="Get content from a JSON file"),
                FunctionTool(get_excel_data, description="Get data from an Excel file"),
            ]
        )

        # Add OCR tool if enabled
        if self._ocr_enabled:
            self._tools.append(FunctionTool(apply_ocr_to_image, description="Apply OCR to an image or PDF file"))

    @property
    def produced_message_types(self) -> Sequence[type[BaseChatMessage]]:
        """The types of messages that the agent produces."""
        return (
            TextMessage,
            FileMessage,
            PDFMessage,
            PDFWithOCRMessage,
            JSONMessage,
            ImageMessage,
            ExcelMessage,
        )

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
        system_messages = self._system_messages
        workbench = self._workbench
        model_client = self._model_client
        model_client_stream = self._model_client_stream

        # STEP 1: Process and extract information from any file messages
        inner_messages: List[BaseAgentEvent | BaseChatMessage] = []
        extracted_content: List[str] = []

        for msg in messages:
            # Add message to model context
            await model_context.add_message(msg.to_model_message())

            # Process file messages
            if isinstance(msg, (FileMessage, PDFMessage, PDFWithOCRMessage, JSONMessage, ImageMessage, ExcelMessage)):
                extracted_info = await self._process_file_message(msg)
                if extracted_info:
                    extracted_content.append(extracted_info)
                    # Add the file to processed files list if not already there
                    if hasattr(msg, "filepath") and msg.filepath not in self._processed_files:
                        self._processed_files.append(msg.filepath)

        # STEP 2: If content was extracted, add it to the model context
        if extracted_content:
            file_content_msg = UserMessage(
                content="File content:\n\n" + "\n\n".join(extracted_content), source="file_extractor"
            )
            await model_context.add_message(file_content_msg)

        # STEP 3: Run the model inference
        model_result = None
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

        assert model_result is not None, "No model result was produced."

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

        # STEP 4: If model returns function calls, execute them
        if isinstance(model_result.content, list):
            # This is a list of function calls
            # Implementation for function calls would go here, similar to AssistantAgent
            pass
        else:
            # Direct text response
            assert isinstance(model_result.content, str)
            yield Response(
                chat_message=TextMessage(
                    content=model_result.content,
                    source=agent_name,
                    models_usage=model_result.usage,
                ),
                inner_messages=inner_messages,
            )

    async def _process_file_message(self, msg: BaseChatMessage) -> str:
        """Process a file message and extract its content."""
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
            text = await msg.extract_text()
            meta_info = f"PDF: {msg.filename}"
            if msg.page_count:
                meta_info += f" ({msg.page_count} pages)"
            if msg.title:
                meta_info += f", Title: {msg.title}"
            if msg.author:
                meta_info += f", Author: {msg.author}"

            # For long PDFs, we might want to truncate or summarize
            if len(text) > 8000 and self._extraction_depth < 3:
                text = text[:8000] + "...[truncated]"

            return f"{meta_info}\n\n{text}"
        except Exception as e:
            return f"Error processing PDF {msg.filename}: {str(e)}"

    async def _process_pdf_ocr_message(self, msg: PDFWithOCRMessage) -> str:
        """Process a PDF with OCR message."""
        try:
            # If OCR has been applied, use OCR text; otherwise, extract regular text
            if msg.ocr_applied and msg.ocr_text:
                text = msg.ocr_text
            else:
                text = await msg.extract_text()

            meta_info = f"PDF with OCR: {msg.filename}"
            if msg.page_count:
                meta_info += f" ({msg.page_count} pages)"

            # For long PDFs, truncate if needed
            if len(text) > 8000 and self._extraction_depth < 3:
                text = text[:8000] + "...[truncated]"

            return f"{meta_info}\n\n{text}"
        except Exception as e:
            return f"Error processing PDF with OCR {msg.filename}: {str(e)}"

    async def _process_json_message(self, msg: JSONMessage) -> str:
        """Process a JSON message."""
        try:
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
            meta_info = f"Image: {msg.filename}"
            if msg.width and msg.height:
                meta_info += f" ({msg.width}x{msg.height})"

            # If OCR is enabled and text has been extracted
            if self._ocr_enabled and msg.ocr_text:
                text = msg.ocr_text.strip()
                if text and not text.startswith("Error") and not text.startswith("Required"):
                    return f"{meta_info}\n\nText content:\n{text}"

            # If no OCR text is available but OCR is enabled, try extracting it
            if self._ocr_enabled and not msg.ocr_text:
                text = await msg.ocr_extract_text()
                if text and not text.startswith("Error") and not text.startswith("Required"):
                    return f"{meta_info}\n\nText content:\n{text}"

            return meta_info
        except Exception as e:
            return f"Error processing image {msg.filename}: {str(e)}"

    async def _process_excel_message(self, msg: ExcelMessage) -> str:
        """Process an Excel message."""
        try:
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
            if self._extraction_depth >= 2:
                # Convert to dict format for all sheets
                data_dict = await msg.to_dict()

                # Format as JSON
                formatted_data = json.dumps(data_dict, indent=2)

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
            tools=[BaseTool.load_component(tool) for tool in config.tools] if config.tools else None,
            description=config.description,
            system_message=config.system_message,
            model_client_stream=config.model_client_stream,
            supported_file_types=config.supported_file_types,
            ocr_enabled=config.ocr_enabled,
            extraction_depth=config.extraction_depth,
            file_handlers=config.file_handlers,
            working_directory=config.working_directory,
            metadata=config.metadata,
        )
