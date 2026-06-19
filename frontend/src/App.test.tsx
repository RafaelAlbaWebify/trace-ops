import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

const shareAccessFinding = {
  status: "finding",
  finding_id: "FACTORYOPS_FILE_SHARE_USER_MISSING_REQUIRED_GROUP",
  severity: "medium",
  confidence: "high",
  summary: "The affected user is not proven to be a member of the required finance share group.",
  evidence_used: ["DNS resolution was attempted.", "SMB reachability was checked.", "Group membership evidence was evaluated."],
  evidence_missing: ["Direct end-user interactive sign-in evidence was not collected."],
  safe_next_steps: ["Validate group membership with the service owner.", "Attach TRACE evidence to the ticket."],
  do_not_change_yet: ["Do not modify AD groups until ownership is confirmed."],
  limitations: ["Lab diagnostic evidence only."],
  read_only_boundary: "kept"
};

function jsonResponse(data: unknown) {
  return {
    ok: true,
    status: 200,
    statusText: "OK",
    text: async () => JSON.stringify(data),
    json: async () => data
  } as Response;
}

function installFetchMock() {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.includes("health") || url.endsWith("/status")) {
      return jsonResponse({ status: "ok" });
    }
    if (url.includes("/api/scan/user-access") || url.includes("history") || url.includes("scans")) {
      return jsonResponse([{ id: 1, user: "jane.doe@example.com", service: "SharePoint Online", status: "ok" }]);
    }
    if (init?.method === "POST") {
      return jsonResponse(shareAccessFinding);
    }
    return jsonResponse({});
  });

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

async function openNavGroup(name: RegExp) {
  const nav = screen.getByRole("navigation", { name: /diagnostic navigation/i });
  const summary = within(nav).getByText(name, { selector: "summary" });
  const details = summary.closest("details");
  if (details && !details.hasAttribute("open")) {
    await userEvent.click(summary);
  }
}

describe("TRACE rebuilt operator shell", () => {
  beforeEach(() => {
    installFetchMock();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("renders the professional shell landmarks", async () => {
    render(<App />);

    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: /diagnostic navigation/i })).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: /diagnostic result panel/i })).toBeInTheDocument();
    expect(await screen.findByText(/Backend ok|Backend unknown/i)).toBeInTheDocument();
  });

  it("opens the share access workflow by default", () => {
    render(<App />);
    const main = screen.getByRole("main");

    expect(within(main).getByRole("heading", { name: /Share access/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Share host/i)).toHaveValue("filesrv01");
    expect(screen.getByLabelText(/User SAM account/i)).toHaveValue("finance.noaccess");
    expect(screen.getByRole("button", { name: /Run diagnostic/i })).toBeInTheDocument();
    expect(screen.getByText(/DNS resolution/i)).toBeInTheDocument();
  });

  it("runs the share access diagnostic and renders a finding", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: /Run diagnostic/i }));

    const findings = await screen.findAllByText(/FACTORYOPS_FILE_SHARE_USER_MISSING_REQUIRED_GROUP/i);
    expect(findings.length).toBeGreaterThan(0);

    const summaryMatches = await screen.findAllByText(/The affected user is not proven/i);
    expect(summaryMatches.length).toBeGreaterThan(0);

    expect(screen.getByText(/Copy/i)).toBeInTheDocument();
    expect(screen.getByText(/Raw JSON/i)).toBeInTheDocument();
  });

  it("shows overview guidance and module maturity labels", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: /Overview/i }));

    const main = screen.getByRole("main");
    expect(within(main).getByRole("heading", { name: /Operator dashboard/i })).toBeInTheDocument();
    expect(within(main).getByRole("heading", { name: /How to use TRACE/i })).toBeInTheDocument();
    expect(screen.getAllByText(/Validated lab diagnostic/i).length).toBeGreaterThan(0);
  });

  it("shows diagnostic history from the backend", async () => {
    const user = userEvent.setup();
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Backend ok|Backend unknown/i)).toBeInTheDocument();
    });

    await openNavGroup(/Evidence/i);
    await user.click(screen.getByRole("button", { name: /History/i }));

    const main = screen.getByRole("main");
    expect(within(main).getByRole("heading", { name: /Diagnostic run history/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(within(main).getByText(/jane.doe@example.com/i)).toBeInTheDocument();
    });
  });
});

