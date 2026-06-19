$collectorRoot = Split-Path -Parent $PSScriptRoot
$dnsScript = Join-Path -Path $collectorRoot -ChildPath "Invoke-TraceDnsDiagnostic.ps1"

Describe "Invoke-TraceDnsDiagnostic" {
    It "returns success when DNS records are provided" {
        $record = [pscustomobject]@{ IPAddress = "192.168.10.10" }

        $result = & $dnsScript -Query "dc01.factory.local" -RecordType "A" -DnsServer "192.168.10.10" -ResolveResultOverride @($record) | ConvertFrom-Json

        $result.status | Should Be "success"
        $result.module | Should Be "dns-diagnostics"
        $result.check | Should Be "dns_diagnostic"
        $result.input.query | Should Be "dc01.factory.local"
        $result.evidence.resolved | Should Be $true
        $result.evidence.records[0] | Should Be "192.168.10.10"
        $result.read_only_boundary.remediation_performed | Should Be $false
        $result.read_only_boundary.dns_configuration_changed | Should Be $false
        $result.read_only_boundary.network_configuration_changed | Should Be $false
    }

    It "returns warning with evidence and finding when DNS resolution fails" {
        $result = & $dnsScript -Query "missing.factory.local" -RecordType "A" -ResolveErrorOverride "DNS name does not exist." | ConvertFrom-Json

        $result.status | Should Be "warning"
        $result.evidence.resolved | Should Be $false
        $result.evidence.error | Should Match "DNS name does not exist"
        $result.findings[0].finding_id | Should Be "DNS_RESOLUTION_FAILED"
        $result.findings[0].evidence_used -join " " | Should Match "missing.factory.local"
        $result.safe_next_steps -join " " | Should Match "Compare"
    }

    It "supports CNAME style result values" {
        $record = [pscustomobject]@{ NameHost = "server01.factory.local" }

        $result = & $dnsScript -Query "app.factory.local" -RecordType "CNAME" -ResolveResultOverride @($record) | ConvertFrom-Json

        $result.status | Should Be "success"
        $result.evidence.records[0] | Should Be "server01.factory.local"
    }

    It "does not contain write or remediation cmdlets" {
        $scriptText = Get-Content -LiteralPath $dnsScript -Raw

        $scriptText | Should Not Match "Set-DnsClientServerAddress"
        $scriptText | Should Not Match "New-NetIPAddress"
        $scriptText | Should Not Match "Remove-NetRoute"
        $scriptText | Should Not Match "Restart-Service"
        $scriptText | Should Not Match "Set-ADUser"
    }
}
