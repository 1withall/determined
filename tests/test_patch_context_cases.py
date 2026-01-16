"""Tests specifically designed to hit context, addition, and removal branches."""
from __future__ import annotations

from pathlib import Path

from determined.mcp.schemas import RequestChange
from determined.mcp import preprocess_request
from determined.mcp.processor import apply_preprocessed_change


CONTEXT_DIFF = """diff --git a/ctx.txt b/ctx.txt
index 0000000..e69de29
--- a/ctx.txt
+++ b/ctx.txt
@@ -1,3 +1,3 @@
 common
-old
+new
 common2
"""


def test_context_lines_and_hunk_copy(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "ctx.txt").write_text("common\nold\ncommon2\n")
    archive = tmp_path / "arch"

    req = RequestChange(summary="Modify with context lines", unified_diff=CONTEXT_DIFF)
    pre = preprocess_request(req)
    res = apply_preprocessed_change(pre, repo, archive)

    assert (repo / "ctx.txt").read_text().splitlines()[1] == "new"
    # ensure the action was recorded as added_or_modified
    assert any(f.get("action") == "added_or_modified" for f in res.details.get("files", []))
