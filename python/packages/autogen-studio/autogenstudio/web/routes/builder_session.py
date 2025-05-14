from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import JSONResponse

from ...database import DatabaseManager
from ...datamodel.types import Response
from ...services.builder import BuilderService
from ..deps import get_current_user, get_db

router = APIRouter(
    prefix="/builder-session",
    tags=["builder-session", "aiplanet"],
    responses={404: {"description": "Not found"}},
)


@router.post("/")
def create_session(
    config: dict = Form(..., description="Workflow Config"),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    try:
        service = BuilderService(db)
        response = service.save(config, user_id)

        return JSONResponse(
            content=response.model_dump(), status_code=status.HTTP_201_CREATED
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/workflow-config")
def get_config(
    user_id: str = Depends(get_current_user), db: DatabaseManager = Depends(get_db)
):
    try:
        service = BuilderService(db)
        config = service.get_workflow_config(user_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
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


@router.get("/config-selection")
def get_config_selection(
    user_id: str = Depends(get_current_user), db: DatabaseManager = Depends(get_db)
):
    try:
        service = BuilderService(db)
        config = service.get_config_selection(user_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
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
def get_messages(
    user_id: str = Depends(get_current_user), db: DatabaseManager = Depends(get_db)
):
    try:
        service = BuilderService(db)
        messages = service.get_messages(user_id)
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
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


@router.get("/session")
def get_session(
    user_id: str = Depends(get_current_user), db: DatabaseManager = Depends(get_db)
):
    try:
        service = BuilderService(db)
        session = service.get_session(user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )

        return Response(
            status=True, message="Session fetched", data=session.model_dump()
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.patch("/")
def update(
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/")
def delete_session(session_id: int = Form(...), db: DatabaseManager = Depends(get_db)):
    try:
        service = BuilderService(db)
        service.delete_session(session_id)

        return Response(status=True, message="Session deleted")

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
