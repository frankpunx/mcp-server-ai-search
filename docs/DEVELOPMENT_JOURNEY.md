# MCP Server with Azure AI Search - Development Journey

This document chronicles the step-by-step development process for building an MCP (Model Context Protocol) server with Azure AI Search agentic retrieval capabilities.

---

## Starting Template

This project was built from a **basic MCP server template** that provides the minimal foundation for deploying an MCP server to Azure Container Apps.

**Base Commit**: [`3cf06ab`](https://github.com/frankpunx/mcp-server-ai-search/commit/3cf06ab) - "simple mcp server container app"

### Template Contents

| Component | Description |
|-----------|-------------|
| `src/server/basic_mcp_http.py` | FastMCP server with HTTP transport (hello, echo, add_numbers tools) |
| `src/server/Dockerfile` | Multi-stage Docker build for production |
| `infra/main.bicep` | Azure Container Apps + Container Registry + Log Analytics |
| `infra/core/host/` | Container App, Environment, Registry Bicep modules |
| `infra/core/security/` | User-assigned identity, registry access |
| `azure.yaml` | Azure Developer CLI configuration |
| `.devcontainer/` | Dev container setup with Python, Node, Azure CLI |
| `.vscode/mcp.json` | VS Code MCP client configuration |

### What the Template Provides

- ✅ Working MCP server with 3 test tools
- ✅ HTTP streamable transport on port 8000
- ✅ Docker containerization ready for Azure
- ✅ Bicep IaC for Container Apps deployment
- ✅ Managed Identity for Azure authentication
- ✅ azd integration (`azd up` deploys everything)
- ✅ Dev container for consistent development

### To Use This Template

```bash
# Clone and deploy
git clone <repo>
cd mcp-server-ai-search
git checkout 3cf06ab  # Base template state
azd up
```

From this foundation, the project evolved to add Azure AI Search, authentication, and more.

---

## Phase 1: Foundation - Basic MCP Server

### Step 1.1: Create Simple MCP Server (stdio)
**File**: `src/server/basic_mcp_stdio.py`

Created a minimal MCP server using FastMCP with stdio transport:
- Basic tools: `hello`, `echo`, `add_numbers`
- Foundation for understanding MCP protocol

```python
from fastmcp import FastMCP
mcp = FastMCP("Basic MCP Server")

@mcp.tool()
def hello(name: str) -> str:
    return f"Hello, {name}!"
```

### Step 1.2: Convert to HTTP Transport
**File**: `src/server/basic_mcp_http.py`

Upgraded to HTTP streamable transport for cloud deployment:
- Changed transport from stdio to `streamable-http`
- Configured for port 8000
- Added structured logging
- Made server accessible over network

```python
mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

---

## Phase 2: Containerization

### Step 2.1: Create Dockerfile
**File**: `src/server/Dockerfile`

Multi-stage Docker build for production:
- Stage 1: Build dependencies with `uv sync`
- Stage 2: Minimal runtime image
- Alpine-based for small footprint
- Non-root user for security

### Step 2.2: Test Locally with Docker
Verified container builds and runs correctly:
```bash
docker build -t mcp-server .
docker run -p 8000:8000 mcp-server
```

---

## Phase 3: Azure Infrastructure (Bicep)

### Step 3.1: Create Core Infrastructure Modules
**Directory**: `infra/core/`

Created reusable Bicep modules:
- `host/container-app.bicep` - Container Apps deployment
- `host/container-apps-environment.bicep` - Environment with logging
- `host/container-registry.bicep` - ACR for images
- `monitor/loganalytics.bicep` - Log Analytics workspace
- `security/user-assigned-identity.bicep` - Managed identity

### Step 3.2: Add AI Services
**Files**: `infra/core/ai/`

- `search.bicep` - Azure AI Search (Basic SKU, semantic search enabled)
- `openai.bicep` - Azure OpenAI with embedding + chat models

### Step 3.3: Add Storage
**File**: `infra/core/storage/storage-account.bicep`

Blob storage for documents with container for indexer source.

### Step 3.4: Create Main Orchestration
**File**: `infra/main.bicep`

Main Bicep file orchestrating all resources:
- Resource group creation
- Service deployments
- Role assignments for managed identities
- Environment variable configuration
- Output values for azd

### Step 3.5: Configure azd
**File**: `azure.yaml`

Azure Developer CLI configuration:
- Service definition pointing to Dockerfile
- Post-provision hook for setup script

---

## Phase 4: Azure AI Search Setup

### Step 4.1: Create Search Setup Script
**File**: `scripts/setup_search.py`

Python script to configure Azure AI Search resources:
1. Create search index with vector fields
2. Create data source connecting to blob storage
3. Create skillset for AI enrichment (embeddings)
4. Create indexer to process documents
5. Create Knowledge Source (links to index)
6. Create Knowledge Base (for agentic retrieval)

### Step 4.2: Fix SDK Type Issues
Resolved type errors with `azure-search-documents` preview SDK:
- Changed from string field references to `SearchIndexFieldReference` objects
- Fixed Knowledge Base/Source API parameter names
- Updated to use ResourceId connection string format for managed identity

---

## Phase 5: RBAC and Security

### Step 5.1: Enable RBAC on Search Service
**File**: `infra/core/ai/search.bicep`

- Enabled `aadOrApiKey` authentication
- Added SystemAssigned managed identity
- Required for postprovision script to work

### Step 5.2: Add Role Assignment Modules
**Files**: `infra/core/security/`

Created role assignments for:
- `search-access.bicep` - MCP server → Search Index Data Contributor
- `search-user-access.bicep` - Current user → Search Service Contributor + Index Data Contributor
- `openai-access.bicep` - MCP server + user + Search service → Cognitive Services OpenAI User
- `storage-access.bicep` - MCP server → Storage Blob Data Contributor
- `storage-blob-reader.bicep` - Search managed identity → Storage Blob Data Reader
- `storage-user-access.bicep` - Current user → Storage Blob Data Contributor (for uploading docs)

### Step 5.3: Update Main Bicep
Added role assignments for:
- MCP server identity (to access AI services at runtime)
- Current user principal (to run setup script)
- Search managed identity (to index from blob storage)

---

## Phase 6: Deployment Fixes

### Step 6.1: Fix Container Image Issue
**File**: `infra/core/host/container-app.bicep`

- Fixed broken ternary that always used placeholder image
- Removed unused `exists` parameter
- `azd deploy` now properly replaces placeholder with built image

### Step 6.2: Fix Port Configuration
Ensured `targetPort: 8000` matches Dockerfile `EXPOSE 8000`.

### Step 6.3: Fix Logging Configuration
**File**: `infra/core/host/container-apps-environment.bicep`

- Simplified to always require Log Analytics
- Removed invalid `azure-monitor` destination that caused deployment failures

---

## Phase 7: Test Documents

### Step 7.1: Create Sample Documents
**Directory**: `docs/test-documents/`

Created 5 diverse test documents:
1. `hr-policy-handbook.md` - Employee policies and benefits
2. `product-manual-smartwidget.md` - IoT device user guide
3. `technical-faq.md` - IT support Q&A
4. `ai-research-whitepaper.md` - Technical research paper
5. `quarterly-report-q3-2025.md` - Financial report

### Step 7.2: Create Upload Script
**File**: `scripts/upload_documents.py`

Script to:
- Upload documents to blob storage
- Trigger search indexer
- Provide sample test queries

### Step 7.3: Create Documentation
**File**: `docs/test-documents/README.md`

Comprehensive guide with:
- Document descriptions and test queries
- Testing scenarios
- Upload instructions
- Validation checklist

---

## Phase 8: Indexer and Document Processing

### Step 8.1: Full Deployment Test
```bash
azd up
```
Validates:
- Infrastructure provisioning
- RBAC assignments
- Post-provision script execution
- Container image build and deploy

### Step 8.2: Fix Index Projections for Chunking
**File**: `scripts/setup_search.py`

The indexer was failing with "vector length 0" because the embedding skill wasn't properly configured for chunking:

**Problem**: Embedding skill had default context `/document` but needed `/document/chunks/*` to process each chunk individually.

**Solution**: 
1. Added `context="/document/chunks/*"` to the AzureOpenAIEmbeddingSkill
2. Added `SearchIndexerIndexProjection` to expand chunks into separate index documents
3. Set `analyzer_name="keyword"` on the index key field (required for index projections)
4. Changed projection mode to `skipIndexingParentDocuments`

```python
# Index projections expand each chunk into a separate index document
index_projection=SearchIndexerIndexProjection(
    selectors=[
        SearchIndexerIndexProjectionSelector(
            target_index_name=index_name,
            parent_key_field_name="parent_id",
            source_context="/document/chunks/*",
            mappings=[
                InputFieldMappingEntry(name="chunk", source="/document/chunks/*"),
                InputFieldMappingEntry(name="chunk_vector", source="/document/chunks/*/chunk_vector"),
                ...
            ],
        ),
    ],
    parameters=SearchIndexerIndexProjectionsParameters(
        projection_mode="skipIndexingParentDocuments",
    ),
)
```

### Step 8.3: Fix Search Service → OpenAI Permission
**File**: `infra/main.bicep`

The Search service's managed identity needs access to Azure OpenAI for the embedding skill:

```bicep
// Grant Search service managed identity access to Azure OpenAI (for embedding skill)
module searchOpenaiAccess 'core/security/openai-access.bicep' = {
  name: 'search-openai-access'
  scope: resourceGroup
  params: {
    openaiAccountName: openai.outputs.name
    principalId: search.outputs.principalId
  }
}
```

### Step 8.4: Add User Storage Upload Permission
**File**: `infra/core/security/storage-user-access.bicep` (NEW)

Added Storage Blob Data Contributor role for the current user to upload documents:

```bicep
// Grant current user access to Storage (for uploading documents)
module userStorageAccess 'core/security/storage-user-access.bicep' = if (!empty(principalId)) {
  name: 'user-storage-access'
  scope: resourceGroup
  params: {
    storageAccountName: storage.outputs.name
    principalId: principalId
  }
}
```

### Step 8.5: Upload and Index Documents
```bash
uv run python scripts/upload_documents.py
```
Result: 6 documents → 27 chunks indexed successfully

### Step 8.6: Verify Agentic Retrieval
Tested the Knowledge Base using `KnowledgeBaseRetrievalClient`:

```python
from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
from azure.search.documents.knowledgebases.models import (
    KnowledgeBaseMessage, 
    KnowledgeBaseMessageTextContent, 
    KnowledgeBaseRetrievalRequest,
)

