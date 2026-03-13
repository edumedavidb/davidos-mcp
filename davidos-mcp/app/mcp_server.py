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
