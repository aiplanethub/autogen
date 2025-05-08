import base64
import io
import os
from typing import Sequence, Optional
from ..datamodel import Run
from autogen_agentchat.messages import ChatMessage, MultiModalMessage, TextMessage
from autogen_core import Image
from autogen_core.models import UserMessage
from loguru import logger

from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

def _get_run(self, run_id: int) -> Optional[Run]:
    """Get run from database

    Args:
        run_id: id of the run to retrieve

    Returns:
        Optional[Run]: Run object if found, None otherwise
    """
    response = self.db_manager.get(Run, filters={"id": run_id}, return_json=False)
    return response.data[0] if response.status and response.data else None

def construct_task(query: str, files: list[dict] | None = None, env_vars: Optional[list[dict]] = None) -> Sequence[ChatMessage]:
    """
    Construct a task from a query string and list of files.
    Returns a list of ChatMessage objects suitable for processing by the agent system.

    Args:
        query: The text query from the user
        files: List of file objects with properties name, content, and type

    Returns:
        List of BaseChatMessage objects (TextMessage, MultiModalMessage)
    """
    if files is None:
        files = []

    messages = []

    # Add the user's text query as a TextMessage
    if query:
        messages.append(TextMessage(source="user", content=query))

    for env_var in env_vars or []:
        if env_var.name == "DOCUMENT_INTEL_ENDPOINT":
            DOCUMENT_INTEL_ENDPOINT = env_var.value
        elif env_var.name == "DOCUMENT_INTEL_KEY":
            DOCUMENT_INTEL_KEY = env_var.value

    # Process each file based on its type
    for file in files:
        try:
            ftype = file.get("type", "")
            fname = file.get("name", "unknown")
            content_b64 = file["content"]

            doc_intel_client = DocumentAnalysisClient(
                endpoint=DOCUMENT_INTEL_ENDPOINT,
                credential=AzureKeyCredential(DOCUMENT_INTEL_KEY),
            )


            if file.get("type", "").startswith("image/"):
                # Handle image file using from_base64 method
                # The content is already base64 encoded according to the convertFilesToBase64 function
                image = Image.from_base64(file["content"])
                messages.append(
                    MultiModalMessage(
                        source="user", content=[image], metadata={"filename": file.get("name", "unknown.img")}
                    )
                )
            elif file.get("type", "").startswith("text/"):
                # Handle text file as TextMessage
                text_content = base64.b64decode(file["content"]).decode("utf-8")
                messages.append(
                    TextMessage(
                        source="user", content=text_content, metadata={"filename": file.get("name", "unknown.txt")}
                    )
                )
            elif ftype == "application/pdf":
                # 1) Decode the PDF bytes
                pdf_bytes = base64.b64decode(content_b64)
                stream = io.BytesIO(pdf_bytes)

                # 2) Invoke Azure’s “prebuilt-document” model to get structured text
                poller = doc_intel_client.begin_analyze_document(
                    "prebuilt-document",
                    document=stream
                )
                result = poller.result()

                # 3) Concatenate everything into one big string (you could also
                #    chunk it by page or section, depending on your needs)
                full_text = []
                for page in result.pages:
                    for line in page.lines:
                        full_text.append(line.content)
                document_text = "\n".join(full_text)

                messages.append(
                    TextMessage(
                        source="user",
                        content=document_text,
                        metadata={"filename": fname, "filetype": ftype},
                    )
                )

            else:
                # Log unsupported file types but still try to process based on best guess
                logger.warning(f"Potentially unsupported file type: {file.get('type')} for file {file.get('name')}")
                if file.get("type", "").startswith("application/"):
                    # Try to treat as text if it's an application type (like JSON)
                    text_content = base64.b64decode(file["content"]).decode("utf-8")
                    messages.append(
                        TextMessage(
                            source="user",
                            content=text_content,
                            metadata={
                                "filename": file.get("name", "unknown.file"),
                                "filetype": file.get("type", "unknown"),
                            },
                        )
                    )
        except Exception as e:
            logger.error(f"Error processing file {file.get('name')}: {str(e)}")
            # Continue processing other files even if one fails

    return messages


def update_team_config(team_config: dict, tasks: Sequence[ChatMessage]) -> dict:
    """
    Build and inject the selector_prompt into team_config based on incoming tasks.
    Returns the updated team_config.
    """
    cfg      = team_config["config"]
    template = cfg.get("selector_prompt", "You are a helpful assistant.")

    # extract first matching TextMessage for context and form
    context = next(
        (t.content for t in tasks
         if isinstance(t, TextMessage) and "context" in t.metadata.get("filename", "").lower()),
        ""
    )
    form = next(
        (t.content for t in tasks
         if isinstance(t, TextMessage) and "form" in t.metadata.get("filename", "").lower()),
        ""
    )

    # append any multimodal filenames
    multimodal_files = [
        t.metadata.get("filename", "unknown.file")
        for t in tasks
        if isinstance(t, MultiModalMessage)
    ]
    if multimodal_files:
        template += "\nIncluded files: " + ", ".join(multimodal_files)

    # format and store back into the config
    cfg["selector_prompt"] = template.format(context=context, form=form)
    return team_config
