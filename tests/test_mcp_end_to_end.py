"""End-to-end tests for the MCP server implementation."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from determined.mcp import MCPServer, preprocess_request
from determined.mcp.schemas import RequestChange


SAMPLE_DIFF = """diff --git a/hello.txt b/hello.txt
index 0000000..e69de29
--- a/hello.txt
+++ b/hello.txt
@@ -0,0 +1,2 @@
+Hello world
+This is a test
"""


def test_validation_rejects_non_diff():
    with pytest.raises(Exception):
        RequestChange(summary="short but valid", unified_diff="this is not a diff")


def test_preprocess_and_analyze(tmp_path: Path):
    req = RequestChange(summary="Add hello file for tests", unified_diff=SAMPLE_DIFF)
    pre = preprocess_request(req)
    assert "change_id" in pre.metadata
    assert pre.metadata["adds"] >= 1
    assert pre.unified_diff.endswith("\n")


def test_apply_changes_and_archive(tmp_path: Path):
    # Prepare a fake repo
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".gitignore").write_text(".mcp_archive\n")

    # Archive dir
    archive = tmp_path / "arch"
    server = MCPServer(repo_root=repo, archive_root=archive)

    req = RequestChange(summary="Add hello file for tests", unified_diff=SAMPLE_DIFF)
    pre = server.preprocess(req.model_dump())
    res = server.apply_approved(pre)

    assert res.applied is True
    assert (res.archived_to / "diff.patch").exists()
    assert (repo / "hello.txt").exists()
    content = (repo / "hello.txt").read_text()
    assert "Hello world" in content

    # Ensure artifacts are JSON-serializable in the archive
    details = json.loads((res.archived_to / "apply_details.json").read_text())
    assert isinstance(details, dict)


def test_apply_nonexistent_delete(tmp_path: Path):
    # Create a diff that deletes a file that doesn't exist
    delete_diff = """diff --git a/nope.txt b/nope.txt
index 0000000..0000000
--- a/nope.txt
+++ /dev/null
@@ -1 +0,0 @@
-This file does not exist
"""
    repo = tmp_path / "repo2"
    repo.mkdir()
    archive = tmp_path / "arch2"
    server = MCPServer(repo_root=repo, archive_root=archive)

    req = RequestChange(summary="Attempt delete", unified_diff=delete_diff)
    pre = server.preprocess(req.model_dump())
    res = server.apply_approved(pre)
    # Delete of nonexistent file should be recorded as not applied but overall process should finish
    assert res.applied is True
    details = json.loads((res.archived_to / "apply_details.json").read_text())
    assert any(f.get("reason") == "file_not_found" for f in details.get("files", []))
