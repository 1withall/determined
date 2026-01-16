Thu Jan 15 09:51:23 PM EST 2026 - Add task-based `request_change` workflow with dual human approvals

- Implemented task-capable `request_change` tool (TASK_REQUIRED) that runs as a long-lived task and performs:
  1. Initial human *use* approval (elicitation)
  2. Deterministic Pre-Approval Pipeline (validation, analysis, normalization)
  3. Second human *apply* approval elicitation with processed `diff`, `summary`, and `review_id`
  4. On approval, apply + archive + commit; on rejection, archive rejection metadata
- Added `tests/test_task_workflow.py` exercising the full agent -> human (use + review) -> apply flow using an elicitation callback.
- Updated docs (`docs/mcp/README.md`) with Task-based workflow guidance and examples.
- Added CHANGES and test coverage to ensure 100% coverage remains.

---

Thu Jan 15 08:54:44 PM EST 2026 - Add MCP protocol adapter + VS Code workspace config

- Added `main.py` MCP adapter that exposes `determined.mcp` as a Model Context Protocol server over `stdio` and `streamable-http` transports.
- Added `mcp.json` workspace config registering the `determined` stdio server for IDE/client integration.
- Added `.vscode/settings.json` to point VS Code at the workspace `mcp.json` (non-invasive workspace settings).
- Added `tests/test_main_server.py` validating an in-memory stdio client can call the `preprocess` tool and receive deterministic output.
- Updated `docs/mcp/README.md` with quickstart instructions for running the adapter and configuring VS Code.
- This change adds no remote services and adheres to on-premise usage requirements.

Thu Jan 15 08:03:46 PM EST 2026 - Added local MCP server package

- Implemented `determined.mcp` package with:
  - `schemas.py`: Pydantic models for `RequestChange` and `PreprocessedChange`.
  - `processor.py`: Deterministic preprocessing, analysis, normalization, and safe apply/archival of unified diffs.
  - `server.py`: `MCPServer` class with `preprocess` and `apply_approved` methods (no CLI/UI).
- Added comprehensive tests to achieve 100% coverage for `determined.mcp`.
- Added developer docs: `determined/mcp/README.md` and `docs/mcp/README.md`.
- Ensured all artifacts are archived to an `.mcp`-style archive directory when applying changes.
