"""DavidOS MCP Server package."""

from .mcp_server import mcp_server, main, run_http, run_stdio

__version__ = "1.0.0"
__all__ = ["mcp_server", "main", "run_http", "run_stdio"]
