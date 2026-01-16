"""MCP request/response schemas.

Provides Pydantic models used throughout the MCP server implementation.
"""
from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field
from pydantic import field_validator


class RequestChange(BaseModel):
    """A deterministic, minimal schema for requesting filesystem changes.

    Fields:
        summary: A concise, meaningful natural language description of the change.
        unified_diff: A unified diff (text) describing the change to the repo.
    """

    summary: str = Field(..., min_length=10, max_length=2000)
    unified_diff: str = Field(..., min_length=1)

    @field_validator("summary")
    def summary_must_be_meaningful(cls, v: str) -> str:  # pragma: no cover - trivial
        if not v.strip():
            raise ValueError("summary must be non-empty")
        return v

    @field_validator("unified_diff")
    def unified_diff_must_look_like_a_diff(cls, v: str) -> str:
        v_stripped = v.lstrip()
        if not (v_stripped.startswith("diff --git") or v_stripped.startswith("--- ") or v_stripped.startswith("*** ")):
            raise ValueError("unified_diff does not look like a unified diff")
        return v


class PreprocessedChange(BaseModel):
    """Represents a preprocessed change that is ready to be presented for human approval.

    This is deterministic output from the pre-approval pipeline.
    """

    summary: str
    unified_diff: str
    metadata: Dict[str, Any]


__all__ = ["RequestChange", "PreprocessedChange"]
