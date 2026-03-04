"""Search endpoints — GraphRAG and RAG search via Cognee."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.models.user import User
from app.services import knowledge

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    mode: str = "graph"  # "graph", "rag", "insights"


class SearchResult(BaseModel):
    query: str
    mode: str
    results: list


@router.post("/", response_model=SearchResult)
async def search(
    request: SearchRequest,
    user: User = Depends(get_current_user),
):
    if request.mode == "rag":
        results = await knowledge.search_rag(request.query)
    elif request.mode == "insights":
        results = await knowledge.search_insights(request.query)
    else:
        results = await knowledge.search_graph(request.query)

    return SearchResult(
        query=request.query,
        mode=request.mode,
        results=results,
    )
