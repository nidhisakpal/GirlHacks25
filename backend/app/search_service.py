import logging
import os
from typing import List, Optional

try:
    from azure.core.credentials import AzureKeyCredential
    from azure.search.documents.aio import SearchClient
except ImportError:  # pragma: no cover - optional dependency
    AzureKeyCredential = None  # type: ignore
    SearchClient = None  # type: ignore

from app.models import Citation

LOGGER = logging.getLogger(__name__)


class SearchService:
    """Azure AI Search helper that returns citations or an empty list."""

    def __init__(self) -> None:
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.key = os.getenv("AZURE_SEARCH_API_KEY")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")

        self._client: Optional[SearchClient] = None
        if (
            self.endpoint
            and self.key
            and self.index_name
            and AzureKeyCredential
            and SearchClient
        ):
            self._client = SearchClient(
                endpoint=self.endpoint,
                index_name=self.index_name,
                credential=AzureKeyCredential(self.key),
            )
        else:
            LOGGER.warning(
                "Azure Search disabled (endpoint=%s, key=%s, index=%s, libs=%s)",
                bool(self.endpoint),
                bool(self.key),
                bool(self.index_name),
                bool(AzureKeyCredential and SearchClient),
            )

    async def search(self, query: str, intent: Optional[str] = None) -> List[Citation]:
        results: List[Citation] = []
        if self._client:
            try:
                search_kwargs = {
                    "search_text": query,
                    "top": 3,
                    "select": [
                        "id",
                        "title",
                        "url",
                        "source",
                        "description",
                        "scraped_at",
                        "category",
                        "tags",
                    ],
                }

                LOGGER.debug(
                    "Azure Search request",
                    extra={"query": query, "intent": intent, "kwargs": search_kwargs},
                )
                azure_results = await self._client.search(**search_kwargs)
                async for item in azure_results:
                    LOGGER.debug(
                        "Azure Search hit",
                        extra={
                            "id": item.get("id"),
                            "title": item.get("title"),
                            "score": item.get("@search.score"),
                        },
                    )
                    results.append(
                        Citation(
                            id=str(item.get("id") or item.get("@search.action", "azure")),
                            title=item.get("title", "NJIT Resource"),
                            url=item.get("url", ""),
                            source=item.get("source", "Azure AI Search"),
                            snippet=item.get("description", ""),
                            retrieved=item.get("retrieved") or item.get("scraped_at"),
                        )
                    )
            except Exception as exc:
                LOGGER.exception("Azure Search request failed", exc_info=exc)

        if results:
            return results[:3]

        LOGGER.info("Azure Search returned no results for query: %s", query)
        return []
