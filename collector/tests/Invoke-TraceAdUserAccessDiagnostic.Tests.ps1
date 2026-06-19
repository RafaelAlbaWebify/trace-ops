Describe 'Invoke-TraceAdUserAccessDiagnostic fixture mode' {
    BeforeAll {
        $script:ScriptPath = Join-Path $PSScriptRoot '..\Invoke-TraceAdUserAccessDiagnostic.ps1'
    }

    It 'returns a finding for disabled account fixture evidence' {
        $json = powershell.exe -NoProfile -ExecutionPolicy Bypass -File $script:ScriptPath -UserPrincipalName 'jane.doe@factory.local' -AffectedService 'Factory ERP' -Scenario 'ad-account-disabled'
        $result = $json | ConvertFrom-Json

        $result.status | Should Be 'finding'
        $result.check | Should Be 'ad_user_access_diagnostic'
        $result.input.fixture_mode | Should Be $true
        $result.evidence.user.enabled | Should Be $false
        $result.findings[0].finding_id | Should Be 'AD_ACCOUNT_DISABLED'
        $result.read_only_boundary.real_ad_query_performed | Should Be $false
    }

    It 'returns a finding for missing required group fixture evidence' {
        $json = powershell.exe -NoProfile -ExecutionPolicy Bypass -File $script:ScriptPath -UserPrincipalName 'jane.doe@factory.local' -AffectedService 'Factory VPN' -Scenario 'ad-required-group-missing'
        $result = $json | ConvertFrom-Json

        $result.status | Should Be 'finding'
        $result.findings[0].finding_id | Should Be 'AD_REQUIRED_GROUP_MISSING'
        $result.evidence.group_requirements.Count | Should Be 1
    }

    It 'returns success when fixture baseline has no AD blocker' {
        $json = powershell.exe -NoProfile -ExecutionPolicy Bypass -File $script:ScriptPath -UserPrincipalName 'jane.doe@factory.local' -AffectedService 'Factory ERP' -Scenario 'ad-successful-baseline'
        $result = $json | ConvertFrom-Json

        $result.status | Should Be 'success'
        $result.findings.Count | Should Be 0
        $result.evidence.real_ad_query_performed | Should Be $false
    }

    It 'returns controlled error when real AD query mode is requested' {
        $command = "& '$($script:ScriptPath)' -UserPrincipalName 'jane.doe@factory.local' -AffectedService 'Factory ERP' -Scenario 'ad-account-disabled' -UseFixtureData:`$false"
        $encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
        $json = powershell.exe -NoProfile -ExecutionPolicy Bypass -EncodedCommand $encodedCommand
        $result = $json | ConvertFrom-Json

        $result.status | Should Be 'error'
        $result.error.code | Should Be 'REAL_AD_QUERY_NOT_ENABLED'
        $result.read_only_boundary.real_ad_query_performed | Should Be $false
    }

    It 'does not contain AD modification, password change, or group change command families' {
        $scriptText = Get-Content -Raw -Path $script:ScriptPath
        $scriptText | Should Not Match 'Set-AD'
        $scriptText | Should Not Match 'New-AD'
        $scriptText | Should Not Match 'Remove-AD'
        $scriptText | Should Not Match 'Add-ADGroup'
        $scriptText | Should Not Match 'Remove-ADGroup'
        $scriptText | Should Not Match 'Set-LocalUser'
    }
}
