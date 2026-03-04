# User Stories — Corporate Knowledge Base

## Context
- **Users**: 2-10 people, all equal (no admin/user distinction)
- **Goals**: Search, content generation, knowledge management
- **Sources**: Local files, SharePoint, Google Drive, Teams chats
- **Interfaces**: Telegram bot, Web UI (Zettelkasten)

---

## Epic 1: Document Ingestion (Загрузка документов)

### US-1.1: Upload documents via Web UI
**As a** team member
**I want to** upload PDF and Excel files through the web interface
**So that** they become searchable in the knowledge base

**Acceptance criteria:**
- Drag-and-drop or file picker upload
- Support for PDF, XLSX, XLS, DOCX formats
- Show upload progress
- After upload: file is parsed, chunked, embedded, and searchable
- Show processing status (queued → processing → ready)

### US-1.2: Batch upload
**As a** team member
**I want to** upload an entire folder of documents at once
**So that** I can quickly populate the knowledge base with existing files

**Acceptance criteria:**
- Select multiple files or a folder
- Background processing of all files
- Progress indicator per file
- Skip duplicates (by file hash)

### US-1.3: Upload audio recordings
**As a** team member
**I want to** upload audio recordings of meetings
**So that** their content becomes searchable

**Acceptance criteria:**
- Support: mp3, wav, m4a, ogg, webm
- Automatic transcription via Whisper
- Transcript is stored and linked to the audio file
- Transcript is chunked and searchable
- Show transcription progress

### US-1.4: Upload via Telegram
**As a** team member
**I want to** send a document to the Telegram bot
**So that** it gets added to the knowledge base without opening the web UI

**Acceptance criteria:**
- Send file to bot → bot uploads to S3 → triggers processing
- Bot replies with confirmation when processing is complete
- Support same file types as web upload

### US-1.5: Sync from SharePoint
**As a** team member
**I want to** connect the knowledge base to our SharePoint
**So that** documents stored there are automatically indexed

**Acceptance criteria:**
- Connect via Microsoft Graph API (OAuth2 flow)
- Browse and select SharePoint sites/libraries to sync
- Initial full sync: all documents from selected libraries
- Incremental sync: detect new/modified/deleted files (via delta API)
- Configurable sync interval (e.g. every 1h, daily)
- Show sync status and last sync time per library
- Support for folder structure — preserve as metadata/tags
- Handle permissions: sync only files accessible to the connected account

### US-1.6: Sync from Google Drive
**As a** team member
**I want to** connect the knowledge base to our Google Drive
**So that** documents stored there are automatically indexed

**Acceptance criteria:**
- Connect via Google Drive API (OAuth2 flow)
- Browse and select folders/shared drives to sync
- Initial full sync of selected folders
- Incremental sync: detect changes via Changes API / watch notifications
- Configurable sync interval
- Show sync status and last sync time per folder
- Support Google Docs/Sheets: export as PDF/XLSX before parsing
- Skip Google-native formats that can't be exported (Forms, Sites)
- Handle shared drives and "Shared with me"

### US-1.7: Import Teams chats
**As a** team member
**I want to** import chat histories from Teams
**So that** past discussions are searchable

**Acceptance criteria:**
- Export Teams chat as file → upload
- Messages are grouped by threads
- Participant names are preserved
- Timestamps are preserved

---

## Epic 2: Search (Поиск)

### US-2.1: Semantic search via Telegram
**As a** team member
**I want to** ask a question in Telegram and get relevant documents
**So that** I can quickly find information without leaving the messenger

**Acceptance criteria:**
- Send a natural language question to the bot
- Bot returns top 3-5 relevant chunks with source references
- Each result shows: snippet, document name, page/timestamp, relevance
- Clickable links to view full document in web UI

### US-2.2: Semantic search via Web UI
**As a** team member
**I want to** search the knowledge base in the web interface
**So that** I can see results with full context and filters

**Acceptance criteria:**
- Search bar with instant results
- Results show highlighted snippets
- Click result → open document at the right page/position
- Filter by: document type, date range, tags

### US-2.3: Exact data lookup
**As a** team member
**I want to** ask for specific data (numbers, dates, names) from Excel files
**So that** I get precise answers, not just relevant documents

**Acceptance criteria:**
- Query: "What was revenue in Q3 2025?" → returns the exact number
- System recognizes structured data queries
- Falls back to RAG if structured query fails

### US-2.4: Search within audio transcripts
**As a** team member
**I want to** search for what was discussed in a meeting
**So that** I can find specific decisions or statements

**Acceptance criteria:**
- Search returns transcript chunks with timestamps
- Click result → jump to that position in the transcript
- Show speaker name (if available)

---

## Epic 3: AI-Powered Generation (Генерация)

### US-3.1: Question answering (RAG)
**As a** team member
**I want to** ask a question in natural language and get a synthesized answer
**So that** I don't have to read through multiple documents myself

**Acceptance criteria:**
- Answer is generated based on relevant documents in the knowledge base
- Answer includes citations: [Source: filename, page X]
- User can click citation to view the source
- If no relevant info found, system says so (no hallucination)
- Works in both Telegram and Web UI

### US-3.2: Document summarization
**As a** team member
**I want to** get a summary of a specific document or meeting recording
**So that** I can quickly understand its content

**Acceptance criteria:**
- Select document → "Summarize" → get structured summary
- For meetings: participants, topics discussed, decisions, action items
- For documents: key points, conclusions
- Summary is saved as a note in Zettelkasten

### US-3.3: Report generation
**As a** team member
**I want to** generate a report based on multiple documents
**So that** I can compile information from different sources

