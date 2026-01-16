"""Lightweight, local-only MCP server core.

This module defines an in-process server API that can be used by a chat-based
controller to present changes for human approval, and to apply approved
changes deterministically.

The server intentionally does not start HTTP listeners or CLIs by default to
adhere to the project's restriction on UIs.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

from .processor import (
    ApplyResult,
    apply_preprocessed_change,
    preprocess_request,
)
from .schemas import PreprocessedChange, RequestChange


class MCPServer:
    """Core MCP server that exposes deterministic operations.

    Usage pattern (chat-based):
      1. call `preprocess` with a dict-like request -> receives `PreprocessedChange`
      2. present the result to a human for approval out-of-band
      3. if approved, call `apply_approved` with the `PreprocessedChange`
    """

    def __init__(self, repo_root: Path, archive_root: Path):
        self.repo_root = repo_root
        self.archive_root = archive_root
        self.archive_root.mkdir(parents=True, exist_ok=True)

    def preprocess(self, payload: Dict) -> PreprocessedChange:
        req = RequestChange(**payload)
        pre = preprocess_request(req)
        return pre

    def apply_approved(self, pre: PreprocessedChange) -> ApplyResult:
        return apply_preprocessed_change(pre, self.repo_root, self.archive_root)


__all__ = ["MCPServer"]
