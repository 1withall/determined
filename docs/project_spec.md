# PROJECT SPEC SHEET

This document contains the core principles and philosophies that developers are expected to align the code they write with in this repo.

## Primary Purpose

The primary purpose of this project is to develop an MCP server tool that can be used by an AI co-developing agent (CDA) to make potentially destructive changes to the codebase/filesystem as deterministically and safely as possible while generating a wealth of data that can be capitalized-on later, such as with the creation of extremely useful fine-tuning datasets for the model. This is accomplished through the following methods:

- **GATED**: We manually remove the CDA's access to any other tools that it could use to make potentially destructive changes to the codebase/filesystem so it has no choice but to use this tool.
- **STRUCTURED OUTPUT**: We force the CDA to provide two (2) pieces of information in a highly constrained, Pydantic-validated schema (`request_change`) as the tool call:
  - `summary`: Contains a **MEANINGFUL**, natural language description of why the CDA is requesting the change(s)
  - `unified_diff`: Contains the change(s) (as a unified diff) that the CDA wants to make to the codebase/fs
- **MINIMAL RELIANCE ON LLM**: The CDA will have **EXACTLY** *two* (2) fields to fill out in order to make **any** change to the codebase/fs (create file/dir; edit file; move file/dir; rename file/dir; or delete file/dir). Everything else is handled deterministically/programmatically:
  - Pre-Approval Pipeline: CDA's input (tool call) is validated via Pydantic, then checked for syntax/policy violations, then linted. The unified diff is deterministically analyzed and processed dynamically according to the type of change requested. Any failure during this stage is returned to the agent with deterministically-derived feedback. Only submissions which pass these steps make it to the next step, the Human Review.
  - Human Review: The human will be presented with the validated, well-formed change(s) requested **in the chat**, with an option to approve or reject the request **in the chat**. If the human rejects the request, they will be given the option **in the chat** to provide feedback to the CDA as to why they rejected the request. If the human approves the request, the process immediately moves to the next step, the Post-Approval Pipeline.
  - Post-Approval Pipeline: The human-approved `request_change` is executed, then all artifacts created throughout the process are archived. The changes are all automatically staged and committed with an in-depth, data-rich commit using the agent's `summary` + any/all relevant metadata collected/generated throughout the entire process in the commit message.

## Core Principles

The code in this repo **MUST** align with these principles:

### On-Premise/Local

- This tool must use **OPEN-SOURCE**, **ZERO-AUTH**, **NATIVELY-INSTALLED**, **LOCALLY-SERVED** tools and services **ONLY**.
- "Remote" or "cloud" services are **NOT** authorized in this repo.
- "Containerized" and/or "virtualized" solutions are **NOT** authorized in this repo.
- Any/all "phone-home," "remote telemetry," or other such automated background features of packages **MUST** be proactively **DISABLED**

### Maximal Parameterization

- This tool **MUST** be highly configurable, which means that **ALL** parameters/settings that are available must **ALWAYS** be exposed in the code with sane defaults.

### Maximal Modularity

- This tool must be as **MODULAR** as possible, with clear separation of concerns.

### Organized

- The repo **MUST** be meticulously organized according to modern best practices.
- All artifacts must be assigned semantically-meaningful UUIDs deterministically and persisted to highly-structured, logically-organized directories on a per-file/per-change basis.
