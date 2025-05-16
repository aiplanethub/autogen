from autogen_core import CancellationToken, Component, ComponentModel
from autogen_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing_extensions import Self
from typing import List, Optional
from aiplanet_core.tools.weaviate.weaviate_service import WeaviateService

class WeaviateSearchInput(BaseModel):
    query: str = Field(description="The search query to look up in Weaviate")
    collection_name: str = Field(description="The name of the Weaviate collection to search")
    num_results: int = Field(default=5, description="Number of results to return")

class WeaviateSearchResultItem(BaseModel):
    id: int
    content: Optional[str] = None

class WeaviateSearchResult(BaseModel):
    success: bool
    results: List[WeaviateSearchResultItem]
    error: Optional[str] = None

class WeaviateSearchToolConfig(BaseModel):
    """Configuration for WeaviateSearchTool"""
    description: str = "Search a Weaviate vector database for semantically similar documents."

class WeaviateSearchTool(BaseTool[WeaviateSearchInput, WeaviateSearchResult], Component[WeaviateSearchToolConfig]):
    component_config_schema = WeaviateSearchToolConfig
    component_provider_override = "aiplanet_core.tools.weaviate.WeaviateSearchTool"

    def __init__(self):
        super().__init__(
            WeaviateSearchInput,
            WeaviateSearchResult,
            "WeaviateSearch",
            "Search a Weaviate vector database for semantically similar documents."
        )

    async def run(
        self,
        args: WeaviateSearchInput,
        cancellation_token: CancellationToken
    ) -> WeaviateSearchResult:
        try:
            async with WeaviateService() as weaviate_service:
                results = await weaviate_service.query_weaviate(args.query, args.collection_name)
                formatted_results = [
                    WeaviateSearchResultItem(id=i+1, content=content)
                    for i, content in enumerate(results[:args.num_results])
                ]
                return WeaviateSearchResult(success=True, results=formatted_results)
        except Exception as e:
            return WeaviateSearchResult(success=False, results=[], error=str(e))

    def _to_config(self) -> WeaviateSearchToolConfig:
        return WeaviateSearchToolConfig()

    @classmethod
    def _from_config(cls, config: WeaviateSearchToolConfig) -> Self:
        return cls()
