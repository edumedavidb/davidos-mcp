"""MCP tool implementations for DavidOS."""

import logging
from datetime import datetime
from typing import Dict, Any, List

from .file_manager import FileManager, FileManagerError

logger = logging.getLogger("davidos-mcp")

# Initialize file manager
file_manager = FileManager()


def get_context() -> Dict[str, Any]:
    """Get strategic context from context.md."""
    try:
        content = file_manager.read_file("context.md")
        return {
            "content": [
                {"type": "text", "text": "Retrieved strategic context"}
            ],
            "structuredContent": {
                "context": content
            },
            "_meta": {
                "openai/outputTemplate": "ui://widget/context",
                "openai/toolInvocation/invoking": "Loading context...",
                "openai/toolInvocation/invoked": "Context loaded"
            }
        }
    except Exception as e:
        logger.error(f"get_context failed: {e}")
        return {
            "content": [
                {"type": "text", "text": f"Error: {str(e)}"}
            ]
        }


def read_file(path: str) -> Dict[str, Any]:
    """Read a DavidOS file."""
    try:
        content = file_manager.read_file(path)
        return {
            "content": [
                {"type": "text", "text": f"Read {path}"}
            ],
            "structuredContent": {
                "path": path,
                "content": content
            },
            "_meta": {
                "openai/outputTemplate": "ui://widget/file",
                "openai/toolInvocation/invoking": f"Reading {path}...",
                "openai/toolInvocation/invoked": f"Read {path}"
            }
        }
    except Exception as e:
        logger.error(f"read_file failed: {e}")
        return {
            "content": [
                {"type": "text", "text": f"Error reading {path}: {str(e)}"}
            ]
        }


def search_memory(query: str) -> Dict[str, Any]:
    """Search across DavidOS content."""
    try:
        results = file_manager.search_files(query)
        
        # Format results for display
        result_text = f"Found {len(results)} results for '{query}'"
        
        return {
            "content": [
                {"type": "text", "text": result_text}
            ],
            "structuredContent": {
                "query": query,
                "results": results
            },
            "_meta": {
                "openai/outputTemplate": "ui://widget/search",
                "openai/toolInvocation/invoking": f"Searching for '{query}'...",
                "openai/toolInvocation/invoked": f"Found {len(results)} results"
            }
        }
    except Exception as e:
        logger.error(f"search_memory failed: {e}")
        return {
            "content": [
                {"type": "text", "text": f"Error searching: {str(e)}"}
            ]
        }


def append_decision(
    context: str,
    decision: str,
    options_considered: List[str] = None,
    implications: str = "",
    review_date: str = ""
) -> Dict[str, Any]:
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
        
        return {
            "content": [
                {"type": "text", "text": "Decision recorded in decision-log.md"}
            ],
            "structuredContent": {
                "decision": decision,
                "context": context,
                "timestamp": timestamp,
                "options_considered": options_considered,
                "implications": implications
            },
            "_meta": {
                "openai/outputTemplate": "ui://widget/decision",
                "openai/toolInvocation/invoking": "Recording decision...",
                "openai/toolInvocation/invoked": "Decision saved"
            }
        }
    except Exception as e:
        logger.error(f"append_decision failed: {e}")
        return {
            "content": [
                {"type": "text", "text": f"Error recording decision: {str(e)}"}
            ]
        }


def append_question(question: str, category: str = "General") -> Dict[str, Any]:
    """Append a new open question."""
    try:
        timestamp = datetime.now().isoformat()
        entry = f"\n## {category} - {timestamp}\n\n{question}\n"
        
        file_manager.append_to_file("strategy/open-questions.md", entry)
        
        return {
            "content": [
                {"type": "text", "text": f"Added question to open-questions.md in category '{category}'"}
            ],
            "structuredContent": {
                "question": question,
                "category": category,
                "timestamp": timestamp
            },
            "_meta": {
                "openai/outputTemplate": "ui://widget/question",
                "openai/toolInvocation/invoking": "Adding question...",
                "openai/toolInvocation/invoked": "Question added"
            }
        }
    except Exception as e:
        logger.error(f"append_question failed: {e}")
        return {
            "content": [
                {"type": "text", "text": f"Error adding question: {str(e)}"}
            ]
        }


def append_weekly_note(note: str, week_date: str = None) -> Dict[str, Any]:
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
        
        return {
            "content": [
                {"type": "text", "text": f"Note added to weekly-notes.md for week {week_date}"}
            ],
            "structuredContent": {
                "note": note,
                "week_date": week_date
            },
            "_meta": {
                "openai/toolInvocation/invoking": "Adding weekly note...",
                "openai/toolInvocation/invoked": "Note added"
            }
        }
    except Exception as e:
        logger.error(f"append_weekly_note failed: {e}")
        return {
            "content": [
                {"type": "text", "text": f"Error adding note: {str(e)}"}
            ]
        }


def update_section(path: str, section: str, content: str) -> Dict[str, Any]:
    """Update a markdown section in a DavidOS file."""
    try:
        file_manager.update_section(path, section, content)
        
        return {
            "content": [
                {"type": "text", "text": f"Updated section '{section}' in {path}"}
            ],
            "structuredContent": {
                "path": path,
                "section": section,
                "updated": True
            },
            "_meta": {
                "openai/toolInvocation/invoking": f"Updating {path}...",
                "openai/toolInvocation/invoked": "Section updated"
            }
        }
    except Exception as e:
        logger.error(f"update_section failed: {e}")
        return {
            "content": [
                {"type": "text", "text": f"Error updating section: {str(e)}"}
            ]
        }
