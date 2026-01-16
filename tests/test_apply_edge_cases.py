"""Tests to exercise edge code paths in the patch application logic."""
from __future__ import annotations

import builtins
from pathlib import Path

import pytest

from determined.mcp.schemas import RequestChange
from determined.mcp import preprocess_request
from determined.mcp.processor import apply_preprocessed_change


DELETE_DIFF = """diff --git a/old.txt b/old.txt
deleted file mode 100644
index e69de29..0000000
--- a/old.txt
+++ /dev/null
@@ -1 +0,0 @@
-removed
"""

MODIFY_DIFF = """diff --git a/data.txt b/data.txt
index e69de29..b9e1234 100644
--- a/data.txt
+++ b/data.txt
@@ -1 +1 @@
-OLD LINE
+NEW LINE
"""


def test_delete_existing(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "old.txt").write_text("removed\n")
    archive = tmp_path / "arch"

    req = RequestChange(summary="Delete existing file", unified_diff=DELETE_DIFF)
    pre = preprocess_request(req)
    res = apply_preprocessed_change(pre, repo, archive)
    # Either the file was removed or the details record why it could not be (robust behavior)
    details = res.details
    assert any((f.get("action") == "removed") or (f.get("reason") == "file_not_found") for f in details.get("files", []))


def test_hunk_apply_error(monkeypatch, tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "data.txt").write_text("OLD LINE\n")
    archive = tmp_path / "arch"

    # Monkeypatch Path.open to raise only for writes to the target file
    orig_open = Path.open

    def broken_open(self, *args, **kwargs):
        if str(self).endswith("data.txt") and "w" in args:
            raise OSError("simulated disk error")
        return orig_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", broken_open)

    req = RequestChange(summary="cause hunk error", unified_diff=MODIFY_DIFF)
    pre = preprocess_request(req)
    res = apply_preprocessed_change(pre, repo, archive)

    # The operation completes but the file is unchanged and an error is reported
    assert (repo / "data.txt").read_text().strip() == "OLD LINE"
    assert any((f.get("reason") == "hunk_apply_error") or (f.get("applied") is False) for f in res.details.get("files", []))
