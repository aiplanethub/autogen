import datetime
import json
from typing import Any, List, Optional

from ..database import DatabaseManager
from ..datamodel import (
    BuilderConfigSelection,
    BuilderMessage,
    BuilderRole,
    BuilderSession,
    MessageMeta,
)


class BuilderService:

    def __init__(self, db: DatabaseManager):
        self.db = db

    def create(
        self,
        user_id: str,
        name: str,
    ) -> BuilderSession:
        """Create the builder model and config selection"""
        builder_model = BuilderSession(
            name=name,
            is_active=True,
            workflow_config={},
            user_id=user_id,
        )
        response = self.db.upsert(builder_model, return_json=False)
        if not response.status:
            raise Exception(response.message)

        builder = response.data

        try:
            builder_config_selection = BuilderConfigSelection(
                builder_session_id=builder.id,
                knowledgebases=[],
                agents=[],
                tools=[],
                gallery_id=None,
            )
            response = self.db.upsert(builder_config_selection, return_json=False)
            # if not response.status:
            #     raise Exception(response.message)
        except Exception as e:
            print(str(e))

        return builder

    def create_message(
        self,
        builder_id: int,
        role: BuilderRole,
        prompt: str,
        metadata: MessageMeta,
    ) -> BuilderMessage | None:
        builder_message_model = BuilderMessage(
            builder_session_id=builder_id,
            role=role,
            content=prompt,
            message_meta=json.loads(metadata.model_dump_json()),
        )
        message = self.db.upsert(builder_message_model, return_json=False)

        if not message.status:
            raise Exception(message.message)

        return message.data

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

        builder = self.db.upsert(session, return_json=False)
        if not builder.status:
            raise Exception(builder.message)

        return builder.data

    def delete_session(self, builder_id):
        response = self.db.delete(BuilderSession, {"id": builder_id})

        if not response.status:
            raise Exception(response.message)

    def list_sessions(self, user_id: str) -> list[BuilderSession] | None:
        filters = {"user_id": user_id, "is_active": True}
        response = self.db.get(BuilderSession, filters)
        if response.status:
            return response.data

        return None

    def get_session(self, builder_id: str) -> BuilderSession:
        filters = {"id": builder_id, "is_active": True}
        response = self.db.get(BuilderSession, filters)
        if response.status and len(response.data) != 0:
            return response.data[0]

        return None

    def get_messages(self, builder_id: str):
        filters = {"builder_session_id": builder_id}
        response = self.db.get(BuilderMessage, filters)
        print(response)

        if response.status:
            return response.data

        return []

    def get_agents(self, builder_id: int):
        config = self.get_config_selection(builder_id)
        return config.agents

    def get_tools(self, builder_id: int):
        config = self.get_config_selection(builder_id)
        return config.tools

    def get_knowledge_bases(self, builder_id: int):
        config = self.get_config_selection(builder_id)
        return config.knowledgebases

    def get_workflow_config(self, builder_id: str):
        session = self.get_session(builder_id)
        if not session:
            return None

        return session.workflow_config

    def get_config_selection(self, builder_id: int) -> BuilderConfigSelection:
        filters = {"builder_session_id": builder_id}
        response = self.db.get(BuilderConfigSelection, filters)

        print(response.data)
        if response.status and response.data:
            return response.data[0]

        raise Exception(response.message)

    def update_config_selection(
        self,
        builder_id: int,
        agents: List[str] = [],
        tools: List[str] = [],
        knowledge_bases: list[str] = [],
        gallery_id: Optional[int] = None,
    ):

        builder_config = self.get_config_selection(builder_id)

        if agents:
            builder_config.agents = agents
        if tools:
            builder_config.tools = tools
        if knowledge_bases:
            builder_config.knowledgebases = knowledge_bases
        if gallery_id:
            builder_config.gallery_id = gallery_id

        new_config = self.db.upsert(builder_config)
        return new_config
