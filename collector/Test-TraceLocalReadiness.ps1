[CmdletBinding()]
param(
    [string]$DnsProbeName = "localhost",
    [string]$HostnameOverride = "",
    [string]$OsDescriptionOverride = "",
    [string]$PowerShellVersionOverride = "",
    [object[]]$NetworkAdaptersOverride = @(),
    [object[]]$IpConfigurationsOverride = @(),
    [string]$DomainJoinedOverride = "",
    [string]$DomainNameOverride = "",
    [string]$WorkgroupOverride = "",
    [object]$DnsProbeOverride = $null,
    [object]$GatewayProbeOverride = $null
)

$ErrorActionPreference = "Stop"
$limitations = New-Object System.Collections.Generic.List[string]
$safeNextSteps = New-Object System.Collections.Generic.List[string]

function Add-Limitation {
    param([string]$Message)
    if ($Message -and -not $limitations.Contains($Message)) { $limitations.Add($Message) | Out-Null }
}

function Add-SafeNextStep {
    param([string]$Message)
    if ($Message -and -not $safeNextSteps.Contains($Message)) { $safeNextSteps.Add($Message) | Out-Null }
}

function Convert-ToBoolOrNull {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return $null }
    if ($Value -match '^(true|1|yes)$') { return $true }
    if ($Value -match '^(false|0|no)$') { return $false }
    return $null
}

function Get-SafeHostname {
    if ($HostnameOverride) { return $HostnameOverride }
    if ($env:COMPUTERNAME) { return $env:COMPUTERNAME }
    return [System.Net.Dns]::GetHostName()
}

function Get-SafeOsDescription {
    if ($OsDescriptionOverride) { return $OsDescriptionOverride }
    try {
        $os = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
        return $os.Caption
    } catch {
        Add-Limitation "Could not read OS description from Win32_OperatingSystem."
        return $null
    }
}

function Get-SafeComputerSystem {
    $domainJoined = Convert-ToBoolOrNull -Value $DomainJoinedOverride
    $domainName = if ($DomainNameOverride) { $DomainNameOverride } else { $null }
    $workgroup = if ($WorkgroupOverride) { $WorkgroupOverride } else { $null }

    if ($null -ne $domainJoined -or $domainName -or $workgroup) {
        return [ordered]@{
            domain_joined = $domainJoined
            domain_name = $domainName
            workgroup = $workgroup
        }
    }

    try {
        $cs = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
        return [ordered]@{
            domain_joined = [bool]$cs.PartOfDomain
            domain_name = if ($cs.PartOfDomain) { $cs.Domain } else { $null }
            workgroup = if (-not $cs.PartOfDomain) { $cs.Workgroup } else { $null }
        }
    } catch {
        Add-Limitation "Could not read domain/workgroup status from Win32_ComputerSystem."
        return [ordered]@{
            domain_joined = $null
            domain_name = $null
            workgroup = $null
        }
    }
}

function Get-SafeNetworkAdapters {
    if ($NetworkAdaptersOverride.Count -gt 0) { return @($NetworkAdaptersOverride) }
    try {
        return @(Get-NetAdapter -ErrorAction Stop | Select-Object -First 12 | ForEach-Object {
            [ordered]@{
                name = $_.Name
                status = $_.Status
                interface_description = $_.InterfaceDescription
                mac_address = $_.MacAddress
            }
        })
    } catch {
        Add-Limitation "Could not read network adapters with Get-NetAdapter."
        return @()
    }
}

function Get-SafeIpConfigurations {
    if ($IpConfigurationsOverride.Count -gt 0) { return @($IpConfigurationsOverride) }
    try {
        return @(Get-NetIPConfiguration -ErrorAction Stop | Select-Object -First 12 | ForEach-Object {
            [ordered]@{
                interface_alias = $_.InterfaceAlias
                ipv4_addresses = @($_.IPv4Address | ForEach-Object { $_.IPAddress })
                dns_servers = @($_.DNSServer.ServerAddresses)
                default_gateway = ($_.IPv4DefaultGateway | Select-Object -First 1).NextHop
            }
        })
    } catch {
        Add-Limitation "Could not read IP configuration with Get-NetIPConfiguration."
        return @()
    }
}

