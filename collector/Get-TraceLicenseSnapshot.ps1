[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Scenario,

    [bool]$UseSampleData = $true
)

$requestedScenario = $Scenario
. (Join-Path -Path $PSScriptRoot -ChildPath "Get-TraceSampleScenario.ps1")

function New-TraceSnapshotError {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Code,

        [Parameter(Mandatory = $true)]
        [string]$Message,

        [string]$Scenario
    )

    [ordered]@{
        status = "error"
        module = "m365-access-path-analyzer"
        evidence_area = "licenses"
        error = [ordered]@{
            code = $Code
            message = $Message
            scenario = $Scenario
        }
    }
}

function New-TraceSnapshotLimitation {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Area,

        [Parameter(Mandatory = $true)]
        [string]$Scenario
    )

    [ordered]@{
        status = "limited"
        module = "m365-access-path-analyzer"
        scenario_id = $Scenario
        evidence_area = $Area
        limitation = [ordered]@{
            code = "EVIDENCE_AREA_MISSING"
            message = "The selected sample does not contain the requested evidence area."
        }
    }
}

if (-not $UseSampleData) {
    New-TraceSnapshotError `
        -Code "REAL_COLLECTION_NOT_IMPLEMENTED" `
        -Message "TRACE collector MVP only supports sample data. Real Microsoft Graph collection is not implemented in Phase 1." `
        -Scenario $requestedScenario |
        ConvertTo-Json -Depth 20
    exit 0
}

$sample = Get-TraceSampleScenario -Scenario $requestedScenario
if ($sample.status -eq "error") {
    $sample | ConvertTo-Json -Depth 20
    exit 0
}

if ($sample.PSObject.Properties.Name -notcontains "licenses") {
    New-TraceSnapshotLimitation -Area "licenses" -Scenario $requestedScenario | ConvertTo-Json -Depth 20
    exit 0
}

[ordered]@{
    status = "ok"
    module = $sample.module
    scenario_id = $sample.scenario_id
    evidence_area = "licenses"
    licenses = $sample.licenses
} | ConvertTo-Json -Depth 20
