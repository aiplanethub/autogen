from autogen_core import CancellationToken, Component
from autogen_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing_extensions import Self
from typing import Optional
import os

class PromptTemplateInput(BaseModel):
    user_input: str = Field(description="User requirements for the system prompt.")

class PromptTemplateResult(BaseModel):
    success: bool
    system_prompt: str

class PromptTemplateToolConfig(BaseModel):
    """Configuration for PromptTemplateTool"""
    description: str = "Generate a well-crafted system prompt based on user requirements."

class PromptTemplateTool(BaseTool[PromptTemplateInput, PromptTemplateResult], Component[PromptTemplateToolConfig]):
    component_config_schema = PromptTemplateToolConfig
    component_provider_override = "aiplanet_core.tools.prompt_template.PromptTemplateTool"

    def __init__(self):
        super().__init__(
            PromptTemplateInput,
            PromptTemplateResult,
            "PromptTemplate",
            "Generate a well-crafted system prompt based on user requirements."
        )

    async def run(
        self,
        args: PromptTemplateInput,
        cancellation_token: CancellationToken
    ) -> PromptTemplateResult:
        try:
            from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
            from autogen_core.models import UserMessage
            azure_client = AzureOpenAIChatCompletionClient(
                azure_deployment=os.getenv("AZURE_DEPLOYMENT"),
                model=os.getenv("AZURE_MODEL"),
                api_version=os.getenv("AZURE_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_ENDPOINT"),
                api_key=os.getenv("AZURE_API_KEY"),
            )
            prompt = f"""
Create a well-crafted system prompt for an AI assistant based on this user request:
"{args.user_input}"

Return only the system prompt text without any explanations or formatting instructions.
"""
            result = await azure_client.create([UserMessage(content=prompt, source="user")])
            if result and hasattr(result, "content"):
                return PromptTemplateResult(success=True, system_prompt=result.content.strip())
            return PromptTemplateResult(success=True, system_prompt="You are a helpful assistant.")
        except Exception as e:
            return PromptTemplateResult(success=False, system_prompt=f"Error generating system prompt: {str(e)}")

    def _to_config(self) -> PromptTemplateToolConfig:
        return PromptTemplateToolConfig()

    @classmethod
    def _from_config(cls, config: PromptTemplateToolConfig) -> Self:
        return cls()
