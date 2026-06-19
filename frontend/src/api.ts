export const SAMPLE_SCENARIOS = [
  "account-disabled",
  "missing-license",
  "ca-details-missing",
  "ca-device-noncompliant",
  "mfa-requirement-not-satisfied",
  "no-recent-signin-evidence",
  "successful-access-baseline"
] as const;

export const AFFECTED_SERVICES = [
  "Microsoft 365 general access",
  "Exchange Online / Outlook",
  "SharePoint Online / OneDrive",
  "Microsoft Teams"
] as const;

export type ScanRequest = {
  user_principal_name: string;
  affected_service: string;
  scenario: string;
};

export type Finding = {
  rule_id: string;
  title: string;
  severity: string;
  confidence: string;
  likely_cause: string;
  evidence: string[];
  next_steps: string[];
  what_not_to_change_yet: string[];
  limitations: string[];
};

export type ScanResponse = {
  status: string;
  history_id?: number;
  result?: {
    scenario_id: string;
    module: string;
    input: ScanRequest;
  };
  analysis?: {
    status: string;
    primary_finding: Finding | null;
    findings: Finding[];
    summary: string;
    confidence: string;
    limitations: string[];
  };
  error?: {
    code: string;
    message: string;
    scenario?: string;
  };
};


export type GraphReadinessResponse = {
  status: string;
  module: string;
  check: string;
  required_scopes?: string[];
  evidence?: {
    graph_module_available: boolean;
    connected_to_graph: boolean;
    tenant_id?: string | null;
    account?: string | null;
    available_scopes?: string[];
    missing_scopes?: string[];
  };
  safe_next_steps: string[];
  limitations: string[];
  read_only_boundary: {
    remediation_performed: boolean;
    automatic_connection_attempted: boolean;
    tenant_wide_scan_performed: boolean;
  };
  error?: {
    code: string;
    message: string;
  };
};

export type LocalReadinessResponse = {
  status: string;
  module: string;
  check: string;
  evidence?: {
    hostname?: string | null;
    os_description?: string | null;
    powershell_version?: string | null;
    domain_joined?: boolean | null;
    domain_name?: string | null;
    workgroup?: string | null;
    network_adapters?: Array<{
      name?: string | null;
      status?: string | null;
      interface_description?: string | null;
      mac_address?: string | null;
    }>;
    ip_configurations?: Array<{
      interface_alias?: string | null;
      ipv4_addresses?: string[];
      dns_servers?: string[];
      default_gateway?: string | null;
    }>;
    dns_probe?: {
      query?: string | null;
      succeeded?: boolean | null;
      addresses?: string[];
      error?: string | null;
    };
    gateway_probe?: {
      target?: string | null;
      reachable?: boolean | null;
      error?: string | null;
    };
  };
  safe_next_steps: string[];
  limitations: string[];
  read_only_boundary: {
    remediation_performed: boolean;
    network_configuration_changed: boolean;
    service_control_performed: boolean;
  };
  error?: {
    code: string;
    message: string;
  };
};


export type AdReadinessResponse = {
  status: string;
  module: string;
  check: string;
  evidence?: {
    hostname?: string | null;
    domain_joined?: boolean | null;
    domain_name?: string | null;
    workgroup?: string | null;
    active_directory_module_available?: boolean | null;
    domain_controller?: {
      discovered?: boolean | null;
      domain_controller?: string | null;
      method?: string | null;
      error?: string | null;
    };
    ldap_probe?: {
      target?: string | null;
      port?: number | null;
      reachable?: boolean | null;
      error?: string | null;
    };
    current_user_context?: {
      user_domain?: string | null;
      username?: string | null;
    };
  };
  safe_next_steps: string[];
  limitations: string[];
  read_only_boundary: {
    remediation_performed: boolean;
    ad_objects_modified: boolean;
    group_membership_changed: boolean;
    password_or_account_state_changed: boolean;
  };
  error?: {
    code: string;
    message: string;
  };
};


export const AD_USER_ACCESS_SCENARIOS = [
  "ad-account-disabled",
  "ad-account-locked",
  "ad-password-expired",
  "ad-required-group-missing",
  "ad-successful-baseline"
] as const;

export type AdUserAccessDiagnosticRequest = {
  user_principal_name: string;
  affected_service: string;
  scenario: (typeof AD_USER_ACCESS_SCENARIOS)[number];
};

export type AdUserAccessDiagnosticResponse = {
  status: string;
  module: string;
  check: string;
  input?: AdUserAccessDiagnosticRequest & { fixture_mode?: boolean };
  evidence?: {
    user?: {
      user_principal_name?: string;
      sam_account_name?: string;
      enabled?: boolean;
      locked_out?: boolean;
      password_expired?: boolean;
      member_of?: string[];
    } | null;
    group_requirements?: string[];
    fixture_mode?: boolean;
    real_ad_query_performed?: boolean;
  };
  findings?: Array<{
    finding_id?: string;
    rule_id?: string;
    title?: string;
    severity?: string;
    confidence?: string;
    likely_cause?: string;
    evidence_used?: string[];
    evidence_missing?: string[];
    safe_next_steps?: string[];
    what_not_to_change_yet?: string[];
    limitations?: string[];
  }>;
  safe_next_steps: string[];
  limitations: string[];
  read_only_boundary: {
    remediation_performed: boolean;
    ad_objects_modified: boolean;
    group_membership_changed: boolean;
    password_or_account_state_changed: boolean;
    real_ad_query_performed: boolean;
  };
  error?: {
    code: string;
    message: string;
  };
};

