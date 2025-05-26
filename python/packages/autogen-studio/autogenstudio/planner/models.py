import inspect
from typing import Any, List, Literal, Optional, Union, override

from pydantic import BaseModel, ConfigDict, Field


# === Termination Condition Models ===


class TextMentionTerminationConfig(BaseModel):
    text: str


class TextMentionTermination(BaseModel):
    description: str
    label: str
    config: TextMentionTerminationConfig

    @override
    def model_dump(self, **kwargs) -> dict[str, Any]:
        json_data = super().model_dump(**kwargs)
        json_data["provider"] = "autogen_agentchat.conditions.TextMentionTermination"
        json_data["version"] = 1
        json_data["component_version"] = 1
        json_data["component_type"] = "termination"

        return json_data


class MaxMessageTerminationConfig(BaseModel):
    max_messages: int
    include_agent_event: bool


class MaxMessageTermination(BaseModel):
    description: str
    label: str
    config: MaxMessageTerminationConfig

    @override
    def model_dump(self, **kwargs) -> dict[str, Any]:
        json_data = super().model_dump(**kwargs)
        json_data["provider"] = "autogen_agentchat.conditions.MaxMessageTermination"
        json_data["version"] = 1
        json_data["component_version"] = 1
        json_data["component_type"] = "termination"

        return json_data


# === Termination Condition Union Type ===

TerminationConditionType = Union[TextMentionTermination, MaxMessageTermination]


# === AndTerminationCondition type ===


class AndTerminationConditionConfig(BaseModel):
    conditions: List[TerminationConditionType]


class AndTerminationCondition(BaseModel):
    label: str
    config: AndTerminationConditionConfig

    @override
    def model_dump(self, **kwargs) -> dict[str, Any]:
        json_data = super().model_dump(**kwargs)
        json_data["provider"] = "autogen_agentchat.base.AndTerminationCondition"
        json_data["version"] = 1
        json_data["component_version"] = 1
        json_data["component_type"] = "termination"

        return json_data


# === OrTerminationCondition ===


class OrTerminationConditionConfig(BaseModel):
    conditions: List[TerminationConditionType]


class OrTerminationCondition(BaseModel):
    label: str
    config: OrTerminationConditionConfig

    @override
    def model_dump(self, **kwargs) -> dict[str, Any]:
        json_data = super().model_dump(**kwargs)
        json_data["provider"] = "autogen_agentchat.base.OrTerminationCondition"
        json_data["version"] = 1
        json_data["component_version"] = 1
        json_data["component_type"] = "termination"

        return json_data


# === Model Context ===


class UnboundedChatCompletionContext(BaseModel):
    description: str
    label: str
    config: dict = Field(alias="config")

    model_config = ConfigDict(
        json_schema_extra={"required": ["description", "label", "config"]}
    )

    @override
    def model_dump(self, **kwargs) -> dict[str, Any]:
        json_data = super().model_dump(**kwargs)
        json_data["provider"] = (
            "autogen_core.model_context.UnboundedChatCompletionContext"
        )
        json_data["version"] = 1
        json_data["component_version"] = 1
        json_data["component_type"] = "chat_completion_context"

        return json_data


# === Model Client ===


class OpenAIChatCompletionClient(BaseModel):
    description: str
    label: str
    config: dict = Field(alias="config")

    model_config = ConfigDict(
        json_schema_extra={"required": ["description", "label", "config"]}
    )

    @override
    def model_dump(self, **kwargs) -> dict[str, Any]:
        json_data = super().model_dump(**kwargs)
        json_data["provider"] = "autogen_ext.models.openai.OpenAIChatCompletionClient"
        json_data["version"] = 1
        json_data["component_version"] = 1
        json_data["component_type"] = "model"

        return json_data


# === AssistantAgent ===


class AssistantAgentConfig(BaseModel):
    name: str
    model_client: OpenAIChatCompletionClient
    tools: List[str] = Field(default_factory=list)
    handoffs: List[str] = Field(default_factory=list)
    model_context: UnboundedChatCompletionContext
    description: str
    system_message: str
    model_client_stream: bool
    reflect_on_tool_use: bool
    tool_call_summary_format: str

    model_config = ConfigDict(
        json_schema_extra={
            "required": [
                "name",
                "model_client",
                "model_context",
                "description",
                "system_message",
            ]
        }
    )


class AssistantAgent(BaseModel):
    description: str
    label: str
    config: AssistantAgentConfig

    model_config = ConfigDict(
        json_schema_extra={"required": ["description", "label", "config"]}
    )

    @override
    def model_dump(self, **kwargs) -> dict[str, Any]:
        json_data = super().model_dump(**kwargs)
        json_data["provider"] = "autogen_agentchat.agents.AssistantAgent"
        json_data["version"] = 1
        json_data["component_version"] = 1
        json_data["component_type"] = "agent"

        return json_data


# === Shared GroupChat Config ===


class BaseGroupChatConfig(BaseModel):
    participants: List[AssistantAgent]
    termination_condition: OrTerminationCondition  # OrTerminationCondition includes its own schema for provider etc.

    model_config = ConfigDict(
        json_schema_extra={"required": ["participants", "termination_condition"]}
    )


class BaseGroupChat(BaseModel):
    description: str
    label: str
    config: BaseGroupChatConfig

    model_config = ConfigDict(
        json_schema_extra={"required": ["description", "label", "config"]}
    )

    @override
    def model_dump(self, **kwargs) -> dict[str, Any]:
        json_data = super().model_dump(**kwargs)
        json_data["provider"] = "autogen_agentchat.teams.BaseGroupChat"
        json_data["version"] = 1
        json_data["component_version"] = 1
        json_data["component_type"] = "team"

        return json_data


# === RoundRobinGroupChat ===


class RoundRobinGroupChat(BaseGroupChat):
    prompt: str

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"required": ["description", "label", "config", "prompt"]},
    )

    @override
    def model_dump(self, **kwargs) -> dict[str, Any]:
        json_data = super().model_dump(
            **kwargs
        )  # Gets provider, version etc from BaseGroupChat
        json_data["provider"] = (
            "autogen_agentchat.teams.RoundRobinGroupChat"  # Overrides provider
        )

        return json_data


# === SelectorGroupChat ===


class SelectorGroupChat(BaseGroupChat):
    prompt: str

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"required": ["description", "label", "config", "prompt"]},
    )

    @override
    def model_dump(self, **kwargs) -> dict[str, Any]:
        json_data = super().model_dump(
            **kwargs
        )  # Gets provider, version etc from BaseGroupChat
        json_data["provider"] = (
            "autogen_agentchat.teams.SelectorGroupChat"  # Overrides provider
        )

        return json_data


# union types for all the above
Agent = Union[AssistantAgent]
ChatContext = Union[UnboundedChatCompletionContext]
Model = Union[OpenAIChatCompletionClient]
TerminationCondition = Union[
    TextMentionTermination,
    MaxMessageTermination,
    OrTerminationCondition,
    AndTerminationCondition,
]
GroupChat = Union[RoundRobinGroupChat, SelectorGroupChat]
