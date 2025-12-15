#!/usr/bin/env python
"""
Upload test documents to Azure Blob Storage and trigger indexer.
Run after azd up completes.
"""

import os
import subprocess
from pathlib import Path


def get_azd_env(key: str) -> str:
    """Get value from azd environment."""
    result = subprocess.run(
        ["azd", "env", "get-value", key],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def main():
    # Get Azure resources from azd environment
    storage_account = get_azd_env("AZURE_STORAGE_ACCOUNT_URL")
    container_name = get_azd_env("AZURE_STORAGE_CONTAINER")
    resource_group = get_azd_env("AZURE_RESOURCE_GROUP")
    search_endpoint = get_azd_env("AZURE_SEARCH_ENDPOINT")
    
    # Extract storage account name from URL
    # https://storagename.blob.core.windows.net -> storagename
    storage_name = storage_account.replace("https://", "").split(".")[0]
    
    # Extract search service name from endpoint
    # https://searchname.search.windows.net -> searchname
    search_name = search_endpoint.replace("https://", "").split(".")[0]
    
    print(f"📦 Storage Account: {storage_name}")
    print(f"📁 Container: {container_name}")
    print(f"🔍 Search Service: {search_name}")
    print()
    
    # Find test documents
    docs_dir = Path(__file__).parent.parent / "docs" / "test-documents"
    
    if not docs_dir.exists():
        print(f"❌ Test documents directory not found: {docs_dir}")
        return 1
    
    documents = [
        doc for doc in docs_dir.glob("*.md")
        if doc.name.lower() != "readme.md"
    ]
    
    if not documents:
        print(f"❌ No markdown files found in {docs_dir}")
        return 1
    
    print(f"📄 Found {len(documents)} documents to upload (excluding README.md):")
    for doc in documents:
        print(f"   - {doc.name}")
    print()
    
    # Upload documents
    print("⬆️  Uploading documents to blob storage...")
    for doc in documents:
        print(f"   Uploading {doc.name}...")
        subprocess.run([
            "az", "storage", "blob", "upload",
            "--account-name", storage_name,
            "--container-name", container_name,
            "--file", str(doc),
            "--name", doc.name,
            "--auth-mode", "login",
            "--overwrite"
        ], check=True, capture_output=True)
    
    print("✅ All documents uploaded!")
    print()
    
    # Run indexer via REST API (az search indexer command not available)
    print("🔄 Running search indexer...")
    
    # Get access token for Azure Search
    token_result = subprocess.run(
        ["az", "account", "get-access-token", "--resource", "https://search.azure.com", "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, check=True
    )
    token = token_result.stdout.strip()
    
    # Run indexer via REST API
    import urllib.request
    import urllib.error
    
    indexer_url = f"{search_endpoint}/indexers/documents-indexer/run?api-version=2024-07-01"
    req = urllib.request.Request(
        indexer_url,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    try:
        urllib.request.urlopen(req)
        print("✅ Indexer started!")
    except urllib.error.HTTPError as e:
        if e.code == 409:
            print("⚠️  Indexer already running (409 Conflict)")
        else:
            print(f"❌ Failed to start indexer: {e.code} {e.reason}")
            return 1
    
    print()
    
    # Check indexer status via REST API
    print("📊 Checking indexer status...")
    import time
    time.sleep(3)  # Give indexer a moment to start
    
    status_url = f"{search_endpoint}/indexers/documents-indexer/status?api-version=2024-07-01"
    status_req = urllib.request.Request(
        status_url,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        import json
        with urllib.request.urlopen(status_req) as response:
            status_data = json.loads(response.read().decode())
            last_result = status_data.get("lastResult", {})
            status = last_result.get("status", "unknown")
            doc_count = last_result.get("itemsProcessed", 0)
            print(f"   Indexer status: {status}")
            if doc_count > 0:
                print(f"   Documents processed: {doc_count}")
    except Exception as e:
        print(f"   Could not get status: {e}")
    
    print()
    
    print("=" * 60)
    print("🎉 Documents uploaded and indexing started!")
    print()
    print("Test queries you can try:")
    print("  • 'What is the vacation policy?'")
    print("  • 'How do I reset my password?'")
    print("  • 'What are the SmartWidget LED colors?'")
    print("  • 'What was Q3 2025 revenue?'")
    print("  • 'What is agentic retrieval?'")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit(main())
