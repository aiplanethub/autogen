from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import ChatAgent
from autogen_agentchat.conditions import HandoffTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat, Swarm


def planner_orchestrator(model_client, agents: list[ChatAgent], *args):

    terminate = AssistantAgent(
        name="terminate",
        description="standin for terminating swarms",
        system_message='response with "TERMINATE"',
        model_client=model_client,
    )

    termination = HandoffTermination(target="terminate") | TextMentionTermination(
        "TERMINATE", ["terminate"]
    )
    agents.append(terminate)  # add the terminate agent
    swarm = Swarm(agents, termination_condition=termination)

    return swarm

    selector_prompt = """
    Your task is to orchestrate the agents to generate a plan.
    You have {roles}.
    
    This is the current conversation history
    {history}

    this should be the flow
    if clarifying agent has questions -> user agent
    if user agent is anwering questions -> clarifying agent
    if clarifying agent does not have questions -> planner agent
    if planner agent responds -> user agent
    if user agent approves -> TERMINATE
    if user agent rejects -> planner agent

    select the next agent using from {participants}
    """

    # def selector_func(messages: Sequence[BaseAgentEvent | BaseChatMessage]):
    #     pass

    return SelectorGroupChat(
        # selector_func=selector_func,
        selector_prompt=selector_prompt,
        participants=agents,
        model_client=model_client,
        model_client_streaming=True,
        termination_condition=termination,
        *args,
    )