function Test-SafeDnsProbe {
    if ($null -ne $DnsProbeOverride) { return $DnsProbeOverride }
    try {
        $records = Resolve-DnsName -Name $DnsProbeName -ErrorAction Stop | Select-Object -First 8
        return [ordered]@{
            query = $DnsProbeName
            succeeded = $true
            addresses = @($records | Where-Object { $_.IPAddress } | ForEach-Object { $_.IPAddress })
            error = $null
        }
    } catch {
        Add-Limitation "DNS probe did not complete successfully for '$DnsProbeName'."
        return [ordered]@{
            query = $DnsProbeName
            succeeded = $false
            addresses = @()
            error = $_.Exception.Message
        }
    }
}

function Test-SafeGatewayProbe {
    param([object[]]$IpConfigurations)
    if ($null -ne $GatewayProbeOverride) { return $GatewayProbeOverride }

    $gateway = $IpConfigurations | ForEach-Object { $_.default_gateway } | Where-Object { $_ } | Select-Object -First 1
    if (-not $gateway) {
        Add-Limitation "No IPv4 default gateway was detected."
        return [ordered]@{
            target = $null
            reachable = $null
            error = "No default gateway detected."
        }
    }

    try {
        $reachable = Test-NetConnection -ComputerName $gateway -InformationLevel Quiet -WarningAction SilentlyContinue -ErrorAction Stop
        return [ordered]@{
            target = $gateway
            reachable = [bool]$reachable
            error = $null
        }
    } catch {
        Add-Limitation "Default gateway probe did not complete successfully."
        return [ordered]@{
            target = $gateway
            reachable = $false
            error = $_.Exception.Message
        }
    }
}

$hostname = Get-SafeHostname
$osDescription = Get-SafeOsDescription
$computerSystem = Get-SafeComputerSystem
$networkAdapters = @(Get-SafeNetworkAdapters)
$ipConfigurations = @(Get-SafeIpConfigurations)
$dnsProbe = Test-SafeDnsProbe
$gatewayProbe = Test-SafeGatewayProbe -IpConfigurations $ipConfigurations

if ($networkAdapters.Count -eq 0) { Add-SafeNextStep "Verify that the target machine has at least one visible network adapter before running network diagnostics." }
if ($ipConfigurations.Count -eq 0) { Add-SafeNextStep "Verify local IP configuration before using TRACE against lab services." }
if (-not $dnsProbe.succeeded) { Add-SafeNextStep "Check the configured DNS server from this machine before running AD or service-name diagnostics." }
if ($gatewayProbe.reachable -eq $false) { Add-SafeNextStep "Compare default gateway reachability from this machine and from a known-good lab endpoint." }
if ($computerSystem.domain_joined -eq $false) { Add-SafeNextStep "For AD diagnostics, run TRACE from a domain-joined machine or clearly mark the result as non-domain context." }

$status = "ok"
if ($limitations.Count -gt 0 -or $safeNextSteps.Count -gt 0) { $status = "warning" }

[ordered]@{
    status = $status
    module = "local-infrastructure-readiness"
    check = "local_readiness"
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    evidence = [ordered]@{
        hostname = $hostname
        os_description = $osDescription
        powershell_version = if ($PowerShellVersionOverride) { $PowerShellVersionOverride } else { $PSVersionTable.PSVersion.ToString() }
        domain_joined = $computerSystem.domain_joined
        domain_name = $computerSystem.domain_name
        workgroup = $computerSystem.workgroup
        network_adapters = $networkAdapters
        ip_configurations = $ipConfigurations
        dns_probe = $dnsProbe
        gateway_probe = $gatewayProbe
    }
    safe_next_steps = @($safeNextSteps)
    limitations = @($limitations)
    read_only_boundary = [ordered]@{
        remediation_performed = $false
        network_configuration_changed = $false
        service_control_performed = $false
    }
} | ConvertTo-Json -Depth 20
