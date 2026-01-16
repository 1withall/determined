Thu Jan 15 08:03:46 PM EST 2026 - Added local MCP server package

- Implemented `determined.mcp` package with:
  - `schemas.py`: Pydantic models for `RequestChange` and `PreprocessedChange`.
  - `processor.py`: Deterministic preprocessing, analysis, normalization, and safe apply/archival of unified diffs.
  - `server.py`: `MCPServer` class with `preprocess` and `apply_approved` methods (no CLI/UI).
- Added comprehensive tests to achieve 100% coverage for `determined.mcp`.
- Added developer docs: `determined/mcp/README.md` and `docs/mcp/README.md`.
- Ensured all artifacts are archived to an `.mcp`-style archive directory when applying changes.
