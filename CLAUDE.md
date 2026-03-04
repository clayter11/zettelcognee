# ZettelCognee

Corporate knowledge base powered by Cognee (GraphRAG), Gemini & Claude.

## Quick start

```bash
cp .env.example .env   # add your Gemini API key
make up                 # starts backend + db + redis + UI
make test               # run 15 tests (no docker needed)
```

- API: http://localhost:8000 (Swagger: /docs)
- UI: http://localhost:8501 (Streamlit chat)
- MCP: see mcp-server/README.md

## Architecture

See ARCHITECTURE.md for full details. Key decisions:
- **Cognee** — GraphRAG engine (not classic RAG), ~93% accuracy
- **Gemini** — embeddings (free), entity extraction, transcription
- **Claude** — high-quality answer generation
- **No OpenAI** — project explicitly avoids OpenAI

## Project structure

```
backend/          FastAPI + SQLAlchemy + Cognee
  app/api/        REST endpoints (auth, documents, search)
  app/models/     DB models (User, Document, Connector, Note)
  app/services/   Business logic (knowledge.py, storage.py)
  tests/          pytest (SQLite in-memory, Cognee mocked)
ui/               Streamlit chat interface
mcp-server/       MCP server for Claude Desktop / Claude Code
```

## Development

- Tests: `cd backend && pytest tests/ -v`
- Tests use SQLite (no Postgres needed), Cognee is mocked
- Models use `JSON` (not `JSONB`) for SQLite compatibility
- Cognee is lazy-imported to avoid heavy import chain in tests
- Auto-commit hook in `.claude/hooks/auto-commit.sh`

## Key files

- `backend/app/services/knowledge.py` — Cognee wrapper
- `backend/app/api/documents.py` — document upload + CRUD
- `backend/app/api/search.py` — GraphRAG search
- `ui/app.py` — Streamlit UI
- `mcp-server/server/main.py` — MCP server
