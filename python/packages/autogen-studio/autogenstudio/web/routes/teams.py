import asyncio
import datetime
import json
import traceback
from typing import Dict, Optional
from loguru import logger
import logging

from autogen_agentchat.base._task import TaskResult
from autogen_agentchat.messages import BaseChatMessage, UserInputRequestedEvent
from autogen_agentchat.teams import Swarm
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogenstudio.core.config import get_settings
from autogenstudio.planner.clarification_agent import ClarificationAgent
from autogenstudio.planner.orchestrator import planner_orchestrator
from autogenstudio.planner.planner_agent import get_planner_agent
from autogenstudio.planner.queue_userproxy import QueueUserProxyAgent
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import StreamingResponse

from ...database import DatabaseManager
from ...datamodel import BuilderRole, Gallery, MessageMeta, Team
from ...gallery.builder import create_default_gallery
from ...planner.models import SelectorGroupChatModel
from ...services.builder import BuilderService
from ..deps import get_db

router = APIRouter()

websockets: Dict[int, WebSocket] = {}
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


async def upsert_and_stream(builder_id: int, gc: Swarm, db, prompt: str = ""):
    global websockets

    service = BuilderService(db)

    try:
        async for chunk in gc.run_stream(task=prompt):

            if isinstance(chunk, BaseChatMessage):
                if chunk.type == "HandoffMessage":
                    print("HandoffMessage received, skipping")
                    print(chunk.to_model_text())
                    continue

                print("############################################")
                print(chunk.source, chunk.type)
                print(chunk.to_model_text())
                message_text = chunk.to_model_text()

                # Try to parse as JSON if it looks like JSON
                if message_text.strip().startswith(
                    "{"
                ) and message_text.strip().endswith("}"):
                    try:
                        # Try to parse the message as JSON
                        json_data = json.loads(message_text)
                        # If it's from the planner, try to convert it to a SelectorGroupChatModel
                        if chunk.source.lower() == "planner":
                            try:
                                # Validate against the model
                                model_instance = SelectorGroupChatModel.model_validate(
                                    json_data
                                )
                                received_data = model_instance.model_dump()
                            except Exception as e:
                                # If validation fails, just use the raw JSON
                                received_data = json_data
                        else:
                            received_data = json_data
                    except json.JSONDecodeError:
                        # If it's not valid JSON, use the raw text
                        received_data = message_text
                else:
                    # Not JSON, use raw text
                    received_data = message_text

                data = {
                    "text": received_data,
                    "role": (
                        BuilderRole.USER
                        if chunk.source.lower() in ["user", "user_proxy"]
                        else BuilderRole.ASSISTANT
                    ),
                }

                service.create_message(
                    builder_id,
                    data["role"],
                    message_text,  # Store the original message text
                    MessageMeta(
                        task=prompt,
                        time=datetime.datetime.now(datetime.timezone.utc),
                    ),
                )

                yield f"data: {json.dumps(data)}\n\n"

            elif isinstance(chunk, UserInputRequestedEvent):
                print("user input requested")
                ws = websockets.get(builder_id)
                if ws:
                    await ws.send_text("user_input")

            elif isinstance(chunk, TaskResult):
                print("result", chunk)

        yield ""

    except Exception as e:
        error_msg = f"Error in streaming: {str(e)} {traceback.format_exc()}"
        print(error_msg)
        yield f"data: {json.dumps({'error': error_msg})}\n\n"
    finally:
        yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"


@router.post("/plan")
async def plan_team(
    builder_id: int = Form(...),
    gallery_id: int = Form(...),
    prompt: str = Form(...),
    knowledge_base: Optional[str] = Form(default=None),
    # file: Optional[UploadFile] = File(None),
    db: DatabaseManager = Depends(get_db),
) -> Dict:
    try:
        settings = get_settings()
        service = BuilderService(db)
        result = db.get(Gallery, filters={"id": gallery_id})
        if not result.data or len(result.data) == 0:
            # create a default gallery entry
            gallery_config = create_default_gallery()
            default_gallery = Gallery(id=gallery_id, config=gallery_config.model_dump())
            result = db.upsert(default_gallery, return_json=False)

        tools = result.data[0].config["components"]["tools"]
        agents = result.data[0].config["components"]["agents"]
        terminations = result.data[0].config["components"]["terminations"]

        # update builder config selection
        service.update_config_selection(
            builder_id,
            [agent["label"] for agent in agents],
            [tool["label"] for tool in tools],
            [],
            gallery_id,
        )

        model_client = AzureOpenAIChatCompletionClient(
            azure_deployment=settings.AZURE_DEPLOYMENT,
            api_key=settings.AZURE_API_KEY,
            api_version=settings.AZURE_VERSION,
            azure_endpoint=settings.AZURE_ENDPOINT,
            model=settings.AZURE_MODEL,
        )

        planner_agent = get_planner_agent()

        clarification_agent = ClarificationAgent(
            model_client=model_client,
            kb_collection_name=knowledge_base,
        )

        # create the queue for user input
        builder_queues.setdefault(builder_id, asyncio.Queue(maxsize=1))

        user_proxy_agent = QueueUserProxyAgent(
            "user_proxy", model_client, builder_queues[builder_id]
        )
        selector_gc = planner_orchestrator(
            model_client=model_client,
            agents=[clarification_agent, user_proxy_agent, planner_agent],
        )

        return StreamingResponse(
            upsert_and_stream(
                builder_id=builder_id, gc=selector_gc, db=db, prompt=prompt
            ),
            media_type="text/event-stream",
        )

    except Exception as e:
        print(e)
        logger.exception(f"Error in planning: {str(e)}")
        return HTTPException(status_code=500, detail=f"Error in planning: {str(e)}")


@router.websocket("/ws/{builder_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    builder_id: int,
    db: DatabaseManager = Depends(get_db),
):
    await websocket.accept()

    try:
        builder_queues.setdefault(builder_id, asyncio.Queue(maxsize=1))
        websockets.setdefault(builder_id, websocket)
        queue = builder_queues[builder_id]

        # Send initial connection message
        await websocket.send_json({"status": "connected", "builder_id": builder_id})

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            print(f"Received message for builder_id {builder_id}: {message}")
            await queue.put(message["message"])

            await websocket.send_json({"status": "message_received"})

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
