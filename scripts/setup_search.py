#!/usr/bin/env python3
"""
Post-provision script to set up Azure AI Search index, indexer, and knowledge base.
Run automatically via azd postprovision hook or manually.

This script creates:
1. Search Index with vector and semantic configuration
2. Data Source connection to Blob Storage
3. Skillset for chunking and embedding
4. Indexer for automated document processing
5. Knowledge Source (wraps the index)
6. Knowledge Base (for agentic retrieval)
"""

import os
import sys
import time
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    # Index
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    SemanticConfiguration,
    SemanticSearch,
    SemanticPrioritizedFields,
    SemanticField,
    # Data Source
    SearchIndexerDataSourceConnection,
    SearchIndexerDataContainer,
    # Skillset
    SearchIndexerSkillset,
    SplitSkill,
    AzureOpenAIEmbeddingSkill,
    InputFieldMappingEntry,
    OutputFieldMappingEntry,
    # Indexer
    SearchIndexer,
    IndexingParameters,
    IndexingParametersConfiguration,
    FieldMapping,
    FieldMappingFunction,
    # Index Projections (for one-to-many chunk expansion)
    SearchIndexerIndexProjection,
    SearchIndexerIndexProjectionSelector,
    SearchIndexerIndexProjectionsParameters,
    # Knowledge Base (preview)
    KnowledgeBase,
    KnowledgeSourceReference,
    KnowledgeBaseAzureOpenAIModel,
    KnowledgeRetrievalOutputMode,
    KnowledgeRetrievalLowReasoningEffort,
    # Knowledge Source
    SearchIndexKnowledgeSource,
    SearchIndexKnowledgeSourceParameters,
    SearchIndexFieldReference,
)


def get_env_or_fail(name: str) -> str:
    """Get environment variable or exit with error."""
    value = os.environ.get(name)
    if not value:
        print(f"ERROR: Missing required environment variable: {name}")
        sys.exit(1)
    return value


def get_credential():
    """Get Azure credential based on environment."""
    client_id = os.environ.get("AZURE_CLIENT_ID")
    if client_id:
        print(f"Using Managed Identity: {client_id}")
        return ManagedIdentityCredential(client_id=client_id)
    else:
        print("Using DefaultAzureCredential (Azure CLI)")
        return DefaultAzureCredential()


def create_index(index_client: SearchIndexClient, index_name: str, openai_endpoint: str, embedding_deployment: str):
    """Create search index with vector and semantic configuration."""
    print(f"\n📑 Creating search index: {index_name}")
    
    # Vector search configuration
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="hnsw-algorithm"),
        ],
        profiles=[
            VectorSearchProfile(
                name="vector-profile",
                algorithm_configuration_name="hnsw-algorithm",
                vectorizer_name="openai-vectorizer",
            ),
        ],
        vectorizers=[
            AzureOpenAIVectorizer(
                vectorizer_name="openai-vectorizer",
                parameters=AzureOpenAIVectorizerParameters(
                    resource_url=openai_endpoint,
                    deployment_name=embedding_deployment,
                    model_name="text-embedding-3-small",
                ),
            ),
        ],
    )
    
    # Semantic search configuration
    semantic_config = SemanticConfiguration(
        name="default",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            content_fields=[SemanticField(field_name="chunk")],
            keywords_fields=[SemanticField(field_name="keywords")],
        ),
    )
    
    # Index fields
    fields = [
        # Key field must use keyword analyzer for index projections
        SearchField(name="id", type=SearchFieldDataType.String, key=True, sortable=True, analyzer_name="keyword"),
        SearchField(name="chunk", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="title", type=SearchFieldDataType.String, searchable=True, filterable=True, sortable=True),
        SearchField(name="source_url", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="keywords", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="last_modified", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
        SearchField(
            name="chunk_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="vector-profile",
        ),
        # Parent document reference
        SearchField(name="parent_id", type=SearchFieldDataType.String, filterable=True),
    ]
    
    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=SemanticSearch(configurations=[semantic_config], default_configuration_name="default"),
    )
    
    result = index_client.create_or_update_index(index)
    print(f"✅ Index '{result.name}' created/updated")
    return result


def create_data_source(indexer_client: SearchIndexerClient, name: str, storage_resource_id: str, container_name: str):
    """Create data source connection to Blob Storage using managed identity."""
    print(f"\n📦 Creating data source: {name}")
    
    # Use ResourceId format for managed identity authentication
    # Format: ResourceId=/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Storage/storageAccounts/{account};
    connection_string = f"ResourceId={storage_resource_id};"
    
    data_source = SearchIndexerDataSourceConnection(
        name=name,
        type="azureblob",
        connection_string=connection_string,
        container=SearchIndexerDataContainer(name=container_name),
    )
    
    result = indexer_client.create_or_update_data_source_connection(data_source)
    print(f"✅ Data source '{result.name}' created/updated")
    return result


