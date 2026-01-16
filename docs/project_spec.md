# PROJECT SPEC SHEET

This document contains the core principles and philosophies that developers are expected to align the code they write with in this repo.

## Primary Purpose

The primary purpose of this project is to develop an MCP server tool that can be used by an AI co-developing agent (CDA) to make potentially destructive changes to the codebase/filesystem as deterministically and safely as possible while generating a wealth of data that can be capitalized-on later, such as with the creation of extremely useful fine-tuning datasets for the model. This is accomplished through the following methods:

- **STRUCTURED OUTPUT**: We force the CDA to provide two (2) pieces of information in a highly constrained, Pydantic-validated schema (`request_change`) as the tool call:
  - `summary`: Contains a **MEANINGFUL**, natural language description of why the CDA is requesting the change(s). This field **MUST** be constrained to force the LLM to provide a **MEANINGFUL** summary of the changes it intends to make.
  - `diff`: Contains the change that the CDA wants to make to the codebase/fs in the form of a diff.
- **MINIMAL RELIANCE ON LLM**: The CDA will have **EXACTLY** *two* (2) fields to fill out in order to make **any** change to the codebase/fs (create file/dir; edit file; move file/dir; rename file/dir; or delete file/dir). Everything else is handled deterministically/programmatically. This **drastically** reduces the contact surface while allowing for deterministic code to drive the vast majority of processes within the tool's pipeline.

## Secondary Purpose

The secondary purpose of this tool is to generate/capture as much data from the process as possible throughout the process that can help inform QA and for potential use in future fine-tuning datasets to enhance the LLM's future capabilities. This data **MUST** be maintained in a highly structured, meticulously-organized (programmatically) manner in a .gitignored `.determined` sub-directory in the project root.

## Core Principles

The code in this repo **MUST** align with these principles:

### On-Premise/Local

- This tool must use **OPEN-SOURCE**, **ZERO-AUTH**, **NATIVELY-INSTALLED**, **LOCALLY-SERVED** tools and services **ONLY**.
- "Remote" or "cloud" services are **NOT** authorized in this repo.
- "Containerized" and/or "virtualized" solutions are **NOT** authorized in this repo.
- Any/all "phone-home," "remote telemetry," or other such automated background features of packages **MUST** be proactively **DISABLED**

### Maximal Modularity

- This tool must be as **MODULAR** as possible, with clear separation of concerns.
- Developers **MUST** avoid creating monolithic scripts that handle multiple

### Organized

- The repo **MUST** be meticulously organized according to modern best practices.
- All artifacts must be assigned semantically-meaningful UUIDs deterministically and persisted to highly-structured, logically-organized directories on a per-file/per-change basis.
