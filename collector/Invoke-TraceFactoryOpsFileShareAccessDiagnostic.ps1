param(
    [Parameter(Mandatory=$true)]
    [string]$ShareHost,

    [Parameter(Mandatory=$true)]
    [string]$ShareName,

    [Parameter(Mandatory=$true)]
    [string]$UserSamAccountName,

    [Parameter(Mandatory=$true)]
    [string]$RequiredGroupSamAccountName,

    [string]$DomainName = 'factory.local',

    [string]$DnsServer,

    [Nullable[bool]]$ObservedAccessDenied,

    [object[]]$DnsRecordsOverride,

    [object]$AdUserOverride,

    [object]$RequiredGroupOverride,

    [Nullable[bool]]$AdModuleAvailableOverride,

    [hashtable]$PortProbeOverride
)

$ErrorActionPreference = 'Stop'

function ConvertTo-TraceJson {
    param([Parameter(Mandatory=$true)]$Value)
    $Value | ConvertTo-Json -Depth 30
}

function New-TraceFinding {
    param(
        [Parameter(Mandatory=$true)][string]$FindingId,
        [Parameter(Mandatory=$true)][string]$Title,
        [Parameter(Mandatory=$true)][string]$Severity,
        [Parameter(Mandatory=$true)][string]$Confidence,
        [Parameter(Mandatory=$true)][string]$LikelyCause,
        [string[]]$EvidenceUsed = @(),
        [string[]]$EvidenceMissing = @(),
        [string[]]$SafeNextSteps = @(),
        [string[]]$WhatNotToChangeYet = @(),
        [string[]]$Limitations = @()
    )

    [ordered]@{
        finding_id = $FindingId
        rule_id = $FindingId
        title = $Title
        severity = $Severity
        confidence = $Confidence
        likely_cause = $LikelyCause
        evidence_used = @($EvidenceUsed)
        evidence_missing = @($EvidenceMissing)
        safe_next_steps = @($SafeNextSteps)
        what_not_to_change_yet = @($WhatNotToChangeYet)
        limitations = @($Limitations)
        source_module = 'factoryops-file-share-access-diagnostic'
    }
}

function ConvertTo-TraceHostName {
    param([Parameter(Mandatory=$true)][string]$Name, [Parameter(Mandatory=$true)][string]$Domain)
    $trimmed = $Name.Trim()
    if ($trimmed -match '\.') { return $trimmed.ToLowerInvariant() }
    return ($trimmed + '.' + $Domain.Trim()).ToLowerInvariant()
}

function Convert-TraceDnsRecord {
    param([Parameter(Mandatory=$true)]$Record)
    $value = $null
    if ($Record.PSObject.Properties.Name -contains 'IPAddress') { $value = [string]$Record.IPAddress }
    elseif ($Record.PSObject.Properties.Name -contains 'NameHost') { $value = [string]$Record.NameHost }
    elseif ($Record.PSObject.Properties.Name -contains 'QueryResults') { $value = [string]$Record.QueryResults }
    else { $value = [string]$Record }

    [ordered]@{
        name = [string]($Record.Name)
        type = [string]($Record.Type)
        value = $value
    }
}

function Test-TracePort {
    param([string]$Target, [int]$Port)
    $key = $Target + ':' + $Port
    if ($PortProbeOverride -and $PortProbeOverride.ContainsKey($key)) { return [bool]$PortProbeOverride[$key] }
    try { return [bool](Test-NetConnection -ComputerName $Target -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue) }
    catch { return $false }
}

function Get-TracePropertyValue {
    param([object]$Object, [string]$Name)
    if ($null -eq $Object) { return $null }
    if ($Object.PSObject.Properties.Name -contains $Name) { return $Object.$Name }
    return $null
}

