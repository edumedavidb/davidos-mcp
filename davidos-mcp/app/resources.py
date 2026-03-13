"""Widget resource management for DavidOS MCP."""

import logging
from pathlib import Path

logger = logging.getLogger("davidos-mcp")

# Path to widget components
COMPONENTS_DIR = Path(__file__).parent.parent / "components"


def load_widget(filename: str) -> str:
    """Load a widget HTML file."""
    widget_path = COMPONENTS_DIR / filename
    
    if not widget_path.exists():
        logger.error(f"Widget not found: {filename}")
        return f"<html><body>Widget not found: {filename}</body></html>"
    
    try:
        with open(widget_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading widget {filename}: {e}")
        return f"<html><body>Error loading widget: {str(e)}</body></html>"


def get_decision_widget() -> str:
    """Get decision widget HTML."""
    return load_widget("decision_widget.html")


def get_context_widget() -> str:
    """Get context widget HTML."""
    return load_widget("context_widget.html")


def get_question_widget() -> str:
    """Get question widget HTML."""
    return load_widget("question_widget.html")


def get_search_widget() -> str:
    """Get search widget HTML."""
    return load_widget("search_widget.html")


def get_file_widget() -> str:
    """Get file widget HTML."""
    return load_widget("file_widget.html")
