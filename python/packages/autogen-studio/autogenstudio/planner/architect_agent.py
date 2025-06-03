from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from autogen_agentchat.agents import AssistantAgent
from autogenstudio.datamodel.types import SelectorGroupChatConfig


# ——————————————————————————————————————————————
# ArchitectConfig - Using simplified structure
# ——————————————————————————————————————————————
class ArchitectConfig(BaseModel):
    provider: str = Field(..., description="The provider of the team component")
    component_type: Literal["team"] = Field(..., description="The type of component")
    version: int = Field(..., description="The version number")
    component_version: int = Field(..., description="The component version number")
    description: str = Field(..., description="Description of the team")
    label: str = Field(..., description="The label of the team")
    config: SelectorGroupChatConfig = Field(..., description="The team configuration")

    model_config = ConfigDict(extra="forbid")


SYSTEM_MESSAGE = """
You are a team configuration agent. When you respond, output a JSON object that matches the ArchitectConfig schema.

The schema requires:
- "provider": The provider of the team component (e.g., "autogen_agentchat.teams.SelectorGroupChat")
- "component_type": Must be "team"
- "version": The version number as an integer
- "component_version": The component version number as an integer
- "description": A description of the team
- "label": A label for the team
- "config": A SelectorGroupChatConfig object with:
  - "participants": List of agent configurations
  - "model_client": The model client configuration
  - "termination_condition": The termination condition configuration
  - "selector_prompt": The prompt for the selector
  - "allow_repeated_speaker": Boolean indicating if speakers can repeat
  - "max_selector_attempts": Maximum number of selector attempts

Each participant must have:
- "provider": The provider of the agent (e.g., "autogen_agentchat.agents.AssistantAgent")
- "component_type": Must be "agent"
- "version": The version number as an integer
- "component_version": The component version number as an integer
- "description": A description of the agent
- "label": A label for the agent
- "config": An AssistantAgentConfig object with:
  - "name": The name of the agent
  - "model_client": The model client configuration
  - "tools": A list of tool configurations (optional)
  - "model_context": The model context configuration
  - "description": A description of the agent
  - "system_message": The system message for the agent
  - "model_client_stream": Boolean indicating if the model client streams
  - "reflect_on_tool_use": Boolean indicating if the agent reflects on tool use
  - "tool_call_summary_format": The format for tool call summaries

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
