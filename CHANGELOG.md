Thu Jan 15 08:54:44 PM EST 2026 - Add MCP protocol adapter + VS Code workspace config

- Added `main.py` MCP adapter that exposes `determined.mcp` as a Model Context Protocol server over `stdio` and `streamable-http` transports.
- Added `mcp.json` workspace config registering the `determined` stdio server for IDE/client integration.
- Added `.vscode/settings.json` to point VS Code at the workspace `mcp.json` (non-invasive workspace settings).
- Added `tests/test_main_server.py` validating an in-memory stdio client can call the `preprocess` tool and receive deterministic output.
- Updated `docs/mcp/README.md` with quickstart instructions for running the adapter and configuring VS Code.
- This change adds no remote services and adheres to on-premise usage requirements.

---

Thu Jan 15 08:03:46 PM EST 2026 - Added local MCP server package

- Implemented `determined.mcp` package with:
  - `schemas.py`: Pydantic models for `RequestChange` and `PreprocessedChange`.
  - `processor.py`: Deterministic preprocessing, analysis, normalization, and safe apply/archival of unified diffs.
  - `server.py`: `MCPServer` class with `preprocess` and `apply_approved` methods (no CLI/UI).
- Added comprehensive tests to achieve 100% coverage for `determined.mcp`.
- Added developer docs: `determined/mcp/README.md` and `docs/mcp/README.md`.
- Ensured all artifacts are archived to an `.mcp`-style archive directory when applying changes.
