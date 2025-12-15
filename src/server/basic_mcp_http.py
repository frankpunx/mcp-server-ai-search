"""
MCP Server with Azure AI Search (HTTP Streamable Transport)

Run locally:     uv run src/server/basic_mcp_http.py
Debug:           F5 in VS Code
MCP Inspector:   npx @modelcontextprotocol/inspector http://localhost:8000/mcp
"""

import json
import logging
import os
from typing import Annotated

from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.search.documents import SearchClient
from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
from azure.search.documents.knowledgebases.models import (
    KnowledgeBaseMessage,
    KnowledgeBaseMessageTextContent,
    KnowledgeBaseRetrievalRequest,
    KnowledgeRetrievalLowReasoningEffort,
    SearchIndexKnowledgeSourceParams,
)
from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

load_dotenv(override=True)

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AISearchMCP")

# API Key authentication (optional)
MCP_API_KEY = os.getenv("MCP_API_KEY")

# Azure configuration
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "documents")
AZURE_KNOWLEDGE_BASE_NAME = os.getenv("AZURE_KNOWLEDGE_BASE_NAME", "documents-kb")
AZURE_KNOWLEDGE_SOURCE_NAME = os.getenv("AZURE_KNOWLEDGE_SOURCE_NAME", "documents-ks")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")  # For managed identity

# Initialize Azure credential
if AZURE_CLIENT_ID:
    # Use managed identity in Azure Container Apps
    credential = ManagedIdentityCredential(client_id=AZURE_CLIENT_ID)
    logger.info(f"Using Managed Identity: {AZURE_CLIENT_ID}")
else:
    # Use DefaultAzureCredential for local development
    credential = DefaultAzureCredential()
    logger.info("Using DefaultAzureCredential")

# Initialize Knowledge Base client (lazy initialization)
_kb_client = None
_search_client = None


def get_kb_client() -> KnowledgeBaseRetrievalClient:
    """Get or create the Knowledge Base client."""
    global _kb_client
    if _kb_client is None:
        if not AZURE_SEARCH_ENDPOINT:
            raise ValueError("AZURE_SEARCH_ENDPOINT environment variable is required")
        _kb_client = KnowledgeBaseRetrievalClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            knowledge_base_name=AZURE_KNOWLEDGE_BASE_NAME,
            credential=credential,
        )
        logger.info(f"Initialized KB client: {AZURE_SEARCH_ENDPOINT} / {AZURE_KNOWLEDGE_BASE_NAME}")
    return _kb_client


def get_search_client() -> SearchClient:
    """Get or create the Search client for direct index queries."""
    global _search_client
    if _search_client is None:
        if not AZURE_SEARCH_ENDPOINT:
            raise ValueError("AZURE_SEARCH_ENDPOINT environment variable is required")
        _search_client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            index_name=AZURE_SEARCH_INDEX,
            credential=credential,
        )
        logger.info(f"Initialized Search client: {AZURE_SEARCH_ENDPOINT} / {AZURE_SEARCH_INDEX}")
    return _search_client


# Initialize the MCP server
mcp = FastMCP("Azure AI Search MCP Server")


# ==================== Health Check Endpoint ====================
# Required for Azure Container Apps health probes (startup, readiness, liveness)
@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request):
    """
    Health check endpoint for Azure Container Apps probes.
    
    Returns a simple JSON response indicating the service is healthy.
    Container Apps uses this for:
    - Startup probes: Verify container started successfully
    - Readiness probes: Verify service can accept traffic  
    - Liveness probes: Verify service is still running
    """
    from starlette.responses import JSONResponse
    return JSONResponse({
        "status": "healthy", 
        "service": "mcp-ai-search-server"
    })


