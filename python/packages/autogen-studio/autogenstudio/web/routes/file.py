from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import File as FastAPIFile
from fastapi import HTTPException, Query, UploadFile

from ...database import DatabaseManager
from ...datamodel.file import File, ListFilesFilters
from ...datamodel.types import Response
from ...services import file_service, s3_service
from ..deps import get_current_user, get_db

router = APIRouter(
    prefix="/file",
    tags=["file", "aiplanet"],
    responses={404: {"description": "Not found"}},
)


@router.post("/upload")
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    db: DatabaseManager = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> Response:
    """Upload a file and store its metadata in the database."""

    try:
        # Read file content
        content = await file.read()

        # Upload file to S3
        async with s3_service.S3Service() as s3:
            s3_key = await s3.upload_file_to_s3(
                content=content, file_name=file.filename, content_type=file.content_type
            )

        # Create a file record in the database
        new_file = File(
            file_name=file.filename,
            mime_type=file.content_type,
            file_size=len(content),
            s3_key=s3_key,
            status="uploaded",
            user_id=user_id,
        )
        created_file = file_service.FileService(db).create(new_file)

        return Response(
            status=True,
            data={"id": created_file.id, "s3_key": created_file.s3_key},
            message="File uploaded successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@router.get("/{file_id}")
async def fetch_file(
    file_id: int,
    db: DatabaseManager = Depends(get_db),
) -> Response:
    """Fetch file metadata and S3 URL."""
    try:
        # Retrieve file metadata from the database
        file_record = file_service.FileService(db).get(file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")

        # Generate S3 URL
        async with s3_service.S3Service() as s3:
            s3_url = s3.get_s3_url(file_record.s3_key)

        return Response(
            status=True,
            data={
                "id": file_record.id,
                "file_name": file_record.file_name,
                "mime_type": file_record.mime_type,
                "file_size": file_record.file_size,
                "s3_url": s3_url,
            },
            message="File fetched successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File fetch failed: {str(e)}")


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    db: DatabaseManager = Depends(get_db),
) -> Response:
    """Delete a file from the database and S3."""
    try:
        # Retrieve file metadata from the database
        file_record = file_service.FileService(db).get(file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")

        # Delete file from S3
        async with s3_service.S3Service() as s3:
            await s3.delete_file_from_s3(file_record.s3_key)

        # Soft delete the file record in the database
        file_service.FileService(db).soft_delete(file_id)

        return Response(status=True, message="File deleted successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")


@router.get("/")
async def get_files(
    filters: Annotated[ListFilesFilters, Query()],
    db: DatabaseManager = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> Response:
    """Fetch a list of files based on filters."""
    try:
        f = filters.model_dump()
        f["user_id"] = user_id
        files = file_service.FileService(db).list(f)
        return Response(
            status=True,
            data=[
                {
                    "id": file.id,
                    "file_name": file.file_name,
                    "mime_type": file.mime_type,
                    "file_size": file.file_size,
                    "status": file.status,
                    "s3_key": file.s3_key,
                }
                for file in files
            ],
            message="Files fetched successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch files: {str(e)}")


@router.patch("/{file_id}")
async def update_file(
    file_id: int,
    updated_data: dict,
    db: DatabaseManager = Depends(get_db),
) -> Response:
    """Update a file's name or status."""
    try:
        updated_file = file_service.FileService(db).update(file_id, updated_data)
        return Response(
            status=True,
            data={
                "id": updated_file.id,
                "file_name": updated_file.file_name,
                "status": updated_file.status,
            },
            message="File updated successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update file: {str(e)}")
