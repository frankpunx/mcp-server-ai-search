# MCP Server with Azure AI Search - Development Journey

This document chronicles the step-by-step development process for building an MCP (Model Context Protocol) server with Azure AI Search agentic retrieval capabilities.

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

## Phase 10: AI Search MCP Integration (TODO)

### Step 10.1: Add Search Tool to MCP Server
Add tool to query Azure AI Search Knowledge Base from the MCP server.

### Step 10.2: Deploy Updated MCP Server
Redeploy with AI Search capabilities enabled.

---

## File Structure Summary

```
mcp-server-ai-search/
├── azure.yaml                    # azd configuration
├── pyproject.toml               # Python dependencies
├── src/server/
│   ├── basic_mcp_http.py        # Basic MCP server (hello, echo, add)
│   ├── ai_search_mcp.py         # AI Search MCP server (TODO: deploy)
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
