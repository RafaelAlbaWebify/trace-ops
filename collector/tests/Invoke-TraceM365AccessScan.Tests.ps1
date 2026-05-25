$collectorRoot = Split-Path -Parent $PSScriptRoot
$scanScript = Join-Path -Path $collectorRoot -ChildPath "Invoke-TraceM365AccessScan.ps1"
$sampleLoaderScript = Join-Path -Path $collectorRoot -ChildPath "Get-TraceSampleScenario.ps1"
$snapshotScripts = @(
    @{
        Path = Join-Path -Path $collectorRoot -ChildPath "Get-TraceUserIdentitySnapshot.ps1"
        Area = "identity"
        Property = "identity"
    },
    @{
        Path = Join-Path -Path $collectorRoot -ChildPath "Get-TraceLicenseSnapshot.ps1"
        Area = "licenses"
        Property = "licenses"
    },
    @{
        Path = Join-Path -Path $collectorRoot -ChildPath "Get-TraceSignInSnapshot.ps1"
        Area = "signin_logs"
        Property = "signin_logs"
    },
    @{
        Path = Join-Path -Path $collectorRoot -ChildPath "Get-TraceConditionalAccessSnapshot.ps1"
        Area = "conditional_access"
        Property = "conditional_access"
    },
    @{
        Path = Join-Path -Path $collectorRoot -ChildPath "Get-TraceDeviceComplianceSnapshot.ps1"
        Area = "device"
        Property = "device"
    }
)

$knownScenarios = @(
    "account-disabled",
    "missing-license",
    "ca-details-missing",
    "ca-device-noncompliant",
    "no-recent-signin-evidence",
    "successful-access-baseline"
)

Describe "Invoke-TraceM365AccessScan sample mode" {
    foreach ($snapshotScript in $snapshotScripts) {
        $scriptPath = $snapshotScript.Path
        $area = $snapshotScript.Area
        $propertyName = $snapshotScript.Property

        It "returns valid JSON from $area snapshot for ca-device-noncompliant" {
            $json = & $scriptPath -Scenario "ca-device-noncompliant" -UseSampleData:$true
            { $json | ConvertFrom-Json -ErrorAction Stop } | Should Not Throw

            $result = $json | ConvertFrom-Json
            $result.status | Should Be "ok"
            $result.scenario_id | Should Be "ca-device-noncompliant"
            $result.evidence_area | Should Be $area
            $result.$propertyName | Should Not BeNullOrEmpty
        }

        It "returns controlled error from $area snapshot for invalid scenario" {
            $result = & $scriptPath -Scenario "not-a-scenario" -UseSampleData:$true | ConvertFrom-Json

            $result.status | Should Be "error"
            $result.module | Should Be "m365-access-path-analyzer"
            $result.error.code | Should Be "INVALID_SAMPLE_SCENARIO"
        }
    }

    foreach ($scenario in $knownScenarios) {
        It "returns valid JSON for sample scenario $scenario" {
            $json = & $scanScript `
                -UserPrincipalName "jane.doe@example.com" `
                -AffectedService "Microsoft 365 general access" `
                -Scenario $scenario `
                -UseSampleData:$true

            { $json | ConvertFrom-Json -ErrorAction Stop } | Should Not Throw
        }
    }

    foreach ($scenario in $knownScenarios) {
        It "returns required top-level fields for sample scenario $scenario" {
            $result = & $scanScript `
                -UserPrincipalName "jane.doe@example.com" `
                -AffectedService "Microsoft 365 general access" `
                -Scenario $scenario `
                -UseSampleData:$true |
                ConvertFrom-Json

            $result.scenario_id | Should Be $scenario
            $result.module | Should Be "m365-access-path-analyzer"
            $result.input | Should Not BeNullOrEmpty
            $result.identity | Should Not BeNullOrEmpty
            $result.licenses | Should Not BeNullOrEmpty
            $result.signin_logs | Should Not BeNullOrEmpty
            $result.conditional_access | Should Not BeNullOrEmpty
            $result.device | Should Not BeNullOrEmpty
        }
    }

    It "returns a controlled error for an invalid scenario" {
        $result = & $scanScript `
            -UserPrincipalName "jane.doe@example.com" `
            -AffectedService "Microsoft 365 general access" `
            -Scenario "not-a-scenario" `
            -UseSampleData:$true |
            ConvertFrom-Json

        $result.status | Should Be "error"
        $result.module | Should Be "m365-access-path-analyzer"
        $result.error.code | Should Be "INVALID_SAMPLE_SCENARIO"
        $result.error.known_scenarios.Count | Should Be $knownScenarios.Count
    }

    It "does not contain Microsoft Graph connection calls" {
        $collectorScripts = @($scanScript, $sampleLoaderScript) + ($snapshotScripts | ForEach-Object { $_.Path })
        $scriptText = ($collectorScripts | ForEach-Object { Get-Content -LiteralPath $_ -Raw }) -join "`n"

        $scriptText | Should Not Match "Connect-MgGraph"
        $scriptText | Should Not Match "Get-Mg"
        $scriptText | Should Not Match "Invoke-MgGraphRequest"
    }

    It "returns a controlled error when real collection is requested" {
        $result = & $scanScript `
            -UserPrincipalName "jane.doe@example.com" `
            -AffectedService "Microsoft 365 general access" `
            -Scenario "account-disabled" `
            -UseSampleData:$false |
            ConvertFrom-Json

        $result.status | Should Be "error"
        $result.error.code | Should Be "REAL_COLLECTION_NOT_IMPLEMENTED"
    }
}
