param(
    [Parameter(Mandatory=$true)]
    [string]$ComputerName,

    [string]$DomainName = 'factory.local',

    [string]$DnsServer,

    [string]$ExpectedIpv4Address,

    [object[]]$DnsRecordsOverride,

    [object]$AdComputerOverride,

    [Nullable[bool]]$AdModuleAvailableOverride,

    [hashtable]$ReachabilityOverride,

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
        source_module = 'factoryops-computer-diagnostic'
    }
}

function ConvertTo-TraceComputerName {
    param([Parameter(Mandatory=$true)][string]$Name, [Parameter(Mandatory=$true)][string]$Domain)
    $trimmed = $Name.Trim()
    if ($trimmed -match '\.') { return $trimmed.ToLowerInvariant() }
    return ($trimmed + '.' + $Domain.Trim()).ToLowerInvariant()
}

function Get-TraceShortComputerName {
    param([Parameter(Mandatory=$true)][string]$Name)
    return (($Name.Trim() -split '\.')[0]).ToUpperInvariant()
}

function Convert-TraceDnsRecord {
    param([Parameter(Mandatory=$true)]$Record)
    $value = $null
    if ($Record.PSObject.Properties.Name -contains 'IPAddress') { $value = [string]$Record.IPAddress }
    elseif ($Record.PSObject.Properties.Name -contains 'NameHost') { $value = [string]$Record.NameHost }
    elseif ($Record.PSObject.Properties.Name -contains 'NameExchange') { $value = [string]$Record.NameExchange }
    elseif ($Record.PSObject.Properties.Name -contains 'Strings') { $value = ([string[]]$Record.Strings) -join '' }
    elseif ($Record.PSObject.Properties.Name -contains 'QueryResults') { $value = [string]$Record.QueryResults }
    else { $value = [string]$Record }

    [ordered]@{
        name = [string]($Record.Name)
        type = [string]($Record.Type)
        value = $value
    }
}

$computerFqdn = ConvertTo-TraceComputerName -Name $ComputerName -Domain $DomainName
$shortName = Get-TraceShortComputerName -Name $ComputerName
$findings = @()
$limitations = @(
    'TRACE collected read-only FactoryOps computer evidence only.',
    'TRACE did not change DNS, IP settings, firewall rules, AD objects, services, passwords, group membership, or endpoint configuration.'
)
$safeNextSteps = @(
    'Review DNS, AD computer, and connectivity evidence before changing any DNS, firewall, endpoint, or AD setting.',
    'If evidence is missing, collect a targeted screenshot or command output from trace-admin01 before opening a remediation task.'
)
$whatNotToChange = @(
    'Do not edit DNS records from this diagnostic alone.',
    'Do not change firewall rules, IP settings, AD computer objects, services, or endpoint configuration from this diagnostic alone.'
)
$boundary = [ordered]@{
    remediation_performed = $false
    dns_configuration_changed = $false
    network_configuration_changed = $false
    firewall_configuration_changed = $false
    ad_objects_modified = $false
    service_control_performed = $false
    remote_command_executed = $false
    credentials_or_tokens_stored = $false
}

$dnsRecords = @()
$dnsError = $null
try {
    if ($null -ne $DnsRecordsOverride) {
        $dnsRecords = @($DnsRecordsOverride | ForEach-Object { Convert-TraceDnsRecord -Record $_ })
    } else {
        $dnsParams = @{ Name = $computerFqdn; Type = 'A'; ErrorAction = 'Stop' }
        if ($DnsServer) { $dnsParams.Server = $DnsServer }
        $dnsRecords = @(Resolve-DnsName @dnsParams | ForEach-Object { Convert-TraceDnsRecord -Record $_ })
    }
} catch {
    $dnsError = $_.Exception.Message
}

$ipv4Records = @($dnsRecords | Where-Object { $_.type -eq 'A' -and $_.value })
$resolvedIpv4 = @($ipv4Records | ForEach-Object { $_.value })
$reverseRecords = @()
foreach ($ip in $resolvedIpv4) {
    try {
        if (-not $DnsRecordsOverride) {
            $ptr = @(Resolve-DnsName -Name $ip -Type PTR -ErrorAction Stop | ForEach-Object { Convert-TraceDnsRecord -Record $_ })
            $reverseRecords += $ptr
        }
    } catch {
        $reverseRecords += [ordered]@{ name = $ip; type = 'PTR'; value = $null; error = $_.Exception.Message }
    }
}

