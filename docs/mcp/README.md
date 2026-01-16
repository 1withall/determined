# MCP Server Design Notes

This directory contains design notes and developer-facing documentation for the
local, deterministic MCP server implementation in `determined.mcp`.

Key design goals
- On-premise / local-only: no remote services used by default
- Maximal modularity: clear separation between `schemas`, `processor`, and `server`
- Deterministic pre-approval pipeline: `preprocess_request` for producing
  `PreprocessedChange` objects suitable for human review
- Archiving of all artifacts into a git-ignored archive directory

Security Notes
- The implementation is careful and conservative about applying patches.
- For large or risky changes, prefer a manual review of the resulting patchset
  prior to invoking `apply_approved`.

Human Review & Auditing
- Use `MCPServer.prepare_human_review` to build a chat-friendly payload that
  includes `summary`, `unified_diff`, and `metadata` to present to a human.
- Use `MCPServer.handle_review_response` to record the human's decision. If
  approved, the change will be applied and committed; if rejected, feedback is
  recorded in the archive for deterministic auditability.
- All decisions, diffs, and apply-details are archived under `.mcp_archive/<change_id>/`.


## Quickstart: Running the Determined MCP adapter (stdio)

This repository includes a small adapter that exposes the local,
deterministic `MCPServer` implementation over the Model Context Protocol so
that MCP-aware clients and IDEs (e.g., Visual Studio Code or other MCP
extensions) can connect to it.

Run the stdio server (suitable for editor integrations):

    uv run python main.py stdio

The adapter exposes the following tools (examples):
- `preprocess` — Accepts a `RequestChange`-like payload and returns a
  processed `PreprocessedChange` encoded as JSON inside a text content block.
- `prepare_human_review` — Given a `change_id` will produce a review payload
  that is suitable for in-chat human presentation.
- `handle_review_response` — Accepts `review_id`, `approved` (bool), and
  optional `feedback` and will either apply the change or record a rejection.

### Integrating with Visual Studio Code

To make it easy to use this adapter in VS Code, the repository contains a
root-level `mcp.json` that registers a `determined` stdio server. If you use
an MCP-aware VS Code extension, it should automatically discover `mcp.json` in
this workspace and make the server available for selection.

If your extension does not automatically detect the file, use the command
palette (Cmd/Ctrl+Shift+P) and choose **MCP: Add server...** then enter the
appropriate connection details (for stdio use `uv run python main.py stdio`)
or point it at `http://localhost:<port>` if you prefer to run the adapter in
HTTP mode (`uv run python main.py http --port 8000`).
