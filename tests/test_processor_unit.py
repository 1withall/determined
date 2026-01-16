"""Unit tests for individual processor utilities to increase coverage."""
from __future__ import annotations

from pathlib import Path

from determined.mcp.processor import (
    analyze_diff,
    compute_change_id,
    normalize_diff,
    apply_preprocessed_change,
)
from determined.mcp.schemas import RequestChange
from determined.mcp import preprocess_request


MODIFY_DIFF = """diff --git a/data.txt b/data.txt
index e69de29..b9e1234 100644
--- a/data.txt
+++ b/data.txt
@@ -1 +1 @@
-OLD LINE
+NEW LINE
"""

ADD_DIFF = """diff --git a/newfile.txt b/newfile.txt
index 0000000..e69de29
--- a/newfile.txt
+++ b/newfile.txt
@@ -0,0 +1 @@
+created
"""


def test_normalize_and_compute_idempotence():
    raw = "line1\nline2"
    norm = normalize_diff(raw)
    assert norm.endswith("\n")
    # idempotence
    assert normalize_diff(norm) == norm


def test_compute_change_id_matches_for_same_input():
    id1 = compute_change_id("summary one", ADD_DIFF)
    id2 = compute_change_id("summary one", ADD_DIFF)
    assert id1 == id2


def test_analyze_diff_add_modify_delete_counts():
    add = analyze_diff(ADD_DIFF)
    assert add["adds"] >= 1

    modify = analyze_diff(MODIFY_DIFF)
    assert modify["modifies"] >= 1

    # Use a delete-style diff that is slightly malformed and exercise parse_error
    delete = """diff --git a/old.txt b/old.txt
--- a/old.txt
+++ /dev/null
@@ -1 +0,0 @@
-removed
"""
    res = analyze_diff(delete)
    assert res.get("parse_error") is True


def test_apply_modify_and_add(tmp_path: Path):
    # Prepare repo
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "data.txt").write_text("OLD LINE\n")
    archive = tmp_path / "arch"

    # Modify existing file
    req = RequestChange(summary="modify data", unified_diff=MODIFY_DIFF)
    pre = preprocess_request(req)
    res = apply_preprocessed_change(pre, repo, archive)
    assert (repo / "data.txt").read_text().strip() == "NEW LINE"

    # Add new file via ADD_DIFF
    req2 = RequestChange(summary="Add new file for tests", unified_diff=ADD_DIFF)
    pre2 = preprocess_request(req2)
    res2 = apply_preprocessed_change(pre2, repo, archive)
    assert (repo / "newfile.txt").read_text().strip() == "created"
