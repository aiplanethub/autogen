# api/routes/teams.py
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, Form, File

from ...datamodel import Team, Gallery
from ...gallery.builder import create_default_gallery
from ..deps import get_db
from autogenstudio.planner.orchestrator import planner_orchestrator
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogenstudio.utils.constants import PLANNER_PROMPT
import traceback
from autogenstudio.planner.clarification_agent import ClarificationAgent
from autogenstudio.core.config import get_settings

router = APIRouter()


@router.get("/")
async def list_teams(user_id: str, db=Depends(get_db)) -> Dict:
    """List all teams for a user"""
    response = db.get(Team, filters={"user_id": user_id})

    if not response.data or len(response.data) == 0:
        default_gallery = create_default_gallery()
        default_team = Team(
            user_id=user_id, component=default_gallery.components.teams[0].model_dump()
        )

        db.upsert(default_team)
        response = db.get(Team, filters={"user_id": user_id})

    return {"status": True, "data": response.data}


@router.get("/{team_id}")
async def get_team(team_id: int, user_id: str, db=Depends(get_db)) -> Dict:
    """Get a specific team"""
    response = db.get(Team, filters={"id": team_id, "user_id": user_id})
    if not response.status or not response.data:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"status": True, "data": response.data[0]}


@router.post("/")
async def create_team(team: Team, db=Depends(get_db)) -> Dict:
    """Create a new team"""
    response = db.upsert(team)
    if not response.status:
        raise HTTPException(status_code=400, detail=response.message)
    return {"status": True, "data": response.data}


@router.post("/plan")
async def plan_team(
    user_id: str = Form(...),
    prompt: str = Form(...),
    knowledge_base: str = Form(...),
    file: UploadFile = File(None),
    db=Depends(get_db),
) -> Dict:
    try:
        settings = get_settings()
        result = db.get(Gallery, filters={"user_id": user_id})
        if not result.data or len(result.data) == 0:
            # create a default gallery entry
            gallery_config = create_default_gallery()
            default_gallery = Gallery(
                user_id=user_id, config=gallery_config.model_dump()
            )
            db.upsert(default_gallery)
            result = db.get(Gallery, filters={"user_id": user_id})

        tools = result.data[0].config["components"]["tools"]
        planner_system_message = PLANNER_PROMPT.format(
            query=prompt,
            knowledge_base=knowledge_base,
            available_tools=[
                tool["description"]
                for tool in result.data[0].config["components"]["tools"]
            ],
        )

        model_client = AzureOpenAIChatCompletionClient(
            azure_deployment=settings.AZURE_DEPLOYMENT,
            api_key=settings.AZURE_API_KEY,
            api_version=settings.AZURE_VERSION,
            azure_endpoint=settings.AZURE_ENDPOINT,
            model=settings.AZURE_MODEL,
        )

        planner_agent = AssistantAgent(
            name="PlannerAgent",
            system_message=planner_system_message,
            model_client=model_client,
            memory=[],
            tools=[],
            model_context=None,
        )
        clarification_agent = ClarificationAgent(
            model_client=model_client,
            kb_collection_name=knowledge_base,
        )

        user_proxy_agent = UserProxyAgent("user_proxy")

        selector_gc = planner_orchestrator(
            model_client=model_client,
            agents=[planner_agent, clarification_agent],
        )
        result = await selector_gc.run(task=prompt)
        return {
            "status": True,
            "data": {
                "response": result.messages[-1].content.dict(),
                "agents": [
                    agent.model_dump() for agent in selector_gc._participant_names
                ],
            },
        }
    except Exception as e:
        print(f"Error in planning: {str(e)} {traceback.format_exc()}")
        return Response(status=False, data=[], message=f"Error in planning: {str(e)}")


@router.delete("/{team_id}")
async def delete_team(team_id: int, user_id: str, db=Depends(get_db)) -> Dict:
    """Delete a team"""
    db.delete(filters={"id": team_id, "user_id": user_id}, model_class=Team)
    return {"status": True, "message": "Team deleted successfully"}
