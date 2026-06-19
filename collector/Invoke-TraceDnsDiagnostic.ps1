[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Query,

    [ValidateSet('A','AAAA','CNAME','MX','TXT','PTR')]
    [string]$RecordType = 'A',

    [string]$DnsServer = '',

    [object[]]$ResolveResultOverride = $null,

    [string]$ResolveErrorOverride = ''
)

$ErrorActionPreference = 'Stop'

function Convert-TraceDnsRecordValue {
    param([Parameter(Mandatory = $true)]$Record)

    if ($null -ne $Record.IPAddress) { return [string]$Record.IPAddress }
    if ($null -ne $Record.NameHost) { return [string]$Record.NameHost }
    if ($null -ne $Record.NameExchange) { return [string]$Record.NameExchange }
    if ($null -ne $Record.Strings) { return (($Record.Strings | ForEach-Object { [string]$_ }) -join ' ') }
    if ($null -ne $Record.Name) { return [string]$Record.Name }
    return ($Record | ConvertTo-Json -Depth 5 -Compress)
}

function New-TraceDnsOutput {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Status,
        [Parameter(Mandatory = $true)]
        [bool]$Resolved,
        [string[]]$Records,
        [string]$ErrorMessage = ''
    )

    $findings = @()
    $safeNextSteps = @()
    $limitations = @(
        'DNS diagnostics only verifies name resolution evidence. It does not validate application permissions, firewall paths, AD health, or service availability.'
    )

    if (-not $Resolved) {
        $findings += [ordered]@{
            finding_id = 'DNS_RESOLUTION_FAILED'
            title = 'DNS resolution did not return records'
            severity = 'medium'
            confidence = 'medium'
            likely_cause = 'The requested DNS name did not resolve from this machine or the selected DNS server.'
            evidence_used = @(
                ('query = {0}' -f $Query),
                ('record_type = {0}' -f $RecordType),
                ('dns_server = {0}' -f ($(if ($DnsServer) { $DnsServer } else { 'system default' }))),
                ('error = {0}' -f ($(if ($ErrorMessage) { $ErrorMessage } else { 'no records returned' })))
            )
            evidence_missing = @('No authoritative DNS zone data was collected.', 'No remote endpoint comparison was performed.')
            safe_next_steps = @(
                'Compare the same DNS query from a known healthy endpoint in the same VLAN or subnet.',
                'Verify the client DNS server points to the expected lab DNS/DC server before checking AD-dependent services.'
            )
            what_not_to_change_yet = @('Do not change DNS client/server settings from TRACE. This diagnostic is read-only.')
            limitations = $limitations
            source_module = 'dns-diagnostics'
        }
        $safeNextSteps += 'Compare this query from another endpoint and verify the expected DNS server path.'
    } else {
        $safeNextSteps += 'Use this DNS evidence as one input only; continue checking service reachability and identity/access evidence if the user issue persists.'
    }

    [ordered]@{
        status = $Status
        module = 'dns-diagnostics'
        check = 'dns_diagnostic'
        generated_at = (Get-Date).ToUniversalTime().ToString('o')
        input = [ordered]@{
            query = $Query
            record_type = $RecordType
            dns_server = $(if ($DnsServer) { $DnsServer } else { $null })
        }
        evidence = [ordered]@{
            query = $Query
            record_type = $RecordType
            dns_server = $(if ($DnsServer) { $DnsServer } else { $null })
            resolver = $(if ($DnsServer) { $DnsServer } else { 'system default' })
            resolved = $Resolved
            records = @($Records)
            record_count = @($Records).Count
            error = $(if ($ErrorMessage) { $ErrorMessage } else { $null })
        }
        findings = @($findings)
        safe_next_steps = @($safeNextSteps)
        limitations = @($limitations)
        read_only_boundary = [ordered]@{
            remediation_performed = $false
            dns_configuration_changed = $false
            network_configuration_changed = $false
        }
    } | ConvertTo-Json -Depth 20
}

if ($Query.Length -gt 253) {
    New-TraceDnsOutput -Status 'error' -Resolved $false -Records @() -ErrorMessage 'DNS query is too long.'
    exit 0
}

try {
    if ($ResolveErrorOverride) {
        throw $ResolveErrorOverride
    }

    if ($null -ne $ResolveResultOverride) {
        $results = @($ResolveResultOverride)
    } else {
        $params = @{ Name = $Query; Type = $RecordType; ErrorAction = 'Stop' }
        if ($DnsServer) { $params.Server = $DnsServer }
        $results = @(Resolve-DnsName @params)
    }

    $records = @($results | ForEach-Object { Convert-TraceDnsRecordValue -Record $_ } | Where-Object { $_ })
    if ($records.Count -gt 0) {
        New-TraceDnsOutput -Status 'success' -Resolved $true -Records $records
        exit 0
    }

    New-TraceDnsOutput -Status 'warning' -Resolved $false -Records @() -ErrorMessage 'DNS query returned no records.'
    exit 0
} catch {
    New-TraceDnsOutput -Status 'warning' -Resolved $false -Records @() -ErrorMessage $_.Exception.Message
    exit 0
}
