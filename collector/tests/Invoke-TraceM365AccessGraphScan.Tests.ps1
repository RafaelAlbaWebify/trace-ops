$collectorRoot = Split-Path -Parent $PSScriptRoot
$graphScanScript = Join-Path -Path $collectorRoot -ChildPath "Invoke-TraceM365AccessGraphScan.ps1"

$requiredScopes = @(
    "User.Read.All",
    "AuditLog.Read.All",
    "LicenseAssignment.Read.All"
)

function Clear-TraceGraphTestDoubles {
    @(
        "Get-MgContext",
        "Get-MgUser",
        "Get-MgUserLicenseDetail",
        "Get-MgAuditLogSignIn",
        "Connect-MgGraph"
    ) | ForEach-Object {
        if (Test-Path -LiteralPath "Function:\global:$_") {
            Remove-Item -LiteralPath "Function:\global:$_" -Force
        }
    }
}

function Set-TraceGraphTestDoubles {
    param(
        [bool]$Connected = $true,
        [string[]]$Scopes = $requiredScopes,
        $User = ([pscustomobject]@{
            Id = "user-123"
            UserPrincipalName = "jane.doe@example.com"
            DisplayName = "Jane Doe"
            AccountEnabled = $true
            UserType = "Member"
        }),
        $LicenseDetails = @(
            [pscustomobject]@{
                SkuId = "sku-123"
                SkuPartNumber = "ENTERPRISEPACK"
                ServicePlans = @(
                    [pscustomobject]@{
                        ServicePlanName = "TEAMS1"
                        ProvisioningStatus = "Success"
                        AppliesTo = "User"
                    }
                )
            }
        ),
        $SignInEvents = @(
            [pscustomobject]@{
                CreatedDateTime = "2026-05-25T10:00:00Z"
                AppDisplayName = "Microsoft Teams"
                Status = [pscustomobject]@{
                    ErrorCode = 53003
                    FailureReason = "Access has been blocked by Conditional Access policies."
                }
                ConditionalAccessStatus = "failure"
                DeviceDetail = [pscustomobject]@{
                    DeviceId = "device-123"
                    DisplayName = "LAPTOP-123"
                    IsCompliant = $false
                    TrustType = "Azure AD registered"
                    OperatingSystem = "Windows"
                    Browser = "Edge"
                }
                IpAddress = "203.0.113.10"
                ConditionalAccessPolicies = @(
                    [pscustomobject]@{
                        DisplayName = "Require compliant device"
                        Result = "failure"
                    }
                )
            }
        )
    )

    if ($Connected) {
        Set-Item -Path Function:\global:Get-MgContext -Value {
            [pscustomobject]@{
                TenantId = "tenant-123"
                Account = "admin@example.com"
                Scopes = $global:TraceTestScopes
            }
        }
    }
    else {
        Set-Item -Path Function:\global:Get-MgContext -Value { $null }
    }

    $global:TraceTestScopes = $Scopes
    $global:TraceTestUser = $User
    $global:TraceTestLicenseDetails = $LicenseDetails
    $global:TraceTestSignInEvents = $SignInEvents
    $global:TraceLastUserId = $null
    $global:TraceLastSignInFilter = $null

    Set-Item -Path Function:\global:Get-MgUser -Value {
        param(
            [string]$UserId,
            [string]$Property,
            [string]$ErrorAction
        )
        $global:TraceLastUserId = $UserId
        if ($null -eq $global:TraceTestUser) {
            throw "ResourceNotFound: User not found"
        }
        $global:TraceTestUser
    }

    Set-Item -Path Function:\global:Get-MgUserLicenseDetail -Value {
        param(
            [string]$UserId,
            [string]$ErrorAction
        )
        $global:TraceTestLicenseDetails
    }

    Set-Item -Path Function:\global:Get-MgAuditLogSignIn -Value {
        param(
            [string]$Filter,
            [int]$Top,
            [string]$ErrorAction
        )
        $global:TraceLastSignInFilter = $Filter
        $global:TraceLastSignInTop = $Top
        $global:TraceTestSignInEvents
    }
}

