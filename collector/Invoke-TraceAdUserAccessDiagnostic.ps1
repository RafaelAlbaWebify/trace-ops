param(
    [Parameter(Mandatory=$true)]
    [string]$UserPrincipalName,

    [Parameter(Mandatory=$true)]
    [string]$AffectedService,

    [Parameter(Mandatory=$true)]
    [ValidateSet('ad-account-disabled','ad-account-locked','ad-password-expired','ad-required-group-missing','ad-successful-baseline')]
    [string]$Scenario,

    [bool]$UseFixtureData = $true
)

$ErrorActionPreference = 'Stop'

function ConvertTo-TraceJson {
    param([Parameter(Mandatory=$true)]$Value)
    $Value | ConvertTo-Json -Depth 20
}

$baseBoundary = [ordered]@{
    remediation_performed = $false
    ad_objects_modified = $false
    group_membership_changed = $false
    password_or_account_state_changed = $false
    real_ad_query_performed = $false
}

if (-not $UseFixtureData) {
    ConvertTo-TraceJson ([ordered]@{
        status = 'error'
        module = 'active-directory-user-access-diagnostic'
        check = 'ad_user_access_diagnostic'
        input = [ordered]@{
            user_principal_name = $UserPrincipalName
            affected_service = $AffectedService
            scenario = $Scenario
            fixture_mode = $false
        }
        error = [ordered]@{
            code = 'REAL_AD_QUERY_NOT_ENABLED'
            message = 'Phase 6 only supports fixture-mode AD user access diagnostics.'
        }
        evidence = [ordered]@{
            user = $null
            group_requirements = @()
            fixture_mode = $false
        }
        findings = @()
        safe_next_steps = @('Use fixture mode until the real AD query design is explicitly implemented and reviewed.')
        limitations = @('TRACE did not query Active Directory in Phase 6. This diagnostic uses fixture data only.')
        read_only_boundary = $baseBoundary
    })
    exit 0
}

$fixture = [ordered]@{
    user_principal_name = $UserPrincipalName
    sam_account_name = ($UserPrincipalName -split '@')[0]
    distinguished_name = 'CN=' + (($UserPrincipalName -split '@')[0]) + ',OU=FactoryUsers,DC=factory,DC=local'
    enabled = $true
    locked_out = $false
    password_expired = $false
    password_last_set = '2026-05-20T09:15:00Z'
    member_of = @('CN=FactoryUsers,OU=Groups,DC=factory,DC=local')
}

$requiredGroups = @()
$findings = @()
$status = 'success'
$safeNextSteps = @('Use this fixture evidence to validate the diagnostic workflow only. Confirm real AD evidence before changing any account, password, group, DNS, or endpoint setting.')
$limitations = @('Fixture-mode diagnostic only. TRACE did not query or modify Active Directory users, groups, passwords, DNS, services, or endpoint settings.')

