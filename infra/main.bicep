targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name which is used to generate a short unique hash for each resource')
param name string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Location for Azure OpenAI (may differ from primary location due to model availability)')
param openaiLocation string = ''

@description('Id of the user or app to assign application roles')
param principalId string = ''

@allowed(['basic', 'standard'])
@description('Azure AI Search SKU. Basic or higher required for agentic retrieval.')
param searchSku string = 'basic'

var resourceToken = toLower(uniqueString(subscription().id, name, location))
var tags = { 'azd-env-name': name }
var prefix = '${name}-${resourceToken}'
var actualOpenaiLocation = empty(openaiLocation) ? location : openaiLocation

// Resource Group
resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: '${name}-rg'
  location: location
  tags: tags
}

// Log Analytics Workspace
module logAnalytics 'core/monitor/loganalytics.bicep' = {
  name: 'loganalytics'
  scope: resourceGroup
  params: {
    name: '${prefix}-loganalytics'
    location: location
    tags: tags
  }
}

// Container Registry
module containerRegistry 'core/host/container-registry.bicep' = {
  name: 'container-registry'
  scope: resourceGroup
  params: {
    name: replace('${prefix}acr', '-', '')
    location: location
    tags: tags
    workspaceId: logAnalytics.outputs.id
  }
}

// Container Apps Environment
module containerAppsEnvironment 'core/host/container-apps-environment.bicep' = {
  name: 'container-apps-environment'
  scope: resourceGroup
  params: {
    name: '${prefix}-containerapps-env'
    location: location
    tags: tags
    logAnalyticsWorkspaceName: logAnalytics.outputs.name
  }
}

// User Assigned Identity for Container App
module serverIdentity 'core/security/user-assigned-identity.bicep' = {
  name: 'server-identity'
  scope: resourceGroup
  params: {
    name: '${prefix}-server-identity'
    location: location
    tags: tags
  }
}

// ==================== AI & Storage Resources ====================

// Azure AI Search
module search 'core/ai/search.bicep' = {
  name: 'search'
  scope: resourceGroup
  params: {
    name: '${prefix}-search'
    location: location
    tags: tags
    sku: searchSku
    indexName: 'documents'
    workspaceId: logAnalytics.outputs.id
  }
}

// Azure OpenAI
module openai 'core/ai/openai.bicep' = {
  name: 'openai'
  scope: resourceGroup
  params: {
    name: '${prefix}-openai'
    location: actualOpenaiLocation
    tags: tags
    customSubDomainName: '${prefix}-openai'
    workspaceId: logAnalytics.outputs.id
    embeddingDeploymentName: 'text-embedding-3-small'
    chatDeploymentName: 'gpt-4o'
  }
}

// Azure Blob Storage (for documents)
module storage 'core/storage/storage-account.bicep' = {
  name: 'storage'
  scope: resourceGroup
  params: {
    name: replace('${prefix}stor', '-', '')
    location: location
    tags: tags
    containerName: 'documents'
    workspaceId: logAnalytics.outputs.id
  }
}

// ==================== Role Assignments ====================

// Grant MCP server identity access to AI Search
module searchAccess 'core/security/search-access.bicep' = {
  name: 'search-access'
  scope: resourceGroup
  params: {
    searchServiceName: search.outputs.name
    principalId: serverIdentity.outputs.principalId
  }
}

// Grant MCP server identity access to Azure OpenAI
module openaiAccess 'core/security/openai-access.bicep' = {
  name: 'openai-access'
  scope: resourceGroup
  params: {
    openaiAccountName: openai.outputs.name
    principalId: serverIdentity.outputs.principalId
  }
}

// Grant MCP server identity access to Blob Storage
module storageAccess 'core/security/storage-access.bicep' = {
  name: 'storage-access'
  scope: resourceGroup
  params: {
    storageAccountName: storage.outputs.name
    principalId: serverIdentity.outputs.principalId
  }
}

