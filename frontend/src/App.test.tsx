import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

const apiMocks = vi.hoisted(() => ({
  getHealth: vi.fn(),
  getModules: vi.fn(),
  getHistory: vi.fn(),
  runUserAccessScan: vi.fn()
}));

vi.mock("./api", () => ({
  AFFECTED_SERVICES: [
    "Microsoft 365 general access",
    "Exchange Online / Outlook",
    "SharePoint Online / OneDrive",
    "Microsoft Teams"
  ],
  SAMPLE_SCENARIOS: [
    "account-disabled",
    "missing-license",
    "ca-details-missing",
    "ca-device-noncompliant",
    "mfa-requirement-not-satisfied",
    "no-recent-signin-evidence",
    "successful-access-baseline"
  ],
  getHealth: apiMocks.getHealth,
  getModules: apiMocks.getModules,
  getHistory: apiMocks.getHistory,
  runUserAccessScan: apiMocks.runUserAccessScan,
  jsonReportUrl: (historyId: number) => `/api/history/${historyId}/report.json`,
  htmlReportUrl: (historyId: number) => `/api/history/${historyId}/report.html`
}));

const historyResponse = {
  status: "ok",
  records: [
    {
      id: 42,
      created_at: "2026-05-25T10:00:00Z",
      module: "m365-access-path-analyzer",
      scenario: "ca-device-noncompliant",
      user_principal_name: "jane.doe@example.com",
      affected_service: "Microsoft Teams",
      status: "success"
    }
  ]
};

const scanResponse = {
  status: "success",
  history_id: 42,
  result: {
    scenario_id: "ca-device-noncompliant",
    module: "m365-access-path-analyzer",
    input: {
      user_principal_name: "jane.doe@example.com",
      affected_service: "Microsoft Teams",
      scenario: "ca-device-noncompliant"
    }
  },
  analysis: {
    status: "finding",
    primary_finding: {
      rule_id: "CA_DEVICE_COMPLIANCE_BLOCK",
      title: "Conditional Access requires a compliant device",
      severity: "high",
      confidence: "high",
      likely_cause: "Conditional Access requires a compliant device, but the sign-in device is non-compliant.",
      evidence: ["Recent Teams sign-in failed.", "Device compliance state is nonCompliant."],
      next_steps: ["Check Intune compliance policy failure for the device."],
      what_not_to_change_yet: ["Do not disable Conditional Access globally."],
      limitations: ["Synthetic sample data only."]
    },
    findings: [],
    summary: "A compliant device requirement appears to be blocking access.",
    confidence: "high",
    limitations: ["Synthetic sample data only."]
  }
};

function renderApp() {
  apiMocks.getHealth.mockResolvedValue({ status: "ok", product: "TRACE", module_count: 1 });
  apiMocks.getModules.mockResolvedValue({
    product: "TRACE",
    modules: [{ id: "m365-access-path-analyzer", name: "M365 Access Path Analyzer" }]
  });
  apiMocks.getHistory.mockResolvedValue(historyResponse);
  apiMocks.runUserAccessScan.mockResolvedValue(scanResponse);

  return render(<App />);
}

describe("TRACE frontend MVP", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders TRACE header and product text", async () => {
    renderApp();

    expect(screen.getAllByText("TRACE").length).toBeGreaterThan(0);
    expect(screen.getByText("Troubleshooting Reports Across Cloud & Endpoints")).toBeInTheDocument();
    expect(await screen.findByText("Backend ok")).toBeInTheDocument();
  });

  it("shows the sample-mode limitation", () => {
    renderApp();

    expect(screen.getByText("Sample mode only")).toBeInTheDocument();
    expect(
      screen.getByText("No tenant connection, Graph permissions, or remediation actions are available in this MVP.")
    ).toBeInTheDocument();
  });

  it("renders the scan form controls", () => {
    renderApp();

    expect(screen.getByLabelText("User principal name")).toBeInTheDocument();
    expect(screen.getByLabelText("Affected service")).toBeInTheDocument();
    expect(screen.getByLabelText("Sample scenario")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "mfa-requirement-not-satisfied" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run scan" })).toBeInTheDocument();
  });

  it("renders analyzer results and limitations after a successful scan", async () => {
    const user = userEvent.setup();
    renderApp();

    await user.click(screen.getByRole("button", { name: "Run scan" }));

    expect(await screen.findByText("CA_DEVICE_COMPLIANCE_BLOCK")).toBeInTheDocument();
    expect(screen.getByText("Conditional Access requires a compliant device, but the sign-in device is non-compliant.")).toBeInTheDocument();
    expect(screen.getByText("Recent Teams sign-in failed.")).toBeInTheDocument();
    expect(screen.getByText("Check Intune compliance policy failure for the device.")).toBeInTheDocument();
    expect(screen.getByText("Do not disable Conditional Access globally.")).toBeInTheDocument();
    expect(screen.getByText("Synthetic sample data only.")).toBeInTheDocument();

    await waitFor(() => {
      expect(apiMocks.runUserAccessScan).toHaveBeenCalledWith({
        user_principal_name: "jane.doe@example.com",
        affected_service: "Microsoft Teams",
        scenario: "ca-device-noncompliant"
      });
    });
  });

  it("renders recent history with JSON and HTML report links", async () => {
    renderApp();

    expect(await screen.findByText("Recent History")).toBeInTheDocument();
    expect(screen.getByText("jane.doe@example.com")).toBeInTheDocument();

    const jsonLink = screen.getByRole("link", { name: "JSON" });
    const htmlLink = screen.getByRole("link", { name: "HTML" });

    expect(jsonLink).toHaveAttribute("href", "/api/history/42/report.json");
    expect(htmlLink).toHaveAttribute("href", "/api/history/42/report.html");
  });
});
