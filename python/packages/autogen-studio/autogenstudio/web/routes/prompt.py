from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from loguru import logger

from ...datamodel.types import Response
from ...database import DatabaseManager
from ...datamodel import Prompt
from ...services.prompt import PromptService
from ..deps import get_current_user, get_db

router = APIRouter(
    prefix="/prompt",
    tags=["prompt", "aiplanet"],
    responses={404: {"description": "Not found"}},
)


class GetPromptModel(BaseModel):
    prompt_id: Optional[int] = Field(default=None, description="prompt id")
    user_id: Optional[str] = Field(default=None, description="user_id")


GetPrompt = Annotated[GetPromptModel, Query(...)]


@router.get("/")
async def get_prompt(data: GetPrompt, db: DatabaseManager = Depends(get_db)):
    try:
        service = PromptService(db)
        prompts = None
        if data.prompt_id:
            prompt = service.get_one(data.prompt_id)
            if not prompt:
                return JSONResponse(
                    status_code=204, content={"message": "No prompt found"}
                )

            data = {
                "id": prompt.id,
                "created_at": str(prompt.created_at),
                "updated_at": str(prompt.updated_at),
                "title": prompt.title,
                "content": prompt.content,
            }

        elif data.user_id:
            prompts = service.list_user(data.user_id)
            if not prompts:
                return JSONResponse(
                    status_code=204, content={"message": "No prompt found"}
                )
        else:
            prompts = service.list()
            if not prompts:
                return JSONResponse(
                    status_code=204, content={"message": "No prompt found"}
                )
        if prompts:
            data = [
                {
                    "id": prompt.id,
                    "created_at": str(prompt.created_at),
                    "updated_at": str(prompt.updated_at),
                    "title": prompt.title,
                    "content": prompt.content,
                }
                for prompt in prompts
            ]

        return JSONResponse(content=data)

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))


class CreatePrompt(BaseModel):
    title: str = Field(..., description="Prompt title")
    content: str = Field(..., description="prompt")


@router.post("/")
async def create_prompt(data: CreatePrompt, db: DatabaseManager = Depends(get_db)):
    try:
        service = PromptService(db)
        prompt = service.create(data.title, data.content)
        print(prompt)

        return JSONResponse(
            content={
                "id": prompt.id,
                "created_at": str(prompt.created_at),
                "updated_at": str(prompt.updated_at),
                "title": prompt.title,
                "content": prompt.content,
            },
            status_code=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))


class UpdatePrompt(BaseModel):
    prompt_id: int = Field(..., description="prompt id")
    title: Optional[str] = Field(default=None, description="Prompt title")
    content: Optional[str] = Field(default=None, description="prompt")
    is_deleted: Optional[bool] = Field(default=None, descripton="Soft delete flag")
    user_id: Optional[str] = Field(default=None, description="user id")


@router.patch("/")
async def update(
    data: UpdatePrompt,
    db: DatabaseManager = Depends(get_db),
):
    try:
        service = PromptService(db)
        prompt = service.update(
            data.prompt_id, data.title, data.content, data.is_deleted, data.user_id
        )

        return Response(
            status=True,
            message="Prompt updated",
            data={
                "id": prompt.id,
                "created_at": str(prompt.created_at),
                "updated_at": str(prompt.updated_at),
                "title": prompt.title,
                "content": prompt.content,
            },
        )

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


class DeletePrompt(BaseModel):
    prompt_id: int = Field(..., description="prompt id")


@router.delete("/")
async def delete_session(data: DeletePrompt, db: DatabaseManager = Depends(get_db)):
    try:
        service = PromptService(db)
        service.delete(data.prompt_id)
        return Response(status=True, message="Prompt deleted")

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
