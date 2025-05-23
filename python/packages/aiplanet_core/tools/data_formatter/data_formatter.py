from autogen_core import CancellationToken, Component
from autogen_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing_extensions import Self
from typing import Any, Dict
import json
import os

class DataFormatterInput(BaseModel):
    data: str= Field(description="the data given by the user to be formatted")
    format_type: str = Field(default="json", description="Format type: 'json', 'yaml' ")

class DataFormatterResult(BaseModel):
    success: bool
    formatted: str

class DataFormatterToolConfig(BaseModel):
    description: str = "Format data as JSON or YAML, or use LLM for conversion."

class DataFormatterTool(BaseTool[DataFormatterInput, DataFormatterResult], Component[DataFormatterToolConfig]):
    """A tool to format data as JSON, YAML, or use an LLM for conversion if needed."""

    component_config_schema = DataFormatterToolConfig
    component_provider_override = "aiplanet_core.tools.data_formatter.DataFormatterTool"

    def __init__(self):
        super().__init__(
            DataFormatterInput,
            DataFormatterResult,
            "DataFormatter",
            "Format data as JSON or YAML, or use LLM for conversion."
        )

    async def run(
        self,
        args: DataFormatterInput,
        cancellation_token: CancellationToken
    ) -> DataFormatterResult:
        try:
            if args.format_type == "json":
                formatted = json.dumps(args.data, indent=2)
                # Validate JSON
                try:
                    json.loads(formatted)
                except Exception as e:
                    return DataFormatterResult(success=False, formatted=json.dumps({"error": f"Invalid JSON output: {str(e)}"}))
                return DataFormatterResult(success=True, formatted=formatted)
            elif args.format_type == "yaml":
                import yaml
                formatted = yaml.dump(args.data)
                # Validate YAML
                try:
                    yaml.safe_load(formatted)
                except Exception as e:
                    return DataFormatterResult(success=False, formatted=json.dumps({"error": f"Invalid YAML output: {str(e)}"}))
                return DataFormatterResult(success=True, formatted=formatted)
            else:
                # Use LLM to convert to valid JSON format
                AZURE_DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT")
                MODEL_NAME = os.getenv("MODEL_NAME")
                VERSION = os.getenv("VERSION")
                AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
                API_KEY = os.getenv("API_KEY")
                try:
                    from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
                    from autogen_core.models import UserMessage

                    azure_client = AzureOpenAIChatCompletionClient(
                        azure_deployment=AZURE_DEPLOYMENT,
                        model=MODEL_NAME,
                        api_version=VERSION,
                        azure_endpoint=AZURE_ENDPOINT,
                        api_key=API_KEY,
                    )

                    prompt = f"""
                    Convert the following data to valid JSON format:
                    {args.data}

                    Return ONLY the JSON with no explanations or markdown formatting.
                    """

                    result = await azure_client.create([UserMessage(content=prompt, source="user")])
                    if result and hasattr(result, "content"):
                        content = result.content.strip()
                        # Validate LLM output as JSON
                        try:
                            json.loads(content)
                        except Exception as e:
                            return DataFormatterResult(success=False, formatted=json.dumps({"error": f"LLM output is not valid JSON: {str(e)}", "raw": content}))
                        return DataFormatterResult(success=True, formatted=content)
                    return DataFormatterResult(success=False, formatted=json.dumps({"error": "Failed to process with LLM"}))
                except Exception as e:
                    return DataFormatterResult(success=False, formatted=json.dumps({"error": f"Format conversion error: {str(e)}"}))
        except Exception as e:
            return DataFormatterResult(success=False, formatted=json.dumps({"error": f"DataFormatter error: {str(e)}"}))

    def _to_config(self) -> DataFormatterToolConfig:
        return DataFormatterToolConfig()

    @classmethod
    def _from_config(cls, config: DataFormatterToolConfig) -> Self:
        return cls()
