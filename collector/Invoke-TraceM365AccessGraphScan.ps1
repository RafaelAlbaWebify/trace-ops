[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$UserPrincipalName,

    [string]$AffectedService = "Microsoft 365",

    [ValidateRange(1, 168)]
    [int]$LookbackHours = 24,

    [switch]$AsJson
)

$requiredScopes = @(
    "User.Read.All",
    "AuditLog.Read.All",
    "LicenseAssignment.Read.All"
)

$requiredCommands = @(
    "Get-MgContext",
    "Get-MgUser",
    "Get-MgUserLicenseDetail",
    "Get-MgAuditLogSignIn"
)

function ConvertTo-TraceJson {
    param(
        [Parameter(Mandatory = $true)]
        $Data
    )

    $Data | ConvertTo-Json -Depth 30
}

function Get-TraceUtcNow {
    return (Get-Date).ToUniversalTime().ToString("o")
}

function Get-TraceProperty {
    param(
        $InputObject,
        [string]$Name
    )

    if ($null -eq $InputObject) {
        return $null
    }

    if ($InputObject -is [System.Collections.IDictionary] -and $InputObject.Contains($Name)) {
        return $InputObject[$Name]
    }

    if ($InputObject.PSObject.Properties.Name -contains $Name) {
        return $InputObject.$Name
    }

    return $null
}

function New-TraceGraphError {
    param(
        [string]$Code,
        [string]$Message,
        [string[]]$SafeNextSteps,
        [string]$RawException
    )

    $errorBody = [ordered]@{
        code = $Code
        message = $Message
        safe_next_steps = @($SafeNextSteps)
    }

    if ($RawException) {
        $errorBody.raw_exception = $RawException
    }

    return $errorBody
}

function New-TraceGraphResult {
    param(
        [string]$CollectionStatus,
        $Identity = $null,
        $Licenses = $null,
        $SignInLogs = $null,
        $ConditionalAccess = $null,
        $Device = $null,
        [string[]]$Limitations = @(),
        $Errors = @()
    )

    return [ordered]@{
        module = "m365-access-path-analyzer"
        mode = "operational_graph"
        collection_status = $CollectionStatus
        input = [ordered]@{
            user_principal_name = $UserPrincipalName
            affected_service = $AffectedService
            lookback_hours = $LookbackHours
        }
        collected_at_utc = Get-TraceUtcNow
        identity = if ($null -ne $Identity) { $Identity } else { [ordered]@{} }
        licenses = if ($null -ne $Licenses) { $Licenses } else { [ordered]@{} }
        signin_logs = if ($null -ne $SignInLogs) { $SignInLogs } else { [ordered]@{} }
        conditional_access = if ($null -ne $ConditionalAccess) { $ConditionalAccess } else { [ordered]@{} }
        device = if ($null -ne $Device) { $Device } else { [ordered]@{} }
        limitations = @($Limitations)
        errors = @($Errors)
    }
}

function Test-TraceGraphCommandsAvailable {
    $missingCommands = @(
        $requiredCommands | Where-Object {
            -not (Get-Command -Name $_ -ErrorAction SilentlyContinue)
        }
    )

    return [ordered]@{
        available = ($missingCommands.Count -eq 0)
        missing_commands = @($missingCommands)
    }
}

