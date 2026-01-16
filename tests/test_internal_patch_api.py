"""Direct tests of the internal apply helper using fake patch objects to hit
branches that are difficult to reach via textual diffs alone."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pytest

from determined.mcp.processor import _apply_patchset_to_directory


class FakeLine:
    def __init__(self, kind: str, value: str):
        self.value = value
        self.is_context = kind == "context"
        self.is_added = kind == "added"
        self.is_removed = kind == "removed"


class FakeHunk(list):
    def __init__(self, source_start: int, lines: Iterable[FakeLine]):
        super().__init__(lines)
        self.source_start = source_start


class FakePatchedFile:
    def __init__(self, path: str, is_removed_file: bool, hunks: Iterable[FakeHunk]):
        self.path = path
        self.is_removed_file = is_removed_file
        self.is_added_file = False
        self._hunks = list(hunks)

    def __iter__(self):
        return iter(self._hunks)

    def __len__(self):
        return len(self._hunks)


def test_internal_apply_branches(tmp_path: Path):
    # Case 1: add lines to non-existent file (is_added behavior)
    pf1 = FakePatchedFile("f1.txt", is_removed_file=False, hunks=[FakeHunk(1, [FakeLine("added", "line1\n")])])

    ok, details = _apply_patchset_to_directory([pf1], tmp_path)
    assert ok is True
    assert (tmp_path / "f1.txt").exists()
    assert any(f.get("action") == "added_or_modified" for f in details.get("files", []))

    # Case 2: modify existing file with context and removed lines
    (tmp_path / "f2.txt").write_text("A\nB\nC\n")
    pf2 = FakePatchedFile("f2.txt", is_removed_file=False, hunks=[FakeHunk(2, [FakeLine("context", "A\n"), FakeLine("removed", "B\n")])])
    ok2, details2 = _apply_patchset_to_directory([pf2], tmp_path)
    assert ok2 is True
    content = (tmp_path / "f2.txt").read_text()
    assert "B" not in content
    assert any(f.get("action") == "added_or_modified" for f in details2.get("files", []))

    # Case 3: remove a file when it exists
    (tmp_path / "f3.txt").write_text("X\n")
    pf3 = FakePatchedFile("f3.txt", is_removed_file=True, hunks=[])
    ok3, details3 = _apply_patchset_to_directory([pf3], tmp_path)
    assert ok3 is True
    assert not (tmp_path / "f3.txt").exists()
    assert any(f.get("action") == "removed" for f in details3.get("files", []))


def test_read_and_write_roundtrip(tmp_path: Path):
    # ensure the read branch is used and the write branch is used
    (tmp_path / "rw.txt").write_text("old\n")
    pf = FakePatchedFile("rw.txt", is_removed_file=False, hunks=[FakeHunk(1, [FakeLine("context", "old\n"), FakeLine("added", "new\n")])])
    ok, details = _apply_patchset_to_directory([pf], tmp_path)
    assert ok is True
    assert (tmp_path / "rw.txt").read_text().strip().endswith("new")
    assert any(f.get("action") == "added_or_modified" for f in details.get("files", []))

def test_read_failure_triggers_hunk_error(monkeypatch, tmp_path: Path):
    # Create file and a patched file that would normally read it
    (tmp_path / "rfile.txt").write_text("l1\nl2\n")

    pf = FakePatchedFile("rfile.txt", is_removed_file=False, hunks=[FakeHunk(1, [FakeLine("context", "l1\n")])])

    orig_open = Path.open

    def broken_open(self, *args, **kwargs):
        # Make reads raise
        mode = kwargs.get("mode") or (args[0] if args else None)
        if str(self).endswith("rfile.txt") and (mode == "r" or mode is None):
            raise OSError("simulated read failure")
        return orig_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", broken_open)

    ok, details = _apply_patchset_to_directory([pf], tmp_path)
    # The helper returns True but should record a hunk_apply_error
    assert ok is True
    assert any(f.get("reason") == "hunk_apply_error" or f.get("applied") is False for f in details.get("files", []))
