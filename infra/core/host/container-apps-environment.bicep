param name string
param location string = resourceGroup().location
param tags object = {}

param logAnalyticsWorkspaceName string = ''

var useLogging = !empty(logAnalyticsWorkspaceName)

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' existing = if (useLogging) {
  name: logAnalyticsWorkspaceName
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: useLogging
      ? {
          destination: 'log-analytics'
          logAnalyticsConfiguration: {
            customerId: logAnalyticsWorkspace.properties.customerId
            sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
          }
        }
      : {
          destination: 'azure-monitor'
        }
    zoneRedundant: false
  }
}

output defaultDomain string = containerAppsEnvironment.properties.defaultDomain
output name string = containerAppsEnvironment.name
output resourceId string = containerAppsEnvironment.id
