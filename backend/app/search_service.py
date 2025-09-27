import json
import logging
import os
from pathlib import Path
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
    """Hybrid search over Azure AI Search with offline fallback."""

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
            LOGGER.warning("Azure Search configuration missing; using fallback corpus")

        self._fallback_corpus = self._load_fallback_corpus()

    async def search(self, query: str, intent: Optional[str] = None) -> List[Citation]:
        """Retrieve grounded NJIT resources for the given query."""

        results: List[Citation] = []
        if self._client:
            try:
                async with self._client as client:
                    search_kwargs = {
                        "search_text": query,
                        "top": 3,
                        "select": [
                            "id",
                            "title",
                            "url",
                            "source",
                            "description",
                            "published",
                            "tags",
                        ],
                    }
                    if intent:
                        filter_clause = self._intent_filter(intent)
                        if filter_clause:
                            search_kwargs["filter"] = filter_clause

                    azure_results = await client.search(**search_kwargs)
                    async for item in azure_results:
                        results.append(
                            Citation(
                                id=str(item.get("id") or item.get("@search.action", "azure")),
                                title=item.get("title", "NJIT Resource"),
                                url=item.get("url", ""),
                                source=item.get("source", "Azure AI Search"),
                                snippet=item.get("description", ""),
                                published=item.get("published"),
                            )
                        )
            except Exception as exc:  # pragma: no cover - network/runtime guard
                LOGGER.warning("Azure Search request failed: %s", exc)

        if results:
            return results[:3]

        LOGGER.info("Falling back to local corpus for query: %s", query)
        return self._search_fallback(query, intent)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _intent_filter(self, intent: str) -> str:
        mapping = {
            "academics": "category eq 'academics'",
            "career": "category eq 'career'",
            "events": "category eq 'events'",
            "wellbeing": "category eq 'wellbeing'",
        }
        return mapping.get(intent, "")

    def _load_fallback_corpus(self) -> List[dict]:
        data_path = (
            Path(__file__).resolve().parents[1]
            / "data-ingestion"
            / "njit_resources.json"
        )
        if not data_path.exists():
            return []
        try:
            with data_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception as exc:
            LOGGER.warning("Could not load fallback corpus: %s", exc)
            return []

    def _search_fallback(self, query: str, intent: Optional[str]) -> List[Citation]:
        if not self._fallback_corpus:
            return []

        lowered = query.lower()
        keywords = lowered.split()
        matches: List[Citation] = []
        for item in self._fallback_corpus:
            text_blob = " ".join(
                [
                    str(item.get("title", "")),
                    str(item.get("description", "")),
                    " ".join(item.get("tags", [])),
                ]
            ).lower()
            if keywords and all(token in text_blob for token in keywords[:3]):
                matches.append(self._citation_from_item(item, source="Local Corpus"))
            elif intent and intent in item.get("tags", []):
                matches.append(self._citation_from_item(item, source="Local Corpus"))
            if len(matches) >= 3:
                break
        return matches

    @staticmethod
    def _citation_from_item(item: dict, source: str) -> Citation:
        return Citation(
            id=str(item.get("id", "fallback")),
            title=item.get("title", "NJIT Resource"),
            url=item.get("url", ""),
            source=source,
            snippet=item.get("description", ""),
            published=item.get("published"),
        )

