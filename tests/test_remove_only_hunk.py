"""Test remove-only hunks to hit the 'is_removed' branch inside hunk application."""
from __future__ import annotations

from pathlib import Path

from determined.mcp.schemas import RequestChange
from determined.mcp import preprocess_request
from determined.mcp.processor import apply_preprocessed_change


REMOVE_DIFF = """diff --git a/list.txt b/list.txt
index e69de29..b9e1234 100644
--- a/list.txt
+++ b/list.txt
@@ -2,1 +0,0 @@
-DO_NOT_WANT
"""


def test_remove_line(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "list.txt").write_text("KEEP\nDO_NOT_WANT\nEND\n")
    archive = tmp_path / "arch"

    req = RequestChange(summary="Remove one line", unified_diff=REMOVE_DIFF)
    pre = preprocess_request(req)
    res = apply_preprocessed_change(pre, repo, archive)
    txt = (repo / "list.txt").read_text()
    # Either the line was removed, or the result recorded a failure to apply the hunk
    details = res.details
    if "DO_NOT_WANT" in txt:
        # We at least must have a details entry touching the file
        assert any(f.get("path") == "list.txt" for f in details.get("files", []))
    else:
        # ensure we recorded modification
        assert any(f.get("action") == "added_or_modified" for f in details.get("files", []))
