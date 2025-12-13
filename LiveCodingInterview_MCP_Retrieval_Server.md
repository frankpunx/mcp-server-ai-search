# Live Coding Interview Assignment: MCP Retrieval Server  
### (Design-First, AI-Assisted, Thought-Process Focus)

## Overview

In this live session, we will collaboratively explore how you would design and implement a small **MCP (Model Context Protocol) server** that:

1. Provides **authenticated access**
2. Makes a small set of documents available as **MCP resources**
3. Includes a **retrieval/search system** over those documents
4. Exposes functions (tools) so an LLM (ChatGPT, Claude, etc.) can interact with the system

> ⚠ **This is not a speed-coding challenge.**  
> We care primarily about **your reasoning, decision-making, architecture**, and your ability to use **AI tools** to accelerate development.

You are encouraged to use ChatGPT, Codex, Claude, or other AI tools throughout the process—to generate scaffolding, compare approaches, debug, or document your design.

---

## Phase 1 — High-Level Architecture (Discussion)

You will describe how you would approach:

- Designing an MCP server with:
  - Authentication
  - Document ingestion and retrieval
  - MCP resources for documents
  - MCP tools for search and Q&A
- Choosing a language/framework
- Retrieval strategy (embeddings, keyword search, hybrid)
- How AI tools can support architecture exploration and validation

Use AI tools freely—for generating diagrams, comparing approaches, or scaffolding.

---

## Phase 2 — Minimal MCP Server Skeleton (AI-Assisted Coding)

Using AI code-generation:

- Sketch or generate a minimal MCP server implementation
- Add basic authentication (e.g., API key or bearer token)
- Define stub MCP resources representing the documents
- Define placeholder tool functions:
  - `search_documents(query)`
  - `answer_question(question)`

---

## Phase 3 — Retrieval System Design (AI-Assisted Coding)

You will:

- Describe your ingestion pipeline for a few example DPA documents
- With AI assistance, draft a simple retrieval mechanism:
- Sketch the logic for:
  - Extracting passages
  - Returning citations
  - Integrating with the MCP tool functions

We focus on your **design clarity**, not final implementation.

---

## Phase 4 — Deployment Strategy (Discussion)

You will outline how you would:

- Package and run the MCP server (Docker, local script, etc.)
- Configure authentication and environment variables
- Provide instructions for connecting from an MCP client

You may ask AI tools to generate Dockerfiles, env examples, or run instructions.
