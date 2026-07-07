from pathlib import Path


PRODUCT_ID = "trace"
PRODUCT_NAME = "TRACE"
PRODUCT_FULL_NAME = "Troubleshooting Reports Across Cloud & Endpoints"
FIRST_MODULE_ID = "m365-access-path-analyzer"
FIRST_MODULE_NAME = "M365 Access Path Analyzer"

APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
REPO_ROOT = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
HISTORY_DB_PATH = DATA_DIR / "trace_history.sqlite3"
SAMPLES_DIR = REPO_ROOT / "samples"
COLLECTOR_SCRIPT_PATH = REPO_ROOT / "collector" / "Invoke-TraceM365AccessScan.ps1"
GRAPH_READINESS_SCRIPT_PATH = REPO_ROOT / "collector" / "Test-TraceGraphReadiness.ps1"
LOCAL_READINESS_SCRIPT_PATH = REPO_ROOT / "collector" / "Test-TraceLocalReadiness.ps1"
DNS_DIAGNOSTIC_SCRIPT_PATH = REPO_ROOT / "collector" / "Invoke-TraceDnsDiagnostic.ps1"
AD_READINESS_SCRIPT_PATH = REPO_ROOT / "collector" / "Test-TraceAdReadiness.ps1"
AD_USER_ACCESS_SCRIPT_PATH = REPO_ROOT / "collector" / "Invoke-TraceAdUserAccessDiagnostic.ps1"
FACTORYOPS_COMPUTER_DIAGNOSTIC_SCRIPT_PATH = REPO_ROOT / "collector" / "Invoke-TraceFactoryOpsComputerDiagnostic.ps1"
FACTORYOPS_FILE_SHARE_DIAGNOSTIC_SCRIPT_PATH = REPO_ROOT / "collector" / "Invoke-TraceFactoryOpsFileShareAccessDiagnostic.ps1"
COLLECTOR_TIMEOUT_SECONDS = 30

SUPPORTED_SAMPLE_SCENARIOS = (
    "account-disabled",
    "missing-license",
    "guest-b2b-access-failure",
    "ca-details-missing",
    "ca-device-noncompliant",
    "mfa-requirement-not-satisfied",
    "no-recent-signin-evidence",
    "successful-access-baseline",
)

SUPPORTED_AFFECTED_SERVICES = (
    "Microsoft 365 general access",
    "Exchange Online / Outlook",
    "SharePoint Online / OneDrive",
    "Microsoft Teams",
)