def create_skillset(indexer_client: SearchIndexerClient, name: str, index_name: str, openai_endpoint: str, embedding_deployment: str):
    """Create skillset for document chunking and embedding with index projections."""
    print(f"\n🛠️ Creating skillset: {name}")
    
    skillset = SearchIndexerSkillset(
        name=name,
        description="Skillset for chunking documents and generating embeddings",
        skills=[
            # Split documents into chunks
            SplitSkill(
                name="split-skill",
                description="Split documents into chunks",
                text_split_mode="pages",
                maximum_page_length=2000,
                page_overlap_length=200,
                inputs=[
                    InputFieldMappingEntry(name="text", source="/document/content"),
                ],
                outputs=[
                    OutputFieldMappingEntry(name="textItems", target_name="chunks"),
                ],
            ),
            # Generate embeddings for each chunk
            AzureOpenAIEmbeddingSkill(
                name="embedding-skill",
                description="Generate embeddings using Azure OpenAI",
                context="/document/chunks/*",
                resource_url=openai_endpoint,
                deployment_name=embedding_deployment,
                model_name="text-embedding-3-small",
                dimensions=1536,
                inputs=[
                    # When context is /document/chunks/*, the source is the current item
                    InputFieldMappingEntry(name="text", source="/document/chunks/*"),
                ],
                outputs=[
                    OutputFieldMappingEntry(name="embedding", target_name="chunk_vector"),
                ],
            ),
        ],
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
                        InputFieldMappingEntry(name="title", source="/document/metadata_storage_name"),
                        InputFieldMappingEntry(name="source_url", source="/document/metadata_storage_path"),
                    ],
                ),
            ],
            parameters=SearchIndexerIndexProjectionsParameters(
                projection_mode="skipIndexingParentDocuments",
            ),
        ),
    )
    
    result = indexer_client.create_or_update_skillset(skillset)
    print(f"✅ Skillset '{result.name}' created/updated")
    return result


def create_indexer(
    indexer_client: SearchIndexerClient,
    name: str,
    data_source_name: str,
    index_name: str,
    skillset_name: str,
):
    """Create indexer for automated document processing."""
    print(f"\n⚙️ Creating indexer: {name}")
    
    indexer = SearchIndexer(
        name=name,
        description="Indexer for processing documents from blob storage",
        data_source_name=data_source_name,
        target_index_name=index_name,
        skillset_name=skillset_name,
        # Field mappings from blob metadata to document fields
        # Note: With index projections, chunk fields are mapped in the skillset
        field_mappings=[
            FieldMapping(source_field_name="metadata_storage_last_modified", target_field_name="last_modified"),
        ],
        # Output field mappings not needed - index projections handle chunk expansion
    )
    
    result = indexer_client.create_or_update_indexer(indexer)
    print(f"✅ Indexer '{result.name}' created/updated")
    return result


def create_knowledge_source(index_client: SearchIndexClient, name: str, index_name: str):
    """Create knowledge source that wraps the search index."""
    print(f"\n📚 Creating knowledge source: {name}")
    
    # SearchIndexKnowledgeSourceParameters specifies how to map index fields
    source_params = SearchIndexKnowledgeSourceParameters(
        search_index_name=index_name,
        semantic_configuration_name="default",
        # Map fields to their purposes in retrieval
        source_data_fields=[
            SearchIndexFieldReference(name="chunk"),
            SearchIndexFieldReference(name="title"),
            SearchIndexFieldReference(name="source_url"),
            SearchIndexFieldReference(name="keywords"),
        ],
        search_fields=[
            SearchIndexFieldReference(name="chunk"),
            SearchIndexFieldReference(name="title"),
            SearchIndexFieldReference(name="keywords"),
        ],
    )
    
    knowledge_source = SearchIndexKnowledgeSource(
        name=name,
        description="Knowledge source for document retrieval",
        search_index_parameters=source_params,
    )
    
    result = index_client.create_or_update_knowledge_source(knowledge_source)
    print(f"✅ Knowledge source '{result.name}' created/updated")
    return result


