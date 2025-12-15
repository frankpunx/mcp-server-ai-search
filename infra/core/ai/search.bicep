param name string
param location string = resourceGroup().location
param tags object = {}

@allowed(['basic', 'standard', 'standard2', 'standard3'])
@description('The SKU of the search service. Basic or higher required for agentic retrieval with managed identity.')
param sku string = 'basic'

@description('The name of the search index to create')
param indexName string = 'documents'

@description('Log Analytics workspace ID for diagnostics')
param workspaceId string = ''

@allowed(['disabled', 'free', 'standard'])
@description('Semantic search configuration. Standard required for agentic retrieval.')
param semanticSearch string = 'standard'

resource searchService 'Microsoft.Search/searchServices@2024-03-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    semanticSearch: semanticSearch
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http403'
      }
    }
  }
}

// Diagnostics
resource diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(workspaceId)) {
  name: 'search-diagnostics'
  scope: searchService
  properties: {
    workspaceId: workspaceId
    logs: [
      {
        category: 'OperationLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

output id string = searchService.id
output name string = searchService.name
output endpoint string = 'https://${searchService.name}.search.windows.net'
output indexName string = indexName
output principalId string = searchService.identity.principalId
