"""Tests for the human review in-chat workflow implemented by `MCPServer`.`"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from determined.mcp import MCPServer, preprocess_request
from determined.mcp.schemas import RequestChange


SAMPLE_DIFF = """diff --git a/approve.txt b/approve.txt
index 0000000..e69de29
--- a/approve.txt
+++ b/approve.txt
@@ -0,0 +1 @@
+approved
"""


def test_human_approval_creates_commit_and_archive(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    archive = tmp_path / "arch"
    server = MCPServer(repo_root=repo, archive_root=archive)

    req = RequestChange(summary="Add approve file for tests", unified_diff=SAMPLE_DIFF)
    pre = preprocess_request(req)
    payload = server.prepare_human_review(pre)

    assert "review_id" in payload
    assert payload["summary"].startswith("Add approve file")

    # Simulate human approval
    res = server.handle_review_response(payload["review_id"], approved=True, feedback=None)

    assert res["status"] == "applied"
    archived = Path(res["archived_to"])
    assert (archived / "diff.patch").exists()

    # Verify commit exists
    out = (repo / ".git" / "HEAD").exists()
    assert out is True


def test_handle_unknown_review_raises(tmp_path: Path):
    repo = tmp_path / "repo3"
    repo.mkdir()
    archive = tmp_path / "arch3"
    server = MCPServer(repo_root=repo, archive_root=archive)

    with pytest.raises(KeyError):
        server.handle_review_response("nope", approved=True)


def test_prepare_human_review_requires_change_id(tmp_path: Path):
    repo = tmp_path / "repo4"
    repo.mkdir()
    archive = tmp_path / "arch4"
    server = MCPServer(repo_root=repo, archive_root=archive)

    # Construct a malformed PreprocessedChange without a change_id in metadata
    from determined.mcp.schemas import PreprocessedChange

    bad = PreprocessedChange(summary="bad", unified_diff="diff --git a/a b/b", metadata={})
    with pytest.raises(ValueError):
        server.prepare_human_review(bad)


def test_human_rejection_records_feedback_and_does_not_apply(tmp_path: Path):
    repo = tmp_path / "repo2"
    repo.mkdir()
    archive = tmp_path / "arch2"
    server = MCPServer(repo_root=repo, archive_root=archive)

    req = RequestChange(summary="Try and reject change", unified_diff=SAMPLE_DIFF)
    pre = preprocess_request(req)
    payload = server.prepare_human_review(pre)

    # Simulate human rejection with feedback
    res = server.handle_review_response(payload["review_id"], approved=False, feedback="This is not appropriate")
    assert res["status"] == "rejected"
    decision_path = Path(res["archived_to"]) / "decision.json"
    assert decision_path.exists()
    data = json.loads(decision_path.read_text())
    assert data["approved"] is False
    assert data["feedback"] == "This is not appropriate"

    # Ensure repo unchanged (no .git directory created)
    assert not (repo / ".git").exists()
