import json
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, status
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field

from ...database import DatabaseManager
from ...datamodel.types import Response
from ...services.builder import BuilderService
from ..deps import get_current_user, get_db

router = APIRouter(
    prefix="/builder-session",
    tags=["builder-session", "aiplanet"],
    responses={404: {"description": "Not found"}},
)


class CreateSessionRequest(BaseModel):
    name: str = Field(...)
    user_id: str = Field(...)


class DeleteSessionRequest(BaseModel):
    builder_id: int = Field(...)


@router.post("/")
async def create_session(
    payload: CreateSessionRequest,
    db: DatabaseManager = Depends(get_db),
):
    try:
        service = BuilderService(db)
        response = service.create(payload.user_id, payload.name)

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
            data=json.loads(config.model_dump_json()),
            status=True,
            message="Config fetched successfully",
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/tools")
async def get_tools(
    builder_id: int = Query(...), db: DatabaseManager = Depends(get_db)
):
    try:
        service = BuilderService(db)
        tools = service.get_tools(builder_id)
        if not tools:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT, detail="Session not found"
            )

        return Response(data=tools, status=True, message="tools fetched")

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/knowledge-base")
async def get_agents(
    builder_id: int = Query(...), db: DatabaseManager = Depends(get_db)
):
    try:
        service = BuilderService(db)
        config = service.get_knowledge_bases(builder_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT, detail="Session not found"
            )

        return Response(data=config, status=True, message="Agents fetched")

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/agents")
async def get_agents(
    builder_id: int = Query(...), db: DatabaseManager = Depends(get_db)
):
    try:
        service = BuilderService(db)
        config = service.get_agents(builder_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT, detail="Session not found"
            )

        return Response(data=config, status=True, message="Agents fetched")

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


class UpdateBuilder(BaseModel):
    id: int
    name: Optional[str] = Field(default=None)
    config: Optional[dict] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


@router.patch("/")
async def update(
    data: UpdateBuilder,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    try:
        service = BuilderService(db)
        session = service.save(
            id=data.id,
            workflow_config=data.config,
            name=data.name,
            is_active=data.is_active,
            user_id=user_id,
        )

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


class DeleteSession(BaseModel):
    builder_id: int


@router.delete("/")
async def delete_session(
    payload: DeleteSessionRequest, db: DatabaseManager = Depends(get_db)
):
    try:
        service = BuilderService(db)
        service.delete_session(payload.builder_id)

        return Response(status=True, message="Session deleted")

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


class UpdateConfig(BaseModel):
    builder_id: int
    gallery_id: Optional[int] = Field(default=None)
    tools: Optional[List[str]] = Field(default=None)
    agents: Optional[List[str]] = Field(default=None)
    knowledge_bases: Optional[List[str]] = Field(default=None)


@router.patch("/config")
async def update_config(data: UpdateConfig, db: DatabaseManager = Depends(get_db)):
    try:
        service = BuilderService(db)
        config = service.update_config_selection(
            agents=data.agents,
            tools=data.tools,
            knowledge_bases=data.knowledge_bases,
            builder_id=data.builder_id,
            gallery_id=data.gallery_id,
        )

        return Response(
            status=True,
            message="config updated",
            data=json.loads(config.model_dump_json()),
        )

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
