Describe "Invoke-TraceFactoryOpsFileShareAccessDiagnostic" {
    $scriptPath = Join-Path (Split-Path -Parent $PSScriptRoot) "Invoke-TraceFactoryOpsFileShareAccessDiagnostic.ps1"

    It "returns success when the user is in the required share access group" {
        $dnsRecord = [pscustomobject]@{ Name = "filesrv01.factory.local"; Type = "A"; IPAddress = "10.40.10.20" }
        $user = [pscustomobject]@{
            Name = "Finance Allowed"
            SamAccountName = "finance.ok"
            UserPrincipalName = "finance.ok@factory.local"
            Enabled = $true
            DistinguishedName = "CN=Finance Allowed,OU=FactoryOps Test Users,DC=factory,DC=local"
            MemberOf = @("CN=GG_FINANCE_SHARE_READ,OU=FactoryOps Test Users,DC=factory,DC=local")
        }
        $group = [pscustomobject]@{
            Name = "GG_FINANCE_SHARE_READ"
            SamAccountName = "GG_FINANCE_SHARE_READ"
            DistinguishedName = "CN=GG_FINANCE_SHARE_READ,OU=FactoryOps Test Users,DC=factory,DC=local"
            Members = @("CN=Finance Allowed,OU=FactoryOps Test Users,DC=factory,DC=local")
        }
        $ports = @{ "filesrv01.factory.local:445" = $true }

        $json = & $scriptPath -ShareHost "filesrv01" -ShareName "Finance" -UserSamAccountName "finance.ok" -RequiredGroupSamAccountName "GG_FINANCE_SHARE_READ" -DomainName "factory.local" -DnsServer "10.40.10.10" -ObservedAccessDenied:$false -DnsRecordsOverride @($dnsRecord) -AdUserOverride $user -RequiredGroupOverride $group -AdModuleAvailableOverride $true -PortProbeOverride $ports
        $result = $json | ConvertFrom-Json

        $result.status | Should Be "success"
        $result.check | Should Be "factoryops_file_share_access_diagnostic"
        $result.evidence.reachability.smb_tcp_445_reachable | Should Be $true
        $result.evidence.active_directory.membership_proven | Should Be $true
        $result.read_only_boundary.remediation_performed | Should Be $false
        $result.read_only_boundary.group_membership_changed | Should Be $false
        $result.read_only_boundary.ntfs_or_share_permissions_changed | Should Be $false
    }

    It "returns a finding when the user is missing the required group" {
        $dnsRecord = [pscustomobject]@{ Name = "filesrv01.factory.local"; Type = "A"; IPAddress = "10.40.10.20" }
        $user = [pscustomobject]@{
            Name = "Finance NoAccess"
            SamAccountName = "finance.noaccess"
            UserPrincipalName = "finance.noaccess@factory.local"
            Enabled = $true
            DistinguishedName = "CN=Finance NoAccess,OU=FactoryOps Test Users,DC=factory,DC=local"
            MemberOf = @()
        }
        $group = [pscustomobject]@{
            Name = "GG_FINANCE_SHARE_READ"
            SamAccountName = "GG_FINANCE_SHARE_READ"
            DistinguishedName = "CN=GG_FINANCE_SHARE_READ,OU=FactoryOps Test Users,DC=factory,DC=local"
            Members = @("CN=Finance Allowed,OU=FactoryOps Test Users,DC=factory,DC=local")
        }
        $ports = @{ "filesrv01.factory.local:445" = $true }

        $json = & $scriptPath -ShareHost "filesrv01" -ShareName "Finance" -UserSamAccountName "finance.noaccess" -RequiredGroupSamAccountName "GG_FINANCE_SHARE_READ" -DomainName "factory.local" -ObservedAccessDenied:$true -DnsRecordsOverride @($dnsRecord) -AdUserOverride $user -RequiredGroupOverride $group -AdModuleAvailableOverride $true -PortProbeOverride $ports
        $result = $json | ConvertFrom-Json

        $result.status | Should Be "finding"
        @($result.findings | Where-Object { $_.finding_id -eq "FACTORYOPS_FILE_SHARE_USER_MISSING_REQUIRED_GROUP" }).Count | Should Be 1
        $result.evidence.active_directory.membership_proven | Should Be $false
        $result.evidence.observed_access.access_denied | Should Be $true
    }

    It "preserves the read-only boundary" {
        $scriptText = Get-Content -LiteralPath $scriptPath -Raw

        $scriptText | Should Not Match "Add-ADGroupMember"
        $scriptText | Should Not Match "Remove-ADGroupMember"
        $scriptText | Should Not Match "Set-Acl"
        $scriptText | Should Not Match "icacls"
        $scriptText | Should Not Match "Grant-SmbShareAccess"
        $scriptText | Should Not Match "New-SmbShare"
        $scriptText | Should Not Match "Set-SmbShare"
        $scriptText | Should Not Match "New-NetFirewallRule"
        $scriptText | Should Not Match "Enable-NetFirewallRule"
        $scriptText | Should Not Match "Restart-Service"
    }
}