$shareHostFqdn = ConvertTo-TraceHostName -Name $ShareHost -Domain $DomainName
$shareUncPath = '\\' + $shareHostFqdn + '\' + $ShareName
$findings = @()
$limitations = @(
    'TRACE collected read-only FactoryOps file-share access evidence only.',
    'TRACE did not change DNS, SMB, firewall, AD, NTFS, share permissions, passwords, group membership, or endpoint configuration.',
    'TRACE does not store user passwords and does not impersonate the affected user in this diagnostic.'
)
$safeNextSteps = @(
    'Review DNS, SMB reachability, AD user membership, and share permission evidence before changing AD or file server configuration.',
    'If a real access-denied error was observed, compare the user token group memberships with the required access group and share/NTFS ACLs.'
)
$whatNotToChange = @(
    'Do not add the user to a group until the required access group and business owner approval are confirmed.',
    'Do not broaden Everyone, Domain Users, or Authenticated Users permissions to fix a single access issue.',
    'Do not change firewall, DNS, NTFS, share, or AD permissions from this diagnostic alone.'
)
$boundary = [ordered]@{
    remediation_performed = $false
    dns_configuration_changed = $false
    network_configuration_changed = $false
    firewall_configuration_changed = $false
    ad_objects_modified = $false
    group_membership_changed = $false
    ntfs_or_share_permissions_changed = $false
    service_control_performed = $false
    remote_command_executed = $false
    credentials_or_tokens_stored = $false
    user_impersonation_performed = $false
}

$dnsRecords = @()
$dnsError = $null
try {
    if ($null -ne $DnsRecordsOverride) {
        $dnsRecords = @($DnsRecordsOverride | ForEach-Object { Convert-TraceDnsRecord -Record $_ })
    } else {
        $dnsParams = @{ Name = $shareHostFqdn; Type = 'A'; ErrorAction = 'Stop' }
        if ($DnsServer) { $dnsParams.Server = $DnsServer }
        $dnsRecords = @(Resolve-DnsName @dnsParams | ForEach-Object { Convert-TraceDnsRecord -Record $_ })
    }
} catch {
    $dnsError = $_.Exception.Message
}

$ipv4Records = @($dnsRecords | Where-Object { $_.type -eq 'A' -and $_.value })
$resolvedIpv4 = @($ipv4Records | ForEach-Object { $_.value })
$smbReachable = Test-TracePort -Target $shareHostFqdn -Port 445

$adModuleAvailable = $false
if ($null -ne $AdModuleAvailableOverride) {
    $adModuleAvailable = [bool]$AdModuleAvailableOverride
} else {
    $adModuleAvailable = [bool](Get-Module -ListAvailable -Name ActiveDirectory)
}

$adUser = $null
$requiredGroup = $null
$adUserError = $null
$groupError = $null
try {
    if ($null -ne $AdUserOverride) {
        $adUser = $AdUserOverride
    } elseif ($adModuleAvailable) {
        Import-Module ActiveDirectory -ErrorAction Stop
        $adUser = Get-ADUser -Identity $UserSamAccountName -Properties Enabled,DistinguishedName,MemberOf,SamAccountName,UserPrincipalName -ErrorAction Stop
    } else {
        $adUserError = 'ActiveDirectory PowerShell module is not available.'
    }
} catch {
    $adUserError = $_.Exception.Message
}

try {
    if ($null -ne $RequiredGroupOverride) {
        $requiredGroup = $RequiredGroupOverride
    } elseif ($adModuleAvailable) {
        Import-Module ActiveDirectory -ErrorAction Stop
        $requiredGroup = Get-ADGroup -Identity $RequiredGroupSamAccountName -Properties DistinguishedName,Members,SamAccountName -ErrorAction Stop
    } else {
        $groupError = 'ActiveDirectory PowerShell module is not available.'
    }
} catch {
    $groupError = $_.Exception.Message
}

$userDn = [string](Get-TracePropertyValue -Object $adUser -Name 'DistinguishedName')
$groupDn = [string](Get-TracePropertyValue -Object $requiredGroup -Name 'DistinguishedName')
$userMemberOf = @()
$groupMembers = @()
if ($adUser) { $userMemberOf = @((Get-TracePropertyValue -Object $adUser -Name 'MemberOf')) }
if ($requiredGroup) { $groupMembers = @((Get-TracePropertyValue -Object $requiredGroup -Name 'Members')) }