switch ($Scenario) {
    'ad-account-disabled' {
        $fixture.enabled = $false
        $status = 'finding'
        $findings += [ordered]@{
            finding_id = 'AD_ACCOUNT_DISABLED'
            rule_id = 'AD_ACCOUNT_DISABLED'
            title = 'AD account is disabled in fixture evidence'
            severity = 'high'
            confidence = 'high'
            likely_cause = 'The fixture identity evidence shows the AD account is disabled, which would block interactive access.'
            evidence_used = @('fixture.user.enabled = false', 'affected_service = ' + $AffectedService)
            evidence_missing = @('Real AD user properties were not queried in Phase 6.', 'Recent workstation logon events were not collected.')
            safe_next_steps = @('In a real environment, verify account status with approved read-only AD tools before making any change.', 'Check whether this account state is expected for the user lifecycle or HR process.')
            what_not_to_change_yet = @('Do not change account state based on fixture data.', 'Do not change group membership, DNS, or endpoint settings from this result alone.')
            limitations = $limitations
            source_module = 'active-directory-user-access-diagnostic'
        }
    }
    'ad-account-locked' {
        $fixture.locked_out = $true
        $status = 'finding'
        $findings += [ordered]@{
            finding_id = 'AD_ACCOUNT_LOCKED'
            rule_id = 'AD_ACCOUNT_LOCKED'
            title = 'AD account is locked in fixture evidence'
            severity = 'medium'
            confidence = 'high'
            likely_cause = 'The fixture identity evidence shows the AD account is locked, which can block authentication until the lockout clears or is reviewed.'
            evidence_used = @('fixture.user.locked_out = true', 'affected_service = ' + $AffectedService)
            evidence_missing = @('Real lockout source and event evidence were not collected.', 'Domain controller security events were not queried.')
            safe_next_steps = @('In a real environment, verify lockout state and lockout source with approved read-only evidence before taking action.', 'Check whether repeated failed sign-ins are coming from a stale saved password or mapped drive.')
            what_not_to_change_yet = @('Do not change password or account state based on fixture data.', 'Do not restart services or change endpoint settings from this result alone.')
            limitations = $limitations
            source_module = 'active-directory-user-access-diagnostic'
        }
    }
    'ad-password-expired' {
        $fixture.password_expired = $true
        $fixture.password_last_set = '2025-11-01T08:00:00Z'
        $status = 'finding'
        $findings += [ordered]@{
            finding_id = 'AD_PASSWORD_EXPIRED'
            rule_id = 'AD_PASSWORD_EXPIRED'
            title = 'AD password is expired in fixture evidence'
            severity = 'medium'
            confidence = 'high'
            likely_cause = 'The fixture identity evidence shows an expired password, which can block access depending on service and authentication path.'
            evidence_used = @('fixture.user.password_expired = true', 'fixture.user.password_last_set = 2025-11-01T08:00:00Z')
            evidence_missing = @('Real password policy and user password metadata were not queried.', 'Cloud password sync evidence was not collected.')
            safe_next_steps = @('In a real environment, verify password status and password policy evidence before taking action.', 'Check whether the affected service relies on synced AD credentials.')
            what_not_to_change_yet = @('Do not reset passwords based on fixture data.', 'Do not change Conditional Access, DNS, or endpoint settings from this result alone.')
            limitations = $limitations
            source_module = 'active-directory-user-access-diagnostic'
        }
    }
    'ad-required-group-missing' {
        $requiredGroups = @('CN=FactoryVPNUsers,OU=Groups,DC=factory,DC=local')
        $status = 'finding'
        $findings += [ordered]@{
            finding_id = 'AD_REQUIRED_GROUP_MISSING'
            rule_id = 'AD_REQUIRED_GROUP_MISSING'
            title = 'Required AD group membership is missing in fixture evidence'
            severity = 'medium'
            confidence = 'medium'
            likely_cause = 'The fixture group evidence does not include the required access group for the affected service.'
            evidence_used = @('required_group = CN=FactoryVPNUsers,OU=Groups,DC=factory,DC=local', 'fixture.user.member_of does not include required_group')
            evidence_missing = @('Real group membership was not queried.', 'Service-specific authorization mapping was not validated.')
            safe_next_steps = @('In a real environment, verify group membership and service authorization mapping before requesting any group change.', 'Confirm the required group with the service owner or access model documentation.')
            what_not_to_change_yet = @('Do not add or remove group membership based on fixture data.', 'Do not change ACLs, DNS, or endpoint settings from this result alone.')
            limitations = $limitations
            source_module = 'active-directory-user-access-diagnostic'
        }
    }
    'ad-successful-baseline' {
        $requiredGroups = @('CN=FactoryUsers,OU=Groups,DC=factory,DC=local')
        $safeNextSteps = @('No AD account blocker is present in this fixture baseline. Continue checking DNS, endpoint, M365, or application-specific evidence as needed.')
    }
}

$result = [ordered]@{
    status = $status
    module = 'active-directory-user-access-diagnostic'
    check = 'ad_user_access_diagnostic'
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    input = [ordered]@{
        user_principal_name = $UserPrincipalName
        affected_service = $AffectedService
        scenario = $Scenario
        fixture_mode = $true
    }
    evidence = [ordered]@{
        user = $fixture
        group_requirements = $requiredGroups
        fixture_mode = $true
        real_ad_query_performed = $false
    }
    findings = $findings
    safe_next_steps = $safeNextSteps
    limitations = $limitations
    read_only_boundary = $baseBoundary
}

ConvertTo-TraceJson $result