kb_client = KnowledgeBaseRetrievalClient(
    endpoint=search_endpoint, 
    knowledge_base_name="documents-kb", 
    credential=DefaultAzureCredential()
)

request = KnowledgeBaseRetrievalRequest(
    messages=[
        KnowledgeBaseMessage(
            role="user",
            content=[KnowledgeBaseMessageTextContent(text="What is the vacation policy?")]
        ),
    ],
)

result = kb_client.retrieve(request)
# Returns synthesized answer with citations [ref_id:N]
```

**Test Results**:
| Query | Result |
|-------|--------|
| "What is the vacation policy?" | ✅ Returned PTO details from HR handbook with citations |
| "How do I reset my SmartWidget Pro?" | ✅ Step-by-step instructions from product manual |
| "Q3 2025 revenue?" | ✅ $4.82B figure with YoY comparison |

### Step 8.7: Create Test Script
**File**: `scripts/test_ai_search.py`

Created comprehensive test suite to verify Azure AI Search functionality:

```bash
# Run all tests
uv run python scripts/test_ai_search.py

# Run specific tests
uv run python scripts/test_ai_search.py --test basic      # Keyword search
uv run python scripts/test_ai_search.py --test semantic   # Semantic search
uv run python scripts/test_ai_search.py --test agentic    # Knowledge Base retrieval
uv run python scripts/test_ai_search.py --test stats      # Index statistics
uv run python scripts/test_ai_search.py --test list       # Document listing
uv run python scripts/test_ai_search.py --test kb         # KB/KS configuration
```

**Test Coverage**:
| Test | Description |
|------|-------------|
| Index Stats | Verify index exists and has documents |
| Basic Search | Keyword search across different documents |
| Semantic Search | Semantic ranking with reranker scores |
| Document Listing | Faceted query to list unique documents |
| KB Configuration | Verify Knowledge Base and Source exist |
| Agentic Retrieval | Full end-to-end KB query with answer synthesis |

---

## Phase 9: MCP Server Deployment Fix

### Step 9.1: Fix Dockerfile CMD
**File**: `src/server/Dockerfile`

The Dockerfile was referencing a non-existent file `ai_search_mcp.py`. Fixed to use `basic_mcp_http.py`:

```dockerfile
# Before (broken)
CMD ["python", "ai_search_mcp.py"]

