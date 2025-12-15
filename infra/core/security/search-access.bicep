param searchServiceName string
param principalId string

// Search Index Data Contributor - allows read/write to search index
var searchIndexDataContributor = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
)

resource searchService 'Microsoft.Search/searchServices@2024-03-01-preview' existing = {
  name: searchServiceName
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: searchService
  name: guid(subscription().id, resourceGroup().id, principalId, searchIndexDataContributor)
  properties: {
    roleDefinitionId: searchIndexDataContributor
    principalType: 'ServicePrincipal'
    principalId: principalId
  }
}
