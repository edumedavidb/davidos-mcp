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
from . import mcp_protocol
from . import mcp_init

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

# Initialize MCP tools and resources
mcp_init.initialize_mcp()


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


@app.get("/test")
async def test_page():
    """Serve MCP protocol test page."""
    from fastapi.responses import HTMLResponse
    
    test_html_path = Path(__file__).parent.parent / "test_mcp.html"
    
    if test_html_path.exists():
        with open(test_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            # Update BASE_URL to use relative path
            html_content = html_content.replace(
                "const BASE_URL = 'https://davidos-mcp-production.up.railway.app';",
                "const BASE_URL = window.location.origin;"
            )
            return HTMLResponse(content=html_content)
    
    return HTMLResponse(content="<html><body>Test page not found</body></html>")


@app.get("/privacy")
async def privacy_policy():
    """Privacy policy for ChatGPT App submission."""
    from fastapi.responses import HTMLResponse
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DavidOS MCP - Privacy Policy</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; }
            h1 { color: #1a1a1a; }
            h2 { color: #333; margin-top: 30px; }
            p { color: #666; }
        </style>
    </head>
    <body>
        <h1>Privacy Policy</h1>
        <p><strong>Last Updated:</strong> March 14, 2026</p>
        
        <h2>1. Information We Collect</h2>
        <p>DavidOS MCP collects the following information:</p>
        <ul>
            <li><strong>Authentication Data:</strong> Email address, name, and profile picture from Google OAuth</li>
            <li><strong>Usage Data:</strong> Tool execution logs, timestamps, and operation history</li>
            <li><strong>Content Data:</strong> Strategic documents, decisions, and notes you create or modify</li>
        </ul>
        
        <h2>2. How We Use Your Information</h2>
        <p>We use your information to:</p>
        <ul>
            <li>Authenticate and authorize access to the MCP server</li>
            <li>Store and retrieve your strategic context and decisions</li>
            <li>Provide MCP tools and widgets to ChatGPT</li>
            <li>Monitor system performance and debug issues</li>
        </ul>
        
        <h2>3. Data Storage</h2>
        <p>Your data is stored:</p>
        <ul>
            <li><strong>Session Data:</strong> Encrypted session cookies for authentication</li>
            <li><strong>Content Data:</strong> Markdown files in the server's file system</li>
            <li><strong>Logs:</strong> Server logs on Railway infrastructure</li>
        </ul>
        
        <h2>4. Data Sharing</h2>
        <p>We do not share your data with third parties except:</p>
        <ul>
            <li><strong>Google OAuth:</strong> For authentication purposes only</li>
            <li><strong>Railway:</strong> Infrastructure provider hosting the service</li>
            <li><strong>ChatGPT:</strong> When you explicitly use DavidOS tools in ChatGPT</li>
        </ul>
        
        <h2>5. Domain Restriction</h2>
        <p>Access is currently restricted to users with email addresses from authorized domains (edume.com). This ensures your strategic content remains private to your organization.</p>
        
        <h2>6. Data Security</h2>
        <p>We implement security measures including:</p>
        <ul>
            <li>HTTPS encryption for all communications</li>
            <li>OAuth 2.0 authentication</li>
            <li>Domain-restricted access</li>
            <li>Session-based authorization</li>
        </ul>
        
        <h2>7. Your Rights</h2>
        <p>You have the right to:</p>
        <ul>
            <li>Access your stored data</li>
            <li>Request deletion of your data</li>
            <li>Revoke OAuth access at any time</li>
            <li>Export your strategic documents</li>
        </ul>
        
        <h2>8. Contact</h2>
        <p>For privacy concerns or data requests, contact: <a href="mailto:david.barnes@edume.com">david.barnes@edume.com</a></p>
        
        <h2>9. Changes to This Policy</h2>
        <p>We may update this privacy policy. Changes will be posted on this page with an updated revision date.</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/terms")
async def terms_of_service():
    """Terms of service for ChatGPT App submission."""
    from fastapi.responses import HTMLResponse
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DavidOS MCP - Terms of Service</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; }
            h1 { color: #1a1a1a; }
            h2 { color: #333; margin-top: 30px; }
            p { color: #666; }
        </style>
    </head>
    <body>
        <h1>Terms of Service</h1>
        <p><strong>Last Updated:</strong> March 14, 2026</p>
        
        <h2>1. Acceptance of Terms</h2>
        <p>By accessing and using DavidOS MCP, you agree to be bound by these Terms of Service. If you do not agree, do not use the service.</p>
        
        <h2>2. Description of Service</h2>
        <p>DavidOS MCP is a Model Context Protocol server that provides:</p>
        <ul>
            <li>Strategic context management tools</li>
            <li>Decision logging and tracking</li>
            <li>Knowledge base search and retrieval</li>
            <li>Integration with ChatGPT via MCP protocol</li>
        </ul>
        
        <h2>3. User Accounts</h2>
        <p>To use DavidOS MCP, you must:</p>
        <ul>
            <li>Authenticate via Google OAuth</li>
            <li>Have an email address from an authorized domain</li>
            <li>Maintain the security of your authentication credentials</li>
            <li>Be responsible for all activities under your account</li>
        </ul>
        
        <h2>4. Acceptable Use</h2>
        <p>You agree to:</p>
        <ul>
            <li>Use the service for legitimate strategic planning and decision-making</li>
            <li>Not attempt to bypass authentication or access controls</li>
            <li>Not use the service to store illegal or harmful content</li>
            <li>Not interfere with the service's operation or other users</li>
        </ul>
        
        <h2>5. Content Ownership</h2>
        <p>You retain ownership of all content you create using DavidOS MCP. By using the service, you grant us a license to:</p>
        <ul>
            <li>Store and process your content to provide the service</li>
            <li>Display your content to you via ChatGPT and other interfaces</li>
            <li>Make backups for service reliability</li>
        </ul>
        
        <h2>6. Service Availability</h2>
        <p>We strive to maintain service availability but do not guarantee:</p>
        <ul>
            <li>Uninterrupted access to the service</li>
            <li>Error-free operation</li>
            <li>Data backup or recovery</li>
            <li>Compatibility with future ChatGPT versions</li>
        </ul>
        
        <h2>7. Data Retention</h2>
        <p>We retain your data:</p>
        <ul>
            <li>As long as your account is active</li>
            <li>For 30 days after account deletion (for recovery purposes)</li>
            <li>Logs may be retained for up to 90 days for debugging</li>
        </ul>
        
        <h2>8. Modifications to Service</h2>
        <p>We reserve the right to:</p>
        <ul>
            <li>Modify or discontinue the service at any time</li>
            <li>Update these terms with notice</li>
            <li>Change pricing or access policies</li>
        </ul>
        
        <h2>9. Limitation of Liability</h2>
        <p>DavidOS MCP is provided "as is" without warranties. We are not liable for:</p>
        <ul>
            <li>Data loss or corruption</li>
            <li>Service interruptions</li>
            <li>Decisions made based on the service</li>
            <li>Unauthorized access to your data</li>
        </ul>
        
        <h2>10. Termination</h2>
        <p>We may terminate or suspend access to the service:</p>
        <ul>
            <li>For violation of these terms</li>
            <li>For security reasons</li>
            <li>At our discretion with notice</li>
        </ul>
        
        <h2>11. Governing Law</h2>
        <p>These terms are governed by the laws of the jurisdiction where the service is operated.</p>
        
        <h2>12. Contact</h2>
        <p>For questions about these terms, contact: <a href="mailto:david.barnes@edume.com">david.barnes@edume.com</a></p>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/mcp")
async def mcp_endpoint(request: Request, user: dict = Depends(auth.get_current_user)):
    """MCP protocol endpoint - handles all MCP method calls."""
    try:
        payload = await request.json()
        
        method = payload.get("method")
        params = payload.get("params", {})
        
        logger.info(f"MCP request from {user['email']}: method={method}")
        
        # Route to MCP protocol handler
        result = mcp_protocol.handle_mcp_request(method, params)
        
        return result
        
    except ValueError as e:
        logger.error(f"MCP protocol error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"MCP endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
