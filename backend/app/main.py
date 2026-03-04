from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import auth, documents, search
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: configure Cognee
    from app.services.knowledge import configure_cognee

    await configure_cognee()
    yield
    # Shutdown


app = FastAPI(
    title=settings.app_name,
    description="Corporate knowledge base powered by Cognee (GraphRAG)",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(search.router, prefix="/api/search", tags=["search"])


@app.get("/health")
async def health():
    return {"status": "ok"}
