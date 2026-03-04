"""Cognee knowledge engine wrapper — add, cognify, search."""

import os
from pathlib import Path
from uuid import UUID

import cognee
from cognee.api.v1.search import SearchType

from app.config import settings


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
    await cognee.add(file_path, dataset_name=dataset_name)


async def cognify(dataset_name: str = "default") -> None:
    """Run Cognee's ECL pipeline: Extract → Cognify → Load."""
    await cognee.cognify(dataset_name=dataset_name)


async def add_and_cognify(file_path: str, dataset_name: str = "default") -> None:
    """Add a document and immediately build the knowledge graph."""
    await add_document(file_path, dataset_name)
    await cognify(dataset_name)


async def search_graph(
    query: str,
    search_type: SearchType = SearchType.GRAPH_COMPLETION,
) -> list[dict]:
    """Search the knowledge graph.

    Search types:
        - GRAPH_COMPLETION: complex questions with relationships (default)
        - RAG_COMPLETION: simple factual questions
        - GRAPH_COMPLETION_COT: multi-hop reasoning (chain-of-thought)
        - NATURAL_LANGUAGE: structured queries via Cypher
    """
    results = await cognee.search(search_type, query=query)
    return results


async def search_rag(query: str) -> list[dict]:
    """Simple RAG search — retrieve and generate."""
    return await search_graph(query, SearchType.RAG_COMPLETION)


async def search_insights(query: str) -> list[dict]:
    """Graph-based search with chain-of-thought reasoning."""
    return await search_graph(query, SearchType.GRAPH_COMPLETION)
