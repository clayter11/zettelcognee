"""MCP server for ZettelCognee — gives Claude access to the corporate knowledge base.

Tools:
    - search_knowledge: Search the knowledge graph (GraphRAG)
    - search_simple: Simple RAG search for factual questions
    - list_documents: List all documents in the knowledge base
    - get_document: Get document details by ID
    - upload_text: Add text content to the knowledge base

Resources:
    - zettelcognee://documents — list of all documents
    - zettelcognee://document/{id} — specific document details
"""

import json
import os
import sys

import httpx
from mcp.server.fastmcp import FastMCP

API_URL = os.environ.get("ZETTELCOGNEE_API_URL", "http://localhost:8000")
API_EMAIL = os.environ.get("ZETTELCOGNEE_EMAIL", "dev@zettelcognee.local")
API_PASSWORD = os.environ.get("ZETTELCOGNEE_PASSWORD", "dev123")

mcp = FastMCP(
    "ZettelCognee",
    description="Corporate knowledge base — search documents, meetings, notes via GraphRAG",
)

_token: str | None = None


def _get_token() -> str:
    """Get or create auth token. Auto-registers dev user if needed."""
    global _token
    if _token:
        return _token

    client = httpx.Client(base_url=API_URL, timeout=30)

    # Try login
    resp = client.post("/api/auth/login", data={
        "username": API_EMAIL,
        "password": API_PASSWORD,
    })
    if resp.status_code == 200:
        _token = resp.json()["access_token"]
        return _token

    # Register
    client.post("/api/auth/register", json={
        "email": API_EMAIL,
        "password": API_PASSWORD,
        "full_name": "MCP User",
    })
    resp = client.post("/api/auth/login", data={
        "username": API_EMAIL,
        "password": API_PASSWORD,
    })
    _token = resp.json()["access_token"]
    return _token


def _api(method: str, path: str, **kwargs) -> dict:
    """Make authenticated API call."""
    token = _get_token()
    client = httpx.Client(base_url=API_URL, timeout=60)
    resp = client.request(
        method, path,
        headers={"Authorization": f"Bearer {token}"},
        **kwargs,
    )
    resp.raise_for_status()
    if resp.status_code == 204:
        return {"status": "ok"}
    return resp.json()


# --- Tools ---


@mcp.tool()
def search_knowledge(query: str) -> str:
    """Search the corporate knowledge base using GraphRAG.

    Uses knowledge graph traversal + vector similarity for complex questions
    about relationships between documents, people, projects, contracts.

    Examples:
        - "Какие решения были приняты на встрече по проекту Альфа?"
        - "Кто работает с клиентом Бета и какие договоры с ними?"
        - "Связь между проектом X и расчётом Y"
    """
    data = _api("POST", "/api/search/", json={"query": query, "mode": "graph"})
    results = data.get("results", [])
    if not results:
        return "Ничего не найдено. Попробуйте переформулировать запрос."
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool()
def search_simple(query: str) -> str:
    """Simple RAG search — best for straightforward factual questions.

    Use this for direct questions where graph traversal isn't needed.

    Examples:
        - "Какая цена в предложении для клиента Альфа?"
        - "Дата начала договора №123"
    """
    data = _api("POST", "/api/search/", json={"query": query, "mode": "rag"})
    results = data.get("results", [])
    if not results:
        return "Ничего не найдено."
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool()
def list_documents(skip: int = 0, limit: int = 20) -> str:
    """List documents in the knowledge base.

    Returns document names, types, statuses.
    """
    data = _api("GET", f"/api/documents/?skip={skip}&limit={limit}")
    items = data.get("items", [])
    total = data.get("total", 0)

    lines = [f"Всего документов: {total}\n"]
    for doc in items:
        status = {"ready": "✅", "processing": "⏳", "error": "❌"}.get(doc["status"], "📄")
        lines.append(f"{status} {doc['filename']} (тип: {doc['doc_type']}, id: {doc['id']})")

    return "\n".join(lines)


@mcp.tool()
def get_document(document_id: str) -> str:
    """Get details of a specific document by ID."""
    data = _api("GET", f"/api/documents/{document_id}")
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
def upload_text(title: str, content: str) -> str:
    """Upload text content to the knowledge base for indexing.

    The text will be processed by Cognee and added to the knowledge graph.
    Use this to add meeting notes, summaries, or any text knowledge.

    Args:
        title: Document title (e.g. "Протокол встречи 2026-03-04")
        content: Full text content in any format
    """
    # Create a temporary text file and upload
    files = {"file": (f"{title}.md", content.encode(), "text/markdown")}
    data = _api("POST", "/api/documents/upload", files=files)

    status = data.get("status", "unknown")
    if status == "ready":
        return f"✅ Документ '{title}' добавлен в базу знаний и проиндексирован."
    elif status == "error":
        return f"❌ Ошибка: {data.get('error_message', 'unknown')}"
    return f"⏳ Документ '{title}' загружен, статус: {status}"


# --- Resources ---


@mcp.resource("zettelcognee://documents")
def resource_documents() -> str:
    """List all documents in the knowledge base."""
    return list_documents()


@mcp.resource("zettelcognee://document/{doc_id}")
def resource_document(doc_id: str) -> str:
    """Get specific document details."""
    return get_document(doc_id)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
