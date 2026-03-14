"""Initialize MCP tools and resources for DavidOS."""

import logging
from . import mcp_protocol
from . import tools
from . import resources

logger = logging.getLogger("davidos-mcp")


def initialize_mcp():
    """Register all MCP tools and resources."""
    
    # Register read-only tools with versioned widget URIs
    mcp_protocol.register_tool(
        name="get_context",
        description="Retrieve the strategic context from context.md",
        input_schema={
            "type": "object",
            "properties": {},
            "required": []
        },
        handler=tools.get_context,
        output_template="ui://widget/context/v1",
        read_only=True
    )
    
    mcp_protocol.register_tool(
        name="read_file",
        description="Read a DavidOS file by path",
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file within DavidOS workspace (e.g., 'strategy/risks.md')"
                }
            },
            "required": ["path"]
        },
        handler=tools.read_file,
        output_template="ui://widget/file/v1",
        read_only=True
    )
    
    mcp_protocol.register_tool(
        name="search_memory",
        description="Search across all DavidOS content",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                }
            },
            "required": ["query"]
        },
        handler=tools.search_memory,
        output_template="ui://widget/search/v1",
        read_only=True
    )
    
    # Register write tools with versioned widget URIs (no read_only flag)
    mcp_protocol.register_tool(
        name="append_decision",
        description="Record a strategic decision in the decision log",
        input_schema={
            "type": "object",
            "properties": {
                "context": {
                    "type": "string",
                    "description": "Background and circumstances of the decision"
                },
                "decision": {
                    "type": "string",
                    "description": "The decision that was made"
                },
                "options_considered": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Alternative options that were considered"
                },
                "implications": {
                    "type": "string",
                    "description": "Expected outcomes and tradeoffs"
                },
                "review_date": {
                    "type": "string",
                    "description": "Optional date to review this decision"
                }
            },
            "required": ["context", "decision"]
        },
        handler=tools.append_decision,
        output_template="ui://widget/decision/v1"
    )
    
    mcp_protocol.register_tool(
        name="append_question",
        description="Add an open strategic question",
        input_schema={
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The strategic question to record"
                },
                "category": {
                    "type": "string",
                    "description": "Category for the question (default: General)"
                }
            },
            "required": ["question"]
        },
        handler=tools.append_question,
        output_template="ui://widget/question/v1"
    )
    
    mcp_protocol.register_tool(
        name="append_weekly_note",
        description="Add a note to the weekly review",
        input_schema={
            "type": "object",
            "properties": {
                "note": {
                    "type": "string",
                    "description": "The note content"
                },
                "week_date": {
                    "type": "string",
                    "description": "Week identifier (defaults to current week)"
                }
            },
            "required": ["note"]
        },
        handler=tools.append_weekly_note
    )
    
    mcp_protocol.register_tool(
        name="update_section",
        description="Update a specific section in a DavidOS markdown file",
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path"
                },
                "section": {
                    "type": "string",
                    "description": "Section heading to update"
                },
                "content": {
                    "type": "string",
                    "description": "New content for the section"
                }
            },
            "required": ["path", "section", "content"]
        },
        handler=tools.update_section
    )
    
    # Register widget resources with versioned URIs
    mcp_protocol.register_resource(
        uri="ui://widget/decision/v1",
        name="Decision Widget",
        description="Renders decision summaries",
        mime_type="text/html;profile=mcp-app",
        content_fn=resources.get_decision_widget
    )
    
    mcp_protocol.register_resource(
        uri="ui://widget/context/v1",
        name="Context Widget",
        description="Displays strategic context",
        mime_type="text/html;profile=mcp-app",
        content_fn=resources.get_context_widget
    )
    
    mcp_protocol.register_resource(
        uri="ui://widget/question/v1",
        name="Question Widget",
        description="Shows open questions",
        mime_type="text/html;profile=mcp-app",
        content_fn=resources.get_question_widget
    )
    
    mcp_protocol.register_resource(
        uri="ui://widget/search/v1",
        name="Search Widget",
        description="Displays search results",
        mime_type="text/html;profile=mcp-app",
        content_fn=resources.get_search_widget
    )
    
    mcp_protocol.register_resource(
        uri="ui://widget/file/v1",
        name="File Widget",
        description="Shows file content",
        mime_type="text/html;profile=mcp-app",
        content_fn=resources.get_file_widget
    )
    
    logger.info("MCP tools and resources initialized")
