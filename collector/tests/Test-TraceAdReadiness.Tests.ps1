$collectorRoot = Split-Path -Parent $PSScriptRoot
$readinessScript = Join-Path -Path $collectorRoot -ChildPath "Test-TraceAdReadiness.ps1"

Describe "Test-TraceAdReadiness" {
    It "returns ok when domain, RSAT, DC discovery, and LDAP evidence are ready" {
        $result = & $readinessScript `
            -HostnameOverride "TRACE-CLIENT01" `
            -DomainJoinedOverride "true" `
            -DomainNameOverride "factory.local" `
            -ActiveDirectoryModuleAvailableOverride "true" `
            -DomainControllerDiscoveredOverride "true" `
            -DomainControllerNameOverride "dc01.factory.local" `
            -LdapReachableOverride "true" |
            ConvertFrom-Json

        $result.status | Should Be "ok"
        $result.module | Should Be "active-directory-readiness"
        $result.check | Should Be "ad_readiness"
        $result.evidence.hostname | Should Be "TRACE-CLIENT01"
        $result.evidence.domain_joined | Should Be $true
        $result.evidence.domain_name | Should Be "factory.local"
        $result.evidence.active_directory_module_available | Should Be $true
        $result.evidence.domain_controller.discovered | Should Be $true
        $result.evidence.ldap_probe.reachable | Should Be $true
        $result.read_only_boundary.remediation_performed | Should Be $false
        $result.read_only_boundary.ad_objects_modified | Should Be $false
        $result.read_only_boundary.group_membership_changed | Should Be $false
        $result.read_only_boundary.password_or_account_state_changed | Should Be $false
    }

    It "returns warning for non-domain context" {
        $result = & $readinessScript `
            -HostnameOverride "WORKGROUP-PC" `
            -DomainJoinedOverride "false" `
            -WorkgroupOverride "WORKGROUP" `
            -ActiveDirectoryModuleAvailableOverride "false" `
            -DomainControllerDiscoveredOverride "false" `
            -LdapReachableOverride "false" |
            ConvertFrom-Json

        $result.status | Should Be "warning"
        $result.evidence.domain_joined | Should Be $false
        $result.evidence.workgroup | Should Be "WORKGROUP"
        $result.safe_next_steps -join " " | Should Match "domain-joined"
    }

    It "returns warning when LDAP reachability is not proven" {
        $result = & $readinessScript `
            -HostnameOverride "TRACE-CLIENT01" `
            -DomainJoinedOverride "true" `
            -DomainNameOverride "factory.local" `
            -ActiveDirectoryModuleAvailableOverride "true" `
            -DomainControllerDiscoveredOverride "true" `
            -DomainControllerNameOverride "dc01.factory.local" `
            -LdapReachableOverride "false" |
            ConvertFrom-Json

        $result.status | Should Be "warning"
        $result.evidence.ldap_probe.reachable | Should Be $false
        $result.safe_next_steps -join " " | Should Match "LDAP"
    }

    It "does not contain AD object, group, password, or account-state modification commands" {
        $scriptText = Get-Content -LiteralPath $readinessScript -Raw

        $scriptText | Should Not Match "Set-ADUser"
        $scriptText | Should Not Match "New-ADUser"
        $scriptText | Should Not Match "Remove-ADUser"
        $scriptText | Should Not Match "Enable-ADAccount"
        $scriptText | Should Not Match "Disable-ADAccount"
        $scriptText | Should Not Match "Unlock-ADAccount"
        $scriptText | Should Not Match "Add-ADGroupMember"
        $scriptText | Should Not Match "Remove-ADGroupMember"
    }
}
