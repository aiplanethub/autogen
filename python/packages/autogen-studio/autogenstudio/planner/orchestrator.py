from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.agents import AssistantAgent
from typing import Any


def planner_orchestrator(model_client, agents: list[AssistantAgent | Any], *args):

    return SelectorGroupChat(
        participants=agents,
        model_client=model_client,
        *args,
    )