$membershipProven = $false
if ($groupDn -and ($userMemberOf -contains $groupDn)) { $membershipProven = $true }
if ($userDn -and ($groupMembers -contains $userDn)) { $membershipProven = $true }
if (-not $membershipProven) {
    foreach ($membership in $userMemberOf) {
        if ([string]$membership -match ('CN=' + [regex]::Escape($RequiredGroupSamAccountName) + ',')) { $membershipProven = $true }
    }
}

if ($dnsRecords.Count -eq 0) {
    $findings += New-TraceFinding `
        -FindingId 'FACTORYOPS_FILE_SHARE_DNS_NOT_PROVEN' `
        -Title 'File server DNS record was not proven' `
        -Severity 'high' `
        -Confidence 'high' `
        -LikelyCause 'TRACE could not prove an IPv4 DNS record for the file server.' `
        -EvidenceUsed @('share_host = ' + $shareHostFqdn, 'dns_error = ' + $(if ($dnsError) { $dnsError } else { 'none' })) `
        -EvidenceMissing @('No resolved IPv4 address was available for SMB interpretation.') `
        -SafeNextSteps @('Verify DNS from trace-admin01 before changing file server or share permissions.') `
        -WhatNotToChangeYet $whatNotToChange `
        -Limitations $limitations
}

if (-not $smbReachable) {
    $findings += New-TraceFinding `
        -FindingId 'FACTORYOPS_FILE_SHARE_SMB_NOT_REACHABLE' `
        -Title 'SMB port 445 was not reachable from the TRACE runner' `
        -Severity 'high' `
        -Confidence 'high' `
        -LikelyCause 'TRACE could not reach TCP 445 on the file server from the runner network path.' `
        -EvidenceUsed @('share = ' + $shareUncPath, 'smb_tcp_445_reachable = false') `
        -EvidenceMissing @('TRACE did not collect pfSense rule logs or Windows Firewall event logs.') `
        -SafeNextSteps @('Validate the inter-zone firewall path and the file server inbound SMB firewall scope before changing AD membership.') `
        -WhatNotToChangeYet $whatNotToChange `
        -Limitations $limitations
}

if (-not $adUser) {
    $findings += New-TraceFinding `
        -FindingId 'FACTORYOPS_FILE_SHARE_USER_NOT_PROVEN' `
        -Title 'Affected AD user was not proven' `
        -Severity 'medium' `
        -Confidence 'medium' `
        -LikelyCause 'TRACE could not prove the affected AD user and its group membership.' `
        -EvidenceUsed @('user = ' + $UserSamAccountName, 'ad_module_available = ' + $adModuleAvailable, 'ad_error = ' + $(if ($adUserError) { $adUserError } else { 'none' })) `
        -EvidenceMissing @('AD user Enabled and MemberOf properties were unavailable.') `
        -SafeNextSteps @('Run the diagnostic from a domain management host with RSAT and read-only AD query rights.') `
        -WhatNotToChangeYet $whatNotToChange `
        -Limitations $limitations
}

if (-not $requiredGroup) {
    $findings += New-TraceFinding `
        -FindingId 'FACTORYOPS_FILE_SHARE_REQUIRED_GROUP_NOT_PROVEN' `
        -Title 'Required AD access group was not proven' `
        -Severity 'medium' `
        -Confidence 'medium' `
        -LikelyCause 'TRACE could not prove the AD group expected to grant access to the share.' `
        -EvidenceUsed @('required_group = ' + $RequiredGroupSamAccountName, 'group_error = ' + $(if ($groupError) { $groupError } else { 'none' })) `
        -EvidenceMissing @('Required group DistinguishedName and Members properties were unavailable.') `
        -SafeNextSteps @('Confirm the correct business-approved access group before changing file share permissions.') `
        -WhatNotToChangeYet $whatNotToChange `
        -Limitations $limitations
}

