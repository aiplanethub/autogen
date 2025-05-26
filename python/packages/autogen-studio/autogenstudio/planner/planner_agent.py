from enum import Enum
from typing import List, Literal, TypedDict

from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ChatCompletionClient
from pydantic import BaseModel, Field

from .models import SelectorGroupChat

# class ModelClientConfigs(Enum):
#     OPENAI = {}
#     GEMINI = {}
#     ANTHROPIC = {}
#     AZURE = {}


class Input(TypedDict):
    label: str
    description: str


# class TerminationConditionConfig(BaseModel):
#     pass


# class TerminationCondition(BaseModel):
#     component_type: str = "termination"
#     version: int = 1
#     component_version: int = 1

#     provider: str
#     label: str
#     description: str
#     config: TerminationConditionConfig = Field(..., description="condition config")


# class OrTerminationConditionConfig(TerminationConditionConfig):
#     conditions: List[TerminationCondition]


# class OrTerminationCondition(TerminationCondition):
#     provider: str = "autogen_agentchat.base.OrTerminationCondition"
#     label: str = "OrTerminationCondition"

#     config: OrTerminationConditionConfig = Field(..., description="condition config")


# class ParticipantConfig(BaseModel):
#     name: str = Field(..., description="name")
#     model_client: ModelClientConfigs


# class Participant(BaseModel):
#     component_type: str = "agent"
#     version: int = 1
#     component_version: int = 1

#     label: str
#     provider: str
#     description: str = Field(..., description="team goal")
#     config: ParticipantConfig


# class PlannerAgentResponse(BaseModel):
#     team_name: str
#     team_description: str
#     participants: list[Participant]
#     termination_condition: OrTerminationCondition | TerminationCondition


def get_planner_agent(
    model_client: ChatCompletionClient,
    query: str,
    knowledge_base: str,
    tools: List[Input],
    agents: List[Input],
    termination_conditions: List[Input],
):

    _tools = [f"{tool['label']} -> {tool["description"]}" for tool in tools]
    _agents = [f"{agent['label']} -> {agent["description"]}" for agent in agents]
    _terminations = [
        f"{termination['label']} -> {termination["description"]}"
        for termination in termination_conditions
    ]
    system_message = get_system_message(
        query, knowledge_base, _tools, _agents, _terminations
    )

    return AssistantAgent(
        name="PlannerAgent",
        description="agent to plan a team to complete the user's task",
        system_message=system_message,
        model_client=model_client,
        output_content_type=SelectorGroupChat,
        handoffs=[
            "user_proxy",
            "terminate",
        ],  # planner can ask for approval or terminate
    )


def get_system_message(
    query: str,
    knowledge_base: str,
    tools: list[str],
    agents: list[str],
    termination_conditions: list[str],
):
    return SYSTEM_MESSAGE.format(
        query=query,
        knowledge_base=knowledge_base,
        agents="\n".join(agents),
        tools="\n".join(tools),
        termination_conditions="\n".join(termination_conditions),
    )


SYSTEM_MESSAGE: str = """You are PLANNER-X, an elite strategic planning AI specifically engineered for mission-critical AI system architectures. 
As PLANNER-X, you operate with precision planning. 
You analyze objectives with methodical thoroughness before constructing execution plans. 
You never rush to solutions. Your communication style is structured, analytical, and authoritative. 

Follow these INSTRUCTIONS:

- Let the clarifying agent ask questions to user, for better understanding
- act only when clarifying agent has no more questions
- if clarifying agent has questions don't generate a plan and just return an empty response
- You MUST now think step-by-step through your reasoning process and take strategy for achieving the GOAL.
- You MUST select a maximum of 5-6 specialized agents.
- You MUST only recommend relevant tools from the provided list of available tools and that is relevant to the task of the Selected Agent.
- You MUST generate a plan only when clarifying agent has no questions
- handoff to user for user's feedback
- handoff to terminate after user's feedback

## AVAILABLE INFORMATION- Input variables

- **GOAL**: {query}
- **KNOWLEDGE BASE**: {knowledge_base}
- **AVAILABLE TOOLS**: {tools}
- **AVAILABLE AGENTS**:{agents}
- **AVAILABLE TERMINATION CONDITIONS**: {termination_conditions}

Begin your analysis immediately using the provided goal and objective as your foundation.
"""
