# Live Coding Interview Preparation Guide
## MCP Retrieval Server - Architecture & AI-Assisted Development

> **Focus**: Architectural reasoning, option comparison, and AI-assisted development workflow

---

## PHASE 1: High-Level Architecture Discussion

### 1.1 Authentication Options Comparison

#### Option A: API Key Middleware (Our Choice)
**Pros:**
- ✅ Simple to implement (Starlette middleware)
- ✅ No additional Azure services required
- ✅ Works with any MCP client
- ✅ Low latency (no external calls)

**Cons:**
- ❌ Manual key rotation
- ❌ No built-in rate limiting
- ❌ Limited audit logging
- ❌ Single shared secret

**When to use:** Development, demos, trusted clients

**Key Vault Integration:**
For production API key management, integrate Azure Key Vault:
- Store API keys as secrets in Key Vault
- Use Managed Identity to access Key Vault
- Rotate keys without code changes
- Enable audit logging for key access
- Set expiration policies


#### Option B: Azure API Management (APIM)

**What is APIM?**
Azure API Management is a **full-featured API gateway** that sits between your clients and backend services. Think of it as a sophisticated reverse proxy with enterprise-grade features. Instead of clients connecting directly to your MCP server, they connect to APIM, which applies policies, enforces security, and forwards requests to your backend.

**Architecture:**
```
Client → APIM (gateway) → MCP Server (Container App)
         ↓
    Policies Applied:
    - Authentication (JWT, API Key, OAuth)
    - Rate limiting (10 calls/min per subscription)
    - IP filtering (whitelist corporate IPs)
    - Request transformation (add headers, modify body)
    - Response caching (reduce backend load)
    - Analytics & logging (Application Insights)
```

**How it Works:**

1. **Import API**: Define your MCP server endpoints in APIM
   - Backend URL: `https://your-mcp-server.azurecontainerapps.io`
   - Operations: `GET /health`, `POST /mcp`

2. **Apply Policies**: XML-based rules that execute in pipeline stages
   ```
   Inbound → Backend → Outbound → On-Error
   ```

3. **Manage Subscriptions**: Issue subscription keys to consumers
   - Primary/Secondary keys for rotation
   - Different products (Free, Standard, Premium) with different quotas

4. **Monitor & Analyze**: Built-in analytics dashboard
   - Request volume, latency, errors by consumer
   - Which operations are most used
   - Geographic distribution of calls

**Pros:**
- ✅ **Centralized governance**: Single control plane for all APIs (not just MCP)
- ✅ **Built-in rate limiting**: Per-subscription quotas (prevents abuse)
  ```xml
  <rate-limit calls="100" renewal-period="60" />
  ```
- ✅ **Advanced authentication**: JWT validation, OAuth flows, mutual TLS
- ✅ **API versioning**: Support multiple API versions simultaneously
  - `/v1/mcp`, `/v2/mcp` routing to different backends
- ✅ **Request transformation**: Modify requests/responses on-the-fly
  - Add CORS headers, convert XML to JSON, mask sensitive data
- ✅ **Comprehensive analytics**: Track usage patterns, SLA compliance
- ✅ **Developer portal**: Self-service API discovery for consumers
- ✅ **Multiple subscription keys**: Different keys for dev/staging/prod

**Cons:**
- ❌ **Additional cost**: $50+/month (Developer tier), $2,600+/month (Standard tier)
- ❌ **Increased latency**: Extra network hop adds ~20-50ms
- ❌ **Complex configuration**: Learning curve for policy syntax
- ❌ **Overkill for simple scenarios**: If you only need basic auth, APIM is heavyweight

**When to use:**
- ✅ **Production APIs with multiple consumers** (10+ different teams/apps)
- ✅ **Need governance & compliance** (audit trails, usage quotas, SLA enforcement)
- ✅ **Managing API portfolio** (multiple backend services, not just MCP)
- ✅ **Enterprise integration** (existing APIM for other APIs)
- ✅ **Monetization** (charge different rates for different subscription tiers)

**Entra ID Integration with APIM:**

APIM excels at **validating JWT tokens** issued by Microsoft Entra ID (formerly Azure AD). This enables **enterprise-grade authentication** with individual user identities:

**Authentication Flow:**
1. **User authenticates with Entra ID** (via browser or MSAL library)
   - User enters credentials at `login.microsoftonline.com`
   - Entra ID validates identity and issues JWT token
   
2. **Client includes token in request to APIM**
   ```
   POST https://apim-instance.azure-api.net/mcp
   Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
   ```

3. **APIM validates token** (happens automatically via policy)
   - Checks signature (cryptographically signed by Entra ID)
   - Verifies expiration (`exp` claim)
   - Confirms audience matches (`aud` claim = `api://{client-id}`)
   - Validates issuer (`iss` claim = Entra ID tenant)
   - Optional: Checks user has required roles

4. **If valid, APIM forwards to backend MCP server**
   - Backend receives request with `X-User-Email` header
   - Backend **doesn't need to validate token** (APIM already did)
   - Backend can trust user identity from headers

5. **If invalid, APIM returns 401 immediately**
   - Backend never receives invalid requests

**Benefits:**
- ✅ **Multi-user authentication**: Each user has unique identity (not shared API key)
- ✅ **Role-based access control (RBAC)**: Different users have different permissions
  - Admin role: Can manage knowledge base
  - Reader role: Can only query
- ✅ **SSO integration**: Works with existing enterprise logins (no new passwords)
- ✅ **Audit trails per user**: Know exactly who called which API and when
- ✅ **Token expiration**: Tokens auto-expire (e.g., 1 hour), reducing security risk
- ✅ **Centralized user management**: Disable user in Entra ID → immediately loses API access

**APIM vs AI Gateway:**

| Feature | APIM (Standard) | AI Gateway Add-on |
|---------|----------------|-------------------|
| **Purpose** | General API management | LLM-specific optimization |
| **Rate Limiting** | Request-based | Token-based (prompt + completion) |
| **Caching** | HTTP response cache | Semantic cache (similar prompts) |
| **Load Balancing** | Round-robin, weighted | Model-aware (fallback, priority) |
| **Cost Tracking** | Per API call | Per token, per model |
| **Prompt Management** | ❌ | ✅ Prompt flows & templates |
| **Model Routing** | Manual policies | Automatic based on capacity |
| **Use Case** | REST APIs | LLM/AI workloads |

**AI Gateway is APIM + AI-specific features** - think of it as a specialized configuration for AI workloads.

#### Option C: Azure API Management - AI Gateway (Newest)
**Pros:**
- ✅ All APIM benefits +
- ✅ LLM-specific features (semantic caching, prompt flow)
- ✅ Token-based rate limiting
- ✅ Model load balancing
- ✅ Cost tracking per user/app

**Cons:**
- ❌ Same cost/latency as APIM
- ❌ Overkill if not routing to multiple LLMs
- ❌ Preview feature (limited docs)

**When to use:** Multi-model scenarios, need AI-specific governance

**AI Gateway + MCP Servers:**

AI Gateway can sit in front of an MCP server to provide:

