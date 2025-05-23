from autogen_core import CancellationToken, Component, ComponentModel
from autogen_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing_extensions import Self
from googlesearch import search
import json
from typing import List, Optional

class GoogleSearchInput(BaseModel):
    query: str = Field(description="The search query to look up on Google")
    num_results: int = Field(default=2, description="Number of results to return")
    language: str = Field(default="en", description="Language code for search results")

class SearchResult(BaseModel):
    title: str
    url: str
    description: str

class GoogleSearchResult(BaseModel):
    success: bool
    results: List[SearchResult]

class GoogleSearchToolConfig(BaseModel):
    """Configuration for GoogleSearchTool"""
    description: str = "Search the web using Google Search"

class GoogleSearchTool(BaseTool[GoogleSearchInput, GoogleSearchResult], Component[GoogleSearchToolConfig]):
    """A tool that performs web searches using Google Search.
    
    Example usage:
    ```python
    from aiplanet_core.tools.Google_search import GoogleSearchTool
    
    async def main():
        tool = GoogleSearchTool()
        result = await tool.run(
            GoogleSearchInput(
                query="latest AI developments",
                num_results=2,
                language="en"
            ),
            CancellationToken()
        )
        print(result.results)
    ```
    """

    component_config_schema = GoogleSearchToolConfig
    component_provider_override = "aiplanet_core.tools.Google_search.GoogleSearchTool"

    def __init__(self):
        super().__init__(
            GoogleSearchInput,
            GoogleSearchResult,
            "GoogleSearch",
            "Search the web using Google Search"
        )

    async def run(
        self,
        args: GoogleSearchInput,
        cancellation_token: CancellationToken
    ) -> GoogleSearchResult:
        try:
            # Perform the search
            results = list(search(
                args.query,
                num_results=args.num_results + 2,
                lang=args.language,
                proxy=None,
                advanced=True
            ))
            
            # Process results
            formatted_results = []
            for result in results:
                title = getattr(result, 'title', '')
                url = getattr(result, 'url', '')
                description = getattr(result, 'description', '')
                
                # Filter out invalid results
                if title and url and url != "/" and description and description != "/":
                    formatted_results.append(
                        SearchResult(
                            title=title or 'No title',
                            url=url or '',
                            description=description or 'No description'
                        )
                    )
                    
                    # Break once we have enough valid results
                    if len(formatted_results) >= args.num_results:
                        break
            
            # Return empty result if nothing found
            if not formatted_results:
                formatted_results = [
                    SearchResult(
                        title="No results found",
                        url="",
                        description="No results"
                    )
                ]
            
            return GoogleSearchResult(
                success=True,
                results=formatted_results
            )
            
        except Exception as e:
            return GoogleSearchResult(
                success=False,
                results=[
                    SearchResult(
                        title="Error",
                        url="",
                        description=f"Search error: {str(e)}"
                    )
                ]
            )

    def _to_config(self) -> GoogleSearchToolConfig:
        """Convert current instance to config object"""
        return GoogleSearchToolConfig()

    @classmethod
    def _from_config(cls, config: GoogleSearchToolConfig) -> Self:
        """Create instance from config object"""
        return cls()