$adModuleAvailable = $false
if ($null -ne $AdModuleAvailableOverride) {
    $adModuleAvailable = [bool]$AdModuleAvailableOverride
} else {
    $adModuleAvailable = [bool](Get-Module -ListAvailable -Name ActiveDirectory)
}

$adComputer = $null
$adError = $null
try {
    if ($null -ne $AdComputerOverride) {
        $adComputer = $AdComputerOverride
    } elseif ($adModuleAvailable) {
        Import-Module ActiveDirectory -ErrorAction Stop
        $adComputer = Get-ADComputer -Identity $shortName -Properties DNSHostName,Enabled,DistinguishedName,OperatingSystem,LastLogonDate,IPv4Address,ServicePrincipalName -ErrorAction Stop
    } else {
        $adError = 'ActiveDirectory PowerShell module is not available.'
    }
} catch {
    $adError = $_.Exception.Message
}

function Test-TraceReachability {
    param([string]$Target)
    if ($ReachabilityOverride -and $ReachabilityOverride.ContainsKey($Target)) { return [bool]$ReachabilityOverride[$Target] }
    try { return [bool](Test-Connection -ComputerName $Target -Count 1 -Quiet -ErrorAction Stop) }
    catch { return $false }
}

function Test-TracePort {
    param([string]$Target, [int]$Port)
    $key = $Target + ':' + $Port
    if ($PortProbeOverride -and $PortProbeOverride.ContainsKey($key)) { return [bool]$PortProbeOverride[$key] }
    try { return [bool](Test-NetConnection -ComputerName $Target -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue) }
    catch { return $false }
}

$pingReachable = Test-TraceReachability -Target $computerFqdn
$portProbes = @(
    [ordered]@{ name = 'smb'; port = 445; reachable = (Test-TracePort -Target $computerFqdn -Port 445) },
    [ordered]@{ name = 'rdp'; port = 3389; reachable = (Test-TracePort -Target $computerFqdn -Port 3389) }
)

if ($dnsRecords.Count -eq 0) {
    $findings += New-TraceFinding `
        -FindingId 'FACTORYOPS_COMPUTER_DNS_A_RECORD_NOT_PROVEN' `
        -Title 'Computer DNS A record was not proven' `
        -Severity 'high' `
        -Confidence 'high' `
        -LikelyCause 'TRACE could not prove an A record for the target computer from the selected resolver path.' `
        -EvidenceUsed @('target = ' + $computerFqdn, 'dns_server = ' + $(if ($DnsServer) { $DnsServer } else { 'system default' }), 'dns_error = ' + $(if ($dnsError) { $dnsError } else { 'none' })) `
        -EvidenceMissing @('No resolved IPv4 address was available for downstream connectivity interpretation.') `
        -SafeNextSteps @('Verify the DNS record from trace-admin01 and from the expected client VLAN before changing records.', 'Compare expected DHCP/DNS registration for the target computer.') `
        -WhatNotToChangeYet $whatNotToChange `
        -Limitations $limitations
}

if ($ExpectedIpv4Address -and ($resolvedIpv4 -notcontains $ExpectedIpv4Address)) {
    $findings += New-TraceFinding `
        -FindingId 'FACTORYOPS_COMPUTER_DNS_IP_MISMATCH' `
        -Title 'Resolved IPv4 address does not match the expected FactoryOps address' `
        -Severity 'medium' `
        -Confidence 'high' `
        -LikelyCause 'DNS returned a different IPv4 address than the expected FactoryOps inventory value.' `
        -EvidenceUsed @('expected_ipv4 = ' + $ExpectedIpv4Address, 'resolved_ipv4 = ' + (($resolvedIpv4 -join ', '))) `
        -EvidenceMissing @('DHCP lease ownership and dynamic DNS update evidence were not collected in this phase.') `
        -SafeNextSteps @('Check DHCP lease and DNS registration evidence before changing DNS records.') `
        -WhatNotToChangeYet $whatNotToChange `
        -Limitations $limitations
}