**Acceptance criteria:**
- Specify topic/question + select documents (or let system choose)
- System generates a structured report with citations
- Export as markdown or PDF
- Editable before export

### US-3.4: Draft email/message generation
**As a** team member
**I want to** generate a draft response based on knowledge base context
**So that** I can quickly write informed emails

**Acceptance criteria:**
- Provide context: "Draft a reply to client X about project Y"
- System uses relevant KB documents as context
- Generates draft in specified tone
- Editable before sending

---

## Epic 4: Zettelkasten (Управление знаниями)

### US-4.1: View knowledge graph
**As a** team member
**I want to** see an interactive graph of all notes and their connections
**So that** I can discover relationships between topics

**Acceptance criteria:**
- Interactive force-directed graph
- Nodes = notes, colored by type (document/audio/chat/manual)
- Edges = links between notes, styled by type (manual/auto/semantic)
- Click node → open note
- Zoom, pan, filter by tags
- Search highlights nodes in graph

### US-4.2: Create manual notes
**As a** team member
**I want to** create my own notes in markdown
**So that** I can add my own knowledge and insights

**Acceptance criteria:**
- Markdown editor with preview
- Add tags
- Manually link to other notes via [[note-title]] syntax
- Auto-suggest links while typing (based on similarity)
- Save → embed → integrate into graph

### US-4.3: View backlinks
**As a** team member
**I want to** see all notes that reference the current note
**So that** I can understand how topics are connected

**Acceptance criteria:**
- Sidebar showing "Linked from" list
- Each backlink shows context (surrounding text)
- Click backlink → navigate to that note

### US-4.4: Auto-generated notes from documents
**As a** team member
**I want** the system to automatically create summary notes when documents are uploaded
**So that** I don't have to manually create notes for every document

**Acceptance criteria:**
- On upload: LLM generates summary note
- Summary note is linked to source document chunks
- Key entities (people, projects, companies) are extracted
- Auto-links to existing notes with shared entities
- User can edit auto-generated notes

### US-4.5: Tag management
**As a** team member
**I want to** organize notes and documents with tags
**So that** I can filter and browse by topic

**Acceptance criteria:**
- Add/remove tags on notes and documents
- Tag autocomplete from existing tags
- Filter graph/list by tags
- Tag cloud or tag list in sidebar

### US-4.6: Browse related notes
**As a** team member
**I want to** see notes related to the one I'm viewing
**So that** I can explore connected topics

**Acceptance criteria:**
- "Related notes" section showing semantically similar notes
- Configurable depth: direct links only, or 2-3 hops
- Preview snippet for each related note

---

## Epic 5: Collaboration (Совместная работа)

### US-5.1: See team activity
**As a** team member
**I want to** see what documents were recently added and what notes were created
**So that** I stay aware of team knowledge

**Acceptance criteria:**
- Activity feed on dashboard
- Shows: uploads, new notes, edits
- Filter by person, date

### US-5.2: Comment on documents
**As a** team member
**I want to** leave comments on documents or notes
**So that** I can share thoughts with the team

**Acceptance criteria:**
- Add comment to any note or document
- Comments visible to all team members
- @mention team members (optional)

---

## Epic 6: System & Settings (Системные)

### US-6.1: Simple authentication
**As a** team member
**I want to** log in with a simple method
**So that** only team members can access the system

**Acceptance criteria:**
- Invite link or shared password (for simplicity)
- Session management (stay logged in)
- Telegram bot: authorized by Telegram user ID

### US-6.2: View processing status
**As a** team member
**I want to** see which documents are being processed and their status
**So that** I know when they'll be available for search

**Acceptance criteria:**
- Processing queue visible in web UI
- Status per document: queued → parsing → embedding → ready / error
- Error details if processing failed

### US-6.3: Re-process document
**As a** team member
**I want to** re-trigger processing for a failed or outdated document
**So that** I can fix errors without re-uploading

**Acceptance criteria:**
- "Reprocess" button on document
- Clears old chunks and re-parses from original file

---

## Priority Matrix

| Story | Priority | Phase |
|-------|----------|-------|
| US-1.1 Upload documents | P0 | 1 |
| US-1.2 Batch upload | P1 | 1 |
| US-2.2 Web search | P0 | 2 |
| US-3.1 RAG Q&A | P0 | 2 |
| US-2.1 Telegram search | P0 | 2 |
| US-1.3 Audio upload | P1 | 3 |
| US-3.2 Summarization | P1 | 3 |
| US-4.4 Auto-generated notes | P1 | 3 |
| US-4.1 Knowledge graph | P1 | 4 |
| US-4.2 Manual notes | P1 | 4 |
| US-4.3 Backlinks | P2 | 4 |
| US-4.5 Tags | P1 | 4 |
| US-4.6 Related notes | P2 | 4 |
| US-1.5 SharePoint sync | P1 | 2 |
| US-1.6 Google Drive sync | P1 | 2 |
| US-1.7 Teams import | P2 | 5 |
| US-2.3 Exact data lookup | P2 | 2 |
| US-2.4 Audio search | P2 | 3 |
| US-3.3 Report generation | P2 | 3 |
| US-3.4 Draft email | P3 | 3 |
| US-1.4 Upload via Telegram | P2 | 2 |
| US-5.1 Activity feed | P3 | 4 |
| US-5.2 Comments | P3 | 5 |
| US-6.1 Auth | P0 | 1 |
| US-6.2 Processing status | P1 | 1 |
| US-6.3 Reprocess | P2 | 2 |
