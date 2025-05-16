from autogen_core import CancellationToken, Component, ComponentModel
from autogen_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing_extensions import Self
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import UserMessage
import os
from dotenv import load_dotenv
load_dotenv()

class OpenAIInput(BaseModel):
    query: str = Field(description="The query to send to OpenAI")

class OpenAIResult(BaseModel):
    success: bool
    response: str

class OpenAIToolConfig(BaseModel):
    """Configuration for OpenAITool"""
    description: str = "Query OpenAI with prompts and get responses"
    model: str = Field(default="gpt-4", description="The OpenAI model to use")
    api_key: str = Field(description="OpenAI API key")

class OpenAITool(BaseTool[OpenAIInput, OpenAIResult], Component[OpenAIToolConfig]):
    component_config_schema = OpenAIToolConfig
    component_provider_override = "aiplanet_core.tools.OpenAI.OpenAITool"

    def __init__(self, model: str = "gpt-4", api_key: str = None):
        super().__init__(
            OpenAIInput,
            OpenAIResult,
            "OpenAI",
            "Query OpenAI with prompts and get responses"
        )
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = OpenAIChatCompletionClient(
            api_key=self._api_key,
            model=model,
        )

    async def run(
        self,
        args: OpenAIInput,
        cancellation_token: CancellationToken
    ) -> OpenAIResult:
        try:
            result = await self._client.create([UserMessage(content=args.query, source="user")])
            
            if result and hasattr(result, "content"):
                return OpenAIResult(success=True, response=result.content)
            return OpenAIResult(success=True, response=str(result))
            
        except Exception as e:
            return OpenAIResult(
                success=False,
                response=f"Error querying OpenAI: {str(e)}"
            )

    def _to_config(self) -> OpenAIToolConfig:
        return OpenAIToolConfig(
            model=self._client.model,
            api_key=self._client.api_key
        )

    @classmethod
    def _from_config(cls, config: OpenAIToolConfig) -> Self:
        return cls(
            model=config.model,
            api_key=config.api_key
        )