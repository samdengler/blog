"""A stateless MCP server over Streamable HTTP, using only the standard library.

Each POST carries one JSON-RPC message (or a batch) and gets one JSON response.
There are no sessions and no server-to-client stream, which is all three
read-only tools need.
"""
import json

import blog_tools

SUPPORTED_VERSIONS = ["2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"]
SERVER_INFO = {"name": "dengler-blog", "title": "Sam Dengler's blog", "version": "1.0.0"}
INSTRUCTIONS = ("Tools for reading Sam Dengler's blog. Use search_posts or list_posts to find a post, "
                "then get_post for its full text. Cite the post's url when you use its content.")


def _error(message_id, code, text):
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": text}}


def _call_tool(params):
    name = params.get("name")
    tool = next((t for t in blog_tools.TOOLS if t["name"] == name), None)
    if tool is None:
        raise LookupError(f"Unknown tool: {name}")
    arguments = params.get("arguments") or {}
    allowed = tool["inputSchema"]["properties"]
    try:
        unknown = sorted(set(arguments) - set(allowed))
        if unknown:
            raise ValueError("Unknown argument(s): " + ", ".join(unknown))
        missing = [k for k in tool["inputSchema"].get("required", []) if not arguments.get(k)]
        if missing:
            raise ValueError("Missing required argument(s): " + ", ".join(missing))
        result = tool["call"](**arguments)
    except Exception as problem:  # reported to the model as a tool error, not a protocol error
        return {"content": [{"type": "text", "text": str(problem)}], "isError": True}
    if name == "get_post":
        text = result["markdown"] + f"\n\nSource: {result['url']} ({result['date']})\n"
    else:
        text = json.dumps(result, indent=2, ensure_ascii=False)
    return {"content": [{"type": "text", "text": text}], "isError": False}


def handle_message(message):
    """Answer one JSON-RPC message. Returns None for notifications and responses."""
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return _error(None, -32600, "Invalid JSON-RPC message")
    if "method" not in message or "id" not in message:
        return None
    message_id, method, params = message["id"], message["method"], message.get("params") or {}
    if method == "initialize":
        asked = params.get("protocolVersion")
        result = {
            "protocolVersion": asked if asked in SUPPORTED_VERSIONS else SUPPORTED_VERSIONS[0],
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
            "instructions": INSTRUCTIONS,
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": [{k: v for k, v in t.items() if k != "call"} for t in blog_tools.TOOLS]}
    elif method == "tools/call":
        try:
            result = _call_tool(params)
        except LookupError as problem:
            return _error(message_id, -32602, str(problem))
    else:
        return _error(message_id, -32601, f"Method not found: {method}")
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def handle_http(method, body):
    """Answer one HTTP request. Returns (status, headers, body text)."""
    headers = {"Content-Type": "application/json"}
    if method != "POST":
        # No server-initiated stream and no sessions to end.
        return 405, {**headers, "Allow": "POST"}, json.dumps(_error(None, -32600, "Use POST"))
    try:
        payload = json.loads(body or "")
    except ValueError:
        return 400, headers, json.dumps(_error(None, -32700, "Parse error"))
    if isinstance(payload, list):
        answers = [a for a in map(handle_message, payload) if a is not None]
        return (200, headers, json.dumps(answers)) if answers else (202, {}, "")
    answer = handle_message(payload)
    return (200, headers, json.dumps(answer)) if answer is not None else (202, {}, "")
