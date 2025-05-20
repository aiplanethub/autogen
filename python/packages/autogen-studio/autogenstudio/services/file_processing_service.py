"""
Service for file processing operations
"""

import asyncio
import logging
import tempfile
from typing import Callable

from llama_cloud import TokenTextSplitter
from llama_cloud_services import LlamaParse

from ..core.config import get_settings
from ..datamodel.file import FileType


class FileProcessingService:
    """Service for file_processing operations"""

    def __init__(self):
        """
        Initialize the service with a database session.
        """

        settings = get_settings()

        self.parser = LlamaParse(
            api_key=settings.LLAMA_CLOUD_API_KEY, num_workers=4, language="en"
        )

        self.text_splitter = TokenTextSplitter()

    async def read_file(self, content: bytes, file_type: FileType) -> str:
        """
        read the file's text content
        """

        func_map: dict[FileType, Callable] = {
            FileType.PDF: self.read_pdf,
            FileType.TEXT: self.read_plain_text,
            # FileTypeEnum.CSV: self.read_csv,
        }

        func = func_map.get(file_type)
        if not func:
            raise ValueError(f"Invalid file type {file_type}")

        if asyncio.iscoroutinefunction(func):
            return await func(content)

        return func(content)

    async def read_pdf(self, content: bytes) -> str:
        """
        read the pdf content
        """
        try:
            # Write file bytes to a temporary PDF file
            with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
                tmp_file.write(content)

                tmp_path = tmp_file.name
                result = await self.parser.aparse(tmp_path)

            docs = result.get_text_documents(split_by_page=True)

            text_content = ""
            for doc in docs:
                text_content += doc.text

            return text_content
        except Exception as e:
            logging.exception(e)
            raise

    def read_plain_text(self, content: bytes) -> str:
        """read the plain text document"""
        try:
            return content.decode()
        except:
            raise Exception("Failed to decode plain text file.")

    def split_text_into_chunks(self, text: str) -> list[str]:
        """
        Splits the extracted text into smaller chunks for embedding.
        """
        try:
            chunks = self.text_splitter.split_text(text)
            logging.info(f"Text split into {len(chunks)} chunks.")
            return chunks
        except Exception as e:
            logging.error(f"Error splitting text into chunks: {str(e)}")
            logging.exception(e)
            raise
