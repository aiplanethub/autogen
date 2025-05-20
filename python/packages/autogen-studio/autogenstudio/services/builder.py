import datetime
from typing import Optional
from ..database import DatabaseManager
from ..datamodel import (
    BuilderSession,
    BuilderMessage,
    BuilderConfigSelection,
    BuilderRole,
    MessageMeta,
)


class BuilderService:

    def __init__(self, db: DatabaseManager):
        self.db = db

    def create(
        self, user_id: str, gallery_id: int, prompt: str, knowledge_bases: list[str]
    ) -> BuilderSession:
        """Create the builder model and config selection"""
        builder_model = BuilderSession(
            name="Untitled Session",
            is_active=True,
            workflow_config={},
            user_id=user_id,
        )
        response = self.db.upsert(builder_model)
        if not response.status:
            raise Exception(response.message)

        builder = response.data

        builder_message_model = BuilderMessage(
            builder_session_id=builder.id,
            role=BuilderRole.USER,
            content=prompt,
            message_meta=MessageMeta(
                task=prompt, time=datetime.datetime.now(datetime.timezone.utc)
            ),
        )
        response = self.db.upsert(builder_message_model)
        if not response.status:
            raise Exception(response.message)

        builder_message_model = response.data
        builder_config_selection = BuilderConfigSelection(
            gallery_id=gallery_id,
            builder_session_id=builder.id,
            knowledgebases=knowledge_bases,
        )
        response = self.db.upsert(builder_config_selection)
        if not response.status:
            raise Exception(response.message)

        return builder

    def save(
        self,
        id: Optional[int] = None,
        name: Optional[str] = None,
        workflow_config: Optional[dict] = None,
        user_id: Optional[str] = None,
        is_active: Optional[bool] = True,
    ) -> BuilderSession:
        session = BuilderSession(
            id=id,
            name=name,
            is_active=is_active,
            user_id=user_id,
            workflow_config=workflow_config,
        )

        response = self.db.upsert(session, return_json=False)
        if response.status:
            return response.data

        raise Exception(response.message)

    def delete_session(self, session_id):
        response = self.db.delete(BuilderSession, {"id": session_id})

        if not response.status:
            raise Exception(response.message)

    def list_sessions(self, user_id: str) -> list[BuilderSession] | None:
        filters = {"user_id": user_id, "is_active": True}
        response = self.db.get(BuilderSession, filters)
        if response.status:
            return response.data

        return None

    def get_session(self, builder_id: str) -> BuilderSession | None:
        filters = {"id": builder_id, "is_active": True}
        response = self.db.get(BuilderSession, filters)
        if response.status and len(response.data) != 0:
            return response.data[0]

        return None

    def get_messages(self, user_id: str):
        session = self.get_session(user_id)
        if not session:
            return None

        return session.messages

    def get_workflow_config(self, user_id: str):
        session = self.get_session(user_id)
        if not session:
            return None

        return session.workflow_config

    def get_config_selection(self, user_id):
        session = self.get_session(user_id)
        if not session:
            return None

        return session.config
