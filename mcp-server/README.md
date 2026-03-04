# ZettelCognee MCP Server

MCP сервер для подключения Claude к базе знаний ZettelCognee.

## Установка

```bash
cd mcp-server
uv pip install -e .
```

## Настройка Claude Desktop

Добавить в `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "zettelcognee": {
      "command": "zettelcognee-mcp",
      "env": {
        "ZETTELCOGNEE_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Настройка Claude Code

Добавить в `.claude/settings.json`:

```json
{
  "mcpServers": {
    "zettelcognee": {
      "command": "zettelcognee-mcp",
      "env": {
        "ZETTELCOGNEE_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Доступные инструменты

| Tool | Описание |
|------|----------|
| `search_knowledge` | GraphRAG поиск по графу знаний (сложные вопросы, связи) |
| `search_simple` | Простой RAG поиск (факты, цены, даты) |
| `list_documents` | Список документов в базе |
| `get_document` | Детали конкретного документа |
| `upload_text` | Добавить текст в базу знаний |

## Переменные окружения

| Variable | Default | Description |
|----------|---------|-------------|
| `ZETTELCOGNEE_API_URL` | `http://localhost:8000` | URL бэкенда |
| `ZETTELCOGNEE_EMAIL` | `dev@zettelcognee.local` | Email для авторизации |
| `ZETTELCOGNEE_PASSWORD` | `dev123` | Пароль |
