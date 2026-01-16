Determined MCP Server

This repository includes a minimal, local-only implementation of a Model
Context Protocol (MCP) server in `determined.mcp`. The implementation is
intentionally chat-driven (no CLI or web UI), Pydantic-validated, and
conservative about applying changes to the repository.

See `determined/mcp/README.md` and `docs/mcp/README.md` for more details.

## Quickstart: Running the MCP adapter

Run the stdio adapter (suitable for connecting from an MCP-aware IDE or client):

    uv run python main.py stdio

Or run an HTTP-mode adapter for testing:

    uv run python main.py http --port 8000