if (-not $adComputer) {
    $findings += New-TraceFinding `
        -FindingId 'FACTORYOPS_AD_COMPUTER_OBJECT_NOT_PROVEN' `
        -Title 'AD computer object was not proven' `
        -Severity 'medium' `
        -Confidence 'medium' `
        -LikelyCause 'TRACE could not prove the matching AD computer object from trace-admin01.' `
        -EvidenceUsed @('computer_sam = ' + $shortName, 'ad_module_available = ' + $adModuleAvailable, 'ad_error = ' + $(if ($adError) { $adError } else { 'none' })) `
        -EvidenceMissing @('AD computer properties were unavailable for this diagnostic run.') `
        -SafeNextSteps @('Run the diagnostic from trace-admin01 with RSAT available and confirm read-only AD query rights.') `
        -WhatNotToChangeYet $whatNotToChange `
        -Limitations $limitations
}

if (-not $pingReachable) {
    $findings += New-TraceFinding `
        -FindingId 'FACTORYOPS_COMPUTER_ICMP_NOT_REACHABLE' `
        -Title 'Computer ICMP reachability was not proven' `
        -Severity 'low' `
        -Confidence 'medium' `
        -LikelyCause 'TRACE could not prove ICMP reachability to the target FQDN. This may be firewall policy, routing, or host state.' `
        -EvidenceUsed @('target = ' + $computerFqdn, 'icmp_reachable = false') `
        -EvidenceMissing @('TRACE did not collect firewall policy, route table, or endpoint service state in this phase.') `
        -SafeNextSteps @('Interpret ICMP with caution because Windows Firewall may block it even when the machine is healthy.', 'Use DNS, AD, SMB/RDP port evidence, and secure channel evidence together.') `
        -WhatNotToChangeYet $whatNotToChange `
        -Limitations $limitations
}

$status = 'success'
if ($findings.Count -gt 0) { $status = 'finding' }

$adComputerEvidence = $null
if ($adComputer) {
    $adComputerEvidence = [ordered]@{
        name = [string]$adComputer.Name
        dns_host_name = [string]$adComputer.DNSHostName
        enabled = if ($null -ne $adComputer.Enabled) { [bool]$adComputer.Enabled } else { $null }
        distinguished_name = [string]$adComputer.DistinguishedName
        operating_system = [string]$adComputer.OperatingSystem
        last_logon_date = if ($adComputer.LastLogonDate) { ([datetime]$adComputer.LastLogonDate).ToUniversalTime().ToString('o') } else { $null }
        ipv4_address = [string]$adComputer.IPv4Address
    }
}

$result = [ordered]@{
    status = $status
    module = 'factoryops-computer-diagnostic'
    check = 'factoryops_computer_diagnostic'
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    input = [ordered]@{
        computer_name = $ComputerName
        computer_fqdn = $computerFqdn
        domain_name = $DomainName
        dns_server = if ($DnsServer) { $DnsServer } else { $null }
        expected_ipv4_address = if ($ExpectedIpv4Address) { $ExpectedIpv4Address } else { $null }
    }
    evidence = [ordered]@{
        dns = [ordered]@{
            query = $computerFqdn
            server = if ($DnsServer) { $DnsServer } else { $null }
            records = @($dnsRecords)
            resolved_ipv4_addresses = @($resolvedIpv4)
            reverse_records = @($reverseRecords)
            error = $dnsError
        }
        active_directory = [ordered]@{
            module_available = $adModuleAvailable
            computer_found = [bool]$adComputer
            computer = $adComputerEvidence
            error = $adError
        }
        reachability = [ordered]@{
            target = $computerFqdn
            icmp_reachable = $pingReachable
            port_probes = @($portProbes)
        }
    }
    findings = @($findings)
    safe_next_steps = $safeNextSteps
    limitations = $limitations
    read_only_boundary = $boundary
}

ConvertTo-TraceJson $result
