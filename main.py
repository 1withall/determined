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
    # Enable experimental task support so that tools can run as long-lived
    # tasks and request elicitation from humans during execution.
    tool_server.experimental.enable_tasks()

    # Underlying deterministic server instance
    det = MCPServer(repo_root=repo_root, archive_root=archive_root)

    @tool_server.list_tools()
    async def _list_tools() -> list[Tool]:
        """Return the single gated tool exposed to agents: `request_change`.

        This enforces the project spec's gating requirement — the agent only has
        access to a single, tightly constrained tool for making changes to the
        repository (the human review and application steps are performed outside
        of the agent's toolset).
        """
        from mcp.types import ToolExecution, TASK_REQUIRED

        return [
            Tool(
                name="request_change",
                description=(
                    "Submit a change request (summary + unified_diff). "
                    "The server validates and preprocesses the change and runs as a task to "
                    "support elicitation-based approvals."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "minLength": 10, "maxLength": 2000},
                        "unified_diff": {"type": "string", "minLength": 1},
                    },
                    "required": ["summary", "unified_diff"],
                },
                execution=ToolExecution(taskSupport=TASK_REQUIRED),
                outputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "status": {"type": "string"},
                    },
                    "required": ["task_id", "status"],
                },
            ),
        ]

    @tool_server.call_tool()
    async def _call_tool(name: str, arguments: dict[str, Any]):
        """Dispatch tool calls to the deterministic MCPServer.

        Only `request_change` is available to the agent (gated). The tool returns
        a structured review payload that a human reviewer can present in-chat.
        Returning a dict enables structured output validation by the MCP server.
        """
        if name == "request_change":
            # Task-based implementation per the MCP tasks spec.
            from mcp.types import CreateTaskResult, CallToolResult, TextContent
            from mcp.types import TASK_REQUIRED
            from determined.mcp.schemas import RequestChange

            summary = arguments.get("summary")
            unified_diff = arguments.get("unified_diff")
            if summary is None or unified_diff is None:
                raise ValueError("'summary' and 'unified_diff' are required")

            # Validate input via RequestChange
            req = RequestChange(summary=summary, unified_diff=unified_diff)

            # Server request context
            ctx = tool_server.request_context
            # Enforce that the client calls this tool as a task
            ctx.experimental.validate_task_mode(TASK_REQUIRED)

            async def work(task):
                # 1) Ask human to approve use of the tool (separate from the post-preprocess approval)
                use_schema = {
                    "type": "object",
                    "properties": {"approve_use": {"type": "boolean"}},
                    "required": ["approve_use"],
                }
                # Defensive: ensure that the task exists in the store before elicitation to avoid rare races
                for _ in range(10):
                    all_tasks = task.store.get_all_tasks()
                    if any(t.taskId == task.task.taskId for t in all_tasks):
                        break
                    import anyio as _anyio

                    await _anyio.sleep(0.01)

                use_resp = await task.elicit(message="Approve use of request_change tool?", requestedSchema=use_schema)
                if use_resp.action != "accept" or not use_resp.content.get("approve_use"):
                    return CallToolResult(content=[TextContent(type="text", text="Tool use rejected by human")])

                # 2) Run Pre-Approval Pipeline deterministically
                pre = det.preprocess(req.model_dump())

                # 3) Prepare the human review payload (stores pending review)
                review_payload = det.prepare_human_review(pre)

                # 4) Elicit the human review with the processed diff + summary + review id
                review_schema = {
                    "type": "object",
                    "properties": {
                        "approved": {"type": "boolean"},
                        "feedback": {"type": ["string", "null"]},
                    },
                    "required": ["approved"],
                }

                prompt = (
                    f"Request ID: {review_payload['review_id']}\n"
                    f"Summary: {review_payload['summary']}\n\n"
                    "Please review the processed diff and reply with approved=true to apply or approved=false to reject."
                )

                review_resp = await task.elicit(message=prompt, requestedSchema=review_schema)

                # 5) Apply or reject based on the review response
                if review_resp.action == "accept" and review_resp.content.get("approved"):
                    result = det.handle_review_response(review_payload["review_id"], True, review_resp.content.get("feedback"))
                    return CallToolResult(content=[TextContent(type="text", text=json.dumps({"status": "applied", "archived_to": result.get("archived_to")}))])
                else:
                    result = det.handle_review_response(review_payload["review_id"], False, review_resp.content.get("feedback"))
                    return CallToolResult(content=[TextContent(type="text", text=json.dumps({"status": "rejected", "archived_to": result.get("archived_to")}))])

            # Start the task and return the CreateTaskResult immediately
            return await ctx.experimental.run_task(work)

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