Describe "Invoke-TraceM365AccessGraphScan operational skeleton" {
    BeforeEach {
        Clear-TraceGraphTestDoubles
    }

    AfterEach {
        Clear-TraceGraphTestDoubles
    }

    It "returns controlled error when Graph context is missing" {
        Set-TraceGraphTestDoubles -Connected $false

        $result = & $graphScanScript -UserPrincipalName "jane.doe@example.com" | ConvertFrom-Json

        $result.collection_status | Should Be "error"
        $result.errors[0].code | Should Be "GRAPH_NOT_CONNECTED"
    }

    It "returns controlled error when required scopes are missing" {
        Set-TraceGraphTestDoubles -Scopes @("User.Read.All")

        $result = & $graphScanScript -UserPrincipalName "jane.doe@example.com" | ConvertFrom-Json

        $result.collection_status | Should Be "error"
        $result.errors[0].code | Should Be "GRAPH_REQUIRED_SCOPES_MISSING"
        $result.limitations -join " " | Should Match "AuditLog.Read.All"
        $result.limitations -join " " | Should Match "LicenseAssignment.Read.All"
        $result.limitations -join " " | Should Not Match "Directory.Read.All"
    }

    It "returns controlled error when user is not found" {
        Set-TraceGraphTestDoubles -User $null

        $result = & $graphScanScript -UserPrincipalName "missing@example.com" | ConvertFrom-Json

        $result.collection_status | Should Be "error"
        $result.errors[0].code | Should Be "USER_NOT_FOUND"
    }

    It "returns valid JSON shape for successful user lookup" {
        Set-TraceGraphTestDoubles

        $result = & $graphScanScript -UserPrincipalName "jane.doe@example.com" -AffectedService "Teams" -LookbackHours 24 | ConvertFrom-Json

        $result.module | Should Be "m365-access-path-analyzer"
        $result.mode | Should Be "operational_graph"
        $result.collection_status | Should Be "success"
        $result.input.user_principal_name | Should Be "jane.doe@example.com"
        $result.input.affected_service | Should Be "Teams"
        $result.input.lookback_hours | Should Be 24
        $result.collected_at_utc | Should Not Be $null
    }

    It "includes identity evidence fields" {
        Set-TraceGraphTestDoubles

        $result = & $graphScanScript -UserPrincipalName "jane.doe@example.com" | ConvertFrom-Json

        $result.identity.user_found | Should Be $true
        $result.identity.id | Should Be "user-123"
        $result.identity.user_principal_name | Should Be "jane.doe@example.com"
        $result.identity.display_name | Should Be "Jane Doe"
        $result.identity.account_enabled | Should Be $true
        $result.identity.user_type | Should Be "Member"
    }

    It "includes license evidence fields" {
        Set-TraceGraphTestDoubles

        $result = & $graphScanScript -UserPrincipalName "jane.doe@example.com" | ConvertFrom-Json

        $result.licenses.license_details_available | Should Be $true
        $result.licenses.assigned_skus[0].sku_part_number | Should Be "ENTERPRISEPACK"
        $result.licenses.service_plans[0].service_plan_name | Should Be "TEAMS1"
    }

    It "includes sign-in evidence fields" {
        Set-TraceGraphTestDoubles

        $result = & $graphScanScript -UserPrincipalName "jane.doe@example.com" | ConvertFrom-Json

        $result.signin_logs.logs_available | Should Be $true
        $result.signin_logs.lookback_hours | Should Be 24
        $result.signin_logs.recent_events_count | Should Be 1
        $result.signin_logs.events[0].appDisplayName | Should Be "Microsoft Teams"
        $result.signin_logs.events[0].status.errorCode | Should Be 53003
        $result.signin_logs.events[0].status.failureReason | Should Match "Conditional Access"
        $result.signin_logs.events[0].ipAddress | Should Be "203.0.113.10"
    }

    It "summarizes Conditional Access status from sign-in logs" {
        Set-TraceGraphTestDoubles

        $result = & $graphScanScript -UserPrincipalName "jane.doe@example.com" | ConvertFrom-Json

        ($result.conditional_access.status_values_observed -contains "failure") | Should Be $true
        $result.conditional_access.failed_or_interrupted_events_count | Should Be 1
        $result.conditional_access.policy_details_available | Should Be $true
    }

    It "summarizes device evidence from sign-in logs" {
        Set-TraceGraphTestDoubles

        $result = & $graphScanScript -UserPrincipalName "jane.doe@example.com" | ConvertFrom-Json

        $result.device.device_evidence_available | Should Be $true
        ($result.device.observed_device_ids -contains "device-123") | Should Be $true
        ($result.device.observed_device_display_names -contains "LAPTOP-123") | Should Be $true
        $result.device.compliance_trust_hints[0].is_compliant | Should Be $false
    }

    It "does not query all tenant users by default" {
        Set-TraceGraphTestDoubles

        & $graphScanScript -UserPrincipalName "jane.doe@example.com" | Out-Null

        $global:TraceLastUserId | Should Be "jane.doe@example.com"
        $global:TraceLastSignInFilter | Should Match "userPrincipalName eq 'jane.doe@example.com'"
    }

    It "does not call Connect-MgGraph" {
        Set-TraceGraphTestDoubles
        Set-Item -Path Function:\global:Connect-MgGraph -Value { throw "Connect-MgGraph should not be called" }

        $result = & $graphScanScript -UserPrincipalName "jane.doe@example.com" | ConvertFrom-Json

        $result.collection_status | Should Be "success"
    }

    It "does not request or document write scopes" {
        $scriptText = Get-Content -LiteralPath $graphScanScript -Raw

        $scriptText | Should Not Match "ReadWrite"
        $scriptText | Should Not Match "Directory.AccessAsUser.All"
        $scriptText | Should Not Match "Policy.ReadWrite"
        $scriptText | Should Not Match "DeviceManagement.*ReadWrite"
    }

    It "does not contain tenant write or remediation cmdlets" {
        $scriptText = Get-Content -LiteralPath $graphScanScript -Raw

        $scriptText | Should Not Match "Set-Mg"
        $scriptText | Should Not Match "New-Mg"
        $scriptText | Should Not Match "Update-Mg"
        $scriptText | Should Not Match "Remove-Mg"
        $scriptText | Should Not Match "Add-Mg"
        $scriptText | Should Not Match "Clear-Mg"
        $scriptText | Should Not Match "Grant-Mg"
        $scriptText | Should Not Match "Revoke-Mg"
        $scriptText | Should Not Match "Reset"
        $scriptText | Should Not Match "Enable-Mg"
        $scriptText | Should Not Match "Disable-Mg"
        $scriptText | Should Not Match "Assign-Mg"
    }
}
