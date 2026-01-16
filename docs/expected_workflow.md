# EXPECTED WORKFLOW

This is the official expected workflow from tool call to completion for the `determined` MCP server tool:

1. The AI Co-Developer Agent (CDA) invokes the `determined` `request_change` tool by completing the `summary` and `unified_diff` fields in order to make a potentially-destructive change (PDC) to the codebase/filesystem (CB/FS).
2. The tool call is deterministically validated via Pydantic. Failures result in deterministically-based feedback to CDA with a request to re-submit the tool call.
3. The `unified_diff` is analyzed deterministically (via `unidiff`). Failures result in deterministically-based feedback to CDA with a request to re-submit the tool call.
4. The `unified_diff` is automatically normalized/linted. Failures result in deterministically-based feedback to CDA with a request to re-submit the tool call.
5. The `unified_diff` is pre-processed dynamically based on the results of the analysis conducted in step 3.
6. Once the tool call has been pre-processed, the raw `summary` and processed `unified_diff` are presented to the human in the chat window with the option to approve or reject the request. Failures result in deterministically-based feedback to CDA with a request to re-submit the tool call.
7. Either:
   - the human approves the request, in which case the Post-Approval Pipeline begins; OR
   - the human rejects the request, in which case the human will be given the opportunity in the chat window to voluntarily provide feedback, and then the tool call will be returned as a failure along with the human's feedback (if any).
8. The processed diff is executed.
9. All artifacts are archived to a highly-structured, .gitignored directory in the repo.
10. All changes are staged and committed to git with a comprehensive, deterministically-synthesized commit message using the raw `summary` and all collected/generated metadata, diff, etc.
11. Tool call is complete.
