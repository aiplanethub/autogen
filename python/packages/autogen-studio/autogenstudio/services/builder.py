from ..database import DatabaseManager
from ..datamodel.builder import *


class BuilderService:

    def __init__(self, db: DatabaseManager):
        self.db = db

    def save(
        self, workflow_config: Optional[dict] = {}, user_id: Optional[str] = None
    ) -> BuilderSession:
        session = BuilderSession(
            name="Untitled Session",
            is_active=True,
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

    def get_session(self, user_id: str) -> BuilderSession | None:
        filters = {"user_id": user_id, "is_active": True}
        response = self.db.get(BuilderSession, filters)
        if response.status and len(response.data) != 0:
            return response.data

        if len(response.data == 0):
            return None

        raise Exception(response.message)

    def get_messages(self, user_id: str):
        session = self.get_session(user_id)
        if not session:
            return None

        return session.messages

    def get_config(self, user_id: str):
        session = self.get_session(user_id)
        if not session:
            return None

        return session.config
