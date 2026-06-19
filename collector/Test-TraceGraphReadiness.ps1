[CmdletBinding()]
param(
    [Nullable[bool]]$GraphModuleAvailableOverride = $null,
    [Nullable[bool]]$ConnectedToGraphOverride = $null,
    [string]$TenantIdOverride = $null,
    [string]$AccountOverride = $null,
    [string[]]$AvailableScopesOverride = $null
)

$ErrorActionPreference = 'Stop'

$requiredScopes = @(
    'User.Read.All',
    'AuditLog.Read.All',
    'LicenseAssignment.Read.All'
)

function Test-GraphModuleAvailable {
    if ($null -ne $GraphModuleAvailableOverride) { return [bool]$GraphModuleAvailableOverride }
    $module = Get-Module -ListAvailable -Name 'Microsoft.Graph.Authentication' -ErrorAction SilentlyContinue | Select-Object -First 1
    return ($null -ne $module)
}

function Get-ExistingGraphContextSafe {
    if ($null -ne $ConnectedToGraphOverride) {
        if (-not [bool]$ConnectedToGraphOverride) { return $null }
        return [pscustomobject]@{
            TenantId = $TenantIdOverride
            Account = $AccountOverride
            Scopes = @($AvailableScopesOverride)
        }
    }

    $cmd = Get-Command -Name 'Get-MgContext' -ErrorAction SilentlyContinue
    if (-not $cmd) { return $null }

    try {
        return Get-MgContext -ErrorAction Stop
    } catch {
        return $null
    }
}

$graphModuleAvailable = Test-GraphModuleAvailable
$context = if ($graphModuleAvailable) { Get-ExistingGraphContextSafe } else { $null }
$connectedToGraph = ($null -ne $context)

$availableScopes = @()
if ($connectedToGraph) {
    if ($null -ne $AvailableScopesOverride) {
        $availableScopes = @($AvailableScopesOverride)
    } elseif ($context.Scopes) {
        $availableScopes = @($context.Scopes)
    }
}

$missingScopes = @()
foreach ($scope in $requiredScopes) {
    if (-not $connectedToGraph -or -not ($availableScopes -contains $scope)) {
        $missingScopes += $scope
    }
}

$safeNextSteps = @()
$limitations = @()
$status = 'ok'

if (-not $graphModuleAvailable) {
    $status = 'error'
    $safeNextSteps += 'Install the Microsoft Graph PowerShell SDK before running real Graph diagnostics.'
    $limitations += 'Graph readiness cannot be confirmed because the Microsoft Graph PowerShell authentication module is not available.'
} elseif (-not $connectedToGraph) {
    $status = 'warning'
    $safeNextSteps += ('Sign in explicitly from your own PowerShell session before running real diagnostics, for example: Connect-MgGraph -Scopes "{0}"' -f ($requiredScopes -join ','))
    $limitations += 'No existing Microsoft Graph context was detected. TRACE did not create a connection automatically.'
} elseif ($missingScopes.Count -gt 0) {
    $status = 'warning'
    $safeNextSteps += ('Reconnect with the missing read-only scopes: {0}' -f ($missingScopes -join ', '))
    $limitations += 'The current Graph context is missing one or more required read-only scopes.'
}

$result = [pscustomobject]@{
    status = $status
    module = 'm365-access-path-analyzer'
    check = 'graph_readiness'
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    required_scopes = $requiredScopes
    evidence = [pscustomobject]@{
        graph_module_available = [bool]$graphModuleAvailable
        connected_to_graph = [bool]$connectedToGraph
        tenant_id = if ($connectedToGraph) { $context.TenantId } else { $null }
        account = if ($connectedToGraph) { $context.Account } else { $null }
        available_scopes = $availableScopes
        missing_scopes = $missingScopes
    }
    safe_next_steps = $safeNextSteps
    limitations = $limitations
    read_only_boundary = [pscustomobject]@{
        remediation_performed = $false
        automatic_connection_attempted = $false
        tenant_wide_scan_performed = $false
    }
}

$result | ConvertTo-Json -Depth 8
