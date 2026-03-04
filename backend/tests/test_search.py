"""Search API tests."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@patch("app.api.search.knowledge.search_graph", new_callable=AsyncMock, return_value=[{"answer": "test result"}])
async def test_search_graph(mock_search, client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/search/",
        headers=auth_headers,
        json={"query": "what is the project about?", "mode": "graph"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "what is the project about?"
    assert data["mode"] == "graph"
    assert len(data["results"]) == 1
    mock_search.assert_called_once()


@patch("app.api.search.knowledge.search_rag", new_callable=AsyncMock, return_value=[])
async def test_search_rag(mock_search, client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/search/",
        headers=auth_headers,
        json={"query": "test", "mode": "rag"},
    )
    assert resp.status_code == 200
    assert resp.json()["mode"] == "rag"
    mock_search.assert_called_once()


async def test_search_unauthorized(client: AsyncClient):
    resp = await client.post("/api/search/", json={"query": "test"})
    assert resp.status_code == 401
