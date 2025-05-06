"""
Service for weaviate operations
"""

import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from openai import AsyncAzureOpenAI
import weaviate
from fastapi import HTTPException, status
from weaviate.classes.config import Configure
from weaviate.classes.init import Auth

from autogenstudio.core.config import get_settings


class WeaviateService:
    """Service for weaviate operations"""

    def __init__(self):
        """
        Initialize the service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.settings = get_settings()

    async def __aenter__(self):
        if not self.settings.WEAVIATE_URL:
            raise ValueError("WEAVIATE_URL is not configured")
        if not self.settings.WEAVIATE_API_KEY:
            raise ValueError("WEAVIATE_API_KEY is missing")
        weaviate_api_key = self.settings.WEAVIATE_API_KEY
        self.client = weaviate.connect_to_weaviate_cloud(
            cluster_url=self.settings.WEAVIATE_URL,
            auth_credentials=Auth.api_key(weaviate_api_key),
            headers={
                "X-Azure-Api-Key": self.settings.AZURE_API_KEY,
                "X-Azure-Deployment-Id": self.settings.AZURE_DEPLOYMENT,
                "X-Azure-Resource-Name": self.settings.AZURE_MODEL,
            },
        )
        if not self.client.is_ready():
            raise Exception("Weaviate client connection failed")

        self.embeddings = AsyncAzureOpenAI(
            azure_deployment=self.settings.AZURE_EMBEDDING_DEPLOYMENT,
            azure_endpoint=self.settings.AZURE_EMBEDDING_ENDPOINT,
            api_key=self.settings.AZURE_EMBEDDING_API_KEY,
            api_version=self.settings.AZURE_EMBEDDING_API_VERSION,
        )

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """
        Close the Weaviate client connection.
        """
        self.client.close()
        await self.embeddings.close()

    def __get_collection(self, collection_name: str):
        """
        Get a collection from Weaviate.
        If the collection does not exist, it will be created.
        """
        if self.client.collections.exists(collection_name):
            collection = self.client.collections.get(collection_name)
        else:
            collection = self.client.collections.create(
                collection_name,
                generative_config=Configure.Generative.azure_openai(
                    resource_name=self.settings.AZURE_MODEL,
                    deployment_id=self.settings.AZURE_DEPLOYMENT,
                    base_url=self.settings.AZURE_ENDPOINT,
                ),
            )
        return collection

    async def __generate_embedding(self, text):
        start_time = time.time()

        embedding = await self.embeddings.embeddings.create(
            model="text-embedding-3-small", input=[text]  # or your deployed model name
        )
        end_time = time.time()
        print(f"Embedding Generation Time: {end_time - start_time:.2f} seconds")

        return embedding.data[0].embedding

    def add(
        self,
        collection_name: str,
        properties: dict[str, Any],
        references: Optional[dict[str, Any]] = None,
    ):
        collection = self.__get_collection(collection_name)
        collection.data.insert(properties, references)

    async def query_weaviate(self, query: str, collection_name: str):
        """
        Query Weaviate for a specific collection.

        Args:
            query: The query to be executed
        Returns:
            The result of the query
        """
        try:
            query_embedding = await self.__generate_embedding(query)
            collection = self.__get_collection(collection_name)
            response = collection.query.hybrid(
                query=query, alpha=0.5, vector=query_embedding
            )

            result = [o.properties.get("content") for o in response.objects]
            return result
        except weaviate.exceptions.UnexpectedStatusCodeException as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error querying Weaviate: {e}",
            ) from e