# After (working)
CMD ["python", "basic_mcp_http.py"]
```

### Step 9.2: Fix Upload Script Indexer Command
**File**: `scripts/upload_documents.py`

The Azure CLI doesn't have `az search indexer run` built-in. Changed to use REST API:

```python
# Get access token
token_result = subprocess.run(
    ["az", "account", "get-access-token", "--resource", "https://search.azure.com", 
     "--query", "accessToken", "-o", "tsv"],
    capture_output=True, text=True, check=True
)

# Run indexer via REST API
indexer_url = f"{search_endpoint}/indexers/documents-indexer/run?api-version=2024-07-01"
req = urllib.request.Request(
    indexer_url,
    method="POST",
    headers={"Authorization": f"Bearer {token}"}
)
urllib.request.urlopen(req)
```

Also excluded README.md from uploads:
```python
documents = [
    doc for doc in docs_dir.glob("*.md")
    if doc.name.lower() != "readme.md"
]
```

### Step 9.3: Create MCP Server Test Script
**File**: `scripts/test_mcp_server.py`

Created test script to verify deployed MCP server:

```bash
uv run python scripts/test_mcp_server.py
```

**Tests**:
1. MCP initialize handshake
2. List available tools
3. Call `hello` tool
4. Call `add_numbers` tool

**Test Results**:
```
✅ Server: Basic MCP Server v2.14.0
✅ Protocol: 2024-11-05
✅ Found 3 tools: hello, echo, add_numbers
✅ hello("World") → "Hello, World! Welcome to the MCP Server."
✅ add_numbers(42, 58) → 100.0
```

### Step 9.4: Update Architecture Diagrams
**File**: `docs/diagrams/README.md`

Updated Mermaid diagrams to reflect current implementation:
- Changed "Knowledge Agent" → "Knowledge Base" (correct terminology)
- Added Search Service Identity with permissions to OpenAI and Storage
- Simplified Data Flow diagram to show actual KB retrieve flow
- Updated MCP Protocol Surfaces to show actual implemented tools

---

## Phase 10: AI Search MCP Integration

### Step 10.1: Add Search Tool to MCP Server
**File**: `src/server/basic_mcp_http.py`

Added the `search` tool that integrates Azure AI Search Knowledge Base retrieval:

```python
from azure.search.documents.knowledgebases.models import (
    KnowledgeBaseMessage,
    KnowledgeBaseMessageTextContent,
    KnowledgeBaseRetrievalRequest,
    KnowledgeRetrievalLowReasoningEffort,
    SearchIndexKnowledgeSourceParams,
)

