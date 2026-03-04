"""Document API tests — upload, list, get, delete."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@patch("app.api.documents.knowledge.add_and_cognify", new_callable=AsyncMock)
async def test_upload_document(mock_cognify, client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/documents/upload",
        headers=auth_headers,
        files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["filename"] == "test.pdf"
    assert data["status"] == "ready"
    mock_cognify.assert_called_once()


async def test_upload_unauthorized(client: AsyncClient):
    resp = await client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", b"fake", "application/pdf")},
    )
    assert resp.status_code == 401


@patch("app.api.documents.knowledge.add_and_cognify", new_callable=AsyncMock)
async def test_list_documents(mock_cognify, client: AsyncClient, auth_headers: dict):
    # Upload two docs
    for name in ["a.pdf", "b.pdf"]:
        await client.post(
            "/api/documents/upload",
            headers=auth_headers,
            files={"file": (name, b"content", "application/pdf")},
        )

    resp = await client.get("/api/documents/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@patch("app.api.documents.knowledge.add_and_cognify", new_callable=AsyncMock)
async def test_get_document(mock_cognify, client: AsyncClient, auth_headers: dict):
    upload_resp = await client.post(
        "/api/documents/upload",
        headers=auth_headers,
        files={"file": ("doc.pdf", b"content", "application/pdf")},
    )
    doc_id = upload_resp.json()["id"]

    resp = await client.get(f"/api/documents/{doc_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == doc_id


@patch("app.api.documents.knowledge.add_and_cognify", new_callable=AsyncMock)
async def test_delete_document(mock_cognify, client: AsyncClient, auth_headers: dict):
    upload_resp = await client.post(
        "/api/documents/upload",
        headers=auth_headers,
        files={"file": ("del.pdf", b"content", "application/pdf")},
    )
    doc_id = upload_resp.json()["id"]

    resp = await client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = await client.get(f"/api/documents/{doc_id}", headers=auth_headers)
    assert resp.status_code == 404
