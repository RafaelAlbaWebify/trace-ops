import { generatedEndpoints } from "./generatedEndpoints";

export type DiagnosticStatus = "success" | "ok" | "warning" | "finding" | "error" | "not_run" | string;

export type StandardDiagnosticResult = {
  title: string;
  status?: DiagnosticStatus;
  findingId?: string | null;
  severity?: string | null;
  confidence?: string | null;
  summary?: string | null;
  evidenceUsed?: string[];
  evidenceMissing?: string[];
  safeNextSteps?: string[];
  doNotChangeYet?: string[];
  limitations?: string[];
  readOnlyKept?: boolean;
  ticketSummary?: string | null;
  raw?: unknown;
};

export type ShareAccessInput = {
  shareHost: string;
  shareName: string;
  userSam: string;
  requiredGroup: string;
  domain: string;
  dnsServer?: string;
  observedAccessDenied: boolean;
};

export type AccessEvidenceInput = {
  sourceType: "generic_access_log_text" | "entra_signin_csv" | "resource_assignment_json";
  affectedUser?: string;
  affectedService?: string;
  content: string;
  notes?: string;
};

type EndpointMap = Record<string, string[]>;

declare global {
  interface Window {
    __TRACE_ENDPOINTS__?: EndpointMap;
  }
}

const fallbackEndpoints: EndpointMap = {
  health: ["/api/health", "/health", "/api/status"],
  history: ["/api/logs/history", "/api/history", "/api/scans", "/api/reports/history", "/api/diagnostics/history"],
  shareAccess: [
    "/api/factoryops/file-share-access/diagnose",
    "/api/factoryops/file-share-access-diagnostic",
    "/api/factoryops/file-share-access",
    "/api/diagnostics/factoryops/file-share-access",
    "/api/diagnostics/factoryops-file-share-access",
    "/api/diagnostics/factoryops/file-share",
    "/api/diagnostics/file-share-access",
    "/api/diagnostics/file-share",
    "/api/file-share-access",
    "/factoryops/file-share-access/diagnose"
  ],
  accessEvidence: ["/api/logs/analyze"],
  dns: ["/api/diagnostics/dns", "/api/dns-diagnostic", "/api/dns/lookup", "/api/dns"],
  adUser: ["/api/diagnostics/ad-user-access", "/api/ad-user-access", "/api/diagnostics/ad-user"],
  readiness: ["/api/readiness", "/api/local-infra-readiness", "/api/diagnostics/readiness"]
};

function endpointsFor(key: string): string[] {
  const generated = generatedEndpoints[key] ?? [];
  const discovered = window.__TRACE_ENDPOINTS__?.[key] ?? [];
  const fallback = fallbackEndpoints[key] ?? [];
  return Array.from(new Set([...generated, ...discovered, ...fallback]));
}

async function parseResponseJson(response: any): Promise<unknown> {
  if (response && typeof response.text === "function") {
    const text = await response.text();
    if (!text) return {};
    return JSON.parse(text);
  }

  if (response && typeof response.json === "function") {
    return await response.json();
  }

  if (response && typeof response === "object" && "data" in response) {
    return response.data;
  }

  if (response && typeof response === "object") {
    return response;
  }

  return {};
}

async function tryJson(url: string, init?: RequestInit): Promise<unknown> {
  const response: any = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });

  const ok = response?.ok ?? (typeof response?.status === "number" ? response.status >= 200 && response.status < 300 : true);
  if (!ok) {
    throw new Error(`${response?.status ?? "unknown"} ${response?.statusText ?? "request failed"}`);
  }

  return await parseResponseJson(response);
}

