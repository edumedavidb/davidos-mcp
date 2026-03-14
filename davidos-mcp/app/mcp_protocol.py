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
    output_template: str = None,
    read_only: bool = False
):
    """Register an MCP tool with dual metadata format support."""
    tool_def = {
        "name": name,
        "description": description,
        "inputSchema": input_schema,
        "handler": handler,
        "_meta": {}
    }
    
    # Add widget resource URI if provided (both MCP standard and OpenAI alias)
    if output_template:
        tool_def["_meta"]["ui"] = {
            "resourceUri": output_template
        }
        tool_def["_meta"]["openai/outputTemplate"] = output_template
    
    # Add read-only annotation if applicable
    if read_only:
        tool_def["annotations"] = {
            "readOnlyHint": True
        }
    
    TOOLS[name] = tool_def
    logger.info(f"Registered tool: {name} (read_only={read_only})")


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
        tool_desc = {
            "name": tool["name"],
            "description": tool["description"],
            "inputSchema": tool["inputSchema"],
            "_meta": tool.get("_meta", {})
        }
        # Include annotations if present
        if "annotations" in tool:
            tool_desc["annotations"] = tool["annotations"]
        tools.append(tool_desc)
    return {"tools": tools}


def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """MCP call_tool method with validation and logging."""
    import time
    
    if name not in TOOLS:
        raise ValueError(f"Unknown tool: {name}")
    
    tool = TOOLS[name]
    handler = tool["handler"]
    
    # Log tool execution start
    logger.info(f"Executing tool: {name}")
    logger.debug(f"Tool arguments: {arguments}")
    start_time = time.time()
    
    try:
        result = handler(**arguments)
        
        # Validate response structure
        if not isinstance(result, dict):
            raise ValueError(f"Tool {name} must return a dict, got {type(result)}")
        
        if "content" not in result:
            raise ValueError(f"Tool {name} response missing required field: content")
        
        if not isinstance(result.get("content"), list):
            raise ValueError(f"Tool {name} content must be an array")
        
        if "structuredContent" in result and not isinstance(result["structuredContent"], dict):
            raise ValueError(f"Tool {name} structuredContent must be an object")
        
        if "_meta" in result and not isinstance(result["_meta"], dict):
            raise ValueError(f"Tool {name} _meta must be an object")
        
        # Log successful execution
        execution_time = time.time() - start_time
        logger.info(f"Tool {name} completed successfully in {execution_time:.3f}s")
        
        return result
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Tool {name} failed after {execution_time:.3f}s: {e}")
        logger.exception("Tool execution error details:")
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
    """MCP list_prompts method (optional, future-safe stub)."""
    # Return empty list for now - prompts not yet implemented
    logger.debug("list_prompts called - returning empty list (not yet implemented)")
    return {"prompts": []}


def get_prompt(name: str) -> Dict[str, Any]:
    """MCP get_prompt method (optional, future-safe stub)."""
    # Return error for now - prompts not yet implemented
    logger.warning(f"get_prompt called for '{name}' - not yet implemented")
    raise ValueError(f"Prompts not yet implemented")


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
