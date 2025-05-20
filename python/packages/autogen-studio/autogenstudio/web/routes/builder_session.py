from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Query, status
from fastapi.responses import JSONResponse

from ...database import DatabaseManager
from ...datamodel import BuilderSession
from ...datamodel.types import Response
from ...services.builder import BuilderService
from ..deps import get_current_user, get_db

router = APIRouter(
    prefix="/builder-session",
    tags=["builder-session", "aiplanet"],
    responses={404: {"description": "Not found"}},
)


@router.post("/")
async def create_session(
    name: str = Form(..., description="session name"),
    user_id: str = Form(..., description="user id"),
    db: DatabaseManager = Depends(get_db),
):
    try:
        service = BuilderService(db)
        response = service.save(user_id=user_id, name=name)

        return JSONResponse(
            content={
                "id": response.id,
                "name": response.name,
                "summary": response.summary,
                "config": response.workflow_config,
                "created_at": str(response.created_at),
            },
            status_code=status.HTTP_201_CREATED,
        )

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/")
async def get_builder(
    builder_id: Optional[str] = Query(default=None, description="builder id"),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    try:
        data = None
        service = BuilderService(db)
        if builder_id:
            builder = service.get_session(builder_id)
            if not builder:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT, detail="Session not found"
                )

            data = {
                "id": builder.id,
                "name": builder.name,
                "summary": builder.summary,
                "config": builder.workflow_config,
                "created_at": str(builder.created_at),
            }
        else:
            builders = service.list_sessions(user_id)
            if not builders:
                raise HTTPException(
                    status_code=status.HTTP_204_NO_CONTENT, detail="Session not found"
                )

            data = [
                {
                    "id": builder.id,
                    "name": builder.name,
                    "summary": builder.summary,
                    "config": builder.workflow_config,
                    "created_at": str(builder.created_at),
                }
                for builder in builders
            ]

        return Response(
            data=data,
            status=True,
            message="Builder fetched successfully",
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/list")
async def get_builder(user_id: str = Query(...), db: DatabaseManager = Depends(get_db)):
    try:
        service = BuilderService(db)
        builders = service.list_sessions(user_id)
        if not builders:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="No sessions found for this user",
            )
        return Response(
            data=[
                {
                    "id": builder.id,
                    "name": builder.name,
                    "summary": builder.summary,
                    "config": builder.workflow_config,
                    "created_at": str(builder.created_at),
                }
                for builder in builders
            ],
            status=True,
            message="Builder fetched successfully",
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/workflow")
async def get_config(
    builder_id: str = Query(...), db: DatabaseManager = Depends(get_db)
):
    try:
        service = BuilderService(db)
        config = service.get_workflow_config(builder_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT, detail="Session not found"
            )

        return Response(
            data=config.model_dump(), status=True, message="Config fetched successfully"
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/config")
async def get_config_selection(
    builder_id: str = Query(...), db: DatabaseManager = Depends(get_db)
):
    try:
        service = BuilderService(db)
        config = service.get_config_selection(builder_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT, detail="Session not found"
            )

        return Response(
            data=config.model_dump(), status=True, message="Config fetched successfully"
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/messages")
async def get_messages(
    builder_id: str = Query(...), db: DatabaseManager = Depends(get_db)
):
    try:
        service = BuilderService(db)
        messages = service.get_messages(builder_id)
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT, detail="Session not found"
            )

        return Response(
            status=True, message="Messages fetched successfully", data=messages
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/message")
async def post_message(message: str = Form(...), db: DatabaseManager = Depends(get_db)):
    """Post a user's feedback message"""

    service = BuilderService(db)

    pass


@router.patch("/")
async def update(
    config: dict = Form(..., description="Workflow Config"),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    try:
        service = BuilderService(db)
        session = service.save(config, user_id)

        return Response(
            status=True, message="Session fetched", data=session.model_dump()
        )

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/")
async def delete_session(
    session_id: int = Form(...), db: DatabaseManager = Depends(get_db)
):
    try:
        service = BuilderService(db)
        service.delete_session(session_id)

        return Response(status=True, message="Session deleted")

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
