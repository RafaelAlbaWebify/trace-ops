$collectorRoot = Split-Path -Parent $PSScriptRoot
$readinessScript = Join-Path -Path $collectorRoot -ChildPath "Test-TraceGraphReadiness.ps1"

$requiredScopes = @(
    "User.Read.All",
    "AuditLog.Read.All",
    "LicenseAssignment.Read.All"
)

Describe "Test-TraceGraphReadiness" {
    It "returns JSON output with required shape" {
        $result = & $readinessScript `
            -GraphModuleAvailableOverride $true `
            -ConnectedToGraphOverride $true `
            -TenantIdOverride "00000000-0000-0000-0000-000000000000" `
            -AccountOverride "admin@example.com" `
            -AvailableScopesOverride $requiredScopes |
            ConvertFrom-Json

        $result.status | Should Be "ok"
        $result.module | Should Be "m365-access-path-analyzer"
        $result.check | Should Be "graph_readiness"
        $result.evidence.graph_module_available | Should Be $true
        $result.evidence.connected_to_graph | Should Be $true
        $result.evidence.tenant_id | Should Be "00000000-0000-0000-0000-000000000000"
        $result.evidence.account | Should Be "admin@example.com"
        $result.required_scopes.Count | Should Be 3
        ($result.required_scopes -contains "Directory.Read.All") | Should Be $false
        ($result.required_scopes -contains "LicenseAssignment.Read.All") | Should Be $true
    }

    It "returns error when Graph module is missing" {
        $result = & $readinessScript `
            -GraphModuleAvailableOverride $false `
            -ConnectedToGraphOverride $false |
            ConvertFrom-Json

        $result.status | Should Be "error"
        $result.evidence.graph_module_available | Should Be $false
        $result.evidence.connected_to_graph | Should Be $false
        $result.safe_next_steps -join " " | Should Match "Install the Microsoft Graph PowerShell SDK"
    }

    It "returns warning when not connected to Graph" {
        $result = & $readinessScript `
            -GraphModuleAvailableOverride $true `
            -ConnectedToGraphOverride $false |
            ConvertFrom-Json

        $result.status | Should Be "warning"
        $result.evidence.graph_module_available | Should Be $true
        $result.evidence.connected_to_graph | Should Be $false
        $result.evidence.missing_scopes.Count | Should Be 3
        $result.safe_next_steps -join " " | Should Match "Connect-MgGraph"
    }

    It "returns warning when required scopes are missing" {
        $result = & $readinessScript `
            -GraphModuleAvailableOverride $true `
            -ConnectedToGraphOverride $true `
            -AvailableScopesOverride @("User.Read.All") |
            ConvertFrom-Json

        $result.status | Should Be "warning"
        $result.evidence.connected_to_graph | Should Be $true
        ($result.evidence.missing_scopes -contains "AuditLog.Read.All") | Should Be $true
        ($result.evidence.missing_scopes -contains "LicenseAssignment.Read.All") | Should Be $true
        ($result.evidence.missing_scopes -contains "Directory.Read.All") | Should Be $false
    }

    It "returns ok when connected with required scopes" {
        $result = & $readinessScript `
            -GraphModuleAvailableOverride $true `
            -ConnectedToGraphOverride $true `
            -AvailableScopesOverride $requiredScopes |
            ConvertFrom-Json

        $result.status | Should Be "ok"
        $result.evidence.missing_scopes.Count | Should Be 0
        $result.safe_next_steps.Count | Should Be 0
    }

    It "does not request or document write scopes in output" {
        $json = & $readinessScript `
            -GraphModuleAvailableOverride $true `
            -ConnectedToGraphOverride $false

        $json | Should Not Match "ReadWrite"
        $json | Should Not Match "Directory.AccessAsUser.All"
        $json | Should Not Match "Policy.ReadWrite"
        $json | Should Not Match "DeviceManagement.*ReadWrite"
    }

    It "does not contain tenant write or remediation cmdlets" {
        $scriptText = Get-Content -LiteralPath $readinessScript -Raw

        $scriptText | Should Not Match "Set-Mg"
        $scriptText | Should Not Match "New-Mg"
        $scriptText | Should Not Match "Update-Mg"
        $scriptText | Should Not Match "Remove-Mg"
        $scriptText | Should Not Match "Reset"
        $scriptText | Should Not Match "Assign-Mg"
    }
}