@mcp.tool
async def search(
    query: Annotated[str, "The search query or question to answer"],
) -> str:
    """Search documents using Azure AI Search with agentic retrieval."""
    kb_client = get_kb_client()
    
    request = KnowledgeBaseRetrievalRequest(
        messages=[
            KnowledgeBaseMessage(
                role="user",
                content=[KnowledgeBaseMessageTextContent(text=query)],
            ),
        ],
        # Per Azure docs: explicitly configure knowledge source params
        knowledge_source_params=[
            SearchIndexKnowledgeSourceParams(
                knowledge_source_name=AZURE_KNOWLEDGE_SOURCE_NAME,
                include_references=True,
                include_reference_source_data=True,
                always_query_source=True,
            )
        ],
        # Include activity for debugging/logging query planning steps
        include_activity=True,
        # Use low reasoning effort for faster responses
        retrieval_reasoning_effort=KnowledgeRetrievalLowReasoningEffort(),
    )
    
    result = kb_client.retrieve(retrieval_request=request)
    # Returns structured JSON with answer, references, and activity
```

**Key Implementation Details**:
- Uses `KnowledgeBaseRetrievalClient` for agentic retrieval
- Lazy initialization of KB client for efficiency
- **Full Azure docs compliance** with all request parameters:
  - `knowledge_source_params` - Explicit source configuration
  - `include_references=True` - Get citation data
  - `include_reference_source_data=True` - Get full chunk content
  - `always_query_source=True` - Always query even for similar queries
  - `include_activity=True` - Get query planning steps
  - `retrieval_reasoning_effort` - Control reasoning depth
- Returns **structured JSON** with:
  - `answer` - Synthesized response with `[ref_id:N]` citations
  - `references` - Full source data including chunk content, URLs
  - `activity` - Query planning, search steps, token usage

**Structured Response Format**:
```json
{
  "answer": "The vacation policy provides... [ref_id:0]",
  "references": [
    {
      "id": "0",
      "document": "hr-policy-handbook.md",
      "score": 2.38,
      "source_data": {
        "chunk": "# Contoso Corporation Employee Handbook...",
        "title": "hr-policy-handbook.md",
        "source_url": "https://storage.blob.../hr-policy-handbook.md"
      }
    }
  ],
  "activity": [
    {"id": 0, "type": "modelQueryPlanning", "elapsed_ms": 1168, "input_tokens": 1470},
    {"id": 1, "type": "searchIndex", "elapsed_ms": 260, "search": "vacation policy details"},
    {"id": 2, "type": "searchIndex", "elapsed_ms": 327, "search": "company vacation policy"},
    {"id": 3, "type": "searchIndex", "elapsed_ms": 222, "search": "standard vacation guidelines"},
    {"id": 4, "type": "agenticReasoning", "reasoning_tokens": 28488},
    {"id": 5, "type": "modelAnswerSynthesis", "elapsed_ms": 2247, "output_tokens": 141}
  ]
}
```

**Citation Parsing Challenge**:
The `doc_key` field contains a hash + base64-encoded blob URL + chunk suffix:
```
hash_aHR0cHM6Ly9zdG9yYWdlLmJsb2IuY29yZS53aW5kb3dzLm5ldC9kb2NzL2hyLXBvbGljeS1oYW5kYm9vay5tZA_chunks_0
```

Solution:
```python
# Extract base64 part between hash and _chunks_
b64_part = doc_key.split("_chunks_")[0].split("_", 1)[1]
# Use URL-safe base64 decode
decoded = base64.urlsafe_b64decode(b64_part).decode("utf-8")
# Extract filename from blob URL
doc_name = decoded.split("/")[-1]
```

### Step 10.2: Add Dev Dependency for Testing
**File**: `pyproject.toml`

Added `httpx` to dev dependencies for the MCP server test script:
```toml
[dependency-groups]
dev = [
    "ruff>=0.8.0",
    "pre-commit>=4.0.0",
    "pytest>=8.0.0",
    "httpx>=0.27.0",
]
```

### Step 10.3: Update Test Script
**File**: `scripts/test_mcp_server.py`

Extended test script to include search tool testing:

```bash
uv run python scripts/test_mcp_server.py
```

**Tests**:
1. MCP initialize handshake
2. List available tools (now 4: hello, echo, add_numbers, search)
3. Call `hello` tool
4. Call `add_numbers` tool
5. Call `search` tool with vacation policy query

### Step 10.4: Deploy to Azure Container Apps
```bash
azd deploy server
```

**Deployment URL**: `https://dev-ectun633rwsrm-server.grayground-936c4d31.eastus2.azurecontainerapps.io/mcp`