# API Key authentication middleware
class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to check for API key in X-API-Key header."""

    async def dispatch(self, request, call_next):
        # Skip auth for health checks
        if request.url.path in ["/health", "/healthz", "/"]:
            return await call_next(request)
        
        # If MCP_API_KEY is set, require authentication
        if MCP_API_KEY:
            api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
            if api_key != MCP_API_KEY:
                client_host = request.client.host if request.client else "unknown"
                logger.warning(f"Unauthorized request from {client_host}")
                return JSONResponse(
                    {"error": "Unauthorized", "message": "Invalid or missing API key"},
                    status_code=401,
                )
        
        return await call_next(request)


# Add middleware to FastMCP's underlying Starlette app
# Note: FastMCP exposes the app via mcp.get_app() after initialization
_middleware_added = False


def _add_api_key_middleware():
    """Add API key middleware to the FastMCP app (called once at startup)."""
    global _middleware_added
    if not _middleware_added and MCP_API_KEY:
        # FastMCP uses Starlette, middleware is added via the ASGI app
        logger.info("API Key authentication enabled (MCP_API_KEY is set)")
        _middleware_added = True
    elif not MCP_API_KEY:
        logger.warning("API Key authentication DISABLED (MCP_API_KEY not set)")


@mcp.tool
async def hello(
    name: Annotated[str, "Name to greet"],
) -> str:
    """Say hello to someone."""
    logger.info(f"Hello called with name: {name}")
    return f"Hello, {name}! Welcome to the MCP Server."


@mcp.tool
async def echo(
    message: Annotated[str, "Message to echo back"],
) -> str:
    """Echo back the provided message."""
    logger.info(f"Echo called with message: {message}")
    return f"Echo: {message}"


@mcp.tool
async def add_numbers(
    a: Annotated[float, "First number"],
    b: Annotated[float, "Second number"],
) -> float:
    """Add two numbers together."""
    result = a + b
    logger.info(f"Add called: {a} + {b} = {result}")
    return result


@mcp.tool
async def query_knowledge_base(
    question: Annotated[str, "The question to answer using the knowledge base"],
) -> str:
    """
    Query the knowledge base using AI-powered agentic retrieval.
    
    This tool uses Azure AI Search to find relevant documents and synthesize
    an answer with citations. The AI reasons about your question, plans
    search queries, and combines information from multiple sources.
    
    Use this for questions about:
    - Company policies and procedures
    - Product documentation and guides
    - Technical specifications
    - Financial reports and metrics
    
    Examples:
    - "What is the vacation policy?"
    - "How do I reset my SmartWidget Pro?"
    - "What was Q3 2025 revenue?"
    """
    logger.info(f"query_knowledge_base called with question: {question}")
    
    try:
        kb_client = get_kb_client()
        
        request = KnowledgeBaseRetrievalRequest(
            messages=[
                KnowledgeBaseMessage(
                    role="user",
                    content=[KnowledgeBaseMessageTextContent(text=question)],
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
        
        # Extract the answer - response is a list of KnowledgeBaseMessage
        answer_parts = []
        if result.response:
            for message in result.response:
                if hasattr(message, "content") and message.content:
                    for content in message.content:
                        # Content can be text or image; we want text
                        content_dict = content.as_dict() if hasattr(content, "as_dict") else {}
                        if "text" in content_dict:
                            answer_parts.append(content_dict["text"])
        
        answer = "\n".join(answer_parts) if answer_parts else "No answer found."
        
        # Extract references with source data
        references = []
        seen_docs = set()
        if result.references:
            for ref in result.references:
                ref_dict = ref.as_dict() if hasattr(ref, "as_dict") else {}
                ref_id = ref_dict.get("id", "?")
                doc_key = ref_dict.get("doc_key", "")
                score = ref_dict.get("reranker_score", 0)
                source_data = ref_dict.get("source_data", {})
                
                # Extract document name from doc_key
                doc_name = "Unknown"
                if doc_key:
                    try:
                        import base64
                        # Format: hash_base64url_chunks_N  
                        # The base64 part encodes the blob URL
                        if "_chunks_" in doc_key:
                            b64_part = doc_key.split("_chunks_")[0].split("_", 1)[1]
                        else:
                            b64_part = doc_key.split("_", 1)[1] if "_" in doc_key else doc_key
                        
                        # Remove trailing digits (chunk index suffix)
                        b64_part = b64_part.rstrip("0123456789")
                        
                        # Fix base64 padding
                        padding = 4 - len(b64_part) % 4
                        if padding != 4:
                            b64_part += "=" * padding
                        
                        decoded = base64.urlsafe_b64decode(b64_part).decode("utf-8")
                        doc_name = decoded.split("/")[-1] if "/" in decoded else decoded
                    except Exception:
                        doc_name = doc_key[-30:] if len(doc_key) > 30 else doc_key
                
                # Deduplicate by document name
                if doc_name not in seen_docs:
                    seen_docs.add(doc_name)
                    references.append({
                        "id": ref_id,
                        "document": doc_name,
                        "score": round(score, 2),
                        "source_data": source_data,
                    })
        
        # Extract activity (query planning, search steps, token usage)
        activity = []
        if result.activity:
            for act in result.activity:
                activity.append(act.as_dict() if hasattr(act, "as_dict") else {})
        
        # Build structured response
        structured_response = {
            "answer": answer,
            "references": references,
            "activity": activity,
        }
        
        logger.info(f"Search returned {len(references)} unique references, {len(activity)} activity steps")
        return json.dumps(structured_response, indent=2)
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return json.dumps({"error": str(e)})


# ==================== Document Functions ====================

async def _list_documents_impl() -> str:
    """Implementation for listing documents."""
    try:
        search_client = get_search_client()
        
        # Query all documents and aggregate by title
        results = search_client.search(
            search_text="*",
            select=["title", "source_url"],
            top=1000,  # Get all chunks
        )
        
        # Aggregate chunks by document title
        documents: dict[str, dict] = {}
        for result in results:
            title = result.get("title", "Unknown")
            if title not in documents:
                documents[title] = {
                    "title": title,
                    "source_url": result.get("source_url", ""),
                    "chunk_count": 0,
                }
            documents[title]["chunk_count"] += 1
        
        doc_list = sorted(documents.values(), key=lambda x: x["title"])
        
        logger.info(f"list_documents returned {len(doc_list)} documents")
        return json.dumps({
            "total_documents": len(doc_list),
            "documents": doc_list,
        }, indent=2)
        
    except Exception as e:
        logger.error(f"list_documents failed: {e}")
        return json.dumps({"error": str(e)})


async def _get_document_impl(title: str) -> str:
    """Implementation for getting a document by title."""
    try:
        search_client = get_search_client()
        
        # Search for all chunks of this document
        results = search_client.search(
            search_text="*",
            filter=f"title eq '{title}'",
            select=["title", "chunk", "source_url"],
            top=100,  # Get all chunks of this document
            order_by=["id asc"],  # Order by chunk ID to reconstruct document
        )
        
        chunks = []
        source_url = ""
        for result in results:
            chunks.append(result.get("chunk", ""))
            if not source_url:
                source_url = result.get("source_url", "")
        
        if not chunks:
            return json.dumps({"error": f"Document '{title}' not found"})
        
        # Concatenate chunks to reconstruct document
        full_content = "\n\n".join(chunks)
        
        logger.info(f"get_document returned {len(chunks)} chunks for '{title}'")
        return json.dumps({
            "title": title,
            "source_url": source_url,
            "chunk_count": len(chunks),
            "content": full_content,
        }, indent=2)
        
    except Exception as e:
        logger.error(f"get_document failed: {e}")
        return json.dumps({"error": str(e)})


# ==================== MCP Resources ====================
# Note: Document listing and reading is exposed via Resources (not Tools)
# per MCP best practices:
# - Resources: For static/semi-static data reading (URI-based, cacheable)
# - Tools: For actions with parameters and computation (like 'search' with AI reasoning)

# TODO(docs resources): This Search-index-backed docs browser is temporary.
# - It's convenient for a PoC because the indexer normalizes mixed formats (PDF/DOCX/etc) into
#   extracted text that is chat-friendly.
# - It is NOT efficient/scalable because listing/reading documents requires scanning and
#   stitching chunk records (cost grows with number of chunks, not number of documents).
#
# Preferred scalable design:
# - Make `docs://list` list blobs (1 blob = 1 document) from Azure Blob Storage.
# - Make `docs://{title}` download the blob for text formats;

@mcp.resource("resource://info")
async def get_server_info() -> str:
    """Get information about the MCP server."""
    return f"Azure AI Search MCP Server v1.0.0 - Knowledge Base: {AZURE_KNOWLEDGE_BASE_NAME}"


@mcp.resource("docs://list")
async def resource_list_documents() -> str:
    """
    List all available documents as an MCP resource.
    
    URI: docs://list
    Returns: JSON list of document titles with metadata
    """
    logger.info("Resource docs://list accessed")
    return await _list_documents_impl()


@mcp.resource("docs://{title}")
async def resource_get_document(title: str) -> str:
    """
    Get a specific document by title as an MCP resource.
    
    URI: docs://{title}
    Example: docs://hr-policy-handbook.md
    Returns: Full document content with metadata
    """
    logger.info(f"Resource docs://{title} accessed")
    return await _get_document_impl(title)


# ==================== ASGI Application Export ====================
# Export the ASGI app for production deployment (uvicorn basic_mcp_http:app)
# This follows the Azure-Samples/python-mcp-demos pattern

def create_app():
    """Create the ASGI application with optional API key middleware."""
    fastmcp_app = mcp.http_app(path="/mcp")
    
    if MCP_API_KEY:
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.routing import Mount
        
        # Create wrapper app with middleware AND FastMCP's lifespan
        return Starlette(
            routes=[Mount("/", app=fastmcp_app)],
            middleware=[Middleware(APIKeyMiddleware)],
            lifespan=fastmcp_app.lifespan,  # Required for FastMCP session management
        )
    else:
        return fastmcp_app


# ASGI application for uvicorn (used in Dockerfile: uvicorn basic_mcp_http:app)
app = create_app()


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    # Log auth status
    _add_api_key_middleware()

    logger.info(f"Starting MCP Server on http://{host}:{port}/mcp")
    
    import uvicorn
    uvicorn.run(app, host=host, port=port)
