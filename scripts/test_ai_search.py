#!/usr/bin/env python3
"""
Test script for Azure AI Search functionality.

This script verifies:
1. Basic search index operations
2. Semantic search queries
3. Knowledge Base agentic retrieval
4. Document listing and facets

Usage:
    uv run python scripts/test_ai_search.py
    
    # Run specific test
    uv run python scripts/test_ai_search.py --test basic
    uv run python scripts/test_ai_search.py --test semantic
    uv run python scripts/test_ai_search.py --test agentic
    uv run python scripts/test_ai_search.py --test all
"""

import argparse
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(".azure/dev/.env", override=True)


def get_config():
    """Get configuration from environment variables."""
    search_endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
    search_index = os.environ.get("AZURE_SEARCH_INDEX", "documents")
    knowledge_base = os.environ.get("AZURE_SEARCH_KNOWLEDGE_BASE", f"{search_index}-kb")
    knowledge_source = os.environ.get("AZURE_SEARCH_KNOWLEDGE_SOURCE", f"{search_index}-ks")
    
    if not search_endpoint:
        print("❌ ERROR: AZURE_SEARCH_ENDPOINT not set")
        print("   Run: source .azure/dev/.env")
        sys.exit(1)
    
    return {
        "endpoint": search_endpoint,
        "index": search_index,
        "knowledge_base": knowledge_base,
        "knowledge_source": knowledge_source,
    }


def get_credential():
    """Get Azure credential."""
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential()


def test_index_stats(config, credential):
    """Test 1: Verify index exists and has documents."""
    print("\n" + "=" * 60)
    print("TEST 1: Index Statistics")
    print("=" * 60)
    
    from azure.search.documents.indexes import SearchIndexClient
    
    client = SearchIndexClient(endpoint=config["endpoint"], credential=credential)
    
    try:
        stats = client.get_index_statistics(config["index"])
        print(f"✅ Index '{config['index']}' exists")
        
        # Handle both object and dict responses
        if isinstance(stats, dict):
            doc_count = stats.get("document_count", stats.get("documentCount", 0))
            storage_size = stats.get("storage_size", stats.get("storageSize", 0))
        else:
            doc_count = getattr(stats, "document_count", 0)
            storage_size = getattr(stats, "storage_size", 0)
        
        print(f"   Document count: {doc_count}")
        print(f"   Storage size: {storage_size:,} bytes")
        
        if doc_count == 0:
            print("⚠️  Warning: Index is empty. Upload documents first.")
            return False
        return True
    except Exception as e:
        print(f"❌ Failed to get index stats: {e}")
        return False


def test_basic_search(config, credential):
    """Test 2: Basic keyword search."""
    print("\n" + "=" * 60)
    print("TEST 2: Basic Keyword Search")
    print("=" * 60)
    
    from azure.search.documents import SearchClient
    
    client = SearchClient(
        endpoint=config["endpoint"],
        index_name=config["index"],
        credential=credential,
    )
    
    queries = [
        ("vacation policy", "HR handbook"),
        ("SmartWidget", "Product manual"),
        ("Q3 2025 revenue", "Financial report"),
    ]
    
    all_passed = True
    for query, expected_doc in queries:
        try:
            results = client.search(search_text=query, top=3, select=["title", "chunk"])
            results_list = list(results)
            
            if results_list:
                print(f"✅ Query: '{query}'")
                print(f"   Found {len(results_list)} results")
                print(f"   Top result: {results_list[0].get('title', 'N/A')}")
            else:
                print(f"⚠️  Query: '{query}' - No results found")
                all_passed = False
        except Exception as e:
            print(f"❌ Query: '{query}' - Error: {e}")
            all_passed = False
    
    return all_passed