if ($adUser -and $requiredGroup -and (-not $membershipProven)) {
    $findings += New-TraceFinding `
        -FindingId 'FACTORYOPS_FILE_SHARE_USER_MISSING_REQUIRED_GROUP' `
        -Title 'User is not a member of the required file-share access group' `
        -Severity 'high' `
        -Confidence 'high' `
        -LikelyCause 'The user is not present in the required AD group used to authorize read access to the file share.' `
        -EvidenceUsed @('user = ' + $UserSamAccountName, 'required_group = ' + $RequiredGroupSamAccountName, 'membership_proven = false', 'share = ' + $shareUncPath, 'observed_access_denied = ' + $(if ($null -ne $ObservedAccessDenied) { [string][bool]$ObservedAccessDenied } else { 'not supplied' })) `
        -EvidenceMissing @('TRACE did not collect the live NTFS/share ACL from the file server in this diagnostic run.') `
        -SafeNextSteps @('Confirm the user should have access with the data owner, then request membership in the required group through the normal approval path.', 'After membership is changed by an authorized admin, have the user sign out/in or purge tickets before retesting.') `
        -WhatNotToChangeYet $whatNotToChange `
        -Limitations $limitations
}

$status = 'success'
if ($findings.Count -gt 0) { $status = 'finding' }

$userEvidence = $null
if ($adUser) {
    $userEvidence = [ordered]@{
        name = [string](Get-TracePropertyValue -Object $adUser -Name 'Name')
        sam_account_name = [string](Get-TracePropertyValue -Object $adUser -Name 'SamAccountName')
        user_principal_name = [string](Get-TracePropertyValue -Object $adUser -Name 'UserPrincipalName')
        enabled = if ($null -ne (Get-TracePropertyValue -Object $adUser -Name 'Enabled')) { [bool](Get-TracePropertyValue -Object $adUser -Name 'Enabled') } else { $null }
        distinguished_name = $userDn
        member_of = @($userMemberOf | ForEach-Object { [string]$_ })
    }
}

$groupEvidence = $null
if ($requiredGroup) {
    $groupEvidence = [ordered]@{
        name = [string](Get-TracePropertyValue -Object $requiredGroup -Name 'Name')
        sam_account_name = [string](Get-TracePropertyValue -Object $requiredGroup -Name 'SamAccountName')
        distinguished_name = $groupDn
        members = @($groupMembers | ForEach-Object { [string]$_ })
    }
}

$result = [ordered]@{
    status = $status
    module = 'factoryops-file-share-access-diagnostic'
    check = 'factoryops_file_share_access_diagnostic'
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    input = [ordered]@{
        share_host = $ShareHost
        share_host_fqdn = $shareHostFqdn
        share_name = $ShareName
        share_unc_path = $shareUncPath
        user_sam_account_name = $UserSamAccountName
        required_group_sam_account_name = $RequiredGroupSamAccountName
        domain_name = $DomainName
        dns_server = if ($DnsServer) { $DnsServer } else { $null }
        observed_access_denied = if ($null -ne $ObservedAccessDenied) { [bool]$ObservedAccessDenied } else { $null }
    }
    evidence = [ordered]@{
        dns = [ordered]@{
            query = $shareHostFqdn
            server = if ($DnsServer) { $DnsServer } else { $null }
            records = @($dnsRecords)
            resolved_ipv4_addresses = @($resolvedIpv4)
            error = $dnsError
        }
        reachability = [ordered]@{
            target = $shareHostFqdn
            smb_tcp_445_reachable = $smbReachable
        }
        active_directory = [ordered]@{
            module_available = $adModuleAvailable
            user_found = [bool]$adUser
            user = $userEvidence
            required_group_found = [bool]$requiredGroup
            required_group = $groupEvidence
            membership_proven = $membershipProven
            user_error = $adUserError
            group_error = $groupError
        }
        observed_access = [ordered]@{
            access_denied = if ($null -ne $ObservedAccessDenied) { [bool]$ObservedAccessDenied } else { $null }
            supplied_by_operator = ($null -ne $ObservedAccessDenied)
        }
    }
    findings = @($findings)
    safe_next_steps = $safeNextSteps
    limitations = $limitations
    read_only_boundary = $boundary
}

ConvertTo-TraceJson $result
