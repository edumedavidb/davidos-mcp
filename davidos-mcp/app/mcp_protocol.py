"""MCP Protocol implementation for DavidOS."""

import logging
from typing import Dict, Any, Callable, List
from datetime import datetime

from .file_manager import FileManager

logger = logging.getLogger("davidos-mcp")

# Global registries
TOOLS: Dict[str, Dict[str, Any]] = {}
RESOURCES: Dict[str, Dict[str, Any]] = {}
PROMPTS: Dict[str, Dict[str, Any]] = {}


def register_tool(
    name: str,
    description: str,
    input_schema: Dict[str, Any],
    handler: Callable,
    output_template: str = None
):
    """Register an MCP tool."""
    TOOLS[name] = {
        "name": name,
        "description": description,
        "inputSchema": input_schema,
        "handler": handler,
        "_meta": {
            "ui": {
                "resourceUri": output_template
            } if output_template else {}
        }
    }
    logger.info(f"Registered tool: {name}")


def register_resource(uri: str, name: str, description: str, mime_type: str, content_fn: Callable):
    """Register an MCP resource (widget)."""
    RESOURCES[uri] = {
        "uri": uri,
        "name": name,
        "description": description,
        "mimeType": mime_type,
        "content_fn": content_fn
    }
    logger.info(f"Registered resource: {uri}")


def list_tools() -> Dict[str, List[Dict[str, Any]]]:
    """MCP list_tools method."""
    tools = []
    for tool in TOOLS.values():
        tools.append({
            "name": tool["name"],
            "description": tool["description"],
            "inputSchema": tool["inputSchema"],
            "_meta": tool.get("_meta", {})
        })
    return {"tools": tools}


def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """MCP call_tool method."""
    if name not in TOOLS:
        raise ValueError(f"Unknown tool: {name}")
    
    tool = TOOLS[name]
    handler = tool["handler"]
    
    logger.info(f"Calling tool: {name} with args: {arguments}")
    
    try:
        result = handler(**arguments)
        return result
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        raise


def list_resources() -> Dict[str, List[Dict[str, Any]]]:
    """MCP list_resources method."""
    resources = []
    for resource in RESOURCES.values():
        resources.append({
            "uri": resource["uri"],
            "name": resource["name"],
            "description": resource["description"],
            "mimeType": resource["mimeType"]
        })
    return {"resources": resources}


def read_resource(uri: str) -> Dict[str, Any]:
    """MCP read_resource method."""
    if uri not in RESOURCES:
        raise ValueError(f"Unknown resource: {uri}")
    
    resource = RESOURCES[uri]
    content_fn = resource["content_fn"]
    
    logger.info(f"Reading resource: {uri}")
    
    content = content_fn()
    
    return {
        "uri": uri,
        "mimeType": resource["mimeType"],
        "text": content
    }


def list_prompts() -> Dict[str, List[Dict[str, Any]]]:
    """MCP list_prompts method (optional)."""
    prompts = []
    for prompt in PROMPTS.values():
        prompts.append({
            "name": prompt["name"],
            "description": prompt["description"]
        })
    return {"prompts": prompts}


def get_prompt(name: str) -> Dict[str, Any]:
    """MCP get_prompt method (optional)."""
    if name not in PROMPTS:
        raise ValueError(f"Unknown prompt: {name}")
    
    return PROMPTS[name]


def handle_mcp_request(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Route MCP protocol requests to appropriate handlers."""
    
    if method == "list_tools":
        return list_tools()
    
    elif method == "call_tool":
        name = params.get("name")
        arguments = params.get("arguments", {})
        return call_tool(name, arguments)
    
    elif method == "list_resources":
        return list_resources()
    
    elif method == "read_resource":
        uri = params.get("uri")
        return read_resource(uri)
    
    elif method == "list_prompts":
        return list_prompts()
    
    elif method == "get_prompt":
        name = params.get("name")
        return get_prompt(name)
    
    else:
        raise ValueError(f"Unknown MCP method: {method}")
