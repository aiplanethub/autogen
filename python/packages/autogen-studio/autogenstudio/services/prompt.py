from typing import List, Optional
from ..database import DatabaseManager
from ..datamodel import Prompt


class PromptService:

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_one(self, prompt_id: int) -> Prompt | None:
        response = self.db.get(Prompt, {"id": prompt_id, "is_deleted": False})
        if response.status and response.data:
            return response.data[0]

        if not response.data:
            return None

        raise Exception(response.message)

    def list(self) -> List[Prompt]:
        filters = {"is_deleted": False, "user_id": None}
        response = self.db.get(Prompt, filters)
        if response.status:
            return response.data

        raise Exception(response.message)

    def list_user(self, user_id: str) -> List[Prompt]:
        response = self.db.get(Prompt, {"user_id": user_id, "is_deleted": False})
        if response.status:
            return response.data

        raise Exception(response.message)

    def create(self, title: str, content: str) -> Prompt:
        response = self.db.upsert(
            Prompt(title=title, content=content), return_json=False
        )
        if response.status:
            return response.data

        raise Exception(response.message)

    def update(
        self,
        prompt_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        is_deleted: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        response = self.db.upsert(
            Prompt(
                id=prompt_id,
                title=title,
                content=content,
                is_deleted=is_deleted,
                user_id=user_id,
            ),
            return_json=False,
        )
        if response.status:
            return response.data

        raise Exception(response.message)

    def delete(self, prompt_id: int):
        response = self.db.delete(Prompt, {"id": prompt_id})
        if response.status:
            return response.data

        raise Exception(response.message)
