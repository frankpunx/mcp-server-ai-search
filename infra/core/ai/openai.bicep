param name string
param location string = resourceGroup().location
param tags object = {}

@description('Custom subdomain name for the OpenAI account')
param customSubDomainName string = name

@description('Log Analytics workspace ID for diagnostics')
param workspaceId string = ''

@description('Embedding model deployment name')
param embeddingDeploymentName string = 'text-embedding-3-small'

@description('Embedding model capacity (in thousands of tokens per minute)')
param embeddingCapacity int = 120

@description('Chat model deployment name')
param chatDeploymentName string = 'gpt-4o'

@description('Chat model capacity (in thousands of tokens per minute)')
param chatCapacity int = 30

resource openai 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: name
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: customSubDomainName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// Embedding model deployment
resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openai
  name: embeddingDeploymentName
  sku: {
    name: 'Standard'
    capacity: embeddingCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-small'
      version: '1'
    }
  }
}

// Chat model deployment (depends on embedding to avoid concurrent deployment issues)
resource chatDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openai
  name: chatDeploymentName
  sku: {
    name: 'Standard'
    capacity: chatCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-08-06'
    }
  }
  dependsOn: [embeddingDeployment]
}

// Diagnostics
resource diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(workspaceId)) {
  name: 'openai-diagnostics'
  scope: openai
  properties: {
    workspaceId: workspaceId
    logs: [
      {
        category: 'Audit'
        enabled: true
      }
      {
        category: 'RequestResponse'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

output id string = openai.id
output name string = openai.name
output endpoint string = openai.properties.endpoint
output embeddingDeploymentName string = embeddingDeployment.name
output chatDeploymentName string = chatDeployment.name
