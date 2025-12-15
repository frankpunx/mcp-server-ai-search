param storageAccountName string
param principalId string

// Storage Blob Data Reader - allows read access to blob containers (for Search indexer)
var storageBlobDataReader = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
)

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(subscription().id, resourceGroup().id, principalId, storageBlobDataReader)
  properties: {
    roleDefinitionId: storageBlobDataReader
    principalType: 'ServicePrincipal'
    principalId: principalId
  }
}
