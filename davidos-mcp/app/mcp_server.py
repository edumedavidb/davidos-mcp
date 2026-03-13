"""DavidOS MCP Server - Model Context Protocol implementation."""

import asyncio
import logging
import json
from datetime import datetime
from typing import Any
from pathlib import Path

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    Resource,
    TextContent,
    ResourceContent,
)
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from .config import settings, RESOURCE_URIS
from .file_manager import FileManager, FileManagerError, PathTraversalError, FileAccessError

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("davidos-mcp")

# Initialize file manager
file_manager = FileManager()

# MCP Server instance
mcp_server = Server("davidos-mcp")


# === MCP Tools ===

@mcp_server.tool()
async def get_context() -> str:
    """Get the main DavidOS context document."""
    return file_manager.read_file("context.md")


@mcp_server.tool()
async def read_file(path: str) -> str:
    """Read a specific DavidOS file.
    
    Args:
        path: Relative path within DavidOS (e.g., "strategy/risks.md")
    """
    return file_manager.read_file(path)


@mcp_server.tool()
async def list_files() -> str:
    """List all available DavidOS files."""
    files = file_manager.list_files()
    return json.dumps(files, indent=2)


@mcp_server.tool()
async def search_memory(query: str) -> str:
    """Search for text across all DavidOS files.
    
    Args:
        query: Search string
    """
    results = file_manager.search_files(query)
    return json.dumps(results, indent=2)


@mcp_server.tool()
async def append_open_question(question: str, category: str = "General") -> str:
    """Append a new open question.
    
    Args:
        question: The question to add
        category: Category for grouping (e.g., "Compliance", "Distribution")
    """
    timestamp = datetime.now().isoformat()
    entry = f"\n## {category} - {timestamp}\n\n{question}\n"
    
    file_manager.append_to_file("strategy/open-questions.md", entry)
    return f"Added question to open-questions.md in category '{category}'"


@mcp_server.tool()
async def append_decision(
    context: str,
    decision: str,
    options_considered: list[str] = None,
    implications: str = "",
    review_date: str = ""
) -> str:
    """Append a structured decision to the decision log.
    
    Args:
        context: Background and circumstances
        decision: The decision made
        options_considered: List of alternatives evaluated
        implications: Expected outcomes and tradeoffs
        review_date: Optional date to review this decision
    """
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
    return "Decision recorded in decision-log.md"


@mcp_server.tool()
async def append_weekly_note(note: str, week_date: str = None) -> str:
    """Append a note to the weekly review file.
    
    Args:
        note: The note content
        week_date: Optional date (defaults to current week)
    """
    if week_date is None:
        week_date = datetime.now().strftime("%Y-W%U")
    
    # Check if we need a new week header
    try:
        current_content = file_manager.read_file("execution/weekly-notes.md")
        needs_header = week_date not in current_content[:1000]  # Check first 1000 chars
    except FileNotFoundError:
        needs_header = True
    
    if needs_header:
        entry = f"\n# Week {week_date}\n\n## {datetime.now().strftime('%Y-%m-%d')}\n\n{note}\n"
    else:
        entry = f"\n## {datetime.now().strftime('%Y-%m-%d')}\n\n{note}\n"
    
    file_manager.append_to_file("execution/weekly-notes.md", entry)
    return f"Note added to weekly-notes.md for week {week_date}"


@mcp_server.tool()
async def update_section(file: str, section_heading: str, content: str) -> str:
    """Update a markdown section in a DavidOS file.
    
    Args:
        file: Relative file path (e.g., "strategy/risks.md")
        section_heading: Section heading to update (without #)
        content: New section content
    """
    file_manager.update_section(file, section_heading, content)
    return f"Updated section '{section_heading}' in {file}"