function Get-TraceGraphContextEvidence {
    try {
        $context = Get-MgContext -ErrorAction Stop
    }
    catch {
        return [ordered]@{
            connected = $false
            scopes = @()
        }
    }

    if ($null -eq $context) {
        return [ordered]@{
            connected = $false
            scopes = @()
        }
    }

    $scopes = Get-TraceProperty -InputObject $context -Name "Scopes"

    return [ordered]@{
        connected = $true
        tenant_id = Get-TraceProperty -InputObject $context -Name "TenantId"
        account = Get-TraceProperty -InputObject $context -Name "Account"
        scopes = @($scopes)
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

function ConvertTo-TraceIdentityEvidence {
    param(
        $User
    )

    return [ordered]@{
        user_found = $true
        id = Get-TraceProperty -InputObject $User -Name "Id"
        user_principal_name = Get-TraceProperty -InputObject $User -Name "UserPrincipalName"
        display_name = Get-TraceProperty -InputObject $User -Name "DisplayName"
        account_enabled = Get-TraceProperty -InputObject $User -Name "AccountEnabled"
        user_type = Get-TraceProperty -InputObject $User -Name "UserType"
    }
}

function ConvertTo-TraceLicenseEvidence {
    param(
        $LicenseDetails,
        [string]$CollectionError
    )

    if ($CollectionError) {
        return [ordered]@{
            license_details_available = $false
            assigned_skus = @()
            service_plans = @()
            collection_error = $CollectionError
        }
    }

    $assignedSkus = @()
    $servicePlans = @()

    foreach ($license in @($LicenseDetails)) {
        $assignedSkus += ,([ordered]@{
            sku_id = Get-TraceProperty -InputObject $license -Name "SkuId"
            sku_part_number = Get-TraceProperty -InputObject $license -Name "SkuPartNumber"
        })

        foreach ($plan in @((Get-TraceProperty -InputObject $license -Name "ServicePlans"))) {
            $servicePlans += ,([ordered]@{
                sku_part_number = Get-TraceProperty -InputObject $license -Name "SkuPartNumber"
                service_plan_name = Get-TraceProperty -InputObject $plan -Name "ServicePlanName"
                provisioning_status = Get-TraceProperty -InputObject $plan -Name "ProvisioningStatus"
                applies_to = Get-TraceProperty -InputObject $plan -Name "AppliesTo"
            })
        }
    }

    return [ordered]@{
        license_details_available = $true
        assigned_skus = @($assignedSkus)
        service_plans = @($servicePlans)
        collection_error = $null
    }
}

function ConvertTo-TraceSignInEvents {
    param(
        $SignInEvents
    )

    $events = @()

    foreach ($event in @($SignInEvents)) {
        $status = Get-TraceProperty -InputObject $event -Name "Status"

        $events += ,([ordered]@{
            createdDateTime = Get-TraceProperty -InputObject $event -Name "CreatedDateTime"
            appDisplayName = Get-TraceProperty -InputObject $event -Name "AppDisplayName"
            status = [ordered]@{
                errorCode = Get-TraceProperty -InputObject $status -Name "ErrorCode"
                failureReason = Get-TraceProperty -InputObject $status -Name "FailureReason"
            }
            conditionalAccessStatus = Get-TraceProperty -InputObject $event -Name "ConditionalAccessStatus"
            deviceDetail = Get-TraceProperty -InputObject $event -Name "DeviceDetail"
            ipAddress = Get-TraceProperty -InputObject $event -Name "IpAddress"
            conditionalAccessPolicies = Get-TraceProperty -InputObject $event -Name "ConditionalAccessPolicies"
        })
    }

    return ,$events
}

function ConvertTo-TraceSignInEvidence {
    param(
        $SignInEvents
    )

    $events = ConvertTo-TraceSignInEvents -SignInEvents $SignInEvents

    return [ordered]@{
        logs_available = ($events.Count -gt 0)
        lookback_hours = $LookbackHours
        recent_events_count = $events.Count
        events = @($events)
    }
}

function ConvertTo-TraceConditionalAccessEvidence {
    param(
        $Events
    )

    $statusValues = @(
        $Events |
            ForEach-Object { $_.conditionalAccessStatus } |
            Where-Object { $_ } |
            Select-Object -Unique
    )

    $failedOrInterrupted = @(
        $Events | Where-Object {
            $_.conditionalAccessStatus -in @("failure", "interrupted")
        }
    )

    $policyDetails = @()
    foreach ($event in @($Events)) {
        foreach ($policy in @($event.conditionalAccessPolicies)) {
            if ($null -ne $policy) {
                $policyDetails += $policy
            }
        }
    }

    return [ordered]@{
        status_values_observed = @($statusValues)
        failed_or_interrupted_events_count = $failedOrInterrupted.Count
        policy_details_available = ($policyDetails.Count -gt 0)
        policies = @($policyDetails)
        evidence_source = "sign_in_logs"
    }
}

function ConvertTo-TraceDeviceEvidence {
    param(
        $Events
    )

    $deviceDetails = @(
        $Events |
            ForEach-Object { $_.deviceDetail } |
            Where-Object { $null -ne $_ }
    )

    $deviceIds = @(
        $deviceDetails |
            ForEach-Object { Get-TraceProperty -InputObject $_ -Name "DeviceId" } |
            Where-Object { $_ } |
            Select-Object -Unique
    )

    $displayNames = @(
        $deviceDetails |
            ForEach-Object { Get-TraceProperty -InputObject $_ -Name "DisplayName" } |
            Where-Object { $_ } |
            Select-Object -Unique
    )

    $complianceHints = @()
    foreach ($device in @($deviceDetails)) {
        $complianceHints += ,([ordered]@{
            device_id = Get-TraceProperty -InputObject $device -Name "DeviceId"
            display_name = Get-TraceProperty -InputObject $device -Name "DisplayName"
            is_compliant = Get-TraceProperty -InputObject $device -Name "IsCompliant"
            trust_type = Get-TraceProperty -InputObject $device -Name "TrustType"
            operating_system = Get-TraceProperty -InputObject $device -Name "OperatingSystem"
            browser = Get-TraceProperty -InputObject $device -Name "Browser"
        })
    }

    return [ordered]@{
        device_evidence_available = ($deviceDetails.Count -gt 0)
        observed_device_ids = @($deviceIds)
        observed_device_display_names = @($displayNames)
        compliance_trust_hints = @($complianceHints)
        evidence_source = "sign_in_logs"
    }
}

$commandCheck = Test-TraceGraphCommandsAvailable
if (-not $commandCheck.available) {
    $errorBody = New-TraceGraphError `
        -Code "GRAPH_MODULE_MISSING" `
        -Message "Microsoft Graph PowerShell cmdlets required for operational TRACE collection are not available." `
        -SafeNextSteps @(
            "Install the Microsoft Graph PowerShell SDK.",
            "Run the Graph readiness preflight before operational collection.",
            "Use only approved read-only delegated scopes."
        )

    ConvertTo-TraceJson -Data (New-TraceGraphResult -CollectionStatus "error" -Errors @($errorBody))
    return
}

$contextEvidence = Get-TraceGraphContextEvidence
if (-not $contextEvidence.connected) {
    $errorBody = New-TraceGraphError `
        -Code "GRAPH_NOT_CONNECTED" `
        -Message "No active Microsoft Graph context was found for this PowerShell session." `
        -SafeNextSteps @(
            "Authenticate to Microsoft Graph manually with approved read-only scopes.",
            "Run the Graph readiness preflight again.",
            "Ask a tenant administrator for consent if required."
        )

    ConvertTo-TraceJson -Data (New-TraceGraphResult -CollectionStatus "error" -Errors @($errorBody))
    return
}

$missingScopes = Compare-TraceRequiredScopes -RequiredScopes $requiredScopes -AvailableScopes $contextEvidence.scopes
if ($missingScopes.Count -gt 0) {
    $errorBody = New-TraceGraphError `
        -Code "GRAPH_REQUIRED_SCOPES_MISSING" `
        -Message "The current Microsoft Graph context is missing required read-only scopes." `
        -SafeNextSteps @(
            "Reconnect manually with the verified Phase 5A baseline read-only scopes.",
            "Ask a tenant administrator for consent if required.",
            "Do not use write scopes for TRACE operational diagnostics."
        )

    $result = New-TraceGraphResult -CollectionStatus "error" -Errors @($errorBody) -Limitations @(
        "Missing scopes: $($missingScopes -join ', ')"
    )
    ConvertTo-TraceJson -Data $result
    return
}

try {
    $user = Get-MgUser -UserId $UserPrincipalName -Property "id,userPrincipalName,displayName,accountEnabled,userType" -ErrorAction Stop
}
catch {
    $rawException = $_.Exception.Message

    if ($rawException -match "not found|ResourceNotFound|Request_ResourceNotFound") {
        $errorBody = New-TraceGraphError `
            -Code "USER_NOT_FOUND" `
            -Message "The requested user was not found in Microsoft Graph." `
            -SafeNextSteps @(
                "Confirm the user principal name is correct.",
                "Confirm the account exists in the authorized tenant.",
                "Check whether the signed-in administrator can read this user."
            ) `
            -RawException $rawException

        ConvertTo-TraceJson -Data (New-TraceGraphResult -CollectionStatus "error" -Errors @($errorBody))
        return
    }

    $errorBody = New-TraceGraphError `
        -Code "GRAPH_COLLECTION_FAILED" `
        -Message "User lookup failed during Microsoft Graph collection." `
        -SafeNextSteps @(
            "Run the Graph readiness preflight.",
            "Confirm read-only Graph permissions and tenant access.",
            "Retry after transient Graph errors clear."
        ) `
        -RawException $rawException

    ConvertTo-TraceJson -Data (New-TraceGraphResult -CollectionStatus "error" -Errors @($errorBody))
    return
}

if ($null -eq $user) {
    $errorBody = New-TraceGraphError `
        -Code "USER_NOT_FOUND" `
        -Message "The requested user was not found in Microsoft Graph." `
        -SafeNextSteps @(
            "Confirm the user principal name is correct.",
            "Confirm the account exists in the authorized tenant.",
            "Check whether the signed-in administrator can read this user."
        )

    ConvertTo-TraceJson -Data (New-TraceGraphResult -CollectionStatus "error" -Errors @($errorBody))
    return
}

$identityEvidence = ConvertTo-TraceIdentityEvidence -User $user

$licenseDetails = @()
$licenseCollectionError = $null
try {
    $licenseDetails = @(Get-MgUserLicenseDetail -UserId $identityEvidence.id -ErrorAction Stop)
}
catch {
    $licenseCollectionError = $_.Exception.Message
}

$licenseEvidence = ConvertTo-TraceLicenseEvidence -LicenseDetails $licenseDetails -CollectionError $licenseCollectionError

$lookbackStart = (Get-Date).ToUniversalTime().AddHours(-1 * $LookbackHours).ToString("o")
$escapedUpn = $UserPrincipalName.Replace("'", "''")
$filter = "userPrincipalName eq '$escapedUpn' and createdDateTime ge $lookbackStart"

try {
    $signInEvents = @(Get-MgAuditLogSignIn -Filter $filter -Top 50 -ErrorAction Stop)
}
catch {
    $errorBody = New-TraceGraphError `
        -Code "GRAPH_COLLECTION_FAILED" `
        -Message "Sign-in log collection failed during Microsoft Graph collection." `
        -SafeNextSteps @(
            "Confirm AuditLog.Read.All consent and the required Entra roles.",
            "Confirm sign-in log availability for this tenant.",
            "Retry after transient Graph errors clear."
        ) `
        -RawException $_.Exception.Message

    ConvertTo-TraceJson -Data (New-TraceGraphResult -CollectionStatus "error" -Identity $identityEvidence -Licenses $licenseEvidence -Errors @($errorBody))
    return
}

$signInEvidence = ConvertTo-TraceSignInEvidence -SignInEvents $signInEvents
$conditionalAccessEvidence = ConvertTo-TraceConditionalAccessEvidence -Events $signInEvidence.events
$deviceEvidence = ConvertTo-TraceDeviceEvidence -Events $signInEvidence.events

$limitations = @(
    "This operational collector reads only one user and does not scan tenant-wide users.",
    "Conditional Access and device evidence are summarized only from sign-in log fields in this skeleton.",
    "The collector does not remediate, change tenant settings, or store Graph tokens."
)

if (-not $signInEvidence.logs_available) {
    $limitations += "No recent sign-in events were returned for the selected lookback window."
}

if (-not $licenseEvidence.license_details_available) {
    $limitations += "License details were unavailable: $($licenseEvidence.collection_error)"
}

$result = New-TraceGraphResult `
    -CollectionStatus "success" `
    -Identity $identityEvidence `
    -Licenses $licenseEvidence `
    -SignInLogs $signInEvidence `
    -ConditionalAccess $conditionalAccessEvidence `
    -Device $deviceEvidence `
    -Limitations $limitations

ConvertTo-TraceJson -Data $result
