import json
from typing import Dict

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    UploadFile,
    Form,
    File,
    WebSocket,
    WebSocketDisconnect,
)

from ...datamodel import Team, Gallery, BuilderMessage, BuilderRole, MessageMeta
from ...gallery.builder import create_default_gallery
from ..deps import get_db
from autogenstudio.planner.orchestrator import planner_orchestrator
from autogenstudio.planner.queue_userproxy import QueueUserProxyAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogenstudio.utils.constants import PLANNER_PROMPT
import traceback
from autogenstudio.planner.clarification_agent import ClarificationAgent
from autogenstudio.core.config import get_settings
import asyncio
from fastapi.responses import StreamingResponse
from autogen_agentchat.messages import TextMessage, UserInputRequestedEvent
import datetime


router = APIRouter()

builder_queues: Dict[int, asyncio.Queue] = {}


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


async def upsert_and_stream(gallery_id, gc, db, prompt: str = ""):
    try:
        assistant_message = ""
        async for chunk in gc.run_stream(task=prompt):
            if isinstance(chunk, TextMessage) or isinstance(
                chunk, UserInputRequestedEvent
            ):
                data = {"text": chunk.content}
                assistant_message += chunk.content
            else:
                data = chunk

            # Store partial response data in the database
            builder_message_model = BuilderMessage(
                builder_session_id=gallery_id,
                role=BuilderRole.ASSISTANT,
                content=assistant_message,
                message_meta=MessageMeta(
                    task=prompt,
                    time=datetime.datetime.now(datetime.timezone.utc),
                ),
            )
            db.upsert(builder_message_model)

            yield f"data: {json.dumps(data)}\n\n"
    except Exception as e:
        error_msg = f"Error in streaming: {str(e)} {traceback.format_exc()}"
        print(error_msg)
        yield f"data: {json.dumps({'error': error_msg})}\n\n"
    finally:
        yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"


@router.post("/plan")
async def plan_team(
    gallery_id: int = Form(...),
    prompt: str = Form(...),
    knowledge_base: str = Form(...),
    file: UploadFile = File(None),
    db=Depends(get_db),
) -> Dict:
    try:
        settings = get_settings()
        result = db.get(Gallery, filters={"id": gallery_id})
        if not result.data or len(result.data) == 0:
            # create a default gallery entry
            gallery_config = create_default_gallery()
            default_gallery = Gallery(id=gallery_id, config=gallery_config.model_dump())
            db.upsert(default_gallery)
            result = db.get(Gallery, filters={"id": gallery_id})

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

        if gallery_id not in builder_queues:
            builder_queues[gallery_id] = asyncio.Queue(maxsize=1)

        user_proxy_agent = QueueUserProxyAgent("user_proxy", gallery_id, builder_queues)

        selector_gc = planner_orchestrator(
            model_client=model_client,
            agents=[user_proxy_agent, planner_agent, clarification_agent],
        )

        intermediate_task_result = await selector_gc.save_state()

        builder_message_model = BuilderMessage(
            builder_session_id=gallery_id,
            role=BuilderRole.USER,
            content=prompt,
            message_meta=MessageMeta(
                task=prompt,
                time=datetime.datetime.now(datetime.timezone.utc),
                summary_method=json.dumps(intermediate_task_result),
            ),
        )
        db.upsert(builder_message_model)

        return StreamingResponse(
            upsert_and_stream(gallery_id=gallery_id, gc=selector_gc, db=db, prompt=prompt), media_type="text/event-stream"  # type: ignore
        )

    except Exception as e:
        print(f"Error in planning: {str(e)} {traceback.format_exc()}")
        return Response(status=False, data=[], message=f"Error in planning: {str(e)}")  # type: ignore


@router.websocket("/ws/{builder_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    builder_id: int,
    db=Depends(get_db),
):
    await websocket.accept()

    try:
        if builder_id not in builder_queues:
            builder_queues[builder_id] = asyncio.Queue(maxsize=1)

        # Send initial connection message
        await websocket.send_json({"status": "connected", "builder_id": builder_id})

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if not builder_queues[builder_id].full():
                await builder_queues[builder_id].put(message["message"])
                builder_message_model = BuilderMessage(
                    builder_session_id=builder_id,
                    role=BuilderRole.USER,
                    content=message["message"],
                    message_meta=MessageMeta(
                        task=message["message"],
                        time=datetime.datetime.now(datetime.timezone.utc),
                    ),
                )
                db.upsert(builder_message_model)
                await websocket.send_json({"status": "message_received"})
            else:
                await websocket.send_json(
                    {"status": "error", "message": "Queue full, wait for processing"}
                )

    except WebSocketDisconnect:
        print(f"Client disconnected for builder_id: {builder_id}")
    except Exception as e:
        print(f"Error in WebSocket: {str(e)} {traceback.format_exc()}")
        await websocket.send_json({"status": "error", "message": str(e)})


@router.delete("/{team_id}")
async def delete_team(team_id: int, user_id: str, db=Depends(get_db)) -> Dict:
    """Delete a team"""
    db.delete(filters={"id": team_id, "user_id": user_id}, model_class=Team)
    return {"status": True, "message": "Team deleted successfully"}