// Grant Search service managed identity access to Blob Storage (for indexer)
module searchStorageAccess 'core/security/storage-blob-reader.bicep' = {
  name: 'search-storage-access'
  scope: resourceGroup
  params: {
    storageAccountName: storage.outputs.name
    principalId: search.outputs.principalId
  }
}

// Grant Search service managed identity access to Azure OpenAI (for embedding skill)
module searchOpenaiAccess 'core/security/openai-access.bicep' = {
  name: 'search-openai-access'
  scope: resourceGroup
  params: {
    openaiAccountName: openai.outputs.name
    principalId: search.outputs.principalId
  }
}

// Grant current user access to Search (for setup script)
module userSearchAccess 'core/security/search-user-access.bicep' = if (!empty(principalId)) {
  name: 'user-search-access'
  scope: resourceGroup
  params: {
    searchServiceName: search.outputs.name
    principalId: principalId
  }
}

// Grant current user access to OpenAI (for setup script)
module userOpenaiAccess 'core/security/openai-access.bicep' = if (!empty(principalId)) {
  name: 'user-openai-access'
  scope: resourceGroup
  params: {
    openaiAccountName: openai.outputs.name
    principalId: principalId
    principalType: 'User'
  }
}

// Grant current user access to Storage (for uploading documents)
module userStorageAccess 'core/security/storage-user-access.bicep' = if (!empty(principalId)) {
  name: 'user-storage-access'
  scope: resourceGroup
  params: {
    storageAccountName: storage.outputs.name
    principalId: principalId
  }
}

// MCP Server Container App
module server 'core/host/container-app.bicep' = {
  name: 'server'
  scope: resourceGroup
  dependsOn: [searchAccess, openaiAccess, storageAccess]
  params: {
    name: '${prefix}-server'
    location: location
    tags: union(tags, { 'azd-service-name': 'server' })
    containerAppsEnvironmentName: containerAppsEnvironment.outputs.name
    containerRegistryName: containerRegistry.outputs.name
    identityName: serverIdentity.outputs.name
    targetPort: 8000
    // Environment variables for AI services
    env: [
      { name: 'AZURE_SEARCH_ENDPOINT', value: search.outputs.endpoint }
      { name: 'AZURE_SEARCH_INDEX', value: search.outputs.indexName }
      { name: 'AZURE_OPENAI_ENDPOINT', value: openai.outputs.endpoint }
      { name: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT', value: openai.outputs.embeddingDeploymentName }
      { name: 'AZURE_OPENAI_CHAT_DEPLOYMENT', value: openai.outputs.chatDeploymentName }
      { name: 'AZURE_STORAGE_ACCOUNT_URL', value: storage.outputs.primaryEndpoint }
      { name: 'AZURE_STORAGE_CONTAINER', value: storage.outputs.containerName }
      { name: 'AZURE_CLIENT_ID', value: serverIdentity.outputs.clientId }
    ]
  }
}

// Outputs for azd
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = resourceGroup.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.outputs.name
output SERVICE_SERVER_NAME string = server.outputs.name
output SERVICE_SERVER_URI string = server.outputs.uri

// AI Service outputs
output AZURE_SEARCH_ENDPOINT string = search.outputs.endpoint
output AZURE_SEARCH_INDEX string = search.outputs.indexName
output AZURE_OPENAI_ENDPOINT string = openai.outputs.endpoint
output AZURE_OPENAI_EMBEDDING_DEPLOYMENT string = openai.outputs.embeddingDeploymentName
output AZURE_OPENAI_CHAT_DEPLOYMENT string = openai.outputs.chatDeploymentName
output AZURE_STORAGE_ACCOUNT_URL string = storage.outputs.primaryEndpoint
output AZURE_STORAGE_RESOURCE_ID string = storage.outputs.id
output AZURE_STORAGE_CONTAINER string = storage.outputs.containerName
