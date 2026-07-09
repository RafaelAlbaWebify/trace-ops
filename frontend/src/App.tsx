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

  return (
    <AppShell health={health} activeId={activeId} onSelect={setActiveId} result={result}>
      {activeId === "overview" && <OverviewPage health={health} historyCount={history.length} onSelect={setActiveId} />}
      {activeId === "share-access" && <ShareAccessPage onResult={(next) => { setResult(next); refreshHistory(); }} />}
      {activeId === "access-evidence" && <AccessEvidencePage onResult={(next) => { setResult(next); refreshHistory(); }} />}
      {activeId === "dns-lookup" && <DnsLookupPage onResult={(next) => { setResult(next); refreshHistory(); }} />}
      {activeId === "ad-user-access" && <AdUserAccessPage onResult={(next) => { setResult(next); refreshHistory(); }} />}
      {(activeId === "ad-readiness" || activeId === "local-readiness" || activeId === "cloud-readiness" || activeId === "m365-sample") && activeModule && (
        <ReadinessPage module={activeModule} onResult={(next) => { setResult(next); refreshHistory(); }} />
      )}
      {activeId === "history" && <HistoryPage history={history} refresh={refreshHistory} />}
    </AppShell>
  );
}

export default App;
