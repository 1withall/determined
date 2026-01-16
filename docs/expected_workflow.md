# EXPECTED WORKFLOW

This is the official expected workflow from tool call to completion for the `determined` MCP server tool:

1. The AI Co-Developer Agent (CDA) invokes the `request_change` tool to make a potentially-destructive change to the codebase/filesystem (CB/FS).
2. The tool call is deterministically validated via Pydantic. Failures result in informative, deterministically-based feedback to CDA with a request to re-submit the tool call.
3. The `diff` is analyzed deterministically (via `unidiff`). This should inform the rest of the pipeline of the **type** of change (edit, create, move, rename, or delete a **single** file or directory) being requested, the file/directory the agent wants to change, the coding language (if a an operation on a file), and any/all other information needed to move forward deterministically. Failures result in informative, deterministically-based feedback to CDA with a request to re-submit the tool call.
4. The `diff` is programmatically linted using an appropriate tool (based on the coding language detected during the analysis conducted in step 3). Failures result in informative, deterministically-based feedback to CDA with a request to re-submit the tool call.
5. The processed `diff` is executed if it passes all previous steps.
6. All artifacts are archived to a highly-structured, .gitignored directory in the repo.
7. All changes are staged and committed to git with a comprehensive, deterministically-synthesized commit message using the raw `summary` and all collected/generated metadata, raw and processed `diff`, etc.
8. Tool call is complete.
