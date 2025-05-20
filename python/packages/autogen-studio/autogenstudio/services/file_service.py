"""
Service for file operations
"""

from typing import List, Optional

from ..database.db_manager import DatabaseManager
from ..datamodel.file import File


class FileService:
    """Service for file operations"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def create(self, file_data: File) -> File:
        """Create a new file record in the database."""
        response = self.db.upsert(file_data, return_json=False)
        if response.status:
            return response.data

        raise Exception(f"Failed to create file: {response.message}")

    def get(self, file_id: int) -> Optional[File]:
        """Retrieve a file record by its ID."""

        filters = {"id": file_id, "is_deleted": False}
        response = self.db.get(File, filters=filters, return_json=False)
        if response.status and response.data:
            return response.data[0]  # Return the first matching record

        return None

    def list(self, filters: Optional[dict] = {}) -> List[File]:
        """Retrieve a list of files based on filters."""

        filters.setdefault("is_deleted", False)

        response = self.db.get(File, filters=filters, return_json=False)
        if response.status:
            return response.data

        raise Exception(f"Failed to list files: {response.message}")

    def update(self, file_id: int, updated_data: dict) -> File:
        """Update an existing file record."""
        file_record = self.get_file(file_id)
        if not file_record:
            raise Exception(f"File with ID {file_id} not found")

        for key, value in updated_data.items():
            setattr(file_record, key, value)

        response = self.db.upsert(file_record, return_json=False)
        if response.status:
            return response.data

        raise Exception(f"Failed to update file: {response.message}")

    def soft_delete(self, file_id: int) -> bool:
        """Soft delete a file record by its ID"""

        response = self.update(file_id, {"is_deleted": True})
        if response.status:
            return True

        raise Exception(f"Failed to delete file: {response.message}")

    def restore_file(self, file_id: int) -> bool:
        """Restore a soft deleted file"""

        response = self.update(file_id, {"is_deleted": False})
        if response.status:
            return True

        raise Exception(f"Failed to restore file: {response.message}")

    def delete(self, file_id: int) -> bool:
        """Delete a file record by its ID."""
        response = self.db.delete(File, filters={"id": file_id})
        if response.status:
            return True

        raise Exception(f"Failed to delete file: {response.message}")