```
Client → AI Gateway → MCP Server → Azure OpenAI
         ↓
    [Token limiting]
    [Semantic caching]
    [Model fallback]
```


**Benefits for MCP:**
- Reduce costs (cache identical/similar queries)
- Prevent abuse (token-based limits)
- Improve reliability (model fallback if primary fails)
- Track usage per client/app

#### Option D: Managed Identity Only (Zero Auth)
**Pros:**
- ✅ Passwordless Azure service-to-service auth
- ✅ Automatic credential rotation
- ✅ Fine-grained RBAC

**Cons:**
- ❌ Only works within Azure
- ❌ No client authentication
- ❌ Requires network isolation (VNet)

**When to use:** Internal services, private endpoints

#### Option E: Container Apps Easy Auth (Built-in Authentication)

**How it works:**
```
Client → Easy Auth → [Validates token] → MCP Server
         ↓
    [Entra ID, Google, GitHub, etc.]
```

Container Apps has built-in authentication that intercepts requests before they reach your app:

**Configuration (Bicep):**
```bicep
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  properties: {
    configuration: {
      auth: {
        platform: {
          enabled: true
        }
        identityProviders: {
          azureActiveDirectory: {
            enabled: true
            registration: {
              clientId: entraAppClientId
              openIdIssuer: 'https://sts.windows.net/${tenant().tenantId}/v2.0'
            }
          }
        }
      }
    }
  }
}
```

**Pros:**
- ✅ Zero code - handled at platform level
- ✅ Automatic token validation
- ✅ User identity passed in headers (`X-MS-CLIENT-PRINCIPAL`)
- ✅ Works with Entra ID, Google, GitHub, Facebook

**Cons:**
- ❌ Less flexible than custom middleware
- ❌ Requires OAuth flow (not ideal for API clients)
- ❌ Azure-specific (not portable)

**When to use:** Web apps with user login, need SSO

#### Option F: Hybrid API Key + Entra ID

**Scenario:** Support both machine clients (API key) and user clients (Entra ID)

```python
class HybridAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Check for API key first
        api_key = request.headers.get("X-API-Key")
        if api_key and api_key == MCP_API_KEY:
            return await call_next(request)
        
        # Check for Entra ID token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if await validate_entra_token(token):
                return await call_next(request)
        
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

async def validate_entra_token(token: str) -> bool:
    """Validate JWT token from Entra ID."""
    import jwt
    from jwt import PyJWKClient
    
    # Get signing keys from Entra ID
    jwks_url = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"
    jwks_client = PyJWKClient(jwks_url)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    
    # Validate token
    decoded = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=f"api://{CLIENT_ID}"
    )
    return True
```

**Use case:** API supports both:
- Service accounts (bots, scripts) → API key
- Human users (web, mobile) → Entra ID token

#### Our Decision: API Key + Managed Identity Hybrid
```
Client → [API Key] → MCP Server → [Managed Identity] → Azure Services
```
- **API Key**: Protects MCP endpoint (simple, effective)
- **Managed Identity**: Secures Azure resource access (passwordless, RBAC)

---

### 1.2 Document Ingestion: Pull vs Push Models

