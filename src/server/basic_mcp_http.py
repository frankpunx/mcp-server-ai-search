"""
MCP Server with Azure AI Search (HTTP Streamable Transport)

Run locally:     uv run src/server/basic_mcp_http.py
Debug:           F5 in VS Code
MCP Inspector:   npx @modelcontextprotocol/inspector http://localhost:8000/mcp
"""

import logging
import os
from typing import Annotated

from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
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

load_dotenv(override=True)

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AISearchMCP")

# Azure configuration
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
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


# Initialize the MCP server
mcp = FastMCP("Azure AI Search MCP Server")


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
async def search(
    query: Annotated[str, "The search query or question to answer"],
) -> str:
    """
    Search documents using Azure AI Search with agentic retrieval.
    
    This tool searches through indexed documents and returns a synthesized
    answer with citations. Use this for questions about company policies,
    product information, technical documentation, or any indexed content.
    
    Examples:
    - "What is the vacation policy?"
    - "How do I reset my SmartWidget Pro?"
    - "What was Q3 2025 revenue?"
    """
    logger.info(f"Search called with query: {query}")
    
    try:
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
        import json
        structured_response = {
            "answer": answer,
            "references": references,
            "activity": activity,
        }
        
        logger.info(f"Search returned {len(references)} unique references, {len(activity)} activity steps")
        return json.dumps(structured_response, indent=2)
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Search failed: {str(e)}"


@mcp.resource("resource://info")
async def get_server_info() -> str:
    """Get information about the MCP server."""
    return f"Azure AI Search MCP Server v1.0.0 - Knowledge Base: {AZURE_KNOWLEDGE_BASE_NAME}"


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    logger.info(f"Starting MCP Server on http://{host}:{port}/mcp")
    mcp.run(transport="streamable-http", host=host, port=port)