### Step 10.5: Verify Deployed Server

**Test Results**:
```
🔗 Testing MCP Server: https://dev-ectun633rwsrm-server.../mcp
============================================================

1️⃣  Testing initialize...
   ✅ Server: Azure AI Search MCP Server v2.14.0
   ✅ Protocol: 2024-11-05

2️⃣  Testing tools/list...
   ✅ Found 4 tools:
      • hello: Say hello to someone.
      • echo: Echo back the provided message.
      • add_numbers: Add two numbers together.
      • search: Search documents using Azure AI Search with agentic retrieval

3️⃣  Testing tools/call (hello)...
   ✅ Response: Hello, World! Welcome to the MCP Server.

4️⃣  Testing tools/call (add_numbers)...
   ✅ 42 + 58 = 100.0

5️⃣  Testing tools/call (search)...
   ✅ Search response: {"answer": "Contoso Corporation's vacation policy..."}
   📚 [0] hr-policy-handbook.md (score: 2.44)

============================================================
🎉 All MCP server tests passed!
============================================================
```

---

## File Structure Summary

```
mcp-server-ai-search/
├── azure.yaml                    # azd configuration
├── pyproject.toml               # Python dependencies
├── src/server/
│   ├── basic_mcp_http.py        # MCP server with AI Search (deployed)
│   └── Dockerfile               # Container configuration
├── scripts/
│   ├── setup_search.py          # Post-provision AI Search setup
│   ├── upload_documents.py      # Document upload utility
│   ├── test_ai_search.py        # AI Search test suite
│   └── test_mcp_server.py       # MCP server test suite
├── infra/
│   ├── main.bicep               # Main infrastructure
│   └── core/
│       ├── ai/
│       │   ├── search.bicep     # Azure AI Search
│       │   └── openai.bicep     # Azure OpenAI
│       ├── host/
│       │   ├── container-app.bicep
│       │   ├── container-apps-environment.bicep
│       │   └── container-registry.bicep
│       ├── storage/
│       │   └── storage-account.bicep
│       ├── monitor/
│       │   └── loganalytics.bicep
│       └── security/
│           ├── search-access.bicep         # MCP server → Search
│           ├── search-user-access.bicep    # User → Search
│           ├── openai-access.bicep         # Various → OpenAI
│           ├── storage-access.bicep        # MCP server → Storage
│           ├── storage-blob-reader.bicep   # Search → Storage (read)
│           └── storage-user-access.bicep   # User → Storage (upload)
└── docs/
    ├── DEVELOPMENT_JOURNEY.md   # This document
    └── test-documents/
        ├── README.md            # Test documentation
        └── *.md                 # Sample documents (5 files)
```

---

## Key Technologies Used

| Component | Technology | Purpose |
|-----------|------------|---------|
| MCP Framework | FastMCP 2.14.0 | Model Context Protocol server |
| Transport | Streamable HTTP | Cloud-compatible MCP transport |
| Container | Docker + Alpine | Lightweight containerization |
| Orchestration | Azure Container Apps | Serverless container hosting |
| Search | Azure AI Search | Vector + keyword hybrid search |
| Embeddings | Azure OpenAI | text-embedding-3-small |
| LLM | Azure OpenAI | gpt-4o for chat |
| Storage | Azure Blob Storage | Document storage for indexer |
| IaC | Bicep | Infrastructure as Code |
| CLI | Azure Developer CLI (azd) | Deployment automation |
| Auth | Managed Identity + RBAC | Passwordless authentication |

---

## Lessons Learned

