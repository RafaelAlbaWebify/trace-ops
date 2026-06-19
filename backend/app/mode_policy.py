from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

router = APIRouter(tags=["mode-policy"])

MODE_POLICY_CONTRACT_VERSION = "trace-mode-policy-v1"


def _mode(
    mode_id: str,
    title: str,
    purpose: str,
    allowed_capabilities: List[str],
    blocked_capabilities: List[str],
    readiness_required: List[str],
    operator_notes: List[str],
) -> Dict[str, Any]:
    return {
        "mode_id": mode_id,
        "title": title,
        "purpose": purpose,
        "allowed_capabilities": allowed_capabilities,
        "blocked_capabilities": blocked_capabilities,
        "readiness_required": readiness_required,
        "operator_notes": operator_notes,
    }


def build_mode_policy() -> Dict[str, Any]:
    modes = [
        _mode(
            "sample",
            "Sample mode",
            "Use built-in Microsoft 365 sample evidence and fixture scenarios to validate TRACE behavior without external systems.",
            [
                "Run Microsoft 365 sample scenarios.",
                "Generate JSON and HTML reports from sample evidence.",
                "Preview operator runbooks from supplied evidence.",
            ],
            [
                "Real Microsoft Graph collection.",
                "Real Active Directory user lookups.",
                "Tenant-wide inventory collection.",
                "Any configuration change.",
            ],
            ["No external readiness requirement."],
            ["This is the safest default mode for demos, development, and regression testing."],
        ),
        _mode(
            "homelab",
            "Homelab mode",
            "Use local, DNS, AD readiness, DNS diagnostic, and fixture-based AD user diagnostics against a controlled lab design.",
            [
                "Run local infrastructure readiness checks.",
                "Run DNS diagnostics against lab hostnames.",
                "Run AD readiness checks.",
                "Run fixture-based AD user access diagnostics.",
                "Preview homelab scenario files before execution planning.",
            ],
            [
                "Real AD user modification.",
                "Real AD group membership changes.",
                "DNS record changes.",
                "Network configuration changes.",
                "Service control actions.",
            ],
            [
                "Known lab scope.",
                "Operator-controlled host.",
                "No production credentials.",
                "Read-only diagnostic intent confirmed.",
            ],
            ["Use this mode for the VMware factory lab before attempting tenant-connected diagnostics."],
        ),
        _mode(
            "trial_tenant_ready",
            "Trial tenant readiness mode",
            "Prepare TRACE for a short-lived Microsoft 365 or Entra trial tenant without turning on uncontrolled production behavior.",
            [
                "Check Microsoft Graph readiness.",
                "Show required delegated scopes.",
                "Run one-user diagnostics only after explicit operator sign-in and readiness evidence.",
                "Keep reporting and runbook generation read-only.",
            ],
            [
                "Automatic Graph sign-in.",
                "Credential or token storage.",
                "Tenant-wide scans.",
                "Write scopes.",
                "Configuration changes.",
            ],
            [
                "Graph module available.",
                "Existing operator-created Graph context.",
                "Required read scopes present.",
                "Single target user provided by operator.",
                "Trial tenant boundary documented.",
            ],
            [
                "This is preparation only; real Graph collection remains guarded by explicit readiness checks.",
                "Use only a lab or trial tenant until production controls are designed and reviewed.",
            ],
        ),
    ]

    return {
        "status": "ok",
        "mode_policy_contract_version": MODE_POLICY_CONTRACT_VERSION,
        "current_default_mode": "sample",
        "recommended_next_mode": "homelab",
        "modes": modes,
        "global_read_only_boundary": {
            "automatic_connection_attempted": False,
            "credentials_or_tokens_stored": False,
            "tenant_wide_scan_performed": False,
            "write_scopes_requested": False,
            "configuration_changed": False,
            "remediation_performed": False,
        },
        "mode_transition_rules": [
            {
                "from": "sample",
                "to": "homelab",
                "allowed_when": [
                    "Local readiness is understood.",
                    "The operator is working in a controlled lab or workstation context.",
                    "No production environment is targeted.",
                ],
            },
            {
                "from": "homelab",
                "to": "trial_tenant_ready",
                "allowed_when": [
                    "Graph readiness endpoint reports module availability.",
                    "The operator signs in manually from PowerShell.",
                    "The target tenant is a lab or trial tenant.",
                    "Only one target user is diagnosed at a time.",
                ],
            },
        ],
        "limitations": [
            "This endpoint describes operating modes; it does not enable real tenant collection by itself.",
            "Production mode is intentionally not defined in this roadmap.",
            "Any future production mode must have a separate safety design and review.",
        ],
    }


@router.get("/api/mode-policy")
def get_mode_policy() -> Dict[str, Any]:
    return build_mode_policy()