@mcp_server.tool()
async def generate_brief(topic: str, context: str = "") -> str:
    """Generate a strategic brief synthesizing relevant DavidOS content.
    
    Args:
        topic: The topic to research
        context: Additional context for the brief
    """
    # Search for relevant content
    results = file_manager.search_files(topic)
    
    # Also search in context
    context_results = file_manager.search_files(context) if context else []
    
    # Build brief
    brief_parts = [
        f"# Strategic Brief: {topic}",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Relevant DavidOS Content",
        ""
    ]
    
    # Add search results
    all_results = results[:5]  # Top 5 results
    if all_results:
        for r in all_results:
            brief_parts.append(f"### From {r['file']} (line {r['line']})")
            brief_parts.append(f"```")
            brief_parts.append(r['context'])
            brief_parts.append(f"```")
            brief_parts.append("")
    else:
        brief_parts.append("No direct matches found. Consider adding relevant content.")
        brief_parts.append("")
    
    brief_parts.append("## Suggested Actions")
    brief_parts.append("")
    brief_parts.append(f"- Review {len(results)} related entries in DavidOS")
    brief_parts.append("- Consider documenting new insights if gaps exist")
    brief_parts.append("- Reference context.md for strategic alignment")
    
    return "\n".join(brief_parts)


# === MCP Resources ===

@mcp_server.resource("davidos://context")
async def resource_context() -> ResourceContent:
    """Main context document."""
    content = file_manager.read_file("context.md")
    return ResourceContent(
        uri="davidos://context",
        mimeType="text/markdown",
        text=content
    )


@mcp_server.resource("davidos://index")
async def resource_index() -> ResourceContent:
    """DavidOS index/navigation."""
    content = file_manager.read_file("index.md")
    return ResourceContent(
        uri="davidos://index",
        mimeType="text/markdown",
        text=content
    )


@mcp_server.resource("davidos://strategy/vision")
async def resource_vision() -> ResourceContent:
    """Product vision document."""
    content = file_manager.read_file("strategy/product-vision.md")
    return ResourceContent(
        uri="davidos://strategy/vision",
        mimeType="text/markdown",
        text=content
    )


@mcp_server.resource("davidos://strategy/bets")
async def resource_bets() -> ResourceContent:
    """Strategic bets document."""
    content = file_manager.read_file("strategy/strategic-bets.md")
    return ResourceContent(
        uri="davidos://strategy/bets",
        mimeType="text/markdown",
        text=content
    )


@mcp_server.resource("davidos://strategy/risks")
async def resource_risks() -> ResourceContent:
    """Strategic risks document."""
    content = file_manager.read_file("strategy/risks.md")
    return ResourceContent(
        uri="davidos://strategy/risks",
        mimeType="text/markdown",
        text=content
    )


@mcp_server.resource("davidos://strategy/questions")
async def resource_questions() -> ResourceContent:
    """Open questions document."""
    content = file_manager.read_file("strategy/open-questions.md")
    return ResourceContent(
        uri="davidos://strategy/questions",
        mimeType="text/markdown",
        text=content
    )


@mcp_server.resource("davidos://org/product")
async def resource_org() -> ResourceContent:
    """Product organization document."""
    content = file_manager.read_file("organisation/product-org.md")
    return ResourceContent(
        uri="davidos://org/product",
        mimeType="text/markdown",
        text=content
    )


@mcp_server.resource("davidos://execution/decisions")
async def resource_decisions() -> ResourceContent:
    """Decision log document."""
    content = file_manager.read_file("execution/decision-log.md")
    return ResourceContent(
        uri="davidos://execution/decisions",
        mimeType="text/markdown",
        text=content
    )


@mcp_server.resource("davidos://execution/weekly")
async def resource_weekly() -> ResourceContent:
    """Weekly notes document."""
    try:
        content = file_manager.read_file("execution/weekly-notes.md")
    except FileNotFoundError:
        content = "# Weekly Notes\n\nNo entries yet."
    
    return ResourceContent(
        uri="davidos://execution/weekly",
        mimeType="text/markdown",
        text=content
    )


# === FastAPI HTTP Server ===

app = FastAPI(title="DavidOS MCP Server", version="1.0.0")


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


# === Entry Points ===

async def run_stdio():
    """Run MCP server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="davidos-mcp",
                server_version="1.0.0",
                capabilities=mcp_server.get_capabilities()
            )
        )


def run_http():
    """Run HTTP server."""
    uvicorn.run(
        "davidos_mcp.app.mcp_server:app",
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
