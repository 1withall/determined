import anyio
import json
from pathlib import Path

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


@pytest.mark.asyncio
async def test_preprocess_tool_roundtrip(tmp_path: Path) -> None:
    # Use in-process stdio via `uv run python main.py stdio` by launching the adapter
    # through the stdio client helper. We run the server installed in-tree via
    # the 'uv' project runner; this mirrors how editors typically launch MCP
    # servers for local development.
    params = StdioServerParameters(command="uv", args=["run", "python", "main.py", "stdio"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Call preprocess tool with a minimal, valid RequestChange payload
            payload = {
                "summary": "Make a harmless single-line change",
                "unified_diff": "diff --git a/foo.txt b/foo.txt\n--- a/foo.txt\n+++ b/foo.txt\n@@ -1 +1 @@\n-foo\n+bar",
            }

            result = await session.call_tool("preprocess", {"payload": payload})
            # The adapter returns a JSON-encoded text result with summary and unified_diff
            assert len(result.content) > 0
            text = result.content[0].text
            data = json.loads(text)
            assert data["summary"] == payload["summary"]
            assert "unified_diff" in data
