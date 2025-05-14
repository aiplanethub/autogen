from fastapi import APIRouter, Form, HTTPException, Path, Query, Depends

from ..deps import get_db
from ...database import DatabaseManager
from ...datamodel.types import Response
from ...services.planner_service import PlannerService
from ...datamodel.planner import PlannerConfigSaveData

router = APIRouter(
    prefix="/plan",
    tags=["plan", "aiplanet"],
    responses={404: {"description": "Not found"}},
)


@router.post("/save")
def save_plan(data: PlannerConfigSaveData, db: DatabaseManager = Depends(get_db)):

    try:
        service = PlannerService(db=db)
        response = service.save(data.plan_id, data.config)

        return Response(
            status=True, data=response.model_dump(), message="Updated plan successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def get(
    plan_id: int = Query(default=None),
    agent_id: int = Query(default=None),
    db: DatabaseManager = Depends(get_db),
):

    try:
        service = PlannerService(db)
        data = None
        if plan_id:
            data = service.get_by_plan_id(plan_id)
        if agent_id:
            data = service.get_by_agent_id(agent_id)

        if data:
            return Response(status=True, data=data.model_dump())

        raise HTTPException(
            status_code=400, detail="Failed to fetch plan. Invlaid plan/agent ID"
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
