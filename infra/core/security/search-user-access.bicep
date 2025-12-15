param searchServiceName string
param principalId string

// Search Index Data Contributor - allows read/write to search index
var searchIndexDataContributor = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
)

// Search Service Contributor - allows managing search service resources
var searchServiceContributor = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
)

resource searchService 'Microsoft.Search/searchServices@2024-03-01-preview' existing = {
  name: searchServiceName
}

// Grant Search Index Data Contributor
resource indexDataContributorAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: searchService
  name: guid(subscription().id, resourceGroup().id, principalId, searchIndexDataContributor, 'user')
  properties: {
    roleDefinitionId: searchIndexDataContributor
    principalType: 'User'
    principalId: principalId
  }
}

// Grant Search Service Contributor
resource serviceContributorAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: searchService
  name: guid(subscription().id, resourceGroup().id, principalId, searchServiceContributor, 'user')
  properties: {
    roleDefinitionId: searchServiceContributor
    principalType: 'User'
    principalId: principalId
  }
}
