Thu Jan 15 08:30:41 PM EST 2026 - Add human-in-the-loop review API (chat-based) and commit-on-approval

- Added `MCPServer.prepare_human_review` which returns a structured review payload suitable for in-chat presentation (includes `review_id`, `summary`, `unified_diff`, and `metadata`).
- Added `MCPServer.handle_review_response` to accept an in-chat human decision (`approved: bool`) and optional feedback; approved changes are applied and committed into git; rejections are archived with feedback.
- `apply_preprocessed_change(..., commit=True)` will initialize a repo (if needed), stage, and commit changes with a deterministic, metadata-rich commit message.
- Added tests covering approval and rejection flows and error paths; updated docs to describe the in-chat review API.

---

Thu Jan 15 08:03:46 PM EST 2026 - Added local MCP server package

- Implemented `determined.mcp` package with:
  - `schemas.py`: Pydantic models for `RequestChange` and `PreprocessedChange`.
  - `processor.py`: Deterministic preprocessing, analysis, normalization, and safe apply/archival of unified diffs.
  - `server.py`: `MCPServer` class with `preprocess` and `apply_approved` methods (no CLI/UI).
- Added comprehensive tests to achieve 100% coverage for `determined.mcp`.
- Added developer docs: `determined/mcp/README.md` and `docs/mcp/README.md`.
- Ensured all artifacts are archived to an `.mcp`-style archive directory when applying changes.
