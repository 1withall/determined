# Determined MCP package

Provides a minimal, local-only MCP server implementation intended to be used by
an AI co-developer via a chat-based integration.

Features
- Pydantic-validated `RequestChange` schema
- Deterministic preprocessing (analysis, normalization)
- Safe apply path that writes artifacts to an archive directory
- No CLI or web UI by design

See `docs/mcp` for higher-level design notes.

Basic usage (chat-based integration):

1. Create an `MCPServer` instance pointing to your repo and archive directories:

```python
from pathlib import Path
from determined.mcp import MCPServer

server = MCPServer(repo_root=Path("/path/to/repo"), archive_root=Path("/path/to/.mcp_archive"))
```

2. Preprocess a request (validate + analyze + normalize) and present the
   resulting `PreprocessedChange` to a human for approval:

```python
req = {"summary": "Add a test file", "unified_diff": "diff --git ..."}
pre = server.preprocess(req)
# present `pre` to a human reviewer via chat
```

3. If the human approves the change, call `apply_approved` to execute the
   change and archive artifacts:

```python
res = server.apply_approved(pre)
```

Note: This package intentionally does not expose any CLI or web UI. It is
meant to be used by a chat-based controller that handles human interaction
and decisioning.

Adapter: MCP protocol wrapper
- This repository provides a small MCP protocol adapter in the project root
  (`main.py`) that exposes `determined.mcp` over stdio or HTTP for integration
  with MCP-aware clients and IDEs. See `mcp.json` and `docs/mcp/README.md` for
  details on how to run and integrate with Visual Studio Code.

Human review API (chat-based) 🔧

- `prepare_human_review(pre: PreprocessedChange) -> Dict`:
  - Returns a structured payload suitable for being presented in a chat window.
  - Payload fields: `review_id`, `message`, `summary`, `unified_diff`, `metadata`.
  - Store the returned `review_id` and present `message` + `summary` + `unified_diff` to the human reviewer.

- `handle_review_response(review_id: str, approved: bool, feedback: Optional[str]) -> Dict`:
  - Call this after the human responds in the chat (approved/rejected).
  - If `approved` is True, the change is applied and (by default) committed to the repo; artifacts are archived.
  - If `approved` is False, the rejection and optional feedback are recorded in the archive.

Example (chat controller):

```python
pre = server.preprocess({"summary": "Add test", "unified_diff": "diff --git ..."})
payload = server.prepare_human_review(pre)
# Present payload['message'], payload['summary'], payload['unified_diff'] to human in chat
# Human replies with approved=True/False and optional feedback text
resp = server.handle_review_response(payload['review_id'], approved=True, feedback=None)
```

This approach ensures the human review step happens explicitly in the chat, and
that all decisions and artifacts are deterministically archived for auditing.
