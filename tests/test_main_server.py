import anyio
import json
from pathlib import Path

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from main import create_mcp_adapter




@pytest.mark.asyncio
async def test_tool_declaration_requires_task(tmp_path: Path) -> None:
    server = create_mcp_adapter(repo_root=tmp_path / 'repo', archive_root=tmp_path / 'arch')

    server_to_client_send, server_to_client_receive = anyio.create_memory_object_stream(10)
    client_to_server_send, client_to_server_receive = anyio.create_memory_object_stream(10)

    async def run_server():
        await server.run(client_to_server_receive, server_to_client_send, server.create_initialization_options())

    async def run_client():
        async with ClientSession(server_to_client_receive, client_to_server_send) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {t.name: t for t in tools.tools}
            assert 'request_change' in names
            # execution is a nested object; check the taskSupport field
            exec = names['request_change'].execution
            assert exec is not None
            assert exec.taskSupport == 'required'

    async with anyio.create_task_group() as tg:
        tg.start_soon(run_server)
        tg.start_soon(run_client)
