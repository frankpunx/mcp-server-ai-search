targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment (e.g., dev, prod)')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Id of the user or app to assign application roles')
param principalId string = ''

// Tags for all resources
var tags = {
  'azd-env-name': environmentName
  project: 'azure-mcp-retrieval'
}

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: 'rg-${environmentName}'
  location: location
  tags: tags
}

// Deploy infrastructure modules
module resources './resources.bicep' = {
  name: 'resources'
  scope: rg
  params: {
    environmentName: environmentName
    location: location
    principalId: principalId
    tags: tags
  }
}

// Outputs for azd and application configuration
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = rg.name

// Service endpoints
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = resources.outputs.REGISTRY_ENDPOINT
output AZURE_CONTAINER_APP_ENDPOINT string = resources.outputs.CONTAINER_APP_ENDPOINT
output AZURE_SEARCH_ENDPOINT string = resources.outputs.SEARCH_ENDPOINT
output AZURE_OPENAI_ENDPOINT string = resources.outputs.OPENAI_ENDPOINT

// Service names for azd deploy
output AZURE_CONTAINER_REGISTRY_NAME string = resources.outputs.REGISTRY_NAME
output AZURE_CONTAINER_APP_NAME string = resources.outputs.CONTAINER_APP_NAME
