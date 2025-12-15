targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name which is used to generate a short unique hash for each resource')
param name string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Id of the user or app to assign application roles')
param principalId string = ''

param serverExists bool = false

var resourceToken = toLower(uniqueString(subscription().id, name, location))
var tags = { 'azd-env-name': name }
var prefix = '${name}-${resourceToken}'

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

// MCP Server Container App
module server 'core/host/container-app.bicep' = {
  name: 'server'
  scope: resourceGroup
  params: {
    name: '${prefix}-server'
    location: location
    tags: union(tags, { 'azd-service-name': 'server' })
    containerAppsEnvironmentName: containerAppsEnvironment.outputs.name
    containerRegistryName: containerRegistry.outputs.name
    identityName: serverIdentity.outputs.name
    exists: serverExists
    targetPort: 8000
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
