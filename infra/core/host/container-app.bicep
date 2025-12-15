param name string
param location string = resourceGroup().location
param tags object = {}

param containerAppsEnvironmentName string
param containerRegistryName string
param identityName string

param exists bool = false
param targetPort int = 8000

@description('CPU cores allocated to a single container instance')
param containerCpuCoreCount string = '0.5'

@description('Memory allocated to a single container instance')
param containerMemory string = '1.0Gi'

resource userIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: identityName
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: containerAppsEnvironmentName
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2022-02-01-preview' existing = {
  name: containerRegistryName
}

// Grant ACR Pull role to the identity
module registryAccess '../security/registry-access.bicep' = {
  name: '${deployment().name}-registry-access'
  params: {
    containerRegistryName: containerRegistryName
    principalId: userIdentity.properties.principalId
  }
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: tags
  dependsOn: [registryAccess]
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${userIdentity.id}': {} }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      activeRevisionsMode: 'single'
      ingress: {
        external: true
        targetPort: targetPort
        transport: 'auto'
      }
      registries: [
        {
          server: '${containerRegistry.name}.azurecr.io'
          identity: userIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'main'
          image: exists
            ? 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
            : 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          resources: {
            cpu: json(containerCpuCoreCount)
            memory: containerMemory
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
      }
    }
  }
}

output name string = app.name
output uri string = 'https://${app.properties.configuration.ingress.fqdn}'
output resourceId string = app.id
