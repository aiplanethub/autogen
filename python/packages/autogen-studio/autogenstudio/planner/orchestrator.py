from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.agents import AssistantAgent
from typing import Any
from autogen_agentchat.conditions import _terminations


def planner_orchestrator(
    model_client,
    agents: list[AssistantAgent],
    selector_func: callable | None = None,
    candidate_func: callable | None = None,
    max_turns: int = 5,
    termination_condition: Any[_terminations] | None = None,
    selector_prompt: str | None = None,
    *args
):

    return SelectorGroupChat(
        participants=agents,
        model_client=model_client,
        max_turns=max_turns,
        selector_func=selector_func,
        candidate_func=candidate_func,
        termination_condition=termination_condition,
        selector_prompt=selector_prompt,
        args=args,
    )