**Reference:** [Azure AI Search Indexers Overview](https://learn.microsoft.com/en-us/azure/search/search-indexer-overview)

#### Push Model (Data Upload to Index)
```
App → SDK → Search Index
```
**How it works:**
- Application reads documents
- Extracts text and generates embeddings
- Pushes JSON documents directly to index via SDK

**Pros:**
- ✅ Full control over processing logic
- ✅ Real-time updates (no indexer delay)
- ✅ Custom transformation logic
- ✅ Works with any data source

**Cons:**
- ❌ Must implement chunking, embedding, extraction
- ❌ Must handle failures & retries
- ❌ More code to maintain
- ❌ Scaling requires batching logic

**When to use:** Custom data sources, need real-time updates, complex transformations

#### Pull Model (Indexer - Our Choice)

![alt text](image-2.png)

![alt text](image-3.png)

```
Blob Storage ← Indexer ← AI Search
               ↓
         [Skillset: Split → Embed]
               ↓
         Search Index
```
**How it works:**
- Documents uploaded to Azure Blob Storage
- Indexer automatically detects changes
- Skillset applies transformations (chunking, embedding)
- Results indexed automatically

**Pros:**
- ✅ Zero code for ingestion (declarative config)
- ✅ Built-in skillsets (chunking, OCR, embedding)
- ✅ Automatic retry & error handling
- ✅ Supports PDF, DOCX, images (OCR)
- ✅ Scheduled or on-demand runs

**Cons:**
- ❌ Limited to supported data sources
- ❌ Indexer latency (not real-time)
- ❌ Less flexibility in transformation logic

**When to use:** Standard document formats, batch processing acceptable, want managed solution

#### Our Solution: Pull Model with Skillsets
```python
# 1. Create Data Source (Blob container)
data_source = SearchIndexerDataSourceConnection(
    name="blob-datasource",
    type="azureblob",
    connection_string=f"ResourceId={storage_resource_id};",
    container=SearchIndexerDataContainer(name="documents")
)

# 2. Create Skillset (Chunk + Embed)
skillset = SearchIndexerSkillset(
    skills=[
        SplitSkill(
            text_split_mode="pages",
            maximum_page_length=2000,
            page_overlap_length=200,
        ),
        AzureOpenAIEmbeddingSkill(
            context="/document/chunks/*",
            dimensions=1536,
        )
    ],
    index_projection=...  # One doc per chunk
)

# 3. Create Indexer (connects datasource → skillset → index)
indexer = SearchIndexer(
    data_source_name="blob-datasource",
    skillset_name="chunk-embed-skillset",
    target_index_name="documents"
)
```

**Why we chose this:** 
- Documents are static files (PDFs, markdown)
- Don't need real-time indexing
- Want automatic chunking & embedding
- Minimal code maintenance

---

### 1.3 The Index We Created

#### Index Schema
```python
fields = [
    # Key field (required)
    SearchField(name="id", type=String, key=True, analyzer_name="keyword"),
    
    # Text fields
    SearchField(name="chunk", type=String, searchable=True),
    SearchField(name="title", type=String, searchable=True, filterable=True),
    SearchField(name="source_url", type=String, filterable=True),
    SearchField(name="keywords", type=String, searchable=True),
    
    # Metadata
    SearchField(name="last_modified", type=DateTimeOffset, filterable=True, sortable=True),
    SearchField(name="parent_id", type=String, filterable=True),
    
    # Vector field
    SearchField(
        name="chunk_vector",
        type=Collection(Single),
        searchable=True,
        vector_search_dimensions=1536,
        vector_search_profile_name="vector-profile"
    )
]
```

#### Vector Search Configuration
```python
vector_search = VectorSearch(
    # Algorithm: HNSW (Hierarchical Navigable Small World)
    algorithms=[HnswAlgorithmConfiguration(name="hnsw-algorithm")],
    
    # Profile: Links algorithm + vectorizer
    profiles=[VectorSearchProfile(
        name="vector-profile",
        algorithm_configuration_name="hnsw-algorithm",
        vectorizer_name="openai-vectorizer"
    )],
    
    # Vectorizer: Generates embeddings at query time
    vectorizers=[AzureOpenAIVectorizer(
        vectorizer_name="openai-vectorizer",
        parameters=AzureOpenAIVectorizerParameters(
            deployment_name="text-embedding-3-small",
            model_name="text-embedding-3-small"
        )
    )]
)
```

#### Semantic Search Configuration
```python
semantic_config = SemanticConfiguration(
    name="default",
    prioritized_fields=SemanticPrioritizedFields(
        title_field=SemanticField(field_name="title"),
        content_fields=[SemanticField(field_name="chunk")],
        keywords_fields=[SemanticField(field_name="keywords")]
    )
)
```

**Key Features:**
- **Hybrid Search Ready**: Both text and vector fields
- **Semantic Ranker**: Uses title/content/keywords for L2 reranking
- **Query-time Vectorization**: Automatic embedding generation
- **Chunked Documents**: One index doc per chunk (via index projections)

---

### 1.4 Retrieval Strategy Comparison

#### Strategy A: Hybrid Search (Traditional RAG)
```
Query
  ├─> Vector Search (cosine similarity)
  │     └─> Top K chunks by embedding
  │
  └─> Keyword Search (BM25)
        └─> Top K chunks by text match
        
Merge Results (RRF - Reciprocal Rank Fusion)
  └─> Final Top K chunks
        ↓
  [Semantic Reranker] (L2 Ranking)
  └─> Re-scored Top K chunks
```

**Semantic Ranking (L2 Reranking):**

After hybrid search merges results, the semantic ranker applies deep learning models to re-score results:

**How it works:**
1. **L1 Ranking**: Hybrid search (BM25 + vector) produces initial ranking
2. **L2 Ranking**: Semantic ranker uses Microsoft's language models to:
   - Understand query intent (not just keywords)
   - Analyze semantic similarity between query and document
   - Consider title, content, keywords fields with different weights
   - Generate semantic scores (0-4 scale)
3. **Re-ranking**: Results re-ordered by semantic score

**Example:**
- Query: "How to reset device"
- BM25 might rank "device specifications" high (keyword match)
- Semantic ranker understands intent → ranks "troubleshooting reset" higher

**Configuration:**
```python
results = search_client.search(
    search_text="how to reset device",
    query_type=QueryType.SEMANTIC,  # ← Enable semantic ranking
    semantic_configuration_name="default",
    top=5
)

# Results include semantic scores
for result in results:
    print(f"Score: {result['@search.reranker_score']}")  # 0-4 scale
```

**Cost:** Semantic ranker is included in Standard SKU and higher.

**How it works:**
1. Convert query to embedding
2. Search vector field for similar chunks
3. Simultaneously search text fields with BM25
4. Combine results using Reciprocal Rank Fusion
5. Return merged, ranked chunks

**Pros:**
- ✅ Fast (single query)
- ✅ Handles both semantic and keyword queries
- ✅ Good recall (finds relevant chunks)

**Cons:**
- ❌ No query understanding (literal search)
- ❌ Single-hop only (no follow-up questions)
- ❌ No answer synthesis (returns raw chunks)
- ❌ Manual citation handling

**When to use:** Simple Q&A, known queries, need speed

**Code Example:**
```python
results = search_client.search(
    search_text="vacation policy",
    vector_queries=[VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=10,
        fields="chunk_vector"
    )],
    query_type=QueryType.SEMANTIC,
    semantic_configuration_name="default",
    top=5
)
```

#### Strategy B: Agentic Retrieval (Our Choice)
```
Query
  │
  ├─> [AI Agent] Query Planning
  │     ├─> Decompose into sub-queries
  │     └─> Identify search intents
  │
  ├─> [For each sub-query] Hybrid Search
  │     ├─> Vector + Keyword
  │     └─> Semantic Reranking
  │
  ├─> [AI Agent] Result Synthesis
  │     ├─> Generate coherent answer
  │     ├─> Insert citations [ref_id:N]
  │     └─> Return structured response
  │
  └─> Response: { answer, references, activity }
```

**How it works (Knowledge Base API):**
1. **Query Planning**: GPT-4o analyzes question, generates sub-queries
2. **Multi-Hop Search**: Executes multiple search operations
3. **Context Building**: Collects relevant chunks from all searches
4. **Answer Synthesis**: Generates natural language answer with citations
5. **Reference Tracking**: Returns source metadata for each citation

**Pros:**
- ✅ Understands complex questions
- ✅ Multi-hop reasoning (follow-up queries)
- ✅ Natural language answers (not raw chunks)
- ✅ Automatic citations with references
- ✅ Query intent detection

**Cons:**
- ❌ Slower (multiple LLM calls)
- ❌ Higher cost (GPT-4o inference)
- ❌ Less predictable (AI reasoning)
- ❌ Requires Azure AI Search Knowledge Base

**When to use:** Complex questions, conversational UI, need answers not chunks

**Code Example:**
```python
kb_client = KnowledgeBaseRetrievalClient(
    endpoint=search_endpoint,
    knowledge_base_name="documents-kb",
    credential=DefaultAzureCredential()
)

result = kb_client.retrieve(
    KnowledgeBaseRetrievalRequest(
        messages=[KnowledgeBaseMessage(
            role="user",
            content=[KnowledgeBaseMessageTextContent(
                text="What is the vacation policy and how does it compare to sick leave?"
            )]
        )],
        include_activity=True
    )
)

# Returns:
# {
#   "answer": "According to the HR handbook [ref_id:1], employees receive 15 days PTO...",
#   "references": [{"id": "1", "document": "hr-policy.md", "score": 3.8}],
#   "activity": [
#     {"type": "queryPlanning", "queries": ["vacation policy", "sick leave comparison"]},
#     {"type": "search", "results": 5}
#   ]
# }
```

#### Comparison Table

| Feature | Hybrid Search | Agentic Retrieval |
|---------|---------------|-------------------|
| **Query Understanding** | Literal | AI reasoning |
| **Multi-hop** | ❌ | ✅ |
| **Answer Format** | Raw chunks | Natural language |
| **Citations** | Manual | Automatic |
| **Latency** | ~100ms | ~2-5s |
| **Cost** | $0.002/query | $0.02-0.05/query |
| **Best For** | Simple Q&A | Complex questions |

**Our Decision:** Agentic Retrieval
- Interview documents have complex questions
- Want demonstration of advanced AI capabilities
- Citations are critical for credibility
- Cost acceptable for demo scenario

---

### 1.5 MCP Protocol Design

#### MCP Resources: Document Catalog
```python
@mcp.resource("docs://list")
async def list_documents() -> str:
    """
    Returns: JSON list of all documents with metadata
    Use case: Client wants to see available documents
    """
    return json.dumps({
        "documents": [
            {
                "title": "hr-policy-handbook.md",
                "source_url": "https://...",
                "chunk_count": 5
            }
        ]
    })

@mcp.resource("docs://{title}")
async def get_document(title: str) -> str:
    """
    Returns: Full document content (all chunks concatenated)
    Use case: Client wants to read entire document
    """
    # Query index for all chunks of this document
    # Concatenate and return
```

**Why Resources?**
- Documents are **passive data** (read-only)
- URI-based access pattern (`docs://...`)
- Clients can cache results
- Discovery via `resources/list`

#### MCP Tool: Agentic Search
```python
@mcp.tool
async def query_knowledge_base(question: str) -> str:
    """
    Query the knowledge base using AI-powered agentic retrieval.
    
    Returns: JSON with answer, references, and reasoning activity
    Use case: Client asks a question needing AI synthesis
    """
    kb_client = get_kb_client()
    result = kb_client.retrieve(...)
    
    return json.dumps({
        "answer": "...",
        "references": [...],
        "activity": [...]
    })
```

**Why a Tool?**
- Search is an **action with computation** (AI reasoning)
- Takes arbitrary input (question string)
- Non-deterministic (AI-powered)
- Expensive operation (not cacheable)

**Protocol Distinction:**
- **Resources** = "Here's data you can read"
- **Tools** = "Here's something I can do"

---

### 1.6 Framework & Compute Comparison

#### Compute: Azure Functions vs Container Apps

**Three Hosting Options for MCP Servers:**

##### Option 1: Azure Functions with MCP Extension (Recommended for Functions)
**How it works:**
- Uses Azure Functions MCP bindings
- MCP protocol handled by extension
- Functions act as MCP tools

**Example:**
```python
import azure.functions as func
import azure.functions.mcp as mcp

app = func.FunctionApp()

@app.mcp_tool("search_documents")
def search(query: str) -> str:
    """Search documents."""
    return f"Results for: {query}"

# Extension handles MCP protocol, transport, and registration
```

**Pros:**
- ✅ Automatic MCP protocol handling
- ✅ Serverless scaling
- ✅ Simple deployment

**Cons:**
- ❌ Limited to Functions programming model
- ❌ Preview feature (not GA yet)
- ❌ Less control over transport

##### Option 2: Self-Hosted MCP SDK on Azure Functions
**How it works:**
- Deploy MCP SDK server as a Function
- Use HTTP trigger
- Manual protocol handling

**Example:**
```python
import azure.functions as func
from mcp.server import Server
import json

app = func.FunctionApp()
server = Server("my-mcp-server")

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search":
        return {"result": "..."}

@app.route(route="mcp", methods=["POST"])
async def mcp_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    # Manual MCP protocol handling
    body = json.loads(req.get_body())
    result = await server.handle_request(body)
    return func.HttpResponse(json.dumps(result))
```

**Pros:**
- ✅ Full control over MCP implementation
- ✅ Use official MCP SDK

**Cons:**
- ❌ More complex than extension
- ❌ Manual protocol handling
- ❌ No streaming support (Functions HTTP timeout)

##### Option 3: Container Apps (Our Choice)
**How it works:**
- Deploy full MCP server as Docker container
- Native support for long-running connections
- HTTP Streamable transport

**Example:**
```python
from fastmcp import FastMCP

mcp = FastMCP("My Server")

@mcp.tool
async def search(query: str) -> str:
    return "results..."

# Built-in HTTP Streamable transport
mcp.run(transport="streamable-http", port=8000)
```

**Pros:**
- ✅ Full protocol support (including streaming)
- ✅ Any runtime, any framework
- ✅ Persistent connections
- ✅ Production-ready

**Cons:**
- ❌ Slightly slower cold starts than Functions
- ❌ More deployment complexity

**Comparison Table:**

| Factor | Functions (Extension) | Functions (Self-hosted) | Container Apps | Winner |
|--------|----------------|----------------|---------|
| **Cold Start** | ~1-3s (Python) | ~5-10s | Functions |
| **HTTP Protocol** | Limited (must fit HTTP model) | Any protocol | **Container Apps** |
| **MCP Transport** | Difficult (no streaming) | Native support | **Container Apps** |
| **Cost (idle)** | $0 | $0 (consumption) | Tie |
| **Cost (active)** | $0.20/M requests | $0.18/M requests | Tie |
| **Deployment** | Zip or Docker | Docker only | Functions |
| **Complexity** | Simple | More control | Functions |
| **MCP Fit** | ❌ Poor | ✅ Excellent | **Container Apps** |

**Why Container Apps won:**
- MCP Streamable HTTP requires persistent WebSocket-like connection
- Functions designed for short-lived request/response
- Container Apps native support for long-running connections
- Easy Docker deployment

**Understanding HTTP Streamable Transport:**

**What is it?**
HTTP Streamable is the recommended MCP transport (replaced SSE in March 2025). It uses a single HTTP POST endpoint with streaming responses.

**How it works:**
```
Client                          Server
  |                               |
  |--- POST /mcp ----------------→| (keep connection open)
  |    {jsonrpc request}          |
  |                               |
  |←-- HTTP 200 (chunked) --------| (stream response)
  |    {jsonrpc response chunk 1} |
  |    {jsonrpc response chunk 2} |
  |    ...                        |
  |←-- [connection close] --------|
```

**Key Characteristics:**
- Single endpoint: `POST /mcp`
- Content-Type: `application/json`
- Transfer-Encoding: `chunked` (for large responses)
- Connection stays open for streaming responses
- Supports request/response and notifications

**Why it matters:**
1. **Firewall-friendly**: Uses standard HTTP/HTTPS (unlike WebSocket)
2. **Load balancer compatible**: Works with reverse proxies
3. **Simpler than WebSocket**: No upgrade protocol needed
4. **Cloud-native**: Easy to deploy on any HTTP-capable platform

**Why Functions struggle:**
- Functions have execution time limits (5-10 min)
- Streaming requires keeping connection open
- Functions optimize for quick request/response
- No built-in support for chunked responses

**Why Container Apps excel:**
- No time limits on connections
- Native HTTP streaming support
- Can handle WebSocket-like persistent connections
- Full control over HTTP server behavior

#### MCP Framework: FastMCP vs SDK

| Factor | FastMCP | MCP Python SDK | Winner |
|--------|---------|----------------|---------|
| **API Style** | Decorators (`@mcp.tool`) | Class-based | **FastMCP** |
| **Transport** | Built-in HTTP | Manual setup | **FastMCP** |
| **Learning Curve** | Minimal | Steeper | **FastMCP** |
| **Flexibility** | Opinionated | Full control | SDK |
| **Production Ready** | Yes | Yes | Tie |

**FastMCP Example:**
```python
from fastmcp import FastMCP

mcp = FastMCP("My Server")

@mcp.tool
async def search(query: str) -> str:
    return "results..."

# One line deployment
mcp.run(transport="streamable-http", port=8000)
```

**SDK Example:**
```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

server = Server("my-server")

@server.list_tools()
async def list_tools():
    return [...]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search":
        return ...

# Manual transport setup
async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write)
```

**Our Decision:** FastMCP
- Faster development (decorator API)
- Built-in HTTP transport
- Less boilerplate
- Good for interviews (shows efficiency)

---

## PHASE 2: Minimal MCP Server Skeleton (AI-Assisted)

### AI Prompt Sequence

#### Prompt 0: Architecture Planning
```
Create a comprehensive architecture plan for an MCP Retrieval Server on Azure:

Requirements:
- Document-based Q&A system
- Authenticated access
- Agentic retrieval (AI-powered search)
- Deploy to Azure with IaC
- Cost-optimized serverless

Provide:
1. High-level architecture diagram (mermaid)
2. Component selection with justification:
   - Compute platform (Functions vs Container Apps)
   - Vector database (AI Search vs Cosmos vs PostgreSQL)
   - Authentication strategy
   - Document storage
3. Technology stack:
   - Language and frameworks
   - Azure services
   - Libraries and SDKs
4. Data flow:
   - Document ingestion pipeline
   - Query processing pipeline
5. Deployment strategy:
   - IaC tool (Bicep vs Terraform)
   - CI/CD approach
6. Cost estimation (per 1000 queries)
7. Development phases:
   - Phase 1: Basic MCP server
   - Phase 2: Azure infrastructure
   - Phase 3: Document ingestion
   - Phase 4: Retrieval implementation
   - Phase 5: Production hardening

Output format: Markdown document with diagrams, tables, and decision trees.
```

**What this prompt generates:**
- Complete architecture specification
- Technology selection rationale
- Implementation roadmap
- Cost/benefit analysis
- Risk assessment

**Why start with planning:**
- Validates approach before coding
- Identifies gaps early
- Creates shared understanding (team/stakeholders)
- Serves as reference during implementation

#### Prompt 1: Project Scaffolding
```
Create an Azure Developer CLI (azd) project structure for an MCP server:

Requirements:
- Python 3.11+
- Azure Container Apps for hosting
- Bicep for infrastructure
- Directory structure:
  - src/server/ (MCP server code)
  - infra/ (Bicep modules)
  - scripts/ (setup scripts)

Generate:
1. azure.yaml (azd configuration)
2. pyproject.toml (dependencies: fastmcp, azure-identity, azure-search-documents)
3. Dockerfile (multi-stage build)
4. infra/main.bicep (container apps + registry + log analytics)
```

#### Prompt 2: Basic MCP Server
```
Create a FastMCP server with HTTP Streamable transport:

File: src/server/basic_mcp_http.py

Requirements:
- Use fastmcp library
- HTTP Streamable transport on port 8000
- 3 sample tools: hello, echo, add_numbers
- Structured logging
- Environment variable configuration

Keep it minimal and production-ready.
```

#### Prompt 3: API Key Authentication
```
Add API key authentication middleware to the FastMCP server:

Requirements:
- Use Starlette BaseHTTPMiddleware
- Check X-API-Key header
- Read key from MCP_API_KEY env var
- Skip auth for /health endpoint
- Return 401 for invalid/missing key
- Wrap FastMCP app with middleware

Show the middleware class and integration code.
```

#### Prompt 4: Azure AI Search Infrastructure
```
Create Bicep modules for Azure AI Search setup:

Files:
- infra/core/ai/search.bicep
- infra/core/ai/openai.bicep
- infra/core/storage/storage-account.bicep

Requirements:
- Search service: Basic SKU, semantic search enabled, RBAC auth
- OpenAI: text-embedding-3-small + gpt-4o deployments
- Storage: Blob container named "documents"
- All with managed identity support

Generate the 3 Bicep modules.
```

#### Prompt 5: Search Index with Skillsets
```
Create a Python script to configure Azure AI Search:

File: scripts/setup_search.py

Requirements:
1. Create search index with:
   - Text fields: id, chunk, title, source_url, keywords
   - Vector field: chunk_vector (1536 dims)
   - Semantic configuration

2. Create data source pointing to blob storage (managed identity)

3. Create skillset with:
   - SplitSkill: 2000 token chunks, 200 overlap
   - AzureOpenAIEmbeddingSkill: 1536-dim embeddings
   - Index projections: one doc per chunk

4. Create indexer connecting datasource → skillset → index

Use azure-search-documents SDK. Include error handling.
```

#### Prompt 6: Knowledge Base Setup
```
Extend scripts/setup_search.py to create Knowledge Base for agentic retrieval:

Add two functions:
1. create_knowledge_source() - wraps the search index
2. create_knowledge_base() - configures agentic retrieval

Requirements:
- Knowledge Source: reference the index, semantic config
- Knowledge Base: use gpt-4o model, low reasoning effort
- Enable answer synthesis mode
- Include references and activity logging

Show the function implementations.
```

#### Prompt 7: MCP Resources for Documents
```
Add MCP resources to basic_mcp_http.py for document access:

Requirements:
1. @mcp.resource("docs://list")
   - Query search index
   - Aggregate chunks by document title
   - Return JSON list with title, source_url, chunk_count

2. @mcp.resource("docs://{title}")
   - Query chunks for specific document
   - Order by chunk ID
   - Concatenate and return full content

Use SearchClient, not KnowledgeBaseClient.
Show both resource implementations.
```

#### Prompt 8: MCP Tool for Agentic Retrieval
```
Add an MCP tool for agentic search to basic_mcp_http.py:

Requirements:
@mcp.tool
async def query_knowledge_base(question: str) -> str:
    - Use KnowledgeBaseRetrievalClient
    - Send question as KnowledgeBaseMessage
    - Include references and activity in request
    - Return JSON with:
      {
        "answer": "...",
        "references": [{"id", "document", "score"}],
        "activity": [query planning steps]
      }

Show the complete tool implementation.
```

#### Prompt 9: Health Check Endpoint
```
Add a health check endpoint for Container Apps probes:

Requirements:
- Use @mcp.custom_route("/health", methods=["GET"])
- Return JSON: {"status": "healthy", "service": "mcp-server"}
- Needed for startup, readiness, liveness probes

Update infra/core/host/container-app.bicep to add:
probes: [
  {type: 'Startup', httpGet: {path: '/health', port: 8000}},
  {type: 'Readiness', httpGet: {path: '/health', port: 8000}},
  {type: 'Liveness', httpGet: {path: '/health', port: 8000}}
]
```

#### Prompt 10: RBAC Role Assignments
```
Create Bicep modules for role assignments:

Files needed:
- infra/core/security/search-access.bicep (Search Index Data Contributor)
- infra/core/security/openai-access.bicep (Cognitive Services OpenAI User)
- infra/core/security/storage-access.bicep (Storage Blob Data Contributor)

Each module should:
- Take principalId and resource name as parameters
- Assign appropriate built-in role
- Use scope = resource::roleAssignments

Update infra/main.bicep to wire these up for the MCP server identity.
```

---

## PHASE 3: Retrieval System Design

### 3.1 Ingestion Pipeline Explanation

**Question:** "Walk me through how a document goes from upload to searchable"

**Answer:**
```
1. Upload Phase
   └─> User uploads PDF to Blob Storage "documents" container

2. Detection Phase
   └─> Indexer detects new blob (change tracking)

3. Extraction Phase
   └─> Blob indexer extracts text content
   └─> Metadata extracted (filename, modified date, URL)

4. Skillset Processing Phase
   ├─> SplitSkill: Divide into 2000-token chunks (200 overlap)
   │   Context: /document/content → /document/chunks/*
   │
   └─> EmbeddingSkill: Generate vector for each chunk
       Context: /document/chunks/* (processes each chunk)
       Output: /document/chunks/*/chunk_vector

5. Index Projection Phase
   └─> For each chunk in /document/chunks/*:
       ├─> Create new index document
       ├─> Copy: chunk text, chunk_vector, title, source_url
       └─> Set parent_id to link back to original blob

6. Indexing Phase
   └─> Documents written to search index
   └─> Vector index built (HNSW)
   └─> Inverted index built (BM25)

Result: 1 PDF → N index documents (one per chunk)
```

**Key Insight:** Index projections are the critical piece - they expand the document array into separate index documents.

```python
index_projection=SearchIndexerIndexProjection(
    selectors=[SearchIndexerIndexProjectionSelector(
        target_index_name=index_name,
        parent_key_field_name="parent_id",
        source_context="/document/chunks/*",  # ← "for each chunk"
        mappings=[
            InputFieldMappingEntry(name="chunk", source="/document/chunks/*"),
            InputFieldMappingEntry(name="chunk_vector", source="/document/chunks/*/chunk_vector"),
        ]
    )],
    parameters=SearchIndexerIndexProjectionsParameters(
        projection_mode="skipIndexingParentDocuments"  # ← Don't index full doc
    )
)
```

---

### 3.2 Citation & Passage Extraction

**Question:** "How do you return citations with your answers?"

**Answer:** Knowledge Base API handles this automatically

**Input Query:**
```python
request = KnowledgeBaseRetrievalRequest(
    messages=[
        KnowledgeBaseMessage(
            role="user",
            content=[KnowledgeBaseMessageTextContent(text="What is the vacation policy?")]
        )
    ],
    knowledge_source_params=[
        SearchIndexKnowledgeSourceParams(
            knowledge_source_name="documents-ks",
            include_references=True,              # ← Request citations
            include_reference_source_data=True,   # ← Include source text
            always_query_source=True              # ← Force retrieval
        )
    ],
    include_activity=True  # ← Debug info (query planning)
)
```

**Output Structure:**
```json
{
  "response": [
    {
      "role": "assistant",
      "content": [
        {
          "text": "According to the HR handbook [ref_id:1], employees receive 15 days of PTO annually [ref_id:2]..."
        }
      ]
    }
  ],
  "references": [
    {
      "id": "1",
      "doc_key": "aHR0cHM6Ly9zdG9yYWdlL2hyLXBvbGljeS5tZA_chunks_0",
      "reranker_score": 3.85,
      "source_data": {
        "chunk": "## Paid Time Off\\n\\nFull-time employees receive 15 days...",
        "title": "hr-policy-handbook.md",
        "source_url": "https://storage/hr-policy.md"
      }
    },
    {
      "id": "2",
      "doc_key": "...",
      "reranker_score": 3.72,
      "source_data": {...}
    }
  ],
  "activity": [
    {
      "type": "queryPlanning",
      "queries": ["vacation policy", "PTO days"]
    },
    {
      "type": "search",
      "knowledge_source": "documents-ks",
      "results_count": 5
    },
    {
      "type": "tokenUsage",
      "prompt_tokens": 1200,
      "completion_tokens": 350
    }
  ]
}
```

**Citation Flow:**
1. AI decomposes question → sub-queries
2. Hybrid search for each sub-query
3. Semantic reranker scores results
4. Top chunks sent to GPT-4o with instruction: "cite sources as [ref_id:N]"
5. GPT-4o generates answer with inline citations
6. API returns answer + reference list

**Why this is powerful:** Zero citation code - it's built into the Knowledge Base API.

---

### 3.3 Tool Integration

**Question:** "How does the MCP tool connect to your retrieval?"

**Answer:**

```python
@mcp.tool
async def query_knowledge_base(
    question: Annotated[str, "Question to answer"]
) -> str:
    """
    MCP Tool that wraps Knowledge Base API
    
    Flow:
    1. MCP Client calls this tool with question
    2. Forward to Knowledge Base API (agentic retrieval)
    3. Parse response (answer + references)
    4. Return structured JSON to client
    """
    
    # Get KB client (lazy init with managed identity)
    kb_client = get_kb_client()
    
    # Create retrieval request
    request = KnowledgeBaseRetrievalRequest(
        messages=[KnowledgeBaseMessage(
            role="user",
            content=[KnowledgeBaseMessageTextContent(text=question)]
        )],
        knowledge_source_params=[...],
        include_activity=True
    )
    
    # Execute agentic retrieval
    result = kb_client.retrieve(retrieval_request=request)
    
    # Extract answer from response
    answer_parts = []
    for message in result.response:
        for content in message.content:
            if hasattr(content, 'text'):
                answer_parts.append(content.text)
    answer = "\n".join(answer_parts)
    
    # Extract references
    references = []
    for ref in result.references:
        references.append({
            "id": ref.id,
            "document": extract_doc_name(ref.doc_key),
            "score": ref.reranker_score,
            "source_data": ref.source_data
        })
    
    # Return structured response
    return json.dumps({
        "answer": answer,
        "references": references,
        "activity": [act.as_dict() for act in result.activity]
    }, indent=2)
```

**Key Points:**
- Tool is a thin wrapper around Knowledge Base API
- All intelligence happens in Azure AI Search
- MCP tool just formats the response for clients
- Managed Identity handles auth automatically

---

## PHASE 4: Deployment Strategy

### 4.1 Containerization

**Question:** "How do you package this for production?"

**Answer:** Multi-stage Docker build

**Dockerfile Strategy:**
```dockerfile
# Stage 1: Build dependencies
FROM python:3.13-alpine AS build
RUN apk add gcc musl-dev libffi-dev  # Compile native extensions
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/
WORKDIR /code
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project  # Install deps only
COPY . .
RUN uv sync --locked  # Install project

# Stage 2: Runtime (minimal)
FROM python:3.13-alpine AS final
RUN adduser -S app -G app  # Non-root user
COPY --from=build --chown=app:app /code /code
WORKDIR /code/src/server
USER app
ENV PATH="/code/.venv/bin:$PATH"
EXPOSE 8000
CMD ["python", "basic_mcp_http.py"]
```

**Why multi-stage?**
- Stage 1: Build artifacts (large, has compilers)
- Stage 2: Runtime only (small, secure)
- Final image ~100MB vs ~500MB single-stage

**Why Alpine?**
- Minimal attack surface
- Faster cold starts
- Lower memory footprint

**What is Multi-Stage Docker Build?**

Multi-stage builds use multiple `FROM` statements in a Dockerfile, where each stage can copy artifacts from previous stages:

**Without multi-stage (single build):**
```dockerfile
FROM python:3.13
RUN apt-get update && apt-get install -y gcc g++ musl-dev  # Build tools
COPY . /app
RUN pip install -r requirements.txt  # Installs with native compilation
CMD ["python", "app.py"]
# Final image: ~800MB (includes build tools, source files, build cache)
```

**With multi-stage:**
```dockerfile
# Stage 1: Build (includes compilers, build tools)
FROM python:3.13 AS build
RUN apt-get install gcc g++
COPY requirements.txt .
RUN pip install -r requirements.txt

# Stage 2: Runtime (minimal, only what's needed)
FROM python:3.13-alpine  # Smaller base
COPY --from=build /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY app.py .
CMD ["python", "app.py"]
# Final image: ~100MB (no build tools, only runtime deps)
```

**Benefits:**
1. **Smaller images**: Build artifacts left in build stage
2. **Faster deployments**: Less data to transfer
3. **More secure**: Fewer attack vectors (no compilers in prod)
4. **Better caching**: Build and runtime layers cached separately

**Our Dockerfile uses 2 stages:**
- **Build stage**: Compiles native extensions (cryptography, grpcio)
- **Final stage**: Only compiled wheels + runtime

---

### 4.2 Configuration Management

**Environment Variables (set by Bicep):**
```bash
# Azure resource endpoints
AZURE_SEARCH_ENDPOINT=https://xyz-search.search.windows.net
AZURE_OPENAI_ENDPOINT=https://xyz-openai.openai.azure.com

# Managed Identity
AZURE_CLIENT_ID=abc-123-managed-identity-id

# Optional: API key authentication
MCP_API_KEY=your-secret-key-here

# Index/KB names
AZURE_SEARCH_INDEX=documents
AZURE_KNOWLEDGE_BASE_NAME=documents-kb
AZURE_KNOWLEDGE_SOURCE_NAME=documents-ks
```

**Bicep Configuration:**
```bicep
module server 'core/host/container-app.bicep' = {
  params: {
    name: '${prefix}-server'
    containerImage: containerRegistry.outputs.loginServer + '/server:${tag}'
    
    env: [
      { name: 'AZURE_SEARCH_ENDPOINT', value: search.outputs.endpoint }
      { name: 'AZURE_OPENAI_ENDPOINT', value: openai.outputs.endpoint }
      { name: 'AZURE_CLIENT_ID', value: serverIdentity.outputs.clientId }
      { name: 'AZURE_SEARCH_INDEX', value: 'documents' }
      { name: 'AZURE_KNOWLEDGE_BASE_NAME', value: 'documents-kb' }
      { name: 'AZURE_KNOWLEDGE_SOURCE_NAME', value: 'documents-ks' }
    ]
    
    secrets: !empty(mcpApiKey) ? [
      { name: 'mcp-api-key', value: mcpApiKey }
    ] : []
    
    identity: {
      type: 'UserAssigned'
      userAssignedIdentities: {
        '${serverIdentity.outputs.id}': {}
      }
    }
  }
}
```

---

### 4.3 Client Connection

**VS Code MCP Configuration** (`.vscode/mcp.json`):
```json
{
  "servers": {
    "azure-search-mcp": {
      "type": "http",
      "url": "https://xyz-server.azurecontainerapps.io/mcp",
      "headers": {
        "X-API-Key": "${env:MCP_API_KEY}"
      }
    }
  }
}
```

**Claude Desktop Configuration**:
```json
{
  "mcpServers": {
    "azure-search": {
      "command": "node",
      "args": ["/path/to/mcp-http-proxy.js"],
      "env": {
        "MCP_HTTP_URL": "https://xyz-server.azurecontainerapps.io/mcp",
        "MCP_API_KEY": "your-secret-key-here"
      }
    }
  }
}
```

**Test with MCP Inspector:**
```bash
npx @modelcontextprotocol/inspector https://xyz-server.azurecontainerapps.io/mcp \
  -H "X-API-Key: your-secret-key-here"
```

---

### 4.3.5 Agent-to-Agent Integration

**Question:** "Is your MCP server designed for agent-to-agent communication?"

**Answer:** Yes and no - it depends on the definition:

#### What We Built: LLM-to-Agent Architecture

```
Claude/ChatGPT → [MCP Protocol] → Our MCP Server → Azure AI Search (Agent)
    (Client)                       (Tool Provider)     (Agentic Retrieval)
```

**Our server is a tool provider** that:
- Exposes `query_knowledge_base` tool
- Forwards requests to Azure AI Search's **agentic retrieval** (Knowledge Base API)
- Returns AI-generated answers with citations

**The "agent" in our system is Azure AI Search**, which:
- Plans queries (decomposes complex questions)
- Executes multi-hop searches
- Synthesizes answers with GPT-4o
- Returns structured responses

**So technically:** LLM Client → MCP Server → AI Agent (Azure)

#### True Agent-to-Agent (Not Our Implementation)

**What true agent-to-agent would look like:**

```
Agent A (Orchestrator)     Agent B (Document Expert)
    ↓                              ↓
  [MCP Client]    →    [MCP Server]
                            ↓
                       Azure AI Search
```

**Example scenario:**
```python
# Agent A (research assistant)
agent_a = AutonomousAgent(
    name="Research Assistant",
    mcp_servers=["document-expert", "web-search", "calculator"]
)

# Agent A decides it needs document information
task = "Write a report on Q3 revenue"
agent_a.plan()  # "I need financial data → use document-expert MCP"
result = agent_a.use_tool("document-expert", "query_knowledge_base", 
                          {"question": "What was Q3 2025 revenue?"})

# Agent B (our MCP server) receives request and responds
# Agent A synthesizes the report using Agent B's response
```

**Key differences:**

| Our Implementation | True Agent-to-Agent |
|-------------------|---------------------|
| LLM uses our server as a tool | Agent uses our server as a tool |
| User decides when to query | Agent autonomously decides when to query |
| Single-turn interactions | Multi-turn agent collaboration |
| Stateless server | Potentially stateful agents |

**Future extension (Agent-to-Agent):**

To support true agent-to-agent, add:
1. **Session management**: Track conversation history per agent
2. **Agent authentication**: Identify calling agent, not just user
3. **Usage quotas**: Per-agent rate limits
4. **Callback support**: Agent B can notify Agent A of updates

**Example:**
```python
@mcp.tool
async def query_knowledge_base(
    question: str,
    session_id: str = None,  # ← Track agent session
    callback_url: str = None  # ← Notify agent when done
) -> str:
    # Async processing for long queries
    if callback_url:
        # Process in background, POST result to callback_url
        asyncio.create_task(process_and_callback(question, callback_url))
        return {"status": "processing", "session_id": session_id}
    else:
        # Synchronous response
        return await process_query(question)
```

### 4.4 Deployment Workflow

**Single Command Deployment:**
```bash
azd up
```

**What happens:**

1. **Provision** (`azd provision`)
   - Bicep generates ARM template
   - Creates resource group
   - Deploys all Azure resources
   - Configures RBAC roles
   - Sets environment variables

2. **Post-Provision Hook** (automatic)
   ```bash
   uv run python scripts/setup_search.py
   ```
   - Creates search index
   - Creates skillset & indexer
   - Creates knowledge base

3. **Deploy** (`azd deploy`)
   - Builds Docker image
   - Pushes to Azure Container Registry
   - Updates Container App with new image
   - Waits for health check

4. **Output**
   ```
   MCP Server URL: https://xyz-server.azurecontainerapps.io/mcp
   Search Endpoint: https://xyz-search.search.windows.net
   ```

**azure.yaml:**
```yaml
name: mcp-server-ai-search

services:
  server:
    project: src/server
    host: containerapp
    language: python

hooks:
  postprovision:
    shell: sh
    run: uv run python scripts/setup_search.py
    interactive: true
    continueOnError: false
```

---

### 4.5 Alternative Deployment Methods (Without azd)

**Question:** "What if I don't want to use Azure Developer CLI?"

#### Option 1: Azure CLI + Bicep (Manual)

**Step 1: Deploy infrastructure**
```bash
# Create resource group
az group create --name mcp-rg --location eastus

# Deploy Bicep template
az deployment group create \
  --resource-group mcp-rg \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json \
  --parameters mcpApiKey="$MCP_API_KEY"

# Get outputs
CONTAINER_REGISTRY=$(az deployment group show \
  --resource-group mcp-rg \
  --name main \
  --query properties.outputs.containerRegistryName.value -o tsv)

SEARCH_ENDPOINT=$(az deployment group show \
  --resource-group mcp-rg \
  --name main \
  --query properties.outputs.searchEndpoint.value -o tsv)
```

**Step 2: Run post-provision script**
```bash
# Set environment variables
export AZURE_SEARCH_ENDPOINT=$SEARCH_ENDPOINT
export AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT
export AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_NAME

# Run setup script
python scripts/setup_search.py
```

**Step 3: Build and push Docker image**
```bash
# Login to ACR
az acr login --name $CONTAINER_REGISTRY

# Build and tag
docker build -t $CONTAINER_REGISTRY.azurecr.io/server:latest src/server/

# Push
docker push $CONTAINER_REGISTRY.azurecr.io/server:latest
```

**Step 4: Update Container App**
```bash
az containerapp update \
  --name mcp-server \
  --resource-group mcp-rg \
  --image $CONTAINER_REGISTRY.azurecr.io/server:latest
```

#### Option 2: Terraform (Alternative IaC)

**main.tf:**
```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "main" {
  name     = "mcp-rg"
  location = "East US"
}

resource "azurerm_container_registry" "acr" {
  name                = "mcpregistry"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
}

resource "azurerm_search_service" "search" {
  name                = "mcp-search"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "basic"
  
  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_container_app_environment" "env" {
  name                = "mcp-env"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
}

resource "azurerm_container_app" "server" {
  name                         = "mcp-server"
  container_app_environment_id = azurerm_container_app_environment.env.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  
  template {
    container {
      name   = "server"
      image  = "${azurerm_container_registry.acr.login_server}/server:latest"
      cpu    = 0.5
      memory = "1Gi"
      
      env {
        name  = "AZURE_SEARCH_ENDPOINT"
        value = "https://${azurerm_search_service.search.name}.search.windows.net"
      }
    }
  }
}
```

**Deploy:**
```bash
terraform init
terraform plan
terraform apply
```

#### Option 3: GitHub Actions CI/CD

**.github/workflows/deploy.yml:**
```yaml
name: Deploy MCP Server

on:
  push:
    branches: [main]

env:
  AZURE_RESOURCE_GROUP: mcp-rg
  CONTAINER_REGISTRY: mcpregistry
  CONTAINER_APP: mcp-server

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Deploy Infrastructure
      run: |
        az deployment group create \
          --resource-group $AZURE_RESOURCE_GROUP \
          --template-file infra/main.bicep
    
    - name: Setup Search Index
      run: |
        pip install -r requirements.txt
        python scripts/setup_search.py
      env:
        AZURE_SEARCH_ENDPOINT: ${{ secrets.SEARCH_ENDPOINT }}
    
    - name: Build and Push Docker
      run: |
        az acr login --name $CONTAINER_REGISTRY
        docker build -t $CONTAINER_REGISTRY.azurecr.io/server:${{ github.sha }} .
        docker push $CONTAINER_REGISTRY.azurecr.io/server:${{ github.sha }}
    
    - name: Update Container App
      run: |
        az containerapp update \
          --name $CONTAINER_APP \
          --resource-group $AZURE_RESOURCE_GROUP \
          --image $CONTAINER_REGISTRY.azurecr.io/server:${{ github.sha }}
```

#### Option 4: Azure Portal (Manual/GUI)

**Step-by-step:**
1. **Create Resource Group**: Portal → Resource Groups → Create
2. **Create Container Registry**: Portal → Container Registries → Create
3. **Create AI Search**: Portal → AI Search → Create (Basic SKU)
4. **Create Container Apps Environment**: Portal → Container Apps → Create Environment
5. **Build locally and push**:
   ```bash
   docker build -t myregistry.azurecr.io/server:v1 .
   docker push myregistry.azurecr.io/server:v1
   ```
6. **Create Container App**: Portal → Container Apps → Create
   - Select image from ACR
   - Add environment variables
   - Configure health probes
7. **Run setup script** from local machine with Azure CLI credentials

#### Comparison

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **azd** | One command, integrated | Opinionated | Quick demos, learning |
| **Azure CLI** | Flexible, scriptable | Manual steps | Custom workflows |
| **Terraform** | Multi-cloud, state mgmt | More complex | Enterprise IaC |
| **GitHub Actions** | Automated CI/CD | Requires setup | Production deployments |
| **Portal** | Visual, easy to learn | Not repeatable | One-off testing |

**Environment Management Without azd:**

```bash
# Dev environment
export AZURE_SUBSCRIPTION_ID="dev-sub-id"
export RESOURCE_GROUP="mcp-dev-rg"
export LOCATION="eastus"

# Prod environment
export AZURE_SUBSCRIPTION_ID="prod-sub-id"
export RESOURCE_GROUP="mcp-prod-rg"
export LOCATION="westus2"

# Deploy to specific env
az account set --subscription $AZURE_SUBSCRIPTION_ID
az deployment group create --resource-group $RESOURCE_GROUP ...
```

**Parameter files per environment:**
```
infra/
  main.bicep
  parameters/
    dev.parameters.json
    staging.parameters.json
    prod.parameters.json

# Deploy to staging
az deployment group create \
  --parameters infra/parameters/staging.parameters.json
```

---

## Summary: Key Interview Talking Points

### Architecture Decisions
1. ✅ **API Key + Managed Identity** - Simple client auth, passwordless Azure access
2. ✅ **Pull Model (Indexer)** - Zero-code ingestion, automatic chunking/embedding
3. ✅ **Agentic Retrieval** - AI query planning, answer synthesis, automatic citations
4. ✅ **Container Apps** - Better MCP transport support than Functions
5. ✅ **FastMCP** - Fastest path to working server, decorator API

### AI Tool Usage
- Break complex task into logical prompts
- Generate scaffolding first, then add features incrementally
- Use AI for Bicep/Docker boilerplate (saves time)
- Focus human effort on architecture decisions

### Production Readiness
- Multi-stage Docker (security + size)
- Health probes (startup/readiness/liveness)
- RBAC with Managed Identity (zero secrets)
- Structured logging
- Error handling in skillsets & tools

### What Makes This Special
- **Agentic Retrieval** - Not just vector search, actual AI reasoning
- **Single Command Deploy** - `azd up` does everything
- **MCP Best Practices** - Proper resources vs tools distinction
- **Cost Optimized** - Scale-to-zero when idle
