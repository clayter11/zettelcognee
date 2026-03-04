# Corporate Knowledge Base — Architecture

## Overview

Corporate knowledge base for a small team (2-10 people) that stores documents, chat messages, Teams meetings, and provides search + AI-powered generation (GraphRAG) with a Zettelkasten-style knowledge graph.

**Deployment**: Cloud (GCP preferred, AWS as alternative)
**Data privacy**: External APIs allowed (Google Gemini, Anthropic Claude)
**Scale**: 1000+ documents, 100+ hours of audio
**AI stack**: Google Gemini + Anthropic Claude (no OpenAI)
**Knowledge engine**: Cognee (graph-based RAG, "Senior Librarian" approach)

---

## Design Philosophy: The Senior Librarian

Instead of classic RAG (flat embedding + overlap chunking, ~60% accuracy), we use the **"Senior Librarian"** approach via [Cognee](https://github.com/topoteretes/cognee):

- **Young Employee** (Base LLM) — knows a lot but nothing about your documents
- **Screen Employee** (Classic RAG) — finds facts but doesn't understand structure
- **Senior Librarian** (Cognee/GraphRAG) — **is** the library, knows how everything connects, **~93% accuracy**

Cognee builds a knowledge graph from documents: extracts entities (people, companies, projects), identifies relationships (works_at, requires, funded_by), and uses graph traversal + vector similarity for retrieval.

---

## High-Level Architecture

```
┌─ Data Sources ────────────────────────────────────┐
│  SharePoint      Google Drive      Local Upload    │
│  (Graph API)     (Drive API)       (Web / Telegram)│
└──────┬──────────────┬──────────────────┬──────────┘
       │              │                  │
       ▼              ▼                  ▼
┌─────────────────────────────────────────────────────┐
│              Sync & Connectors Layer                 │
│  - OAuth2 token management                           │
│  - Delta sync (detect new/modified/deleted)           │
│  - Scheduled sync (cron / configurable interval)      │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              Cognee Knowledge Engine                 │
│                                                      │
│  cognee.add() → cognee.cognify() → cognee.search()  │
│                                                      │
│  ┌─────────┐  ┌───────────┐  ┌──────────┐          │
│  │  Kuzu   │  │ PostgreSQL│  │ pgvector │          │
│  │ (graph) │  │ (relational│  │ (vectors)│          │
│  │         │  │  + sync   │  │          │          │
│  │         │  │  state)   │  │          │          │
│  └─────────┘  └───────────┘  └──────────┘          │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────┐
        │       API Server (FastAPI)       │
        │  - search / GraphRAG             │
        │  - notes CRUD                    │
        │  - document management           │
        │  - connector management          │
        │  - user auth                     │
        └──────────┬──────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼                     ▼
┌──────────────┐    ┌──────────────────┐
│ Telegram Bot │    │ Web UI           │
│ (aiogram 3)  │    │ (Next.js/React)  │
│              │    │ + Zettelkasten   │
└──────────────┘    └──────────────────┘

        ┌─────────────────────────────────┐
        │     Background Workers           │
        │     (Celery + Redis)             │
        │                                  │
        │  Gemini Flash → transcription    │
        │  Connector sync → scheduled      │
        │  cognee.cognify() → graph build  │
        └─────────────────────────────────┘

        ┌─────────────────────────────────┐
        │     File Storage (S3 / GCS)      │
        │     Raw files, audio, exports    │
        └─────────────────────────────────┘
```

---

## AI Stack (No OpenAI)

### LLM Providers

| Role | Model | Provider | Cost |
|------|-------|----------|------|
| **Entity extraction** (Cognee cognify) | Gemini 2.0 Flash | Google | ~$15 per 1000 docs |
| **Answer generation** (GraphRAG) | Claude Sonnet | Anthropic | ~$18/month (50 queries/day) |
| **Answer generation** (budget) | Gemini 2.0 Flash | Google | ~$1/month (50 queries/day) |
| **Summaries** | Gemini 2.0 Flash | Google | ~$1 per 1000 docs |
| **Embeddings** | Gemini text-embedding-004 | Google | **Free** (1500 req/min) |
| **Transcription** | Gemini 2.0 Flash (audio) | Google | Token-based, cheaper than Whisper |

### Cognee Configuration

```env
# .env — Cognee config (no OpenAI)
LLM_PROVIDER=gemini
LLM_MODEL=gemini/gemini-2.0-flash
LLM_API_KEY=AIza...

# Embeddings — Gemini (free)
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=models/text-embedding-004
EMBEDDING_API_KEY=AIza...

# For high-quality generation — switch to Claude
# LLM_PROVIDER=anthropic
# LLM_MODEL=claude-sonnet-4-20250514
# LLM_API_KEY=sk-ant-...
```

### Cost Estimate (Monthly)

| Item | One-time | Monthly |
|------|----------|---------|
| Initial indexing (1000 docs, Gemini Flash) | **$15** | — |
| Incremental sync (~50 new docs/month) | — | **$1** |
| Embeddings (Gemini, free) | $0 | $0 |
| Queries: 50/day, Claude Sonnet | — | **$18** |
| Queries: 50/day, Gemini Flash (budget) | — | **$1** |
| Transcription: 10h audio/month, Gemini | — | **$2** |
| **Total (Claude for answers)** | **$15** | **~$21/month** |
| **Total (Gemini for everything)** | **$15** | **~$4/month** |

---

## Components

### 1. Source Connectors (SharePoint, Google Drive)

#### SharePoint Connector
- **API**: Microsoft Graph API (`/sites/{site-id}/drive/items`)
- **Auth**: OAuth2 with Azure AD app registration (client credentials or delegated)
- **Sync strategy**:
  - Initial: full crawl of selected document libraries
  - Incremental: delta API (`/drive/root/delta`) to detect changes since last sync
  - Handles: new files, modified files, deleted files, renamed files
- **Scheduling**: Celery Beat periodic task (configurable: 15min / 1h / daily)
- **State tracking**: `sync_state` table in PostgreSQL stores delta tokens, last sync time

```sql
CREATE TABLE connectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(20) NOT NULL,         -- 'sharepoint', 'google_drive'
    name VARCHAR(200),                 -- e.g. "Marketing SharePoint"
    config JSONB NOT NULL,             -- site_id, folder paths, etc.
    oauth_tokens JSONB,                -- encrypted access/refresh tokens
    delta_token TEXT,                  -- for incremental sync
    last_sync_at TIMESTAMP,
    sync_interval_minutes INT DEFAULT 60,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE synced_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connector_id UUID REFERENCES connectors(id),
    remote_id VARCHAR(500) NOT NULL,   -- file ID in SharePoint/GDrive
    remote_path TEXT,                  -- full path for display
    document_id UUID REFERENCES documents(id),
    remote_modified_at TIMESTAMP,
    etag VARCHAR(200),                 -- for change detection
    UNIQUE(connector_id, remote_id)
);
```

#### Google Drive Connector
- **API**: Google Drive API v3
- **Auth**: OAuth2 with Google Cloud project (service account or user consent)
- **Sync strategy**:
  - Initial: list all files in selected folders / shared drives
  - Incremental: Changes API (`changes.list` with `pageToken`) or push notifications (webhooks)
  - Google Docs → export as PDF, Google Sheets → export as XLSX before parsing
- **Scheduling**: same as SharePoint — Celery Beat
- **Shared drives**: support `supportsAllDrives=true` for Team Drives

#### Connector Flow
```
Connector (scheduled)
    │
    ├─ Fetch file list from remote (delta/changes API)
    ├─ Compare with synced_files table
    │
    ├─ New files → download → S3/GCS → cognee.add() → cognee.cognify()
    ├─ Modified files → re-download → re-cognify (Cognee handles updates)
    └─ Deleted files → mark as deleted, remove from graph
```

---

### 2. Document Classification & Pre-processing

Documents are classified on ingestion and routed through type-specific parsers before Cognee.

#### Classification Flow

```
Document arrives (upload / connector sync)
    │
    ▼
Classifier (Gemini Flash, ~$0.001/doc)
    │
    ├─ "proposal"    → ProposalParser    → CommercialProposal DataPoint → Cognee
    ├─ "contract"    → ContractParser    → Contract DataPoint           → Cognee
    ├─ "calculation" → TableParser       → Calculation DataPoint        → Cognee
    ├─ "drawing"     → DrawingParser     → Drawing DataPoint            → Cognee
    ├─ "meeting"     → TranscriptParser  → MeetingNote DataPoint        → Cognee
    ├─ "spreadsheet" → TableParser       → markdown tables              → Cognee
    └─ "general"     → default           → directly to Cognee
```

#### Custom DataPoints per Document Type

```python
class CommercialProposal(DataPoint):
    """Коммерческое предложение"""
    client: str
    project_name: str
    items: list[str]           # позиции спецификации
    total_price: float
    currency: str
    validity_date: str         # срок действия
    payment_terms: str
    delivery_terms: str
    metadata: dict = {"index_fields": ["client", "project_name", "items"]}

class Contract(DataPoint):
    """Договор"""
    parties: list[str]         # стороны договора
    contract_number: str
    subject: str               # предмет договора
    value: float
    currency: str
    start_date: str
    end_date: str
    payment_schedule: str
    penalties: str
    metadata: dict = {"index_fields": ["parties", "subject", "contract_number"]}

class Calculation(DataPoint):
    """Расчёт / смета / калькуляция"""
    project: str
    calculation_type: str      # "смета", "ТЭО", "калькуляция"
    total: float
    currency: str
    sections: list[str]        # разделы расчёта
    assumptions: list[str]     # допущения
    metadata: dict = {"index_fields": ["project", "calculation_type", "sections"]}

class Drawing(DataPoint):
    """Чертёж / схема"""
    title: str
    drawing_number: str
    scale: str
    description: str           # текстовое описание от Gemini Vision
    related_project: str
    revision: str
    author: str
    metadata: dict = {"index_fields": ["title", "drawing_number", "description"]}

class MeetingNote(DataPoint):
    """Протокол / запись встречи"""
    title: str
    date: str
    participants: list[str]
    decisions: list[str]
    action_items: list[str]
    project: str
    metadata: dict = {"index_fields": ["title", "decisions", "project", "participants"]}
```

#### Type-Specific Parsers

**Tables & Calculations** (Excel, tables in PDF):
- Extract tables as complete markdown (never split a table mid-row)
- Preserve headers, units, formulas context
- Store both as structured DataPoint fields AND as text for Cognee

**Drawings** (PDF with images, scans):
```
PDF with drawing
    ├─ Extract images (PyMuPDF / pdf2image)
    ├─ Gemini Vision: describe the drawing
    │   → "План этажа, масштаб 1:100, 3 помещения,
    │      размеры 12x8м, 6x4м, 10x5м, материал — ж/б"
    ├─ OCR title block (Gemini Vision)
    │   → drawing number, scale, revision, author
    ├─ Assemble Drawing DataPoint
    └─ cognee.add() → cognee.cognify()
```

**Commercial Proposals & Contracts**:
- Parse sections by headers (unstructured)
- Extract key fields into DataPoint via LLM
- Keep full text for context in Cognee graph

**Spreadsheets**:
- Each sheet → separate document
- Tables → markdown format (LLMs understand markdown tables well)
- Named ranges / key cells → structured metadata

#### Why This Matters

Without classification:
> "Какая цена для клиента Альфа?" → finds chunk "...2,500,000 руб..." with no context

With DataPoints:
> "Какая цена для клиента Альфа?" → finds `CommercialProposal(client="Альфа", total_price=2500000, project="Реконструкция", validity="31.03.2026")` → precise, structured answer

---

### 3. Cognee Knowledge Engine (replaces classic RAG pipeline)

#### How Cognee Processes Documents

```
cognee.add(file)
    │
    ▼
┌─ cognee.cognify() — 6-step pipeline ─────────────┐
│  1. Classify document type                         │
│  2. Check permissions                              │
│  3. Extract chunks (semantic splitting)            │
│  4. Extract entities & relationships (LLM)         │
│     → People, companies, projects, dates           │
│     → "works_at", "requires", "funded_by"          │
│  5. Generate summaries                             │
│  6. Embed & commit to graph + vector store         │
└────────────────────────────────────────────────────┘
    │
    ▼
Three storage layers (managed by Cognee):
  ├─ Kuzu (graph DB) — entities, relationships, traversal
  ├─ pgvector (PostgreSQL extension) — embeddings, similarity
  └─ PostgreSQL (relational) — documents, chunks, provenance
```

#### Cognee Search Modes (14 total, key ones for us)

| Mode | Use Case | How It Works |
|------|----------|-------------|
| **GRAPH_COMPLETION** (default) | Complex questions with relationships | Vector hints → graph triplets → traverse → LLM |
| **RAG_COMPLETION** | Simple factual questions | Classic retrieve-then-generate |
| **GRAPH_COMPLETION_COT** | Multi-hop reasoning | Chain-of-thought over graph |
| **TEMPORAL** | "What was discussed last week?" | Time-aware graph search |
| **NATURAL_LANGUAGE** | Structured queries | Query → Cypher → graph |
| **FEELING_LUCKY** | Universal | LLM auto-selects best mode |

#### Custom DataPoints

```python
# Define domain-specific entities for better graph quality
class MeetingNote(DataPoint):
    title: str
    participants: list[str]
    decisions: list[str]
    action_items: list[str]
    project: str
    metadata: dict = {"index_fields": ["title", "decisions", "project"]}

class Contract(DataPoint):
    parties: list[str]
    value: float
    start_date: str
    end_date: str
    metadata: dict = {"index_fields": ["parties"]}
```

#### What Cognee Replaces

| Previously planned | Now handled by Cognee |
|-------------------|----------------------|
| Custom chunking engine | Cognee's semantic chunking |
| Embedding pipeline | Cognee embeds via configured provider |
| Separate vector DB (Qdrant) | pgvector (Cognee default with PostgreSQL) |
| Entity extraction (manual NER) | LLM-based entity + relationship extraction |
| RAG retrieval + reranking | Graph traversal + vector similarity |
| Note auto-linking (Zettelkasten) | Automatic graph connections |

---

### 4. Audio Transcription

#### Gemini Flash for Audio (replaces Whisper)

- **API**: Gemini 2.0 Flash with audio input
- **Russian support**: 70+ languages, auto-detection
- **Built-in diarization**: identifies speakers without extra service
- **Token-based pricing**: cheaper than Whisper for most use cases
- **Flow**:
  ```
  Audio file → upload to Gemini → transcription + speaker labels
      → LLM summary (participants, topics, decisions, action items)
      → cognee.add(transcript) → cognee.cognify()
  ```
- **Fallback**: Google Cloud Speech-to-Text for very long files (>4h)
- Files > Gemini limit: split with `pydub`, process segments sequentially

---

### 5. Zettelkasten Module

Cognee's knowledge graph provides the **automatic** part of Zettelkasten (entity extraction, relationship mapping, similarity-based linking). On top of this, we add manual note management.

#### Additional Data Model (beyond Cognee's graph)

```sql
-- Manual notes created by users
CREATE TABLE user_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,              -- markdown
    source_type VARCHAR(20),           -- 'document', 'audio', 'chat', 'manual'
    source_id UUID,                    -- reference to source document
    tags TEXT[],
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Manual links between notes (automatic links are in Cognee's graph)
CREATE TABLE manual_note_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_note_id UUID REFERENCES user_notes(id) ON DELETE CASCADE,
    to_note_id UUID REFERENCES user_notes(id) ON DELETE CASCADE,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(from_note_id, to_note_id)
);
```

#### How Zettelkasten Uses Cognee

1. **Auto-generated notes**: When a document is cognified, Cognee extracts entities and relationships → these become nodes and edges in the graph
2. **Manual notes**: Users create markdown notes, which are also fed to `cognee.add()` + `cognee.cognify()` → integrated into the same graph
3. **Graph visualization**: Read Cognee's graph (Kuzu) + manual links → render with react-force-graph
4. **Backlinks**: Query Cognee graph for all nodes pointing to a given entity
5. **Related notes**: `cognee.search()` with GRAPH_COMPLETION finds semantically + structurally related content

#### Web UI Features
- **Graph view**: interactive force-directed graph (react-force-graph)
- **Note list**: filterable by tags, type, date, search
- **Editor**: markdown editor with [[wiki-link]] syntax
- **Backlinks**: Obsidian-style — see what references the current note
- **Graph search**: "show all notes connected to project X within 2 hops"

---

### 6. Interfaces

#### Telegram Bot (aiogram 3)
- `/ask <question>` — GraphRAG query via Cognee, returns answer with citations
- `/search <query>` — semantic search, returns top documents
- `/upload` — upload a document for processing
- `/summary <doc_id>` — get document summary
- `/recent` — recent documents and notes
- Inline mode for quick searches

#### Web UI (Next.js)
- Dashboard: recent activity, stats, sync status
- Document browser: upload, view, tag documents
- Zettelkasten: graph view + note editor + backlinks
- Search: GraphRAG + semantic search with filters
- Connectors: connect SharePoint/GDrive, configure sync, view status
- Settings: API keys, user management

---

### 7. Backup Strategy

| Storage | Strategy | Frequency | Target |
|---------|----------|-----------|--------|
| **S3/GCS** (raw files) | Already durable (11 nines). Cross-region replication optional | N/A | Built-in |
| **PostgreSQL** (metadata, sync state, user notes) | `pg_dump` → compress → upload to GCS | Daily + before migrations | GCS bucket |
| **Kuzu** (Cognee graph) | File-based DB → snapshot → upload to GCS | Daily | GCS bucket |
| **pgvector** (embeddings) | Part of PostgreSQL backup | Daily | GCS bucket |

**Simplified**: Use **Google Cloud SQL** (managed PostgreSQL) — automatic daily backups, point-in-time recovery, no manual pg_dump needed.

**Recovery priority**: PostgreSQL is critical (metadata, users, sync state). Kuzu graph and pgvector can be **rebuilt** from source documents via `cognee.cognify()` — slower but possible.

---

### 8. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Knowledge Engine | **Cognee** | GraphRAG, entity extraction, knowledge graph |
| API Server | **FastAPI** (Python 3.12+) | REST API, WebSocket |
| Telegram Bot | **aiogram 3** | Telegram interface |
| Web UI | **Next.js 14** + **React** | Zettelkasten UI |
| Graph Visualization | **react-force-graph** | Knowledge graph display |
| Graph DB | **Kuzu** (via Cognee) | Entity-relationship graph |
| Vector Store | **pgvector** (via Cognee) | Embedding similarity search |
| Relational DB | **PostgreSQL 16** (Cloud SQL) | Metadata, users, sync state, notes |
| File Storage | **Google Cloud Storage** | Raw files, audio, backups |
| SharePoint | **Microsoft Graph API** + `msgraph-sdk` | SharePoint connector |
| Google Drive | **Google Drive API v3** + `google-api-python-client` | GDrive connector |
| Transcription | **Gemini 2.0 Flash** (audio input) | Audio → text + diarization |
| Embeddings | **Gemini text-embedding-004** | Text → vectors (free) |
| LLM (entity extraction) | **Gemini 2.0 Flash** | Cognee cognify pipeline |
| LLM (generation) | **Claude Sonnet** / **Gemini Flash** via LiteLLM | Answer generation |
| Task Queue | **Celery** + **Redis** | Background processing, scheduled sync |
| Auth | **JWT** + **OAuth2** | User auth + connector OAuth flows |
| Deployment | **Docker Compose** → **Google Cloud Run** | Production hosting |

---

### 9. Development Phases

#### Phase 1 — Core + Cognee
- FastAPI project setup
- PostgreSQL schema (documents, users, connectors)
- GCS integration for file upload
- Cognee integration: `add()`, `cognify()`, `search()`
- Configure Cognee with Gemini (LLM + embeddings)
- Basic REST API for document CRUD
- Simple auth (invite link / JWT)

#### Phase 2 — Search + Telegram + Connectors
- GraphRAG search API (wrapping Cognee search modes)
- Telegram bot with `/ask` and `/search`
- **SharePoint connector** (OAuth2, delta sync)
- **Google Drive connector** (OAuth2, changes API)
- Connector management UI (connect, configure, view sync status)
- Claude Sonnet integration for high-quality answers

#### Phase 3 — Audio
- Gemini Flash audio transcription
- Audio file upload and processing
- Transcript → Cognee cognify → searchable
- Meeting summary generation (participants, decisions, action items)

#### Phase 4 — Zettelkasten
- Manual notes CRUD API
- Notes → Cognee cognify (integrate into graph)
- Next.js Web UI: graph view, note editor, backlinks
- Tag management
- Graph search ("show connected notes within N hops")

#### Phase 5 — Teams Integration
- Microsoft Graph API setup (reuse SharePoint auth)
- Chat message ingestion
- Channel/conversation indexing
- Scheduled sync

---

### 10. Project Structure

```
corporate-kb/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings (Gemini/Claude keys, etc.)
│   │   ├── models/              # SQLAlchemy models
│   │   ├── api/                 # API routes
│   │   │   ├── documents.py
│   │   │   ├── search.py        # Wraps Cognee search modes
│   │   │   ├── notes.py         # Zettelkasten notes CRUD
│   │   │   ├── connectors.py    # SharePoint/GDrive management
│   │   │   └── auth.py
│   │   ├── connectors/          # Source connectors
│   │   │   ├── base.py          # Abstract connector interface
│   │   │   ├── sharepoint.py    # SharePoint via MS Graph API
│   │   │   ├── google_drive.py  # Google Drive API v3
│   │   │   └── oauth.py         # OAuth2 flow helpers
│   │   ├── parsers/             # Document type-specific parsers
│   │   │   ├── classifier.py    # Gemini Flash document classifier
│   │   │   ├── datapoints.py    # Custom DataPoints (Proposal, Contract, etc.)
│   │   │   ├── proposal.py      # Commercial proposal parser
│   │   │   ├── contract.py      # Contract parser
│   │   │   ├── calculation.py   # Calculation/estimate parser
│   │   │   ├── drawing.py       # Drawing parser (Gemini Vision)
│   │   │   └── table.py         # Table/spreadsheet → markdown
│   │   ├── services/            # Business logic
│   │   │   ├── knowledge.py     # Cognee wrapper (add, cognify, search)
│   │   │   ├── transcription.py # Gemini Flash audio transcription
│   │   │   └── zettelkasten.py  # Notes, manual links, graph queries
│   │   └── workers/             # Celery tasks
│   │       ├── cognify_document.py  # Background cognee.cognify()
│   │       ├── transcribe_audio.py  # Gemini Flash transcription
│   │       └── sync_connector.py    # Scheduled connector sync
│   ├── alembic/                 # DB migrations
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── bot/
│   ├── main.py                  # Telegram bot
│   ├── handlers/
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js app router
│   │   ├── components/
│   │   │   ├── Graph/           # Knowledge graph (react-force-graph)
│   │   │   ├── NoteEditor/      # Markdown editor with [[links]]
│   │   │   ├── Search/          # GraphRAG search interface
│   │   │   ├── Documents/       # Document browser + upload
│   │   │   └── Connectors/      # Connector setup & sync status
│   │   └── lib/                 # API client, utils
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml           # PostgreSQL, Redis, backend, bot, frontend
└── README.md
```