1. **RBAC must be pre-configured**: Post-provision scripts need role assignments to already exist
2. **Search RBAC requires explicit enablement**: `authOptions: aadOrApiKey` must be set on Search service
3. **Managed identity for indexer**: Search service needs SystemAssigned identity + Storage Blob Data Reader
4. **Search → OpenAI for embeddings**: Search service managed identity needs Cognitive Services OpenAI User role to call embedding API via skillset
5. **User upload permissions**: User needs Storage Blob Data Contributor to upload documents to blob storage
6. **Port alignment**: Dockerfile EXPOSE, Container App targetPort, and server port must match (8000)
7. **azd deploy vs provision**: `provision` creates resources with placeholder; `deploy` builds and pushes actual image
8. **SDK preview versions**: Knowledge Base APIs require `azure-search-documents==11.7.0b2` preview SDK
9. **ResourceId connection strings**: Managed identity data sources require ResourceId format, not blob URLs
10. **Index projections for chunking**: When using skillsets that produce arrays (like SplitSkill), use `SearchIndexerIndexProjection` to expand into separate documents
11. **Keyword analyzer for projections**: Index key field must have `analyzer_name="keyword"` when using index projections
12. **Embedding skill context**: Set `context="/document/chunks/*"` when embedding chunked content
13. **Agentic retrieval client**: Use `KnowledgeBaseRetrievalClient` from `azure.search.documents.knowledgebases`, not `SearchIndexClient`
14. **Streamable HTTP uses SSE**: MCP's streamable-http transport requires SSE (Server-Sent Events) - clients must accept `text/event-stream` and parse `data:` prefixed responses
15. **KB response structure**: `result.response` is a list of messages, each with `content` array; use `as_dict()` for type-safe access
16. **Base64 doc keys**: Knowledge Base references use URL-safe base64 encoded blob URLs in `doc_key` field
17. **Azure docs compliance**: Use `SearchIndexKnowledgeSourceParams` with `include_references`, `include_reference_source_data`, `always_query_source` for full control
18. **Activity logging**: Set `include_activity=True` to get query planning steps, search queries, and token usage
19. **Reasoning effort**: Use `KnowledgeRetrievalLowReasoningEffort` for faster responses, or omit for deeper reasoning

---

## MCP Resources in VS Code / GitHub Copilot

### Understanding MCP Primitives

MCP servers expose three types of primitives to clients:

| Primitive | Purpose | VS Code Usage | Example |
|-----------|---------|---------------|---------|
| **Tools** | Actions with parameters, computation, side effects | Copilot calls automatically or via `#toolname` | `query_knowledge_base`, `add_numbers` |
| **Resources** | URI-addressed read-only data (cacheable) | Add Context → MCP Resources | `docs://list`, `docs://{title}` |
| **Prompts** | Pre-configured prompt templates | `/mcp.servername.promptname` | Slash commands in chat |

### Resources vs Tools: When to Use Each

- **Use Resources** for "give me content" — documents, configs, status text, reference data
- **Use Tools** for "do an action" — search with AI reasoning, mutations, API calls with side effects

Resources are the right abstraction for static/semi-static data because:
- URI-based addressing enables caching and deterministic retrieval
- Read-only surface area reduces security risk
- Better interoperability across MCP clients

### Our Resource Implementation

```python
@mcp.resource("resource://info")
async def get_server_info() -> str:
    """Static server information."""
    return f"Azure AI Search MCP Server v1.0.0 - KB: {AZURE_KNOWLEDGE_BASE_NAME}"

@mcp.resource("docs://list")
async def resource_list_documents() -> str:
    """List all documents in the index."""
    return await _list_documents_impl()

@mcp.resource("docs://{title}")
async def resource_get_document(title: str) -> str:
    """Get document by exact title (e.g., docs://hr-policy-handbook.md)."""
    return await _get_document_impl(title)
```

### Testing Resources in VS Code

1. **Add server to VS Code**: `MCP: Add Server` → HTTP → `http://localhost:8000/mcp`
2. **Browse resources**: Command Palette → `MCP: Browse Resources`
3. **Attach to chat**: In Copilot Chat → Add Context → MCP Resources → select resource
4. **Templated resources**: For `docs://{title}`, enter exact title value (e.g., `hr-policy-handbook.md`)

### Testing Resources via MCP Inspector

```bash
npx @modelcontextprotocol/inspector http://localhost:8000/mcp
```

Then use the UI to call `resources/list` and `resources/read`.

### Testing Resources via curl (JSON-RPC)

```bash
# 1. Initialize and capture session
SESSION=$(curl -s -D - -o /dev/null \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  http://localhost:8000/mcp \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}' \
  | tr -d '\r' | awk 'tolower($1)=="mcp-session-id:"{print $2}')

# 2. List resources
curl -s -N -H "mcp-session-id: $SESSION" \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  http://localhost:8000/mcp \
  --data '{"jsonrpc":"2.0","id":2,"method":"resources/list","params":{}}' | sed -n 's/^data: //p'

# 3. Read a resource
curl -s -N -H "mcp-session-id: $SESSION" \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  http://localhost:8000/mcp \
  --data '{"jsonrpc":"2.0","id":3,"method":"resources/read","params":{"uri":"docs://list"}}' | sed -n 's/^data: //p'
```

### Key Findings

