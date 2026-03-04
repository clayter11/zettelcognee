"""Cognee knowledge engine wrapper — add, cognify, search."""

import os
from enum import Enum

from app.config import settings


class SearchMode(str, Enum):
    GRAPH_COMPLETION = "GRAPH_COMPLETION"
    RAG_COMPLETION = "RAG_COMPLETION"
    GRAPH_COMPLETION_COT = "GRAPH_COMPLETION_COT"
    NATURAL_LANGUAGE = "NATURAL_LANGUAGE"


def _get_cognee():
    """Lazy import cognee to avoid heavy import chain at module level."""
    import cognee
    return cognee


def _get_search_type(mode: SearchMode):
    from cognee.api.v1.search import SearchType
    return getattr(SearchType, mode.value)


async def configure_cognee():
    """Configure Cognee with Gemini providers (no OpenAI)."""
    os.environ["LLM_PROVIDER"] = settings.llm_provider
    os.environ["LLM_MODEL"] = settings.llm_model
    os.environ["LLM_API_KEY"] = settings.llm_api_key
    os.environ["EMBEDDING_PROVIDER"] = settings.embedding_provider
    os.environ["EMBEDDING_MODEL"] = settings.embedding_model
    os.environ["EMBEDDING_API_KEY"] = settings.embedding_api_key


async def add_document(file_path: str, dataset_name: str = "default") -> None:
    """Add a document to Cognee for processing."""
    cognee = _get_cognee()
    await cognee.add(file_path, dataset_name=dataset_name)


async def cognify(dataset_name: str = "default") -> None:
    """Run Cognee's ECL pipeline: Extract → Cognify → Load."""
    cognee = _get_cognee()
    await cognee.cognify(dataset_name=dataset_name)


async def add_and_cognify(file_path: str, dataset_name: str = "default") -> None:
    """Add a document and immediately build the knowledge graph."""
    await add_document(file_path, dataset_name)
    await cognify(dataset_name)


async def search_graph(
    query: str,
    mode: SearchMode = SearchMode.GRAPH_COMPLETION,
) -> list[dict]:
    """Search the knowledge graph."""
    cognee = _get_cognee()
    search_type = _get_search_type(mode)
    results = await cognee.search(search_type, query=query)
    return results


async def search_rag(query: str) -> list[dict]:
    """Simple RAG search — retrieve and generate."""
    return await search_graph(query, SearchMode.RAG_COMPLETION)


async def search_insights(query: str) -> list[dict]:
    """Graph-based search with chain-of-thought reasoning."""
    return await search_graph(query, SearchMode.GRAPH_COMPLETION)
