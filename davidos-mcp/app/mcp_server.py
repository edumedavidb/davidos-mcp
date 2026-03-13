"""DavidOS MCP Server - HTTP API for DavidOS content."""

import logging
import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from .config import settings
from .file_manager import FileManager, FileManagerError, PathTraversalError, FileAccessError

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("davidos-mcp")

# Initialize file manager
file_manager = FileManager()

# FastAPI application
app = FastAPI(title="DavidOS MCP Server", version="1.0.0")


# === HTTP Endpoints ===

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "server": "davidos-mcp", "version": "1.0.0"}


@app.get("/files")
async def http_list_files():
    """HTTP endpoint to list files."""
    return file_manager.list_files()


@app.post("/read")
async def http_read_file(path: str):
    """HTTP endpoint to read a file."""
    try:
        content = file_manager.read_file(path)
        return {"path": path, "content": content}
    except FileManagerError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/search")
async def http_search(query: str):
    """HTTP endpoint to search."""
    return file_manager.search_files(query)


@app.post("/append/question")
async def http_append_question(question: str, category: str = "General"):
    """Append a new open question."""
    try:
        timestamp = datetime.now().isoformat()
        entry = f"\n## {category} - {timestamp}\n\n{question}\n"
        file_manager.append_to_file("strategy/open-questions.md", entry)
        return {"status": "success", "message": f"Added question to open-questions.md in category '{category}'"}
    except FileManagerError as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.post("/append/decision")
async def http_append_decision(
    context: str,
    decision: str,
    options_considered: list[str] = None,
    implications: str = "",
    review_date: str = ""
):
    """Append a structured decision to the decision log."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        entry = f"""
## Decision - {timestamp}

### Context
{context}

### Options Considered
"""
        if options_considered:
            for opt in options_considered:
                entry += f"- {opt}\n"
        else:
            entry += "- (none documented)\n"
        
        entry += f"""
### Decision
{decision}

### Implications
{implications or "(none documented)"}
"""
        
        if review_date:
            entry += f"\n### Review Date\n{review_date}\n"
        
        entry += "\n---\n"
        
        file_manager.append_to_file("execution/decision-log.md", entry)
        return {"status": "success", "message": "Decision recorded in decision-log.md"}
    except FileManagerError as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.post("/append/weekly")
async def http_append_weekly(note: str, week_date: str = None):
    """Append a note to the weekly review file."""
    try:
        if week_date is None:
            week_date = datetime.now().strftime("%Y-W%U")
        
        # Check if we need a new week header
        try:
            current_content = file_manager.read_file("execution/weekly-notes.md")
            needs_header = week_date not in current_content[:1000]
        except FileNotFoundError:
            needs_header = True
        
        if needs_header:
            entry = f"\n# Week {week_date}\n\n## {datetime.now().strftime('%Y-%m-%d')}\n\n{note}\n"
        else:
            entry = f"\n## {datetime.now().strftime('%Y-%m-%d')}\n\n{note}\n"
        
        file_manager.append_to_file("execution/weekly-notes.md", entry)
        return {"status": "success", "message": f"Note added to weekly-notes.md for week {week_date}"}
    except FileManagerError as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.post("/update/section")
async def http_update_section(file: str, section_heading: str, content: str):
    """Update a markdown section in a DavidOS file."""
    try:
        file_manager.update_section(file, section_heading, content)
        return {"status": "success", "message": f"Updated section '{section_heading}' in {file}"}
    except FileManagerError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# === Entry Points ===

def run_http():
    """Run HTTP server."""
    uvicorn.run(
        "app.mcp_server:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=False
    )


def main():
    """Main entry point - runs HTTP server by default."""
    logger.info(f"Starting DavidOS MCP Server on {settings.host}:{settings.port}")
    run_http()


if __name__ == "__main__":
    main()
