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
