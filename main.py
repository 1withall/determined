"""Module entrypoint for running the Determined MCP protocol adapter.

This module provides a small stdio and streamable-HTTP wrapper that adapts the
local `determined.mcp.MCPServer` API to the official MCP protocol so IDEs and
clients (e.g., VS Code) can connect to it.

Run examples:
  - stdio: uv run python main.py stdio
  - http:   uv run python main.py http --port 8000
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

import mcp.types as types
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent

from determined.mcp import MCPServer


def create_mcp_adapter(repo_root: Path | None = None, archive_root: Path | None = None) -> Server:
    """Create and return a configured low-level MCP Server that delegates
    operations to the local `determined.mcp.MCPServer` instance.

    Args:
        repo_root: repository root path (defaults to current working directory)
        archive_root: archive root path (defaults to `.mcp_archive` in cwd)

    Returns:
        Configured `mcp.server.lowlevel.Server` instance.
    """
    repo_root = Path.cwd() if repo_root is None else repo_root
    archive_root = Path(".mcp_archive") if archive_root is None else archive_root

    tool_server = Server("determined-mcp")

    # Underlying deterministic server instance
    det = MCPServer(repo_root=repo_root, archive_root=archive_root)

    @tool_server.list_tools()
    async def _list_tools() -> list[Tool]:
        """Return a small set of tools exposed by the adapter."""
        return [
            Tool(
                name="preprocess",
                description="Preprocess a change request (returns processed change JSON)",
                inputSchema={"type": "object", "properties": {"payload": {"type": "object"}}, "required": ["payload"]},
            ),
            Tool(
                name="prepare_human_review",
                description="Prepare a review payload for a preprocessed change (requires metadata.change_id)",
                inputSchema={"type": "object", "properties": {"change_id": {"type": "string"}}, "required": ["change_id"]},
            ),
            Tool(
                name="handle_review_response",
                description="Handle a human review decision (approved:bool)",
                inputSchema={"type": "object", "properties": {"review_id": {"type": "string"}, "approved": {"type": "boolean"}, "feedback": {"type": ["string", "null"]}}, "required": ["review_id", "approved"]},
            ),
        ]

    @tool_server.call_tool()
    async def _call_tool(name: str, arguments: dict[str, Any]):
        """Dispatch tool calls to the deterministic MCPServer. Results are
        returned as a list of TextContent objects (JSON encoded in the text).
        """
        if name == "preprocess":
            payload = arguments.get("payload")
            if payload is None:
                raise ValueError("missing 'payload' argument")
            pre = det.preprocess(payload)
            return [TextContent(type="text", text=json.dumps(pre.model_dump(), ensure_ascii=False))]

        if name == "prepare_human_review":
            change_id = arguments.get("change_id")
            if change_id is None:
                raise ValueError("missing 'change_id' argument")
            pre = det._pending_reviews.get(change_id)
            if pre is None:
                raise KeyError("unknown change_id")
            payload = det.prepare_human_review(pre)
            return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]

        if name == "handle_review_response":
            review_id = arguments.get("review_id")
            approved = arguments.get("approved")
            feedback = arguments.get("feedback")
            if review_id is None or approved is None:
                raise ValueError("'review_id' and 'approved' required")
            result = det.handle_review_response(review_id, bool(approved), feedback)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        raise ValueError(f"unknown tool: {name}")

    return tool_server


async def run_stdio(repo_root: Path | None = None, archive_root: Path | None = None) -> None:
    """Run adapter over stdio (suitable for IDE integration)."""
    server = create_mcp_adapter(repo_root, archive_root)
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())


def run_http(port: int = 8000, repo_root: Path | None = None, archive_root: Path | None = None) -> None:
    """Start a StreamableHTTP FastMCP server mounted with Uvicorn/Starlette.

    This is intentionally small and intended for local development/testing. For
    production usage follow the official MCP FastMCP examples.
    """
    from mcp.server.fastmcp import FastMCP
    from starlette.applications import Starlette
    from starlette.routing import Mount
    import uvicorn

    mcp = FastMCP("determined-mcp", json_response=True)

    # Add a simple health tool for HTTP-mode checks
    @mcp.tool()
    def status() -> dict[str, str]:
        return {"status": "ok", "server": "determined-mcp"}

    # Mount the FastMCP streamable HTTP app
    app = Starlette(routes=[Mount("/", app=mcp.streamable_http_app())],)

    uvicorn.run(app, host="127.0.0.1", port=port)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run Determined MCP protocol adapter")
    sub = p.add_subparsers(dest="mode", required=True)

    s_stdio = sub.add_parser("stdio", help="Run MCP adapter over stdio")
    s_stdio.add_argument("--repo", type=Path, default=None, help="Repository root (defaults to cwd)")
    s_stdio.add_argument("--archive", type=Path, default=None, help="Archive root (defaults to .mcp_archive)")

    s_http = sub.add_parser("http", help="Run a streamable-http MCP server")
    s_http.add_argument("--port", type=int, default=8000, help="Port to bind HTTP server")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    if args.mode == "stdio":
        asyncio.run(run_stdio(args.repo, args.archive))
    elif args.mode == "http":
        run_http(args.port, args.repo, args.archive)


if __name__ == "__main__":
    main()
