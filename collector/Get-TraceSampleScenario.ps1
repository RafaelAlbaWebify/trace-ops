param(
    [string]$Scenario
)

function New-TraceSampleError {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Code,

        [Parameter(Mandatory = $true)]
        [string]$Message,

        [string]$Scenario,

        [string[]]$KnownScenarios = @()
    )

    [ordered]@{
        status = "error"
        module = "m365-access-path-analyzer"
        error = [ordered]@{
            code = $Code
            message = $Message
            scenario = $Scenario
            known_scenarios = $KnownScenarios
        }
    }
}

function Get-TraceSampleScenario {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Scenario
    )

    $sampleMap = [ordered]@{
        "account-disabled" = "account-disabled.json"
        "missing-license" = "missing-license.json"
        "ca-details-missing" = "ca-details-missing.json"
        "ca-device-noncompliant" = "ca-device-noncompliant.json"
        "mfa-requirement-not-satisfied" = "mfa-requirement-not-satisfied.json"
        "no-recent-signin-evidence" = "no-recent-signin-evidence.json"
        "successful-access-baseline" = "successful-access-baseline.json"
    }

    $knownScenarios = @($sampleMap.Keys)

    if (-not $sampleMap.Contains($Scenario)) {
        return New-TraceSampleError `
            -Code "INVALID_SAMPLE_SCENARIO" `
            -Message "The requested sample scenario does not exist." `
            -Scenario $Scenario `
            -KnownScenarios $knownScenarios
    }

    $repoRoot = Split-Path -Parent $PSScriptRoot
    $samplePath = Join-Path -Path $repoRoot -ChildPath ("samples/{0}" -f $sampleMap[$Scenario])

    if (-not (Test-Path -LiteralPath $samplePath -PathType Leaf)) {
        return New-TraceSampleError `
            -Code "SAMPLE_FILE_NOT_FOUND" `
            -Message "The mapped sample file was not found." `
            -Scenario $Scenario `
            -KnownScenarios $knownScenarios
    }

    try {
        return Get-Content -LiteralPath $samplePath -Raw | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        return New-TraceSampleError `
            -Code "INVALID_SAMPLE_JSON" `
            -Message "The mapped sample file could not be parsed as JSON." `
            -Scenario $Scenario `
            -KnownScenarios $knownScenarios
    }
}

if ($MyInvocation.InvocationName -ne ".") {
    if ([string]::IsNullOrWhiteSpace($Scenario)) {
        New-TraceSampleError `
            -Code "MISSING_SAMPLE_SCENARIO" `
            -Message "A sample scenario is required." `
            -Scenario $Scenario |
            ConvertTo-Json -Depth 20
        exit 0
    }

    Get-TraceSampleScenario -Scenario $Scenario | ConvertTo-Json -Depth 20
}
