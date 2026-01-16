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
