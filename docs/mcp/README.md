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


## Task-based workflow (recommended)

This adapter supports the MCP experimental "tasks" workflow which lets a
single tool call remain active while waiting for human elicitation responses.
This is the preferred flow when you want the agent to remain "locked" into a
single request and avoid repeated tool calls when user input is required.

High-level flow:

1. Agent calls the `request_change` tool as a *task* (the adapter requires task mode for this tool).
2. The server starts a task and first elicits consent to *use* the tool. The human can accept/decline the use of the tool.
3. If the human accepts, the server runs the deterministic Pre-Approval Pipeline on the provided diff (validation, analysis, normalization).
4. The server prepares a human-review payload (`review_id`, `summary`, `unified_diff`, `metadata`) and elicits final approval/rejection from the human for *applying* the change.
5. If approved, the server applies the change, archives artifacts, and commits the change; if rejected, a rejection record is archived.

Example (client-side) - use `ClientSession.experimental.call_tool_as_task(...)` and
supply an `elicitation_callback` that responds to the two elicitation prompts
(approve use, then approve/reject the processed diff). See `tests/test_task_workflow.py` for a working example.


## Quickstart: Running the Determined MCP adapter (stdio)

This repository includes a small adapter that exposes the local,
deterministic `MCPServer` implementation over the Model Context Protocol so
that MCP-aware clients and IDEs (e.g., Visual Studio Code or other MCP
extensions) can connect to it.

Run the stdio server (suitable for editor integrations):

    uv run python main.py stdio

The adapter exposes a single, gated tool for AI agents:
- `request_change` — Accepts `summary` and `unified_diff` and runs the full
  deterministic pre-approval pipeline. Returns a structured review payload
  (`review_id`, `message`, `summary`, `unified_diff`, `metadata`) that must be
  presented to a human for approval. Human approval/rejection is handled by
  calling the repository-side APIs (e.g., the `MCPServer.handle_review_response`
  method) — these steps are intentionally separated from the agent-facing
  tool to enforce gating.

Human operators can still call the `MCPServer` API directly (e.g., via a chat
controller or an administrative tool) to perform `prepare_human_review` and
`handle_review_response` actions when required.

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
