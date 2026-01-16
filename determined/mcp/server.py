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

import json

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
      2. present the result to a human for approval in-chat using the
         `prepare_human_review` payload
      3. call `handle_review_response` with the user's decision (approved: bool)
    """

    def __init__(self, repo_root: Path, archive_root: Path):
        self.repo_root = repo_root
        self.archive_root = archive_root
        self.archive_root.mkdir(parents=True, exist_ok=True)
        # pending reviews map change_id -> PreprocessedChange
        self._pending_reviews: Dict[str, PreprocessedChange] = {}

    def preprocess(self, payload: Dict) -> PreprocessedChange:
        req = RequestChange(**payload)
        pre = preprocess_request(req)
        return pre

    def prepare_human_review(self, pre: PreprocessedChange) -> Dict:
        """Return a structured review payload suitable for presentation in-chat.

        The payload contains:
        - `review_id`: deterministic id for the change (same as change_id)
        - `message`: a short textual message for the human reviewer
        - `summary`, `unified_diff`, `metadata` fields for easy consumption

        The chat controller is responsible for presenting `message` and the
        structured fields to the human, and then calling
        `handle_review_response` with the human's decision.
        """
        review_id = pre.metadata.get("change_id")
        if not review_id:
            raise ValueError("pre must contain a change_id in metadata")
        # Build an elicitation schema to support in-chat human approvals. This
        # schema is a JSON Schema fragment that clients can use to render a
        # form or validate the user's response before calling back into
        # `handle_review_response`.
        elicitation_schema = {
            "type": "object",
            "properties": {
                "approved": {"type": "boolean", "description": "Approval decision"},
                "feedback": {"type": ["string", "null"], "description": "Optional reviewer feedback"},
            },
            "required": ["approved"],
        }

        payload = {
            "review_id": review_id,
            "message": (
                f"Change request: {pre.summary}\n\n"
                "Please review the processed diff and metadata below and reply with:"
                " `{""approved"": true}` to apply or `{""approved"": false}` to reject."
            ),
            "summary": pre.summary,
            "unified_diff": pre.unified_diff,
            "metadata": pre.metadata,
            "elicitation": elicitation_schema,
            "reply_instructions": (
                "Submit your response as a JSON object matching `elicitation` (fields: approved, optional feedback),"
                " or invoke the repository admin API to call `handle_review_response(review_id, approved, feedback)`."
            ),
        }
        # store as pending until decision is made
        self._pending_reviews[review_id] = pre
        return payload

    def handle_review_response(self, review_id: str, approved: bool, feedback: str | None = None) -> Dict:
        """Handle a human review response.

        If approved, the change is applied and committed to git (repo init if needed)
        and the apply artifacts are archived. If rejected, a rejection record
        containing optional feedback is written to the archive.

        Returns a dictionary with the result: either apply result metadata or
        rejection metadata.
        """
        pre = self._pending_reviews.pop(review_id, None)
        if pre is None:
            raise KeyError("unknown review_id")

        # Archive the decision payload for auditing
        decision = {"review_id": review_id, "approved": approved, "feedback": feedback}
        decision_path = self.archive_root / review_id
        decision_path.mkdir(parents=True, exist_ok=True)
        (decision_path / "decision.json").write_text(json.dumps(decision, indent=2), encoding="utf-8")

        if not approved:
            return {"status": "rejected", "archived_to": str(decision_path)}

        # Apply and commit the change;
        result = apply_preprocessed_change(pre, self.repo_root, self.archive_root, commit=True)
        # record apply + decision together
        (decision_path / "apply_summary.json").write_text(json.dumps(result.details, indent=2), encoding="utf-8")
        return {"status": "applied", "archived_to": str(result.archived_to), "apply_details": result.details}

    def apply_approved(self, pre: PreprocessedChange) -> ApplyResult:
        return apply_preprocessed_change(pre, self.repo_root, self.archive_root)


__all__ = ["MCPServer"]
