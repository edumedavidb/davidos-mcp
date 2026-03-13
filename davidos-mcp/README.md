# DavidOS MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with structured access to the DavidOS strategic knowledge base.

## Overview

This server exposes DavidOS content through:
- **MCP Tools**: Operations like reading files, searching, appending decisions, updating sections
- **MCP Resources**: Direct access to key documents via URIs
- **HTTP API**: REST endpoints for health checks and basic operations

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│   MCP Client    │────→│  DavidOS MCP     │────→│  DavidOS    │
│  (Claude, etc)  │     │  Server (HTTP)   │     │  Markdown   │
└─────────────────┘     └──────────────────┘     └─────────────┘
                               │
                               ↓
                        ┌──────────────┐
                        │   Railway    │
                        │  (Hosted)    │
                        └──────────────┘
```

## Quick Start

### Local Development (Docker)

1. **Start the server:**
   ```bash
   cd davidos-mcp
   docker-compose up --build
   ```

2. **Test the health endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **List available files:**
   ```bash
   curl http://localhost:8000/files
   ```

### Local Development (Python)

1. **Install dependencies:**
   ```bash
   cd davidos-mcp
   pip install -r requirements.txt
   ```

2. **Set environment:**
   ```bash
   cp .env.example .env
   # Edit .env to set DAVIDOS_ROOT path
   ```

3. **Run the server:**
   ```bash
   python -m uvicorn app.mcp_server:app --reload
   ```

### Railway Deployment

1. **Push to Git:**
   ```bash
   git add .
   git commit -m "Initial MCP server"
   git push
   ```

2. **Connect to Railway:**
   - Create new project in Railway
   - Deploy from GitHub repo
   - Railway uses `railway.json` configuration

3. **Verify deployment:**
   ```bash
   curl https://your-app.railway.app/health
   ```

## API Reference

### MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_context` | Read main context.md | none |
| `read_file` | Read specific file | `path: str` |
| `list_files` | List all DavidOS files | none |
| `search_memory` | Search across files | `query: str` |
| `append_open_question` | Add to questions | `question, category` |
| `append_decision` | Log a decision | `context, decision, options_considered, implications, review_date` |
| `append_weekly_note` | Add weekly note | `note, week_date` |
| `update_section` | Update markdown section | `file, section_heading, content` |
| `generate_brief` | Create synthesis | `topic, context` |

### MCP Resources

| URI | Content |
|-----|---------|
| `davidos://context` | Main context document |
| `davidos://index` | Navigation/index |
| `davidos://strategy/vision` | Product vision |
| `davidos://strategy/bets` | Strategic bets |
| `davidos://strategy/risks` | Risk analysis |
| `davidos://strategy/questions` | Open questions |
| `davidos://org/product` | Product org docs |
| `davidos://execution/decisions` | Decision log |
| `davidos://execution/weekly` | Weekly notes |

### HTTP Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/files` | GET | List files |
| `/read` | POST | Read file (path param) |
| `/search` | POST | Search files (query param) |

## Example Usage

### Reading Context

```bash
curl -X POST http://localhost:8000/read \
  -H "Content-Type: application/json" \
  -d '{"path": "context.md"}'
```

### Appending a Decision

```python
# Via MCP client
await mcp_client.call_tool("append_decision", {
    "context": "Q2 planning discussion",
    "decision": "Prioritize AI training generation",
    "options_considered": ["Build in-house", "Use vendor API"],
    "implications": "3-month timeline, need ML expertise",
    "review_date": "2026-06-01"
})
```

### Searching Memory

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "compliance"}'
```

### Updating a Section

```python
await mcp_client.call_tool("update_section", {
    "file": "strategy/risks.md",
    "section_heading": "Product evolution risk",
    "content": "Updated risk description..."
})
```

## External Exposure

### ngrok (Testing)

```bash
# Install ngrok
brew install ngrok

# Expose local server
ngrok http 8000

# Use the HTTPS URL for external access
```

### nginx (Local Network)

```nginx
location /davidos-mcp/ {
    proxy_pass http://localhost:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Security

### Guardrails

- **Path containment**: All file access within `DAVIDOS_ROOT`
- **Allowlist enforcement**: Only approved files readable/writable
- **Path traversal protection**: Rejects `..` and absolute paths
- **Audit logging**: All operations logged

### Allowed Files

**Read:** All markdown files in davidos/
**Write:**
- `strategy/open-questions.md`
- `execution/decision-log.md`
- `execution/weekly-notes.md`
- `strategy/risks.md`
- `strategy/strategic-bets.md`
- `strategy/product-vision.md`

### ⚠️ Important

This is a prototype. Do not expose publicly without:
- Authentication
- HTTPS
- Rate limiting
- Input validation hardening

## Testing

```bash
# Run tests
cd davidos-mcp
pytest tests/ -v

# Test manually
curl http://localhost:8000/health
curl http://localhost:8000/files
```

## Project Structure

```
davidos-mcp/
├── app/
│   ├── __init__.py
│   ├── mcp_server.py      # Main server with tools/resources
│   ├── file_manager.py    # Safe file operations
│   └── config.py          # Settings and allowlists
├── tests/
│   └── test_operations.py # Test suite
├── Dockerfile
├── docker-compose.yml
├── railway.json           # Railway deployment config
├── requirements.txt
├── .env.example
└── README.md
```

## Development

### Adding a New Tool

1. Add function in `app/mcp_server.py` with `@mcp_server.tool()` decorator
2. Implement in `app/file_manager.py` if needed
3. Add test in `tests/test_operations.py`
4. Update README

### Adding a New Resource

1. Add function in `app/mcp_server.py` with `@mcp_server.resource("uri")` decorator
2. Add to `RESOURCE_URIS` in `app/config.py`
3. Update README

## Troubleshooting

**File not found errors:**
- Check `DAVIDOS_ROOT` environment variable
- Verify volume mount in docker-compose.yml

**Permission denied:**
- Ensure write permissions on mounted volume
- Check file is in `ALLOWED_WRITE_FILES`

**MCP client connection fails:**
- Verify server is running: `curl http://localhost:8000/health`
- Check port isn't in use: `lsof -i :8000`

## License

Internal use only - David Barnes product operating system.
