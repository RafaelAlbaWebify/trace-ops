from app.entra_signin_analyzer import analyze_entra_signin_export, parse_entra_signin_csv
from app.log_models import LogAnalyzeRequest


def _csv_sample():
    return """createdDateTime,userPrincipalName,appDisplayName,resourceDisplayName,clientAppUsed,conditionalAccessStatus,authenticationRequirement,status.errorCode,status.failureReason
2026-07-07T09:22:11Z,sample.user@contoso.invalid,SharePoint Online,SharePoint Online,Browser,failure,multiFactorAuthentication,53003,Policy evaluation did not pass
"""


def test_entra_csv_parser_normalizes_signin_row():
    events = parse_entra_signin_csv(_csv_sample())

    assert len(events) == 1
    assert events[0].source_type == "entra_signin_csv"
    assert events[0].event_type == "signin"
    assert events[0].event_outcome == "failure"
    assert events[0].user_principal_name == "sample.user@contoso.invalid"
    assert events[0].application == "SharePoint Online"


def test_entra_csv_analysis_returns_finding():
    request = LogAnalyzeRequest(
        source_type="entra_signin_csv",
        affected_user="sample.user@contoso.invalid",
        affected_service="SharePoint Online",
        content=_csv_sample(),
    )

    analysis = analyze_entra_signin_export(request)

    assert analysis.status == "findings"
    assert analysis.primary_finding is not None
    assert analysis.primary_finding["rule_id"] == "LOG_PATTERN_CONDITIONAL_ACCESS_BLOCK"
    assert analysis.normalized_events


def test_entra_csv_empty_input_returns_insufficient_evidence():
    analysis = analyze_entra_signin_export(LogAnalyzeRequest(source_type="entra_signin_csv", content="not,csv"))

    assert analysis.status == "insufficient_evidence"
    assert analysis.primary_finding is not None
    assert analysis.primary_finding["rule_id"] == "LOG_PATTERN_NO_USABLE_EVENTS"
