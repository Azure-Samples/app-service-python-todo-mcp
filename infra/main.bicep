targetScope = 'resourceGroup'

@description('Name of the environment')
param environmentName string

@description('Primary location for all resources')
param location string = resourceGroup().location



// Generate unique resource token
var resourceToken = uniqueString(subscription().id, resourceGroup().id, location, environmentName)

// Define resource prefix
var resourcePrefix = 'tda'

// App Service Plan name
var appServicePlanName = 'az-${resourcePrefix}-plan-${resourceToken}'

// App Service name  
var appServiceName = 'az-${resourcePrefix}-app-${resourceToken}'

// Create App Service Plan (P0V3 Linux)
resource appServicePlan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: appServicePlanName
  location: location
  tags: {
    'azd-env-name': environmentName
  }
  sku: {
    name: 'P0v3'
    tier: 'Premium0V3'
    size: 'P0v3'
    family: 'Pv3'
    capacity: 1
  }
  properties: {
    reserved: true // Linux App Service Plan
  }
  kind: 'linux'
}

// Create App Service
resource appService 'Microsoft.Web/sites@2024-04-01' = {
  name: appServiceName
  location: location
  tags: {
    'azd-env-name': environmentName
    'azd-service-name': 'todo-app'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    reserved: true
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      alwaysOn: true
      ftpsState: 'FtpsOnly'
      appCommandLine: 'python -m uvicorn main:app --host 0.0.0.0 --port 8000'
      appSettings: [
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
        {
          name: 'PYTHONPATH'
          value: '/home/site/wwwroot'
        }
      ]
      cors: {
        allowedOrigins: ['*']
        supportCredentials: false
      }
      healthCheckPath: '/health'
    }
  }
}

// Outputs
output RESOURCE_GROUP_ID string = resourceGroup().id
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = resourceGroup().name
output SERVICE_WEB_NAME string = appService.name
output SERVICE_WEB_URI string = 'https://${appService.properties.defaultHostName}'
output SERVICE_TODO_APP_IDENTITY_PRINCIPAL_ID string = appService.identity.principalId
