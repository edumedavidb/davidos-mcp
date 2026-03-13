"""DavidOS MCP Server - HTTP API for DavidOS content."""

import logging
import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

from .config import settings
from .file_manager import FileManager, FileManagerError, PathTraversalError, FileAccessError
from . import auth

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

# Add session middleware for OAuth
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)


# === Authentication Endpoints ===

@app.get("/login")
async def login(request: Request):
    """Initiate Google OAuth login."""
    return await auth.login(request)


@app.get("/auth/google/callback")
async def auth_callback(request: Request):
    """Handle Google OAuth callback."""
    return await auth.auth_callback(request)


@app.get("/me")
async def get_me(request: Request, user: dict = Depends(auth.get_current_user)):
    """Get current authenticated user."""
    return await auth.get_me(request, user)


@app.get("/logout")
async def logout(request: Request):
    """Logout current user."""
    return await auth.logout(request)


# === Public Endpoints ===

@app.get("/")
async def homepage(request: Request):
    """Homepage - shows login status."""
    user = request.session.get('user')
    if user:
        return {
            "status": "authenticated",
            "user": user.get('email'),
            "message": "You are logged in. Access /mcp/* endpoints or visit /me for user info."
        }
    return {
        "status": "unauthenticated",
        "message": "Visit /login to authenticate"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "server": "davidos-mcp", "version": "1.0.0"}


# === Protected MCP Endpoints ===

@app.get("/mcp/files")
async def http_list_files(user: dict = Depends(auth.get_current_user)):
    """HTTP endpoint to list files. Requires authentication."""
    logger.info(f"User {user['email']} listing files")
    return file_manager.list_files()


@app.post("/mcp/read")
async def http_read_file(path: str, user: dict = Depends(auth.get_current_user)):
    """HTTP endpoint to read a file. Requires authentication."""
    try:
        logger.info(f"User {user['email']} reading file: {path}")
        content = file_manager.read_file(path)
        return {"path": path, "content": content}
    except FileManagerError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/mcp/search")
async def http_search(query: str, user: dict = Depends(auth.get_current_user)):
    """HTTP endpoint to search. Requires authentication."""
    logger.info(f"User {user['email']} searching: {query}")
    return file_manager.search_files(query)


@app.post("/mcp/append/question")
async def http_append_question(question: str, category: str = "General", user: dict = Depends(auth.get_current_user)):
    """Append a new open question. Requires authentication."""
    try:
        logger.info(f"User {user['email']} appending question to category: {category}")
        timestamp = datetime.now().isoformat()
        entry = f"\n## {category} - {timestamp}\n\n{question}\n"
        file_manager.append_to_file("strategy/open-questions.md", entry)
        return {"status": "success", "message": f"Added question to open-questions.md in category '{category}'"}
    except FileManagerError as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.post("/mcp/append/decision")
async def http_append_decision(
    context: str,
    decision: str,
    options_considered: list[str] = None,
    implications: str = "",
    review_date: str = "",
    user: dict = Depends(auth.get_current_user)
):
    """Append a structured decision to the decision log. Requires authentication."""
    try:
        logger.info(f"User {user['email']} appending decision")
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


@app.post("/mcp/append/weekly")
async def http_append_weekly(note: str, week_date: str = None, user: dict = Depends(auth.get_current_user)):
    """Append a note to the weekly review file. Requires authentication."""
    try:
        logger.info(f"User {user['email']} appending weekly note")
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


@app.post("/mcp/update/section")
async def http_update_section(file: str, section_heading: str, content: str, user: dict = Depends(auth.get_current_user)):
    """Update a markdown section in a DavidOS file. Requires authentication."""
    try:
        logger.info(f"User {user['email']} updating section '{section_heading}' in {file}")
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
