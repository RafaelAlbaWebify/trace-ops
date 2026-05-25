[CmdletBinding()]
param(
    [System.Nullable[bool]]$GraphModuleAvailableOverride = $null,

    [System.Nullable[bool]]$ConnectedToGraphOverride = $null,

    [string]$TenantIdOverride,

    [string]$AccountOverride,

    [string[]]$AvailableScopesOverride
)

$requiredScopes = @(
    "User.Read.All",
    "Directory.Read.All",
    "AuditLog.Read.All"
)

function Test-TraceGraphModuleAvailable {
    $connectCommand = Get-Command -Name "Connect-MgGraph" -ErrorAction SilentlyContinue
    $contextCommand = Get-Command -Name "Get-MgContext" -ErrorAction SilentlyContinue

    return [bool]($connectCommand -and $contextCommand)
}

function Get-TraceGraphContextEvidence {
    param(
        [bool]$GraphModuleAvailable
    )

    if (-not $GraphModuleAvailable) {
        return [ordered]@{
            connected_to_graph = $false
            tenant_id = $null
            account = $null
            available_scopes = @()
        }
    }

    try {
        $context = Get-MgContext -ErrorAction Stop
    }
    catch {
        return [ordered]@{
            connected_to_graph = $false
            tenant_id = $null
            account = $null
            available_scopes = @()
        }
    }

    if ($null -eq $context) {
        return [ordered]@{
            connected_to_graph = $false
            tenant_id = $null
            account = $null
            available_scopes = @()
        }
    }

    $scopes = @()
    if ($context.PSObject.Properties.Name -contains "Scopes" -and $null -ne $context.Scopes) {
        $scopes = @($context.Scopes)
    }

    $tenantId = $null
    if ($context.PSObject.Properties.Name -contains "TenantId") {
        $tenantId = $context.TenantId
    }

    $account = $null
    if ($context.PSObject.Properties.Name -contains "Account") {
        $account = $context.Account
    }

    return [ordered]@{
        connected_to_graph = $true
        tenant_id = $tenantId
        account = $account
        available_scopes = $scopes
    }
}

function Compare-TraceRequiredScopes {
    param(
        [string[]]$RequiredScopes,
        [string[]]$AvailableScopes
    )

    $available = @($AvailableScopes | ForEach-Object { $_.ToLowerInvariant() })
    return @(
        $RequiredScopes | Where-Object {
            $available -notcontains $_.ToLowerInvariant()
        }
    )
}

$graphModuleAvailable = if ($null -ne $GraphModuleAvailableOverride) {
    [bool]$GraphModuleAvailableOverride
}
else {
    Test-TraceGraphModuleAvailable
}

$contextEvidence = Get-TraceGraphContextEvidence -GraphModuleAvailable $graphModuleAvailable

if ($null -ne $ConnectedToGraphOverride) {
    $contextEvidence.connected_to_graph = [bool]$ConnectedToGraphOverride
}

if ($TenantIdOverride) {
    $contextEvidence.tenant_id = $TenantIdOverride
}

if ($AccountOverride) {
    $contextEvidence.account = $AccountOverride
}

if ($null -ne $AvailableScopesOverride) {
    $contextEvidence.available_scopes = @($AvailableScopesOverride)
}

$missingScopes = Compare-TraceRequiredScopes -RequiredScopes $requiredScopes -AvailableScopes $contextEvidence.available_scopes
$safeNextSteps = New-Object System.Collections.Generic.List[string]

if (-not $graphModuleAvailable) {
    $safeNextSteps.Add("Install the Microsoft Graph PowerShell SDK.")
}

if (-not $contextEvidence.connected_to_graph) {
    $safeNextSteps.Add('Connect with Connect-MgGraph using required read-only scopes: "User.Read.All","Directory.Read.All","AuditLog.Read.All".')
}
elseif ($missingScopes.Count -gt 0) {
    $safeNextSteps.Add('Reconnect with Connect-MgGraph using required read-only scopes: "User.Read.All","Directory.Read.All","AuditLog.Read.All".')
}

if (-not $graphModuleAvailable -or -not $contextEvidence.connected_to_graph -or $missingScopes.Count -gt 0) {
    $safeNextSteps.Add("Ask a tenant administrator for consent if required.")
}

$status = "ok"
if (-not $graphModuleAvailable) {
    $status = "error"
}
elseif (-not $contextEvidence.connected_to_graph -or $missingScopes.Count -gt 0) {
    $status = "warning"
}

[ordered]@{
    status = $status
    module = "m365-access-path-analyzer"
    check = "graph_readiness"
    required_scopes = $requiredScopes
    evidence = [ordered]@{
        graph_module_available = $graphModuleAvailable
        connected_to_graph = $contextEvidence.connected_to_graph
        tenant_id = $contextEvidence.tenant_id
        account = $contextEvidence.account
        available_scopes = @($contextEvidence.available_scopes)
        missing_scopes = @($missingScopes)
    }
    safe_next_steps = @($safeNextSteps)
    limitations = @(
        "This preflight does not connect to Microsoft Graph automatically.",
        "This preflight does not verify tenant data access beyond the current local Graph context.",
        "Operational diagnostics must be used only with authorized tenant permissions."
    )
} | ConvertTo-Json -Depth 20
