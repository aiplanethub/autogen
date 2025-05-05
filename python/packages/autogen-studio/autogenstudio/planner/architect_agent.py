from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from autogen_agentchat.agents import AssistantAgent


# ——————————————————————————————————————————————
# 1) AssistantAgentConfig
# ——————————————————————————————————————————————
class AssistantAgentConfig(BaseModel):
    name: str
    model_client: str
    model_client_stream: bool
    tools: Optional[List[str]] = None
    workbench: Optional[str] = None
    handoffs: Optional[List[str]] = None
    model_context: Optional[str] = None
    memory: Optional[List[str]] = None
    description: Optional[str] = None
    system_message: Optional[str] = None
    reflect_on_tool_use: Optional[bool] = None
    tool_call_summary_format: Optional[str] = None
    output_content_type: Optional[str] = None
    output_content_type_format: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None

    model_config = ConfigDict(extra="forbid")


# ——————————————————————————————————————————————
# 2) GroupChatConfig - Single class with group_chat field as discriminator
# ——————————————————————————————————————————————
class GroupChatConfig(BaseModel):
    group_chat: str = Field(..., description="Type of group chat")
    participants: List[str] = Field(
        ..., description="List of agent names participating in the group chat."
    )
    termination_condition: Optional[str] = Field(
        None, description="Condition under which the group chat terminates."
    )
    max_turns: Optional[int] = Field(
        None, description="Maximum number of turns allowed in the group chat."
    )
    custom_message_types: Optional[List[str]] = Field(
        None, description="List of custom message types allowed in the group chat."
    )
    emit_team_events: Optional[bool] = Field(
        None, description="Whether the group chat emits team-level events."
    )
    # Optional fields for specific group chat types
    handoff_message_types: Optional[List[str]] = Field(
        None, description="List of message types used for handoffs (Swarm only)."
    )
    task_domains: Optional[List[str]] = Field(
        None, description="List of task domains or categories (MagenticOne only)."
    )

    model_config = ConfigDict(extra="forbid")


# ——————————————————————————————————————————————
# 3) ArchitectConfig - Using simplified structure
# ——————————————————————————————————————————————
class ArchitectConfig(BaseModel):
    group_chat: GroupChatConfig
    agents: List[AssistantAgentConfig]
    inputs: List[str] = Field(
        ..., description="List of input types (e.g., 'file', 'prompt', 'URL', 'JSON')"
    )
    outputs: List[str] = Field(
        ..., description="List of output types (e.g., 'file', 'prompt', 'URL', 'JSON')"
    )

    model_config = ConfigDict(extra="forbid")


SYSTEM_MESSAGE = """
    You are an architect agent. When you respond, output a JSON object that matches the ArchitectConfig schema.

    The schema requires:
    - "group_chat": A GroupChatConfig object with:
      - "group_chat": Type of group chat (must be one of: "RoundRobinGroupChat", "SelectorGroupChat", "Swarm", "MagenticOneGroupChat")
      - "participants": List of agent names participating in the chat
      - "termination_condition": Optional condition for termination
      - "max_turns": Optional maximum number of turns
      - "custom_message_types": Optional list of custom message types
      - "emit_team_events": Optional boolean for team events

    - "agents": A list of AssistantAgentConfig objects, each with:
      - "name": Name of the agent
      - "model_client": Name of the model client
      - "model_client_stream": Boolean for streaming support
      - Optional fields for tools, workbench, handoffs, context, memory, etc.

    - "inputs": List of input types (choose from: "file", "prompt", "URL", "JSON")
    - "outputs": List of output types (choose from: "file", "prompt", "URL", "JSON")

    Provide only the JSON object that matches this schema without additional text.
    """


def architect_agent(model_client, tools: list = None, memory: list = None):

    if memory is None:
        memory = []
    if tools is None:
        tools = []
    return AssistantAgent(
        name="architectAgent",
        system_message=SYSTEM_MESSAGE,
        model_client=model_client,
        memory=memory,
        tools=tools,
        model_context=None,
        output_content_type=ArchitectConfig,
    )
