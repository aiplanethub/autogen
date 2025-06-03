from typing import List, TypedDict

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai._openai_client import AzureOpenAIChatCompletionClient

from ..core.config import get_settings


class Input(TypedDict):
    label: str
    description: str


def get_planner_agent():

    settings = get_settings()

    # Create the model client without response_format
    model_client = AzureOpenAIChatCompletionClient(
        azure_deployment=settings.AZURE_DEPLOYMENT,
        api_key=settings.AZURE_API_KEY,
        api_version=settings.AZURE_VERSION,
        azure_endpoint=settings.AZURE_ENDPOINT,
        model=settings.AZURE_MODEL,
    )

    # Create the agent without output_content_type
    return AssistantAgent(
        name="planner",
        description="agent to plan a team to complete the user's task",
        system_message=SYSTEM_MESSAGE,
        model_client=model_client,
        handoffs=["user_proxy", "terminate"],
        output_content_type_format=json_schema,
    )


json_schema = """{{
  "title": "RoundRobinGroupChat Configuration Schema",
  "type": "object",
  "required": ["provider", "component_type", "version", "component_version", "description", "label", "config"],
  "properties": {{
    "provider": {{ "type": "string", "const": "autogen_agentchat.teams.RoundRobinGroupChat" }},
    "component_type": {{ "type": "string", "const": "team" }},
    "version": {{ "type": "integer" }},
    "component_version": {{ "type": "integer" }},
    "description": {{ "type": "string" }},
    "label": {{ "type": "string" }},
    "config": {{
      "type": "object",
      "required": ["participants", "termination_condition", "emit_team_events"],
      "properties": {{
        "participants": {{
          "type": "array",
          "items": {{
            "type": "object",
            "required": ["provider", "component_type", "version", "component_version", "description", "label", "config"],
            "properties": {{
              "provider": {{ "type": "string", "const": "autogen_agentchat.agents.AssistantAgent" }},
              "component_type": {{ "type": "string", "const": "agent" }},
              "version": {{ "type": "integer" }},
              "component_version": {{ "type": "integer" }},
              "description": {{ "type": "string" }},
              "label": {{ "type": "string" }},
              "config": {{
                "type": "object",
                "required": ["name", "model_client", "workbench", "model_context", "description", "system_message", "model_client_stream", "reflect_on_tool_use", "tool_call_summary_format", "metadata"],
                "properties": {{
                  "name": {{ "type": "string" }},
                  "model_client": {{
                    "type": "object",
                    "required": ["provider", "component_type", "version", "component_version", "description", "label", "config"],
                    "properties": {{
                      "provider": {{ "type": "string", "const": "autogen_ext.models.openai.OpenAIChatCompletionClient" }},
                      "component_type": {{ "type": "string", "const": "model" }},
                      "version": {{ "type": "integer" }},
                      "component_version": {{ "type": "integer" }},
                      "description": {{ "type": "string" }},
                      "label": {{ "type": "string" }},
                      "config": {{
                        "type": "object",
                        "required": ["model"],
                        "properties": {{
                          "model": {{ "type": "string" }}
                        }}
                      }}
                    }}
                  }},
                  "workbench": {{
                    "type": "object",
                    "required": ["provider", "component_type", "version", "component_version", "description", "label", "config"],
                    "properties": {{
                      "provider": {{ "type": "string", "const": "autogen_core.tools.StaticWorkbench" }},
                      "component_type": {{ "type": "string", "const": "workbench" }},
                      "version": {{ "type": "integer" }},
                      "component_version": {{ "type": "integer" }},
                      "description": {{ "type": "string" }},
                      "label": {{ "type": "string" }},
                      "config": {{
                        "type": "object",
                        "required": ["tools"],
                        "properties": {{
                          "tools": {{
                            "type": "array",
                            "items": {{
                              "type": "object",
                              "required": ["provider", "component_type", "version", "component_version", "description", "label", "config"],
                              "properties": {{
                                "provider": {{ "type": "string", "const": "autogen_core.tools.FunctionTool" }},
                                "component_type": {{ "type": "string", "const": "tool" }},
                                "version": {{ "type": "integer" }},
                                "component_version": {{ "type": "integer" }},
                                "description": {{ "type": "string" }},
                                "label": {{ "type": "string" }},
                                "config": {{
                                  "type": "object",
                                  "required": ["source_code", "name", "description", "global_imports", "has_cancellation_support"],
                                  "properties": {{
                                    "source_code": {{ "type": "string" }},
                                    "name": {{ "type": "string" }},
                                    "description": {{ "type": "string" }},
                                    "global_imports": {{ "type": "array", "items": {{ "type": "string" }} }},
                                    "has_cancellation_support": {{ "type": "boolean" }}
                                  }}
                                }}
                              }}
                            }}
                          }}
                        }}
                      }}
                    }}
                  }},
                  "model_context": {{
                    "type": "object",
                    "required": ["provider", "component_type", "version", "component_version", "description", "label", "config"],
                    "properties": {{
                      "provider": {{ "type": "string", "const": "autogen_core.model_context.UnboundedChatCompletionContext" }},
                      "component_type": {{ "type": "string", "const": "chat_completion_context" }},
                      "version": {{ "type": "integer" }},
                      "component_version": {{ "type": "integer" }},
                      "description": {{ "type": "string" }},
                      "label": {{ "type": "string" }},
                      "config": {{ "type": "object" }}
                    }}
                  }},
                  "description": {{ "type": "string" }},
                  "system_message": {{ "type": "string" }},
                  "model_client_stream": {{ "type": "boolean" }},
                  "reflect_on_tool_use": {{ "type": "boolean" }},
                  "tool_call_summary_format": {{ "type": "string" }},
                  "metadata": {{ "type": "object" }}
                }}
              }}
            }}
          }}
        }},
        "termination_condition": {{
          "type": "object",
          "required": ["provider", "component_type", "version", "component_version", "label", "config"],
          "properties": {{
            "provider": {{ "type": "string", "const": "autogen_agentchat.base.OrTerminationCondition" }},
            "component_type": {{ "type": "string", "const": "termination" }},
            "version": {{ "type": "integer" }},
            "component_version": {{ "type": "integer" }},
            "label": {{ "type": "string" }},
            "config": {{
              "type": "object",
              "required": ["conditions"],
              "properties": {{
                "conditions": {{
                  "type": "array",
                  "items": {{
                    "type": "object",
                    "required": ["provider", "component_type", "version", "component_version", "description", "label", "config"],
                    "properties": {{
                      "provider": {{ "type": "string" }},
                      "component_type": {{ "type": "string", "const": "termination" }},
                      "version": {{ "type": "integer" }},
                      "component_version": {{ "type": "integer" }},
                      "description": {{ "type": "string" }},
                      "label": {{ "type": "string" }},
                      "config": {{ "type": "object" }}
                    }}
                  }}
                }}
              }}
            }}
          }}
        }},
        "emit_team_events": {{ "type": "boolean" }}
      }}
    }}
  }}
}}"""

