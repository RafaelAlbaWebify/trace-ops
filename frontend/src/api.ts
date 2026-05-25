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
