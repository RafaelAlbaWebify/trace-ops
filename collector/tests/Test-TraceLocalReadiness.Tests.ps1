$collectorRoot = Split-Path -Parent $PSScriptRoot
$readinessScript = Join-Path -Path $collectorRoot -ChildPath "Test-TraceLocalReadiness.ps1"

Describe "Test-TraceLocalReadiness" {
    It "returns JSON output with required shape" {
        $adapter = [ordered]@{ name = "Ethernet0"; status = "Up"; interface_description = "VMware virtual adapter"; mac_address = "00-11-22-33-44-55" }
        $ipConfig = [ordered]@{ interface_alias = "Ethernet0"; ipv4_addresses = @("192.168.10.20"); dns_servers = @("192.168.10.10"); default_gateway = "192.168.10.1" }
        $dnsProbe = [ordered]@{ query = "dc01.factory.local"; succeeded = $true; addresses = @("192.168.10.10"); error = $null }
        $gatewayProbe = [ordered]@{ target = "192.168.10.1"; reachable = $true; error = $null }

        $result = & $readinessScript `
            -HostnameOverride "TRACE-CLIENT01" `
            -OsDescriptionOverride "Windows 11 Pro" `
            -PowerShellVersionOverride "5.1.19041.1" `
            -NetworkAdaptersOverride @($adapter) `
            -IpConfigurationsOverride @($ipConfig) `
            -DomainJoinedOverride "true" `
            -DomainNameOverride "factory.local" `
            -DnsProbeOverride $dnsProbe `
            -GatewayProbeOverride $gatewayProbe |
            ConvertFrom-Json

        $result.status | Should Be "ok"
        $result.module | Should Be "local-infrastructure-readiness"
        $result.check | Should Be "local_readiness"
        $result.evidence.hostname | Should Be "TRACE-CLIENT01"
        $result.evidence.domain_joined | Should Be $true
        $result.evidence.domain_name | Should Be "factory.local"
        $result.evidence.network_adapters.Count | Should Be 1
        $result.evidence.ip_configurations.Count | Should Be 1
        $result.evidence.dns_probe.succeeded | Should Be $true
        $result.read_only_boundary.remediation_performed | Should Be $false
        $result.read_only_boundary.network_configuration_changed | Should Be $false
        $result.read_only_boundary.service_control_performed | Should Be $false
    }

    It "returns warning when DNS probe fails" {
        $dnsProbe = [ordered]@{ query = "dc01.factory.local"; succeeded = $false; addresses = @(); error = "DNS name does not exist." }
        $gatewayProbe = [ordered]@{ target = "192.168.10.1"; reachable = $true; error = $null }

        $result = & $readinessScript `
            -HostnameOverride "TRACE-CLIENT01" `
            -NetworkAdaptersOverride @([ordered]@{ name = "Ethernet0"; status = "Up"; interface_description = "VMware virtual adapter"; mac_address = "00-11-22-33-44-55" }) `
            -IpConfigurationsOverride @([ordered]@{ interface_alias = "Ethernet0"; ipv4_addresses = @("192.168.10.20"); dns_servers = @("192.168.10.10"); default_gateway = "192.168.10.1" }) `
            -DnsProbeOverride $dnsProbe `
            -GatewayProbeOverride $gatewayProbe |
            ConvertFrom-Json

        $result.status | Should Be "warning"
        $result.evidence.dns_probe.succeeded | Should Be $false
        $result.safe_next_steps -join " " | Should Match "DNS"
    }

    It "returns warning for non-domain context" {
        $dnsProbe = [ordered]@{ query = "localhost"; succeeded = $true; addresses = @("127.0.0.1"); error = $null }
        $gatewayProbe = [ordered]@{ target = $null; reachable = $null; error = "No default gateway detected." }

        $result = & $readinessScript `
            -HostnameOverride "WORKGROUP-PC" `
            -NetworkAdaptersOverride @() `
            -IpConfigurationsOverride @() `
            -DomainJoinedOverride "false" `
            -WorkgroupOverride "WORKGROUP" `
            -DnsProbeOverride $dnsProbe `
            -GatewayProbeOverride $gatewayProbe |
            ConvertFrom-Json

        $result.status | Should Be "warning"
        $result.evidence.domain_joined | Should Be $false
        $result.evidence.workgroup | Should Be "WORKGROUP"
        $result.safe_next_steps -join " " | Should Match "domain-joined"
    }

    It "does not contain write, remediation, or service-control cmdlets" {
        $scriptText = Get-Content -LiteralPath $readinessScript -Raw

        $scriptText | Should Not Match "Set-DnsClientServerAddress"
        $scriptText | Should Not Match "New-NetIPAddress"
        $scriptText | Should Not Match "Remove-NetRoute"
        $scriptText | Should Not Match "Restart-Service"
        $scriptText | Should Not Match "Stop-Service"
        $scriptText | Should Not Match "Start-Service"
        $scriptText | Should Not Match "Enable-ADAccount"
        $scriptText | Should Not Match "Set-ADUser"
    }
}