SYSTEM_MESSAGE: str = f"""
Prompt:
`
You are a Planner Agent responsible for generating structured, modular workflows for a drag-and-drop visual workflow builder. Each workflow is composed of well-defined components like agents, tools, models, contexts, and termination conditions. These workflows are rendered as connected blocks in a node-based UI.

Your goal is to produce a valid JSON configuration that can be serialized to match a strict schema, ensuring compatibility with schema-driven user interfaces.


✅ Objectives
Create a multi-agent team, where each agent has a specific purpose (e.g., reasoning, tool usage, retrieval).

Define each agent with a:

Model (e.g., OpenAI, Anthropic)

Context (e.g., unbounded, limited memory)

Workbench (e.g., with custom tools)

Add tools that agents can use—such as function tools, APIs, calculators, file processors, etc.

Configure termination conditions such as keyword-based or message-count-based termination.

Provide clear component metadata:

provider

component_type

version and component_version

label and description

config with all required keys

🧩 JSON Schema (for guidance)
You must produce output that conforms to the following structure, based on this partial JSON Schema:

{str(json_schema)}
📦 Output Requirements
Return a valid JSON configuration.

Match the nesting, keys, and types defined in the schema above.

Avoid undefined fields. If optional fields are not needed, omit them.

Use descriptive labels and explanations for each component.

Ensure tool source code is safe and syntactically correct if using FunctionTool.

After generating the JSON, return it as a single string without any additional text or formatting.
handoff to the user, then terminate the team with the "terminate" handoff.
"""
