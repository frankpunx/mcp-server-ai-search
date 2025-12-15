param openaiAccountName string
param principalId string

@allowed(['ServicePrincipal', 'User'])
param principalType string = 'ServicePrincipal'

// Cognitive Services OpenAI User - allows using OpenAI models
var cognitiveServicesOpenAIUser = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
)

resource openaiAccount 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' existing = {
  name: openaiAccountName
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: openaiAccount
  name: guid(subscription().id, resourceGroup().id, principalId, cognitiveServicesOpenAIUser, principalType)
  properties: {
    roleDefinitionId: cognitiveServicesOpenAIUser
    principalType: principalType
    principalId: principalId
  }
}
