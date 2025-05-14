import enum
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field

from .db import BaseDBModel


class FileStatus(str, enum.Enum):
    """Status enum for file"""

    PENDING = "pending"
    UPLOADED = "uploaded"
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class FileType(str, enum.Enum):
    """Type enum for file"""

    PDF = "application/pdf"
    TEXT = "text/plain"


class File(BaseDBModel, table=True):
    """Database model for storing file upload data"""

    __table_args__ = {"sqlite_autoincrement": True}

    # Name of the uploaded file
    file_name: str = Field(..., description="Name of the uploaded file")

    # MIME type of the file
    mime_type: FileType = Field(..., description="MIME type of the uploaded file")

    # Size of the file in bytes
    file_size: Optional[int] = Field(
        default=None, description="Size of the uploaded file in bytes"
    )

    is_deleted: bool = Field(default=False)

    # file upload status
    status: FileStatus = Field(default=FileStatus.PENDING, description="upload status")

    # S3 key the file is mapped to
    s3_key: str = Field(default=None, description="S3 key where the file is stored")


class ListFilesFilters(BaseModel):
    """Filters for list all files"""

    status: Optional[FileStatus] = Field(default=None)
    mime_type: Optional[FileType] = Field(default=None)
    is_deleted: Optional[bool] = Field(default=False)