def test_semantic_search(config, credential):
    """Test 3: Semantic search with reranking."""
    print("\n" + "=" * 60)
    print("TEST 3: Semantic Search")
    print("=" * 60)
    
    from azure.search.documents import SearchClient
    
    client = SearchClient(
        endpoint=config["endpoint"],
        index_name=config["index"],
        credential=credential,
    )
    
    queries = [
        "How many days off do employees get per year?",
        "What happens when I press the reset button?",
        "What are the company's financial projections?",
    ]
    
    all_passed = True
    for query in queries:
        try:
            results = client.search(
                search_text=query,
                query_type="semantic",
                semantic_configuration_name="default",
                top=3,
                select=["title", "chunk"],
            )
            results_list = list(results)
            
            if results_list:
                top_result = results_list[0]
                score = top_result.get("@search.reranker_score", top_result.get("@search.score", 0))
                print(f"✅ Query: '{query[:50]}...'")
                print(f"   Top result: {top_result.get('title', 'N/A')}")
                print(f"   Reranker score: {score:.4f}")
            else:
                print(f"⚠️  Query: '{query[:50]}...' - No results")
                all_passed = False
        except Exception as e:
            print(f"❌ Query: '{query[:50]}...' - Error: {e}")
            all_passed = False
    
    return all_passed