20. **Resources ≠ Tools**: Resources use `resources/list` + `resources/read` methods, not `tools/call`
21. **VS Code supports resources**: Add Context → MCP Resources in Copilot Chat (GA in VS Code 1.102+)
22. **Exact title matching**: Templated resources like `docs://{title}` require exact match (including `.md`)
23. **Session required**: Streamable HTTP transport requires `mcp-session-id` header from `initialize` response
24. **SSE parsing**: Responses are Server-Sent Events — parse lines starting with `data: `
25. **TODO (docs resources, scalability)**: Current `docs://list`/`docs://{title}` are Search-index-backed (format-agnostic extracted text), which is convenient for PoC but not efficient/scalable because it scans/stitches chunk records. Prefer Blob-backed resources (1 blob = 1 doc).

---

## Ingestion Pipeline Architecture

### How the Pipeline Works

The ingestion pipeline uses an Azure AI Search **Indexer** with automatic blob change detection:

```
┌─────────────┐    ┌────────────────┐    ┌──────────────┐    ┌─────────────┐
│   Blob      │───▶│    Indexer     │───▶│   Skillset   │───▶│   Index     │
│   Storage   │    │ (change track) │    │ (chunk+embed)│    │ (vectors)   │
└─────────────┘    └────────────────┘    └──────────────┘    └─────────────┘
```

### Adding a New Document

When you add a new file to the index:

1. **Upload to Blob Storage** → File lands in the `documents` container
2. **Indexer Detects Changes** → Built-in change tracking detects:
   - New blobs added
   - Modified blobs (via `Last-Modified` timestamp)
   - Deleted blobs (if soft-delete configured)
3. **Indexer Runs** → Must be triggered (see options below)
4. **Skillset Processing** → For each new/changed blob:
   - `SplitSkill` chunks the document (2000 chars, 200 char overlap)
   - `AzureOpenAIEmbeddingSkill` generates 1536-dim vectors per chunk
5. **Index Projections** → Each chunk becomes a separate document with:
   - `chunk` (text), `chunk_vector` (embedding), `title`, `source_url`, `parent_id`

### Triggering the Indexer

The indexer does **NOT** run automatically on file changes by default. Options:

| Method | How | Use Case |
|--------|-----|----------|
| **Manual script** | `python scripts/upload_documents.py` | Dev/test uploads |
| **REST API** | `POST {endpoint}/indexers/documents-indexer/run` | CI/CD pipelines |
| **Azure Portal** | Click "Run" on indexer blade | One-off manual runs |
| **Schedule** | Configure indexer with `schedule` param | Production auto-refresh |

### Quick Reference Commands

```bash
# Upload a single file and trigger indexer
az storage blob upload \
  --account-name <storage> \
  --container-name documents \
  --file my-new-doc.md \
  --name my-new-doc.md \
  --auth-mode login

# Run indexer via REST API
curl -X POST \
  "https://<search>.search.windows.net/indexers/documents-indexer/run?api-version=2024-07-01" \
  -H "Authorization: Bearer $(az account get-access-token --resource https://search.azure.com --query accessToken -o tsv)"

# Or use the upload script (uploads all docs + triggers indexer)
uv run python scripts/upload_documents.py
```

### Adding a Scheduled Indexer (Optional)

To enable automatic refresh every 5 minutes, modify `scripts/setup_search.py`:

```python
from azure.search.documents.indexes.models import IndexingSchedule
from datetime import timedelta

indexer = SearchIndexer(
    name=name,
    # ... existing config ...
    schedule=IndexingSchedule(interval=timedelta(minutes=5)),
)
```

**Note**: Scheduled indexers have a minimum interval of 5 minutes. For near-real-time ingestion, consider:
- Azure Event Grid triggers on blob events
- Custom Azure Function watching blob changes
- Manual trigger via MCP admin endpoint (not yet implemented)

---

## Phase 12: API Key Authentication & Azure Best Practices