def create_knowledge_base(
    index_client: SearchIndexClient,
    name: str,
    knowledge_source_name: str,
    openai_endpoint: str,
    chat_deployment: str,
):
    """Create knowledge base for agentic retrieval."""
    print(f"\n🧠 Creating knowledge base: {name}")
    
    # Configure the Azure OpenAI model for query planning and answer synthesis
    aoai_params = AzureOpenAIVectorizerParameters(
        resource_url=openai_endpoint,
        deployment_name=chat_deployment,
        model_name="gpt-4o",
    )
    
    knowledge_base = KnowledgeBase(
        name=name,
        description="Knowledge base for MCP server agentic retrieval",
        retrieval_instructions="Use this knowledge source for questions about the indexed documents.",
        answer_instructions="Provide concise, accurate answers based on the retrieved documents. Always cite sources.",
        output_mode=KnowledgeRetrievalOutputMode.ANSWER_SYNTHESIS,
        knowledge_sources=[KnowledgeSourceReference(name=knowledge_source_name)],
        models=[KnowledgeBaseAzureOpenAIModel(azure_open_ai_parameters=aoai_params)],
        retrieval_reasoning_effort=KnowledgeRetrievalLowReasoningEffort(),
    )
    
    result = index_client.create_or_update_knowledge_base(knowledge_base)
    print(f"✅ Knowledge base '{result.name}' created/updated")
    return result


def run_indexer(indexer_client: SearchIndexerClient, indexer_name: str):
    """Run the indexer immediately."""
    print(f"\n🚀 Running indexer: {indexer_name}")
    indexer_client.run_indexer(indexer_name)
    print(f"✅ Indexer '{indexer_name}' started")
    
    # Wait for indexer to complete (with timeout)
    print("⏳ Waiting for indexer to complete...")
    for _ in range(30):  # Max 5 minutes
        time.sleep(10)
        status = indexer_client.get_indexer_status(indexer_name)
        last_result = status.last_result
        if last_result:
            print(f"   Status: {last_result.status}, Documents: {last_result.item_count}")
            if last_result.status in ["success", "transientFailure"]:
                break
    
    print(f"✅ Indexer completed")


def main():
    print("=" * 60)
    print("🔧 Azure AI Search Setup Script")
    print("=" * 60)
    
    # Get configuration from environment
    search_endpoint = get_env_or_fail("AZURE_SEARCH_ENDPOINT")
    index_name = os.environ.get("AZURE_SEARCH_INDEX", "documents")
    openai_endpoint = get_env_or_fail("AZURE_OPENAI_ENDPOINT")
    embedding_deployment = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
    chat_deployment = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")
    storage_resource_id = get_env_or_fail("AZURE_STORAGE_RESOURCE_ID")
    storage_url = os.environ.get("AZURE_STORAGE_ACCOUNT_URL", "")
    container_name = os.environ.get("AZURE_STORAGE_CONTAINER", "documents")
    
    print(f"\nConfiguration:")
    print(f"  Search Endpoint: {search_endpoint}")
    print(f"  Index Name: {index_name}")
    print(f"  OpenAI Endpoint: {openai_endpoint}")
    print(f"  Storage Resource ID: {storage_resource_id}")
    print(f"  Container: {container_name}")
    
    # Get credential
    credential = get_credential()
    
    # Create clients
    index_client = SearchIndexClient(endpoint=search_endpoint, credential=credential)
    indexer_client = SearchIndexerClient(endpoint=search_endpoint, credential=credential)
    
    # Resource names
    data_source_name = f"{index_name}-datasource"
    skillset_name = f"{index_name}-skillset"
    indexer_name = f"{index_name}-indexer"
    knowledge_source_name = f"{index_name}-ks"
    knowledge_base_name = f"{index_name}-kb"
    
    try:
        # 1. Create index
        create_index(index_client, index_name, openai_endpoint, embedding_deployment)
        
        # 2. Create data source
        create_data_source(indexer_client, data_source_name, storage_resource_id, container_name)
        
        # 3. Create skillset with index projections
        create_skillset(indexer_client, skillset_name, index_name, openai_endpoint, embedding_deployment)
        
        # 4. Create indexer
        create_indexer(indexer_client, indexer_name, data_source_name, index_name, skillset_name)
        
        # 5. Create knowledge source
        create_knowledge_source(index_client, knowledge_source_name, index_name)
        
        # 6. Create knowledge base
        create_knowledge_base(index_client, knowledge_base_name, knowledge_source_name, openai_endpoint, chat_deployment)
        
        # 7. Run indexer (optional - will run on schedule anyway)
        if os.environ.get("RUN_INDEXER", "false").lower() == "true":
            run_indexer(indexer_client, indexer_name)
        
        print("\n" + "=" * 60)
        print("✅ Setup complete!")
        print("=" * 60)
        print(f"\nNext steps:")
        print(f"1. Upload documents to: {storage_url}{container_name}/")
        print(f"2. Run indexer manually or wait for schedule")
        print(f"3. Query via knowledge base: {knowledge_base_name}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