def test_agentic_retrieval(config, credential):
    """Test 4: Knowledge Base agentic retrieval with answer synthesis."""
    print("\n" + "=" * 60)
    print("TEST 4: Agentic Retrieval (Knowledge Base)")
    print("=" * 60)
    
    import time
    from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
    from azure.search.documents.knowledgebases.models import (
        KnowledgeBaseMessage,
        KnowledgeBaseMessageTextContent,
        KnowledgeBaseRetrievalRequest,
        SearchIndexKnowledgeSourceParams,
    )
    
    try:
        kb_client = KnowledgeBaseRetrievalClient(
            endpoint=config["endpoint"],
            knowledge_base_name=config["knowledge_base"],
            credential=credential,
        )
    except Exception as e:
        print(f"❌ Failed to create KB client: {e}")
        return False
    
    test_cases = [
        {
            "query": "What is the vacation policy?",
            "expected_keywords": ["PTO", "days", "vacation", "time off"],
        },
        {
            "query": "How do I reset my SmartWidget Pro?",
            "expected_keywords": ["reset", "button", "LED", "seconds"],
        },
        {
            "query": "What was the Q3 2025 revenue?",
            "expected_keywords": ["billion", "revenue", "growth", "$"],
        },
    ]
    
    all_passed = True
    for test in test_cases:
        # Retry logic for rate limiting
        max_retries = 3
        for attempt in range(max_retries):
            try:
                request = KnowledgeBaseRetrievalRequest(
                    messages=[
                        KnowledgeBaseMessage(
                            role="user",
                            content=[KnowledgeBaseMessageTextContent(text=test["query"])]
                        ),
                    ],
                    knowledge_source_params=[
                        SearchIndexKnowledgeSourceParams(
                            knowledge_source_name=config["knowledge_source"],
                            include_references=True,
                        )
                    ],
                )
                
                result = kb_client.retrieve(request)
                
                if result.response and result.response[0].content:
                    answer = result.response[0].content[0].text
                    
                    # Check if expected keywords appear in the answer
                    found_keywords = [kw for kw in test["expected_keywords"] if kw.lower() in answer.lower()]
                    
                    print(f"✅ Query: '{test['query']}'")
                    print(f"   Answer preview: {answer[:150]}...")
                    print(f"   Keywords found: {found_keywords}")
                    
                    if "[ref_id:" in answer:
                        print(f"   ✓ Contains citations")
                    
                    if len(found_keywords) < len(test["expected_keywords"]) // 2:
                        print(f"   ⚠️  Answer may not be fully relevant")
                else:
                    print(f"⚠️  Query: '{test['query']}' - No response")
                    all_passed = False
                
                # Success - break retry loop
                break
                    
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "TooManyRequests" in error_msg:
                    # Rate limited - wait and retry
                    wait_time = 10 * (attempt + 1)
                    if attempt < max_retries - 1:
                        print(f"⏳ Rate limited, waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"⚠️  Query: '{test['query']}' - Rate limited after {max_retries} attempts")
                        all_passed = False
                else:
                    print(f"❌ Query: '{test['query']}' - Error: {e}")
                    all_passed = False
                    break
    
    return all_passed


def test_document_listing(config, credential):
    """Test 5: List unique documents using facets."""
    print("\n" + "=" * 60)
    print("TEST 5: Document Listing (Facets)")
    print("=" * 60)
    
    from azure.search.documents import SearchClient
    
    client = SearchClient(
        endpoint=config["endpoint"],
        index_name=config["index"],
        credential=credential,
    )
    
    try:
        results = client.search(
            search_text="*",
            top=0,
            facets=["title"],
        )
        
        facets = results.get_facets()
        if facets and "title" in facets:
            titles = [f["value"] for f in facets["title"]]
            print(f"✅ Found {len(titles)} unique documents:")
            for title in sorted(titles):
                print(f"   - {title}")
            return True
        else:
            print("⚠️  No facets returned")
            return False
    except Exception as e:
        print(f"❌ Error listing documents: {e}")
        return False


def test_knowledge_base_exists(config, credential):
    """Test 6: Verify Knowledge Base and Knowledge Source exist."""
    print("\n" + "=" * 60)
    print("TEST 6: Knowledge Base Configuration")
    print("=" * 60)
    
    from azure.search.documents.indexes import SearchIndexClient
    
    client = SearchIndexClient(endpoint=config["endpoint"], credential=credential)
    
    try:
        # Check Knowledge Source
        ks = client.get_knowledge_source(config["knowledge_source"])
        print(f"✅ Knowledge Source '{ks.name}' exists")
        print(f"   Type: {type(ks).__name__}")
        
        # Check Knowledge Base
        kb = client.get_knowledge_base(config["knowledge_base"])
        print(f"✅ Knowledge Base '{kb.name}' exists")
        print(f"   Sources: {[s.name for s in kb.knowledge_sources]}")
        print(f"   Has models: {len(kb.models) > 0 if kb.models else False}")
        
        return True
    except Exception as e:
        print(f"❌ Error checking KB/KS: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("🧪 AZURE AI SEARCH TEST SUITE")
    print("=" * 60)
    
    config = get_config()
    credential = get_credential()
    
    print(f"\nConfiguration:")
    print(f"  Endpoint: {config['endpoint']}")
    print(f"  Index: {config['index']}")
    print(f"  Knowledge Base: {config['knowledge_base']}")
    print(f"  Knowledge Source: {config['knowledge_source']}")
    
    results = {}
    
    # Run tests
    results["Index Stats"] = test_index_stats(config, credential)
    results["Basic Search"] = test_basic_search(config, credential)
    results["Semantic Search"] = test_semantic_search(config, credential)
    results["Document Listing"] = test_document_listing(config, credential)
    results["KB Configuration"] = test_knowledge_base_exists(config, credential)
    results["Agentic Retrieval"] = test_agentic_retrieval(config, credential)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Azure AI Search is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Test Azure AI Search functionality")
    parser.add_argument(
        "--test",
        choices=["basic", "semantic", "agentic", "stats", "list", "kb", "all"],
        default="all",
        help="Which test to run (default: all)",
    )
    args = parser.parse_args()
    
    config = get_config()
    credential = get_credential()
    
    if args.test == "all":
        sys.exit(run_all_tests())
    elif args.test == "basic":
        test_basic_search(config, credential)
    elif args.test == "semantic":
        test_semantic_search(config, credential)
    elif args.test == "agentic":
        test_agentic_retrieval(config, credential)
    elif args.test == "stats":
        test_index_stats(config, credential)
    elif args.test == "list":
        test_document_listing(config, credential)
    elif args.test == "kb":
        test_knowledge_base_exists(config, credential)


if __name__ == "__main__":
    main()
