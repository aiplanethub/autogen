from enum import Enum
from typing import List, Optional, Union

from sqlmodel import JSON, Column, Field, Integer, Relationship

from ..datamodel.db import BaseDBModel
from ..datamodel.types import MessageMeta


class BuilderRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class BuilderSession(BaseDBModel, table=True):
    __table_args__ = {"sqlite_autoincrement": True}

    name: Optional[str] = None  # Optional Workflow name
    user_id: Optional[str] = None  # Optional if you're tracking users
    is_active: bool = Field(default=True)
    summary: Optional[str] = None  # Final generated summary
    workflow_config: Optional[dict] = Field(
        default=None, sa_column=Column(JSON)
    )  # Final config

    messages: list["BuilderMessage"] = Relationship(back_populates="builder_session")
    config: "BuilderConfigSelection" = Relationship(back_populates="builder_session")


class BuilderMessage(BaseDBModel, table=True):
    __table_args__ = {"sqlite_autoincrement": True}

    role: BuilderRole = Field(default=BuilderRole.USER)  # user / assistant / system
    content: str  # prompt or response text
    message_meta: Optional[Union[MessageMeta, dict]] = Field(default={}, sa_type=JSON)

    builder_session_id: int = Field(
        sa_type=Integer, foreign_key="buildersession.id", ondelete="CASCADE"
    )
    builder_session: BuilderSession = Relationship(back_populates="messages")


class BuilderConfigSelection(BaseDBModel, table=True):
    __table_args__ = {"sqlite_autoincrement": True}

    agents: List[str] = Field(default_factory=list, sa_type=JSON)
    tools: List[str] = Field(default_factory=list, sa_type=JSON)
    knowledgebases: List[str] = Field(default_factory=list, sa_type=JSON)

    builder_session_id: int = Field(foreign_key="buildersession.id", ondelete="CASCADE")
    builder_session: BuilderSession = Relationship(back_populates="config")
