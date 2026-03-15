"""
DavidOS MCP Server using official FastMCP SDK.

This replaces the manual protocol implementation with the official SDK
to ensure full compatibility with ChatGPT's MCP client.
"""

import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from .file_manager import FileManager
from .mcp_auth import DavidOSTokenVerifier

logger = logging.getLogger("davidos-mcp")

# Initialize file manager
file_manager = FileManager()

# Create authentication provider
auth = DavidOSTokenVerifier()

# Create FastMCP server with stateless HTTP transport (recommended for production)
mcp = FastMCP(
    name="DavidOS MCP Server",
    stateless_http=True,  # Stateless for scalability
    json_response=True,   # JSON responses (not SSE)
    auth=auth             # OAuth token verification
)

# Configure for browser-based clients (ChatGPT)
mcp.settings.streamable_http_path = "/"


# === TOOLS ===

@mcp.tool()
def get_context(query: str = "") -> str:
    """
    Get relevant context from DavidOS knowledge base.
    
    Args:
        query: Optional search query to filter context
    
    Returns:
        Relevant context information
    """
    logger.info(f"get_context called with query: {query}")
    
    # Get all markdown files
    files = file_manager.list_files()
    
    if query:
        # Filter files by query
        matching_files = [f for f in files if query.lower() in f.lower()]
        context_parts = []
        
        for file_path in matching_files[:5]:  # Limit to 5 files
            try:
                content = file_manager.read_file(file_path)
                context_parts.append(f"## {file_path}\n\n{content[:500]}...")
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
        
        return "\n\n".join(context_parts) if context_parts else "No matching context found."
    else:
        # Return summary of available files
        return f"Available files ({len(files)}):\n" + "\n".join(f"- {f}" for f in files[:20])


@mcp.tool()
def read_file(path: str) -> str:
    """
    Read a file from DavidOS.
    
    Args:
        path: Path to the file (e.g., 'decisions/2024-03-14-architecture.md')
    
    Returns:
        File content
    """
    logger.info(f"read_file called for: {path}")
    
    try:
        content = file_manager.read_file(path)
        return content
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
def search_memory(query: str) -> str:
    """
    Search across all DavidOS files.
    
    Args:
        query: Search query
    
    Returns:
        Search results with file paths and snippets
    """
    logger.info(f"search_memory called with query: {query}")
    
    results = file_manager.search_files(query)
    
    if not results:
        return f"No results found for: {query}"
    
    output_parts = [f"Found {len(results)} results for '{query}':\n"]
    
    for result in results[:10]:  # Limit to 10 results
        output_parts.append(f"\n**{result['path']}**")
        output_parts.append(f"```\n{result['snippet']}\n```")
    
    return "\n".join(output_parts)


@mcp.tool()
def append_decision(title: str, content: str, tags: str = "") -> str:
    """
    Append a decision to DavidOS decisions log.
    
    Args:
        title: Decision title
        content: Decision content
        tags: Optional comma-separated tags
    
    Returns:
        Confirmation message
    """
    logger.info(f"append_decision called: {title}")
    
    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"decisions/{date_str}-{title.lower().replace(' ', '-')}.md"
    
    decision_content = f"# {title}\n\n"
    decision_content += f"**Date:** {date_str}\n\n"
    if tags:
        decision_content += f"**Tags:** {tags}\n\n"
    decision_content += f"{content}\n"
    
    try:
        file_manager.write_file(filename, decision_content)
        return f"Decision saved to {filename}"
    except Exception as e:
        return f"Error saving decision: {str(e)}"


@mcp.tool()
def append_question(question: str, context: str = "") -> str:
    """
    Append a question to DavidOS questions log.
    
    Args:
        question: The question
        context: Optional context or background
    
    Returns:
        Confirmation message
    """
    logger.info(f"append_question called: {question[:50]}...")
    
    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    question_entry = f"\n## {date_str}\n\n"
    question_entry += f"**Q:** {question}\n\n"
    if context:
        question_entry += f"**Context:** {context}\n\n"
    
    try:
        file_manager.append_file("questions.md", question_entry)
        return f"Question added to questions.md"
    except Exception as e:
        return f"Error saving question: {str(e)}"


@mcp.tool()
def append_weekly_note(content: str) -> str:
    """
    Append content to this week's note in DavidOS.
    
    Args:
        content: Content to append
    
    Returns:
        Confirmation message
    """
    logger.info(f"append_weekly_note called")
    
    from datetime import datetime
    # Get ISO week number
    now = datetime.now()
    week_num = now.isocalendar()[1]
    year = now.year
    filename = f"weekly/{year}-W{week_num:02d}.md"
    
    entry = f"\n\n---\n\n{content}\n"
    
    try:
        file_manager.append_file(filename, entry)
        return f"Content added to {filename}"
    except Exception as e:
        return f"Error appending to weekly note: {str(e)}"


@mcp.tool()
def update_section(path: str, section_title: str, new_content: str) -> str:
    """
    Update a specific section in a DavidOS file.
    
    Args:
        path: File path
        section_title: Section heading to update (e.g., "## Goals")
        new_content: New content for the section
    
    Returns:
        Confirmation message
    """
    logger.info(f"update_section called for {path}, section: {section_title}")
    
    try:
        # Read current content
        content = file_manager.read_file(path)
        
        # Find section
        lines = content.split('\n')
        section_start = -1
        section_end = len(lines)
        
        for i, line in enumerate(lines):
            if line.strip() == section_title.strip():
                section_start = i
            elif section_start != -1 and line.startswith('#'):
                section_end = i
                break
        
        if section_start == -1:
            return f"Error: Section '{section_title}' not found in {path}"
        
        # Replace section content
        new_lines = lines[:section_start+1] + [new_content] + lines[section_end:]
        new_file_content = '\n'.join(new_lines)
        
        file_manager.write_file(path, new_file_content)
        return f"Section '{section_title}' updated in {path}"
        
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except Exception as e:
        return f"Error updating section: {str(e)}"


logger.info("FastMCP server initialized with 7 tools")
