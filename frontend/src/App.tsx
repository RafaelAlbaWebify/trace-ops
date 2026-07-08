import { useEffect, useMemo, useState } from "react";
import "./styles/trace-shell.css";
window.__TRACE_ENDPOINTS__ = {};

import { getBackendHealth, getHistory, StandardDiagnosticResult } from "./api/traceApi";
import { AppShell } from "./ui/AppShell";
import { BackendHealth, findModule } from "./modules/registry";
import { OverviewPage } from "./modules/overview/OverviewPage";
import { ShareAccessPage } from "./modules/shareAccess/ShareAccessPage";
import { DnsLookupPage } from "./modules/dns/DnsLookupPage";
import { AdUserAccessPage } from "./modules/identity/AdUserAccessPage";
import { ReadinessPage } from "./modules/readiness/ReadinessPage";
import { HistoryPage } from "./modules/history/HistoryPage";
import { AccessEvidencePage } from "./modules/accessEvidence/AccessEvidencePage";

const initialResult: StandardDiagnosticResult = {
  title: "Diagnostic result",
  status: "not_run",
  summary: null,
  evidenceUsed: [],
  evidenceMissing: [],
  safeNextSteps: [],
  doNotChangeYet: [],
  limitations: [],
  readOnlyKept: true,
  raw: {}
};

function App() {
  const [activeId, setActiveId] = useState("access-evidence");
  const [health, setHealth] = useState<BackendHealth>({ ok: false });
  const [history, setHistory] = useState<unknown[]>([]);
  const [result, setResult] = useState<StandardDiagnosticResult>(initialResult);

  function refreshHistory() {
    void getHistory().then(setHistory);
  }

  useEffect(() => {
    void getBackendHealth().then((value) => setHealth({ ok: value.ok, endpoint: value.endpoint }));
    refreshHistory();
  }, []);

  const activeModule = useMemo(() => findModule(activeId), [activeId]);

  function handleResult(nextResult: StandardDiagnosticResult) {
    setResult(nextResult);
    refreshHistory();
  }

  function select(id: string) {
    setActiveId(id);
    const module = findModule(id);
    if (id === "history") {
      refreshHistory();
      setResult({
        title: "Diagnostic run history",
        status: "ok",
        findingId: null,
        summary: "Review previous diagnostic runs and report links.",
        evidenceUsed: [],
        evidenceMissing: [],
        safeNextSteps: [],
        doNotChangeYet: [],
        limitations: [],
        readOnlyKept: true,
        raw: { historyCount: history.length }
      });
    } else if (module) {
      setResult({ ...initialResult, title: module.label });
    } else {
      setResult(initialResult);
    }
  }

  function renderPage() {
    switch (activeId) {
      case "overview":
        return <OverviewPage health={health} historyCount={history.length} onSelect={select} />;
      case "share-access":
        return <ShareAccessPage onResult={handleResult} />;
      case "access-evidence":
        return <AccessEvidencePage onResult={handleResult} />;
      case "dns-lookup":
        return <DnsLookupPage onResult={handleResult} />;
      case "ad-user-access":
        return <AdUserAccessPage type="access" onResult={handleResult} />;
      case "ad-readiness":
        return <AdUserAccessPage type="readiness" onResult={handleResult} />;
      case "local-readiness":
        return <ReadinessPage title="Local readiness" group="Endpoint" onResult={handleResult} />;
      case "cloud-readiness":
        return <ReadinessPage title="Cloud readiness" group="Cloud / M365" onResult={handleResult} />;
      case "m365-sample":
        return <ReadinessPage title="M365 sample" group="Cloud / M365" onResult={handleResult} />;
      case "history":
        return <HistoryPage history={history} />;
      default:
        return <AccessEvidencePage onResult={handleResult} />;
    }
  }

  return (
    <AppShell activeId={activeId} onSelect={select} health={health} result={result}>
      {renderPage()}
      {activeModule && <span className="trace-screen-reader-only">Current module: {activeModule.label}</span>}
    </AppShell>
  );
}

export default App;