export type DnsDiagnosticRequest = {
  query: string;
  record_type: "A" | "AAAA" | "CNAME" | "MX" | "TXT" | "PTR";
  dns_server?: string | null;
};

export type DnsDiagnosticResponse = {
  status: string;
  module: string;
  check: string;
  input?: DnsDiagnosticRequest;
  evidence?: {
    query?: string | null;
    record_type?: string | null;
    dns_server?: string | null;
    resolver?: string | null;
    resolved?: boolean | null;
    records?: string[];
    record_count?: number;
    error?: string | null;
  };
  findings?: Array<{
    finding_id?: string;
    title?: string;
    severity?: string;
    confidence?: string;
    likely_cause?: string;
    evidence_used?: string[];
    safe_next_steps?: string[];
    limitations?: string[];
  }>;
  safe_next_steps: string[];
  limitations: string[];
  read_only_boundary: {
    remediation_performed: boolean;
    dns_configuration_changed: boolean;
    network_configuration_changed: boolean;
  };
  error?: {
    code: string;
    message: string;
  };
};



export type FileShareAccessDiagnosticRequest = {
  share_host: string;
  share_name: string;
  user_sam_account_name: string;
  required_group_sam_account_name: string;
  domain_name: string;
  dns_server?: string | null;
  observed_access_denied?: boolean | null;
};

export type FileShareAccessDiagnosticResponse = {
  status: string;
  module: string;
  check: string;
  input?: FileShareAccessDiagnosticRequest & {
    share_host_fqdn?: string;
    share_unc_path?: string;
  };
  evidence?: {
    dns?: {
      query?: string | null;
      server?: string | null;
      resolved_ipv4_addresses?: string[];
      error?: string | null;
    };
    reachability?: {
      target?: string | null;
      smb_tcp_445_reachable?: boolean | null;
    };
    active_directory?: {
      module_available?: boolean | null;
      user_found?: boolean | null;
      user?: {
        name?: string | null;
        sam_account_name?: string | null;
        user_principal_name?: string | null;
        enabled?: boolean | null;
        distinguished_name?: string | null;
        member_of?: string[];
      } | null;
      required_group_found?: boolean | null;
      required_group?: {
        name?: string | null;
        sam_account_name?: string | null;
        distinguished_name?: string | null;
        members?: string[];
      } | null;
      membership_proven?: boolean | null;
      user_error?: string | null;
      group_error?: string | null;
    };
    observed_access?: {
      access_denied?: boolean | null;
      supplied_by_operator?: boolean | null;
    };
  };
  findings?: Array<{
    finding_id?: string;
    rule_id?: string;
    title?: string;
    severity?: string;
    confidence?: string;
    likely_cause?: string;
    evidence_used?: string[];
    evidence_missing?: string[];
    safe_next_steps?: string[];
    what_not_to_change_yet?: string[];
    limitations?: string[];
    source_module?: string;
  }>;
  safe_next_steps: string[];
  limitations: string[];
  read_only_boundary: {
    remediation_performed: boolean;
    dns_configuration_changed: boolean;
    network_configuration_changed: boolean;
    firewall_configuration_changed: boolean;
    ad_objects_modified: boolean;
    group_membership_changed: boolean;
    ntfs_or_share_permissions_changed: boolean;
    service_control_performed: boolean;
    remote_command_executed: boolean;
    credentials_or_tokens_stored: boolean;
    user_impersonation_performed: boolean;
  };
  error?: {
    code: string;
    message: string;
  };
};

export type HistoryRecord = {
  id: number;
  created_at: string;
  module: string;
  scenario: string;
  user_principal_name: string;
  affected_service: string;
  status: string;
};

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    ...init
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getHealth() {
  return requestJson<{ status: string; product: string; module_count: number }>("/api/health");
}

export function getModules() {
  return requestJson<{ product: string; modules: Array<{ id: string; name: string }> }>("/api/modules");
}

export function runUserAccessScan(scan: ScanRequest) {
  return requestJson<ScanResponse>("/api/scan/user-access", {
    method: "POST",
    body: JSON.stringify(scan)
  });
}

export function getHistory() {
  return requestJson<{ status: string; records: HistoryRecord[] }>("/api/history");
}

export function jsonReportUrl(historyId: number) {
  return `/api/history/${historyId}/report.json`;
}

export function htmlReportUrl(historyId: number) {
  return `/api/history/${historyId}/report.html`;
}


export function getGraphReadiness() {
  return requestJson<GraphReadinessResponse>("/api/readiness/graph");
}

export function getLocalReadiness() {
  return requestJson<LocalReadinessResponse>("/api/readiness/local");
}

export function getAdReadiness() {
  return requestJson<AdReadinessResponse>("/api/readiness/ad");
}

export function runDnsDiagnostic(request: DnsDiagnosticRequest) {
  return requestJson<DnsDiagnosticResponse>("/api/diagnostics/dns", {
    method: "POST",
    body: JSON.stringify(request)
  });
}


export function runAdUserAccessDiagnostic(request: AdUserAccessDiagnosticRequest) {
  return requestJson<AdUserAccessDiagnosticResponse>("/api/diagnostics/ad-user-access", {
    method: "POST",
    body: JSON.stringify(request)
  });
}

export function runFileShareAccessDiagnostic(request: FileShareAccessDiagnosticRequest) {
  return requestJson<FileShareAccessDiagnosticResponse>("/api/diagnostics/factoryops/file-share-access", {
    method: "POST",
    body: JSON.stringify(request)
  });
}
