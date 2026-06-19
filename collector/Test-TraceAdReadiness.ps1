[CmdletBinding()]
param(
    [string]$HostnameOverride,
    [string]$DomainJoinedOverride = "",
    [string]$DomainNameOverride,
    [string]$WorkgroupOverride,
    [string]$ActiveDirectoryModuleAvailableOverride = "",
    [string]$DomainControllerNameOverride,
    [string]$DomainControllerDiscoveredOverride = "",
    [string]$LdapReachableOverride = ""
)

$ErrorActionPreference = "Stop"
$safeNextSteps = New-Object System.Collections.Generic.List[string]
$limitations = New-Object System.Collections.Generic.List[string]

function Add-SafeNextStep {
    param([string]$Message)
    if ($Message -and -not $safeNextSteps.Contains($Message)) { $safeNextSteps.Add($Message) | Out-Null }
}

function Add-Limitation {
    param([string]$Message)
    if ($Message -and -not $limitations.Contains($Message)) { $limitations.Add($Message) | Out-Null }
}

function Convert-OverrideBool {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return $null }
    if ($Value -match '^(true|1|yes)$') { return $true }
    if ($Value -match '^(false|0|no)$') { return $false }
    return $null
}

function Get-SafeHostname {
    if ($HostnameOverride) { return $HostnameOverride }
    try { return $env:COMPUTERNAME } catch { return $null }
}

function Get-SafeComputerSystem {
    $domainJoinedOverride = Convert-OverrideBool $DomainJoinedOverride
    if ($null -ne $domainJoinedOverride) {
        return [ordered]@{
            domain_joined = $domainJoinedOverride
            domain_name = $DomainNameOverride
            workgroup = $WorkgroupOverride
        }
    }

    try {
        $computerSystem = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
        return [ordered]@{
            domain_joined = [bool]$computerSystem.PartOfDomain
            domain_name = if ($computerSystem.PartOfDomain) { $computerSystem.Domain } else { $null }
            workgroup = if (-not $computerSystem.PartOfDomain) { $computerSystem.Workgroup } else { $null }
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

function Test-SafeAdModuleAvailable {
    $override = Convert-OverrideBool $ActiveDirectoryModuleAvailableOverride
    if ($null -ne $override) { return $override }

    try {
        return [bool](Get-Module -ListAvailable -Name ActiveDirectory -ErrorAction SilentlyContinue | Select-Object -First 1)
    } catch {
        Add-Limitation "Could not check whether the ActiveDirectory PowerShell module is available."
        return $false
    }
}

function Get-SafeCurrentUserContext {
    try {
        return [ordered]@{
            user_domain = $env:USERDOMAIN
            username = $env:USERNAME
        }
    } catch {
        return [ordered]@{
            user_domain = $null
            username = $null
        }
    }
}

function Get-SafeDomainControllerEvidence {
    param([string]$DomainName)

    $discoveredOverride = Convert-OverrideBool $DomainControllerDiscoveredOverride
    if ($null -ne $discoveredOverride) {
        return [ordered]@{
            discovered = $discoveredOverride
            domain_controller = $DomainControllerNameOverride
            method = "override"
            error = if ($discoveredOverride) { $null } else { "Domain controller was not discovered in the supplied test fixture." }
        }
    }

    if (-not $DomainName) {
        Add-Limitation "Domain controller discovery was skipped because no domain name is available."
        return [ordered]@{
            discovered = $false
            domain_controller = $null
            method = "skipped"
            error = "No domain name available."
        }
    }

    try {
        $nltestOutput = & nltest.exe "/dsgetdc:$DomainName" 2>&1
        $dcLine = $nltestOutput | Where-Object { $_ -match 'DC:\\\\(.+)$' } | Select-Object -First 1
        $dcName = $null
        if ($dcLine -match 'DC:\\\\(.+)$') { $dcName = $Matches[1].Trim() }
        if ($LASTEXITCODE -eq 0 -and $dcName) {
            return [ordered]@{
                discovered = $true
                domain_controller = $dcName
                method = "nltest"
                error = $null
            }
        }

        Add-Limitation "Domain controller discovery did not return a usable domain controller."
        return [ordered]@{
            discovered = $false
            domain_controller = $null
            method = "nltest"
            error = ($nltestOutput -join " ")
        }
    } catch {
        Add-Limitation "Domain controller discovery could not be completed with nltest."
        return [ordered]@{
            discovered = $false
            domain_controller = $null
            method = "nltest"
            error = $_.Exception.Message
        }
    }
}

function Test-SafeLdapReachability {
    param([string]$DomainController)

    $override = Convert-OverrideBool $LdapReachableOverride
    if ($null -ne $override) {
        return [ordered]@{
            target = $DomainController
            port = 389
            reachable = $override
            error = if ($override) { $null } else { "LDAP port was not reachable in the supplied test fixture." }
        }
    }

    if (-not $DomainController) {
        Add-Limitation "LDAP reachability probe was skipped because no domain controller was discovered."
        return [ordered]@{
            target = $null
            port = 389
            reachable = $null
            error = "No domain controller available."
        }
    }

    try {
        $test = Test-NetConnection -ComputerName $DomainController -Port 389 -WarningAction SilentlyContinue -ErrorAction Stop
        return [ordered]@{
            target = $DomainController
            port = 389
            reachable = [bool]$test.TcpTestSucceeded
            error = $null
        }
    } catch {
        Add-Limitation "LDAP reachability probe did not complete successfully."
        return [ordered]@{
            target = $DomainController
            port = 389
            reachable = $false
            error = $_.Exception.Message
        }
    }
}

$hostname = Get-SafeHostname
$computerSystem = Get-SafeComputerSystem
$adModuleAvailable = Test-SafeAdModuleAvailable
$currentUser = Get-SafeCurrentUserContext
$dcEvidence = Get-SafeDomainControllerEvidence -DomainName $computerSystem.domain_name
$ldapProbe = Test-SafeLdapReachability -DomainController $dcEvidence.domain_controller

if ($computerSystem.domain_joined -ne $true) { Add-SafeNextStep "For AD diagnostics, run TRACE from a domain-joined lab machine or clearly mark the result as non-domain context." }
if (-not $adModuleAvailable) { Add-SafeNextStep "Install RSAT Active Directory PowerShell tools only if AD query diagnostics are required for the lab." }
if (-not $dcEvidence.discovered) { Add-SafeNextStep "Verify domain controller discovery from this machine before running AD user diagnostics." }
if ($ldapProbe.reachable -eq $false) { Add-SafeNextStep "Compare LDAP port reachability to the domain controller from this machine and from a known-good domain endpoint." }

$status = "ok"
if ($limitations.Count -gt 0 -or $safeNextSteps.Count -gt 0) { $status = "warning" }

[ordered]@{
    status = $status
    module = "active-directory-readiness"
    check = "ad_readiness"
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    evidence = [ordered]@{
        hostname = $hostname
        domain_joined = $computerSystem.domain_joined
        domain_name = $computerSystem.domain_name
        workgroup = $computerSystem.workgroup
        active_directory_module_available = $adModuleAvailable
        domain_controller = $dcEvidence
        ldap_probe = $ldapProbe
        current_user_context = $currentUser
    }
    safe_next_steps = @($safeNextSteps)
    limitations = @($limitations)
    read_only_boundary = [ordered]@{
        remediation_performed = $false
        ad_objects_modified = $false
        group_membership_changed = $false
        password_or_account_state_changed = $false
    }
} | ConvertTo-Json -Depth 20
