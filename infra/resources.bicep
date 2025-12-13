param environmentName string
param location string
param principalId string
param tags object

// Generate unique names for globally unique resources
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

// Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: 'cr${resourceToken}'
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
    publicNetworkAccess: 'Enabled'
  }
}

// Log Analytics Workspace for monitoring
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'log-${environmentName}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Container Apps Environment
resource containerEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-${environmentName}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// Azure AI Search (placeholder - will be configured later)
resource search 'Microsoft.Search/searchServices@2023-11-01' = {
  name: 'search-${resourceToken}'
  location: location
  tags: tags
  sku: {
    name: 'basic'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
  }
}

// Azure OpenAI (placeholder - will be configured later)
resource openai 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: 'openai-${resourceToken}'
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: 'openai-${resourceToken}'
    publicNetworkAccess: 'Enabled'
  }
}

// Container App with Managed Identity
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'app-${environmentName}'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
      registries: [
        {
          server: acr.properties.loginServer
          username: acr.listCredentials().username
          passwordSecretRef: 'registry-password'
        }
      ]
      secrets: [
        {
          name: 'registry-password'
          value: acr.listCredentials().passwords[0].value
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'mcp-server'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: [
            {
              name: 'MCP_TRANSPORT'
              value: 'http'
            }
            {
              name: 'AZURE_SEARCH_ENDPOINT'
              value: 'https://${search.name}.search.windows.net'
            }
            {
              name: 'AZURE_SEARCH_INDEX'
              value: 'documents'
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: openai.properties.endpoint
            }
            {
              name: 'AZURE_OPENAI_EMBEDDING'
              value: 'text-embedding-3-small'
            }
            {
              name: 'AZURE_OPENAI_CHAT'
              value: 'gpt-4o'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 10
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// Role assignments for Managed Identity
// Search Index Data Contributor
resource searchRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  name: guid(search.id, containerApp.id, 'Search Index Data Contributor')
  scope: search
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Cognitive Services OpenAI User
resource openaiRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  name: guid(openai.id, containerApp.id, 'Cognitive Services OpenAI User')
  scope: openai
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output REGISTRY_ENDPOINT string = acr.properties.loginServer
output REGISTRY_NAME string = acr.name
output CONTAINER_APP_ENDPOINT string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output CONTAINER_APP_NAME string = containerApp.name
output SEARCH_ENDPOINT string = 'https://${search.name}.search.windows.net'
output OPENAI_ENDPOINT string = openai.properties.endpoint