### Step 12.1: Validate Against Azure Guidelines
**Reference**: [Azure-Samples/python-mcp-demos](https://github.com/Azure-Samples/python-mcp-demos)

Compared our implementation against Microsoft's official MCP demo patterns:

| Aspect | Status | Notes |
|--------|--------|-------|
| FastMCP Framework | ✅ | Using same library |
| HTTP Transport | ✅ | `streamable-http` transport |
| Managed Identity | ✅ | `ManagedIdentityCredential` with `AZURE_CLIENT_ID` |
| DefaultAzureCredential | ✅ | Fallback for local dev |
| Tool Definitions | ✅ | `@mcp.tool` with `Annotated` types |
| Resource Definitions | ✅ | `@mcp.resource("docs://...")` |
| Health Check | ❌ → ✅ | Added `/health` endpoint |
| ASGI Export | ❌ → ✅ | Added `app = create_app()` |
| Health Probes | ❌ → ✅ | Added Bicep probes |

### Step 12.2: Add Health Check Endpoint
**File**: `src/server/basic_mcp_http.py`

Added health endpoint required for Azure Container Apps probes:

```python
@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request):
    """Health check endpoint for Azure Container Apps probes."""
    return JSONResponse({
        "status": "healthy", 
        "service": "mcp-ai-search-server"
    })
```

### Step 12.3: Add Health Probes to Bicep
**File**: `infra/core/host/container-app.bicep`

Added startup, readiness, and liveness probes:

```bicep
probes: [
  {
    type: 'Startup'
    httpGet: { path: '/health', port: targetPort }
    initialDelaySeconds: 10
    periodSeconds: 3
    failureThreshold: 30  // Allow up to 90 seconds for startup
  }
  {
    type: 'Readiness'
    httpGet: { path: '/health', port: targetPort }
    initialDelaySeconds: 5
    periodSeconds: 5
    failureThreshold: 3
  }
  {
    type: 'Liveness'
    httpGet: { path: '/health', port: targetPort }
    periodSeconds: 10
    failureThreshold: 3
  }
]
```

### Step 12.4: Implement API Key Authentication
**File**: `src/server/basic_mcp_http.py`

Added simple API key middleware as an alternative to OAuth:

```python
class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to check for API key in X-API-Key header."""

    async def dispatch(self, request, call_next):
        # Skip auth for health checks
        if request.url.path in ["/health", "/healthz", "/"]:
            return await call_next(request)
        
        if MCP_API_KEY:
            api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
            if api_key != MCP_API_KEY:
                return JSONResponse(
                    {"error": "Unauthorized", "message": "Invalid or missing API key"},
                    status_code=401,
                )
        
        return await call_next(request)
```

### Step 12.5: Add API Key to Infrastructure
**File**: `infra/main.bicep`

Added secure parameter for API key:

```bicep
@secure()
@description('Optional API key for MCP server authentication')
param mcpApiKey string = ''

// Pass to container as secret
secrets: !empty(mcpApiKey) ? [{ name: 'mcp-api-key', value: mcpApiKey }] : []
env: concat(baseEnv, !empty(mcpApiKey) ? [{ name: 'MCP_API_KEY', secretRef: 'mcp-api-key' }] : [])
```

**File**: `infra/main.parameters.json`

Map azd environment variable:

```json
"mcpApiKey": { "value": "${MCP_API_KEY}" }
```

### Step 12.6: Export ASGI App for Production
**File**: `src/server/basic_mcp_http.py`

Following Azure sample pattern, export `app` for uvicorn:

```python
def create_app():
    """Create the ASGI application with optional API key middleware."""
    fastmcp_app = mcp.http_app(path="/mcp")
    
    if MCP_API_KEY:
        return Starlette(
            routes=[Mount("/", app=fastmcp_app)],
            middleware=[Middleware(APIKeyMiddleware)],
            lifespan=fastmcp_app.lifespan,  # Required for FastMCP
        )
    return fastmcp_app

# ASGI app for uvicorn (Dockerfile: uvicorn basic_mcp_http:app)
app = create_app()
```

### Step 12.7: Configure VS Code MCP Client
**File**: `.vscode/mcp.json`

```json
{
  "servers": {
    "my-mcp-server": {
      "type": "http",
      "url": "https://dev-ectun633rwsrm-server.grayground-936c4d31.eastus2.azurecontainerapps.io/mcp",
      "headers": {
        "X-API-Key": "your-secret-key-here"
      }
    }
  }
}
```

### API Key vs OAuth Trade-offs

| Aspect | API Key (Current) | OAuth (Azure Sample) |
|--------|-------------------|---------------------|
| Setup Complexity | ✅ Simple | ❌ Complex (App Registration) |
| CI/CD Friendly | ✅ Just set env var | ❌ Needs Graph API permissions |
| User Identity | ❌ No per-user tracking | ✅ Per-user auth |
| VS Code Integration | ⚠️ Manual header config | ✅ Native OAuth flow |
| Production Ready | ✅ For internal services | ✅ For user-facing apps |

**Recommendation**: API key is ideal for internal/service-to-service auth. For user-facing apps with identity requirements, consider FastMCP's built-in `AzureProvider`.

---

## RBAC Role Assignments Summary

| Principal | Resource | Role | Purpose |
|-----------|----------|------|---------|
| MCP Server Identity | Azure AI Search | Search Index Data Contributor | Query search index |
| MCP Server Identity | Azure OpenAI | Cognitive Services OpenAI User | Call chat/embedding APIs |
| MCP Server Identity | Storage Account | Storage Blob Data Contributor | Read/write blobs |
| Search Service Identity | Azure OpenAI | Cognitive Services OpenAI User | Embedding skill in skillset |
| Search Service Identity | Storage Account | Storage Blob Data Reader | Indexer reads blobs |
| Current User | Azure AI Search | Search Service Contributor | Create/update index, indexer |
| Current User | Azure AI Search | Search Index Data Contributor | Query/populate index |
| Current User | Azure OpenAI | Cognitive Services OpenAI User | Test embeddings/chat |
| Current User | Storage Account | Storage Blob Data Contributor | Upload documents |

---

*Document created: December 2025*
