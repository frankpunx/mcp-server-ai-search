# Architecture Diagrams

This folder contains architecture diagrams for the MCP Server AI Search project.

---

## High-Level Architecture

```mermaid
graph TB
    Client[MCP Client<br/>Claude/ChatGPT/IDE] -->|Streamable HTTP| ACA[Azure Container Apps<br/>MCP Server]
    
    subgraph Azure Cloud
        ACA -->|Managed Identity| Entra[Microsoft Entra ID]
        ACA -->|Agentic Retrieval| AIS[Azure AI Search<br/>Knowledge Base]
        ACA -->|Embeddings + Chat| AOAI[Azure OpenAI Service<br/>text-embedding-3-small<br/>gpt-4o]
        ACA -->|Read Documents| Blob[Azure Blob Storage<br/>Raw Documents]
        
        Blob -.->|Indexer| AIS
        AIS -.->|Embedding Skill| AOAI
    end
    
    style ACA fill:#0078d4
    style AIS fill:#50e6ff
    style AOAI fill:#ff6700
```

---

## Azure Resource Architecture

```mermaid
graph TB
    subgraph RG[Resource Group]
        subgraph Compute
            CAE[Container Apps Environment]
            CA[Container App<br/>MCP Server]
            ACR[Container Registry]
        end
        
        subgraph AI Services
            Search[Azure AI Search<br/>• Semantic Ranker: Standard<br/>• Knowledge Base<br/>• Knowledge Source]
            OpenAI[Azure OpenAI<br/>• text-embedding-3-small<br/>• gpt-4o]
        end
        
        subgraph Storage
            Blob[Blob Storage<br/>documents container]
        end
        
        subgraph Identities
            UAI[MCP Server Identity<br/>User Assigned]
            SMI[Search Service Identity<br/>System Assigned]
        end
        
        subgraph Monitoring
            LA[Log Analytics]
        end
    end
    
    CA --> CAE
    CA -.->|Pull Image| ACR
    
    %% MCP Server Identity permissions
    UAI -->|ACR Pull| ACR
    UAI -->|Search Index Data Contributor| Search
    UAI -->|Cognitive Services OpenAI User| OpenAI
    UAI -->|Storage Blob Data Contributor| Blob
    
    %% Search Service Identity permissions (for skillset)
    SMI -->|Cognitive Services OpenAI User| OpenAI
    SMI -->|Storage Blob Data Reader| Blob
    
    CA --> LA
    Search --> LA
    
    style CA fill:#0078d4
    style Search fill:#50e6ff
    style OpenAI fill:#ff6700
    style UAI fill:#00bcf2
    style SMI fill:#00bcf2
```

---

## Data Flow - Agentic Retrieval

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant MCP as MCP Server
    participant KB as AI Search<br/>Knowledge Base
    participant AOAI as Azure OpenAI
    
    Client->>MCP: search_documents(query)
    MCP->>KB: POST /knowledgeBases/{name}/retrieve
    KB->>AOAI: Query planning (gpt-4o)
    AOAI-->>KB: Subqueries
    KB->>KB: Semantic Search + Rerank
    KB->>AOAI: Answer synthesis (gpt-4o)
    AOAI-->>KB: Formatted answer
    KB-->>MCP: Response with citations [ref_id:N]
    MCP-->>Client: Answer + source attribution
```

---

## Document Ingestion Pipeline

```mermaid
graph LR
    subgraph "azd up"
        Bicep[Bicep IaC] -->|provision| Resources[Azure Resources]
        Resources --> Hook[postprovision hook]
        Hook -->|setup_search.py| Setup[Create Index + Indexer]
    end
    
    subgraph "Automated Indexing"
        Docs[Raw Documents<br/>PDF, DOCX, MD] -->|Upload| Blob[Azure Blob Storage]
        Blob -->|Triggers| Indexer[AI Search Indexer]
        Indexer -->|Skillset| Chunk[Split into Chunks]
        Chunk -->|Azure OpenAI| Embed[Generate Embeddings]
        Embed --> Index[Search Index]
    end
    
    subgraph "Agentic Retrieval"
        Index --> KS[Knowledge Source]
        KS --> KB[Knowledge Base]
        KB -->|retrieve API| Response[Grounded Response]
    end
    
    style Bicep fill:#0078d4
    style Indexer fill:#50e6ff
    style KB fill:#ff6700
```

### Deployment Flow

```
azd up
├── 1. azd provision (Bicep)
│   ├── Search Service (semantic ranker: standard)
│   ├── Azure OpenAI (text-embedding-3-small, gpt-4o)
│   ├── Blob Storage (documents container)
│   └── Container App
│
├── 2. postprovision hook (setup_search.py) ← AUTO
│   ├── Create Search Index
│   ├── Create Data Source (→ Blob)
│   ├── Create Skillset (chunking + embedding)
│   ├── Create Indexer
│   ├── Create Knowledge Source
│   └── Create Knowledge Base
│
└── 3. azd deploy (Docker)
    └── Deploy MCP Server
```

### After Deployment

1. **Upload documents** to Blob Storage container
2. **Indexer runs automatically** (or trigger manually)
3. **MCP Server uses Knowledge Base** for agentic retrieval

---

## Authentication Flow

```mermaid
graph LR
    subgraph Development
        Dev[Developer] -->|Azure CLI| LocalAuth[DefaultAzureCredential]
    end
    
    subgraph Production
        CA[Container App] -->|User Assigned Identity| MI[Managed Identity]
        MI -->|AZURE_CLIENT_ID| UAI[ManagedIdentityCredential]
    end
    
    LocalAuth -->|Token| Services[Azure Services]
    UAI -->|Token| Services
    
    subgraph Services
        Search[AI Search]
        OpenAI[Azure OpenAI]
        Blob[Blob Storage]
    end
    
    style MI fill:#00bcf2
    style UAI fill:#00bcf2
```

---

## MCP Protocol Surfaces

```mermaid
graph TB
    subgraph "MCP Server (FastMCP)"
        subgraph Tools
            T1[search<br/>query: str<br/>Returns grounded response with citations]
        end
        
        subgraph "Transport"
            HTTP[Streamable HTTP<br/>Port 8000]
        end
    end
    
    Client[MCP Client] -->|POST /mcp| HTTP
    HTTP -->|tools/list| Tools
    HTTP -->|tools/call search| T1
    T1 -->|KnowledgeBaseRetrievalClient| KB[AI Search<br/>Knowledge Base]
    
    style Tools fill:#fff3e0
    style HTTP fill:#e1f5fe
    style KB fill:#ff6700
```

### Current Implementation

| MCP Surface | Status | Details |
|-------------|--------|---------|
| **Tools** | ✅ Implemented | `search` - Agentic retrieval via Knowledge Base |
| **Resources** | 🔮 Future | Could expose `docs://` for document access |
| **Prompts** | 🔮 Future | Could add Q&A templates |

---

## Rendering Diagrams

These diagrams use [Mermaid](https://mermaid.js.org/) syntax and render automatically in:
- GitHub (README files, issues, PRs)
- VS Code (with Mermaid extension)
- Azure DevOps Wiki
- Notion, Confluence (with plugins)

To preview locally, install the VS Code extension:
```
ext install bierner.markdown-mermaid
```
