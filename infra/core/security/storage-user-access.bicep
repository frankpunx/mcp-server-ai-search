param storageAccountName string
param principalId string

// Storage Blob Data Contributor - allows read/write access to blob containers (for uploading documents)
var storageBlobDataContributor = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
)

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(subscription().id, resourceGroup().id, principalId, storageBlobDataContributor, 'user')
  properties: {
    roleDefinitionId: storageBlobDataContributor
    principalType: 'User'
    principalId: principalId
  }
}
