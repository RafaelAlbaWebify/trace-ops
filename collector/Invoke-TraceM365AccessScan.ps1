[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$UserPrincipalName,

    [Parameter(Mandatory = $true)]
    [string]$AffectedService,

    [Parameter(Mandatory = $true)]
    [string]$Scenario,

    [bool]$UseSampleData = $true
)

$requestedScenario = $Scenario
. (Join-Path -Path $PSScriptRoot -ChildPath "Get-TraceSampleScenario.ps1")

function New-TraceCollectorError {
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
        error = [ordered]@{
            code = $Code
            message = $Message
            scenario = $Scenario
        }
    }
}

if (-not $UseSampleData) {
    New-TraceCollectorError `
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

$identitySnapshot = & (Join-Path -Path $PSScriptRoot -ChildPath "Get-TraceUserIdentitySnapshot.ps1") -Scenario $requestedScenario -UseSampleData:$true | ConvertFrom-Json
$licenseSnapshot = & (Join-Path -Path $PSScriptRoot -ChildPath "Get-TraceLicenseSnapshot.ps1") -Scenario $requestedScenario -UseSampleData:$true | ConvertFrom-Json
$signInSnapshot = & (Join-Path -Path $PSScriptRoot -ChildPath "Get-TraceSignInSnapshot.ps1") -Scenario $requestedScenario -UseSampleData:$true | ConvertFrom-Json
$conditionalAccessSnapshot = & (Join-Path -Path $PSScriptRoot -ChildPath "Get-TraceConditionalAccessSnapshot.ps1") -Scenario $requestedScenario -UseSampleData:$true | ConvertFrom-Json
$deviceSnapshot = & (Join-Path -Path $PSScriptRoot -ChildPath "Get-TraceDeviceComplianceSnapshot.ps1") -Scenario $requestedScenario -UseSampleData:$true | ConvertFrom-Json

$snapshotResults = @(
    $identitySnapshot,
    $licenseSnapshot,
    $signInSnapshot,
    $conditionalAccessSnapshot,
    $deviceSnapshot
)

$snapshotError = $snapshotResults | Where-Object { $_.status -eq "error" } | Select-Object -First 1
if ($snapshotError) {
    $snapshotError | ConvertTo-Json -Depth 20
    exit 0
}

if (-not $sample.input) {
    $sample | Add-Member -NotePropertyName input -NotePropertyValue ([pscustomobject]@{}) -Force
}

$sample.input | Add-Member -NotePropertyName user_principal_name -NotePropertyValue $UserPrincipalName -Force
$sample.input | Add-Member -NotePropertyName affected_service -NotePropertyValue $AffectedService -Force

[ordered]@{
    scenario_id = $sample.scenario_id
    module = $sample.module
    input = $sample.input
    identity = $identitySnapshot.identity
    licenses = $licenseSnapshot.licenses
    signin_logs = $signInSnapshot.signin_logs
    conditional_access = $conditionalAccessSnapshot.conditional_access
    device = $deviceSnapshot.device
} | ConvertTo-Json -Depth 20
