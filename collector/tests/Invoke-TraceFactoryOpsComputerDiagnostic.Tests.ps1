Describe "Invoke-TraceFactoryOpsComputerDiagnostic" {
    $scriptPath = Join-Path (Split-Path -Parent $PSScriptRoot) "Invoke-TraceFactoryOpsComputerDiagnostic.ps1"

    It "returns success with DNS, AD, and reachability evidence for office-pc01" {
        $dnsRecord = [pscustomobject]@{ Name = "office-pc01.factory.local"; Type = "A"; IPAddress = "10.20.10.100" }
        $adComputer = [pscustomobject]@{
            Name = "OFFICE-PC01"
            DNSHostName = "office-pc01.factory.local"
            Enabled = $true
            DistinguishedName = "CN=OFFICE-PC01,CN=Computers,DC=factory,DC=local"
            OperatingSystem = "Windows Server 2022"
            LastLogonDate = $null
            IPv4Address = "10.20.10.100"
        }
        $reachability = @{ "office-pc01.factory.local" = $true }
        $ports = @{ "office-pc01.factory.local:445" = $true; "office-pc01.factory.local:3389" = $false }

        $json = & $scriptPath -ComputerName "office-pc01" -DomainName "factory.local" -DnsServer "10.40.10.10" -ExpectedIpv4Address "10.20.10.100" -DnsRecordsOverride @($dnsRecord) -AdComputerOverride $adComputer -AdModuleAvailableOverride $true -ReachabilityOverride $reachability -PortProbeOverride $ports
        $result = $json | ConvertFrom-Json

        $result.status | Should Be "success"
        $result.check | Should Be "factoryops_computer_diagnostic"
        $result.evidence.dns.resolved_ipv4_addresses[0] | Should Be "10.20.10.100"
        $result.evidence.active_directory.computer_found | Should Be $true
        $result.evidence.reachability.port_probes[0].port | Should Be 445
        $result.read_only_boundary.remediation_performed | Should Be $false
        $result.read_only_boundary.ad_objects_modified | Should Be $false
        $result.read_only_boundary.remote_command_executed | Should Be $false
    }

    It "returns a finding when the expected IPv4 address does not match DNS evidence" {
        $dnsRecord = [pscustomobject]@{ Name = "office-pc01.factory.local"; Type = "A"; IPAddress = "10.20.10.101" }
        $adComputer = [pscustomobject]@{ Name = "OFFICE-PC01"; DNSHostName = "office-pc01.factory.local"; Enabled = $true; DistinguishedName = "CN=OFFICE-PC01,CN=Computers,DC=factory,DC=local"; OperatingSystem = "Windows Server 2022"; LastLogonDate = $null; IPv4Address = "10.20.10.101" }
        $reachability = @{ "office-pc01.factory.local" = $true }
        $ports = @{ "office-pc01.factory.local:445" = $true; "office-pc01.factory.local:3389" = $false }

        $json = & $scriptPath -ComputerName "office-pc01" -DomainName "factory.local" -ExpectedIpv4Address "10.20.10.100" -DnsRecordsOverride @($dnsRecord) -AdComputerOverride $adComputer -AdModuleAvailableOverride $true -ReachabilityOverride $reachability -PortProbeOverride $ports
        $result = $json | ConvertFrom-Json

        $result.status | Should Be "finding"
        @($result.findings | Where-Object { $_.finding_id -eq "FACTORYOPS_COMPUTER_DNS_IP_MISMATCH" }).Count | Should Be 1
    }

    It "returns findings when DNS and AD evidence are not proven" {
        $reachability = @{ "missing-pc.factory.local" = $false }
        $ports = @{ "missing-pc.factory.local:445" = $false; "missing-pc.factory.local:3389" = $false }

        $json = & $scriptPath -ComputerName "missing-pc" -DomainName "factory.local" -DnsRecordsOverride @() -AdModuleAvailableOverride $false -ReachabilityOverride $reachability -PortProbeOverride $ports
        $result = $json | ConvertFrom-Json

        $result.status | Should Be "finding"
        @($result.findings | Where-Object { $_.finding_id -eq "FACTORYOPS_COMPUTER_DNS_A_RECORD_NOT_PROVEN" }).Count | Should Be 1
        @($result.findings | Where-Object { $_.finding_id -eq "FACTORYOPS_AD_COMPUTER_OBJECT_NOT_PROVEN" }).Count | Should Be 1
        $result.evidence.active_directory.module_available | Should Be $false
    }

    It "preserves the read-only boundary" {
        $scriptText = Get-Content -LiteralPath $scriptPath -Raw

        $scriptText | Should Not Match "Set-DnsClientServerAddress"
        $scriptText | Should Not Match "New-NetIPAddress"
        $scriptText | Should Not Match "Remove-NetRoute"
        $scriptText | Should Not Match "Set-ADUser"
        $scriptText | Should Not Match "New-ADComputer"
        $scriptText | Should Not Match "Remove-ADComputer"
        $scriptText | Should Not Match "Add-ADGroupMember"
        $scriptText | Should Not Match "Restart-Service"
    }
}
