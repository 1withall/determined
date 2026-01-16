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
