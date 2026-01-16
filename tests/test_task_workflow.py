import anyio
import json
from pathlib import Path

import pytest

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, CreateTaskResult

from main import create_mcp_adapter


@pytest.mark.anyio
async def test_request_change_task_workflow(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    archive = tmp_path / "arch"
    archive.mkdir()

    server = create_mcp_adapter(repo_root=repo, archive_root=archive)

    server_to_client_send, server_to_client_receive = anyio.create_memory_object_stream(10)
    client_to_server_send, client_to_server_receive = anyio.create_memory_object_stream(10)

    async def run_server():
        await server.run(client_to_server_receive, server_to_client_send, server.create_initialization_options())

    async def elicitation_callback(context, params):
        # Respond to the two elicitation steps: initial "Approve use" and post-preprocess review
        msg = params.message.lower() if hasattr(params, "message") and params.message else ""
        if "approve use" in msg:
            return type("E", (), {"action": "accept", "content": {"approve_use": True}})()
        if "request id" in msg or "please review" in msg:
            return type("E", (), {"action": "accept", "content": {"approved": True}})()
        # default: accept
        return type("E", (), {"action": "accept", "content": {}})()

    async def run_client():
        # Connect using in-memory streams to the in-process server
        async with ClientSession(server_to_client_receive, client_to_server_send, elicitation_callback=elicitation_callback) as session:
            await session.initialize()

            payload = {
                "summary": "Add approve file via task",
                "unified_diff": "diff --git a/approve_task.txt b/approve_task.txt\nindex 0000000..e69de29\n--- a/approve_task.txt\n+++ b/approve_task.txt\n@@ -0,0 +1 @@\n+task-approved\n",
            }

            # Call tool as task
            result = await session.experimental.call_tool_as_task("request_change", payload)
            task_id = result.task.taskId
            # Allow the server a brief moment to create the task entry
            await anyio.sleep(0.05)

            # Poll until completion (poll_task may raise if the server hasn't yet created the task; retry via brief sleeps)
            async for status in session.experimental.poll_task(task_id):
                if status.status in ("completed", "failed"):
                    break

# Check that repo was updated and a commit exists
                assert (repo / ".git").exists()

                # Ensure the archive contains an apply record (diff.patch) for the request
                found = False
                for child in archive.iterdir():
                    if (child / "diff.patch").exists():
                        found = True
                        break
                assert found is True

    async with anyio.create_task_group() as tg:
        tg.start_soon(run_server)
        tg.start_soon(run_client)