async function tryEndpoints(key: string, init?: RequestInit): Promise<{ data: unknown; endpoint: string }> {
  const errors: string[] = [];
  for (const endpoint of endpointsFor(key)) {
    try {
      const data = await tryJson(endpoint, init);
      return { data, endpoint };
    } catch (error) {
      errors.push(`${endpoint}: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  throw new Error(errors.join(" | "));
}

function asStringArray(value: unknown): string[] {
  if (!value) return [];
  if (Array.isArray(value)) return value.map((item) => typeof item === "string" ? item : JSON.stringify(item));
  if (typeof value === "string") return value ? [value] : [];
  return [JSON.stringify(value)];
}

function pick(obj: Record<string, unknown>, names: string[]): unknown {
  for (const name of names) {
    if (obj[name] !== undefined && obj[name] !== null) return obj[name];
  }
  return undefined;
}

export function normalizeResult(title: string, raw: unknown): StandardDiagnosticResult {
  const obj = (raw && typeof raw === "object" ? raw as Record<string, unknown> : {}) as Record<string, unknown>;
  const primary = obj.primary_finding && typeof obj.primary_finding === "object" ? obj.primary_finding as Record<string, unknown> : {};
  const status = String(pick(obj, ["status", "result_status", "overall_status"]) ?? "ok");
  const findingId = pick(obj, ["finding_id", "findingId", "finding", "finding_code"]) ?? pick(primary, ["finding_id", "rule_id"]);
  const summary = pick(obj, ["summary", "message", "conclusion", "diagnosis"]) ?? pick(primary, ["likely_cause", "summary"]);
  const readOnlyRaw = pick(obj, ["read_only_boundary", "readOnlyKept", "read_only_kept", "read_only"]);
  const readOnlyKept = typeof readOnlyRaw === "boolean"
    ? readOnlyRaw
    : String(readOnlyRaw ?? "true").toLowerCase().includes("kept") || String(readOnlyRaw ?? "true").toLowerCase() === "true";

  return {
    title,
    status,
    findingId: findingId ? String(findingId) : null,
    severity: pick(obj, ["severity"]) ? String(pick(obj, ["severity"])) : pick(primary, ["severity"]) ? String(pick(primary, ["severity"])) : null,
    confidence: pick(obj, ["confidence"]) ? String(pick(obj, ["confidence"])) : pick(primary, ["confidence"]) ? String(pick(primary, ["confidence"])) : null,
    summary: summary ? String(summary) : null,
    evidenceUsed: asStringArray(pick(obj, ["evidence_used", "evidenceUsed", "evidence"]) ?? pick(primary, ["evidence_used", "evidence"])),
    evidenceMissing: asStringArray(pick(obj, ["evidence_missing", "evidenceMissing", "missing_evidence"]) ?? pick(primary, ["evidence_missing"])),
    safeNextSteps: asStringArray(pick(obj, ["safe_next_steps", "safeNextSteps", "next_steps"]) ?? pick(primary, ["safe_next_steps", "next_steps"])),
    doNotChangeYet: asStringArray(pick(obj, ["what_not_to_change_yet", "do_not_change_yet", "doNotChangeYet", "do_not_change"]) ?? pick(primary, ["what_not_to_change_yet"])),
    limitations: asStringArray(pick(obj, ["limitations", "limits"]) ?? pick(primary, ["limitations"])),
    readOnlyKept,
    ticketSummary: pick(obj, ["ticket_summary", "ticketSummary", "report_markdown"]) ? String(pick(obj, ["ticket_summary", "ticketSummary", "report_markdown"])) : null,
    raw
  };
}

export async function getBackendHealth(): Promise<{ ok: boolean; raw?: unknown; endpoint?: string }> {
  try {
    const { data, endpoint } = await tryEndpoints("health");
    return { ok: true, raw: data, endpoint };
  } catch {
    return { ok: false };
  }
}

export async function getHistory(): Promise<unknown[]> {
  try {
    const { data } = await tryEndpoints("history");
    if (Array.isArray(data)) return data;
    if (data && typeof data === "object") {
      const obj = data as Record<string, unknown>;
      const items = obj.items ?? obj.history ?? obj.runs ?? obj.scans;
      if (Array.isArray(items)) return items;
    }
    return [];
  } catch {
    return [];
  }
}

export async function runAccessEvidenceAnalysis(input: AccessEvidenceInput): Promise<StandardDiagnosticResult> {
  const payload = {
    source_type: input.sourceType,
    affected_user: input.affectedUser || undefined,
    affected_service: input.affectedService || undefined,
    content: input.content,
    notes: input.notes || undefined
  };

  try {
    const { data } = await tryEndpoints("accessEvidence", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    return normalizeResult("Access evidence analyzer", data);
  } catch (error) {
    return {
      title: "Access evidence analyzer",
      status: "error",
      findingId: "TRACE_UI_ACCESS_EVIDENCE_ENDPOINT_NOT_REACHED",
      summary: "The UI could not reach the access evidence analyzer endpoint. Backend may not be running, or the API route may have changed.",
      evidenceUsed: ["The UI tried the configured access evidence endpoint."],
      evidenceMissing: ["A successful backend response was not received."],
      safeNextSteps: ["Confirm the backend is running on port 8000.", "Confirm /api/logs/analyze is available."],
      doNotChangeYet: ["Do not make access changes based only on this UI connection error."],
      limitations: [error instanceof Error ? error.message : String(error)],
      readOnlyKept: true,
      raw: { error: error instanceof Error ? error.message : String(error), payload, generatedEndpoints }
    };
  }
}

export async function runShareAccessDiagnostic(input: ShareAccessInput): Promise<StandardDiagnosticResult> {
  const payload = {
    share_host: input.shareHost,
    shareHost: input.shareHost,
    share_name: input.shareName,
    shareName: input.shareName,
    user_sam: input.userSam,
    userSam: input.userSam,
    user: input.userSam,
    required_group: input.requiredGroup,
    requiredGroup: input.requiredGroup,
    domain: input.domain,
    dns_server: input.dnsServer || undefined,
    dnsServer: input.dnsServer || undefined,
    observed_access_denied: input.observedAccessDenied,
    observedAccessDenied: input.observedAccessDenied
  };

  try {
    const { data } = await tryEndpoints("shareAccess", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    return normalizeResult("FactoryOps share access diagnostic", data);
  } catch (error) {
    return {
      title: "FactoryOps share access diagnostic",
      status: "error",
      findingId: "TRACE_UI_API_ENDPOINT_NOT_REACHED",
      summary: "The UI could not reach a compatible share-access diagnostic endpoint. Backend may not be running, or the API route may have changed.",
      evidenceUsed: ["The UI tried discovered and fallback read-only API endpoints."],
      evidenceMissing: ["A successful backend response was not received."],
      safeNextSteps: ["Confirm the backend is running on port 8000.", "Review generated endpoint candidates in the report.", "Do not change AD or file-server permissions based only on this UI error."],
      doNotChangeYet: ["Do not modify AD groups or share permissions until the diagnostic endpoint is confirmed."],
      limitations: [error instanceof Error ? error.message : String(error)],
      readOnlyKept: true,
      raw: { error: error instanceof Error ? error.message : String(error), payload, generatedEndpoints }
    };
  }
}

export function buildTicketSummary(result: StandardDiagnosticResult): string {
  if (result.ticketSummary) return result.ticketSummary;
  const status = result.status ?? "unknown";
  const finding = result.findingId ?? "none";
  const summary = result.summary ?? "No summary was provided.";
  const readOnly = result.readOnlyKept === false ? "Read-only boundary requires review." : "Read-only boundary was kept.";
  return `TRACE diagnostic status: ${status}. Finding: ${finding}. ${summary} ${readOnly}`;
}
