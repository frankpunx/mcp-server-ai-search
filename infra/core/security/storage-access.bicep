param storageAccountName string
param principalId string

// Storage Blob Data Contributor - allows read/write to blob containers
var storageBlobDataContributor = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
)

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(subscription().id, resourceGroup().id, principalId, storageBlobDataContributor)
  properties: {
    roleDefinitionId: storageBlobDataContributor
    principalType: 'ServicePrincipal'
    principalId: principalId
  }
}
