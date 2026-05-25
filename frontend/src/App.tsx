import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  AFFECTED_SERVICES,
  HistoryRecord,
  SAMPLE_SCENARIOS,
  ScanResponse,
  getHealth,
  getHistory,
  getModules,
  htmlReportUrl,
  jsonReportUrl,
  runUserAccessScan
} from "./api";

const defaultUpn = "jane.doe@example.com";

function DetailList({ title, items }: { title: string; items?: string[] }) {
  return (
    <section className="detail-block">
      <h3>{title}</h3>
      {items && items.length > 0 ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="muted">None recorded.</p>
      )}
    </section>
  );
}

function badgeTone(value?: string | null) {
  const normalized = value?.toLowerCase() ?? "";

  if (["ok", "success", "healthy", "low"].some((token) => normalized.includes(token))) {
    return "success";
  }

  if (["critical", "high", "error", "failed"].some((token) => normalized.includes(token))) {
    return "danger";
  }

  if (["medium", "warning", "unknown"].some((token) => normalized.includes(token))) {
    return "warning";
  }

  return "neutral";
}

function App() {
  const [userPrincipalName, setUserPrincipalName] = useState(defaultUpn);
  const [affectedService, setAffectedService] = useState<string>(AFFECTED_SERVICES[3]);
  const [scenario, setScenario] = useState<string>(SAMPLE_SCENARIOS[3]);
  const [scan, setScan] = useState<ScanResponse | null>(null);
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [health, setHealth] = useState<string>("checking");
  const [moduleName, setModuleName] = useState("M365 Access Path Analyzer");
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refreshHistory() {
    const historyResponse = await getHistory();
    setHistory(historyResponse.records);
  }

  useEffect(() => {
    async function loadInitialData() {
      try {
        const [healthResponse, modulesResponse] = await Promise.all([getHealth(), getModules()]);
        setHealth(healthResponse.status);
        setModuleName(modulesResponse.modules[0]?.name ?? "M365 Access Path Analyzer");
        await refreshHistory();
      } catch (loadError) {
        setHealth("offline");
        setError(loadError instanceof Error ? loadError.message : "Backend is unavailable.");
      }
    }

    loadInitialData();
  }, []);

  async function submitScan(event: FormEvent) {
    event.preventDefault();
    setIsScanning(true);
    setError(null);

    try {
      const response = await runUserAccessScan({
        user_principal_name: userPrincipalName,
        affected_service: affectedService,
        scenario
      });
      setScan(response);
      await refreshHistory();
    } catch (scanError) {
      setError(scanError instanceof Error ? scanError.message : "Scan failed.");
    } finally {
      setIsScanning(false);
    }
  }

  const primaryFinding = scan?.analysis?.primary_finding ?? null;
  const reportLinks = useMemo(() => {
    if (!scan?.history_id) {
      return null;
    }
    return {
      json: jsonReportUrl(scan.history_id),
      html: htmlReportUrl(scan.history_id)
    };
  }, [scan?.history_id]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <span className="product-mark">TRACE</span>
          <h1>TRACE</h1>
          <p>Troubleshooting Reports Across Cloud &amp; Endpoints</p>
        </div>
        <div className={`status-pill ${health === "ok" ? "ok" : "warn"}`}>Backend {health}</div>
      </header>

      <section className="module-strip">
        <div>
          <span className="eyebrow">Sample mode only</span>
          <h2>{moduleName}</h2>
        </div>
        <p>No tenant connection, Graph permissions, or remediation actions are available in this MVP.</p>
      </section>

      {error && <div className="alert">{error}</div>}

      <section className="layout">
        <form className="panel scan-form" onSubmit={submitScan}>
          <h2>Run Sample Scan</h2>
          <label>
            Module
            <select value="m365-access-path-analyzer" disabled>
              <option value="m365-access-path-analyzer">{moduleName}</option>
            </select>
          </label>
          <label>
            User principal name
            <input
              value={userPrincipalName}
              onChange={(event) => setUserPrincipalName(event.target.value)}
              type="email"
              required
            />
          </label>
          <label>
            Affected service
            <select value={affectedService} onChange={(event) => setAffectedService(event.target.value)} required>
              {AFFECTED_SERVICES.map((service) => (
                <option key={service} value={service}>
                  {service}
                </option>
              ))}
            </select>
          </label>
          <label>
            Sample scenario
            <select value={scenario} onChange={(event) => setScenario(event.target.value)} required>
              {SAMPLE_SCENARIOS.map((sampleScenario) => (
                <option key={sampleScenario} value={sampleScenario}>
                  {sampleScenario}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" disabled={isScanning}>
            {isScanning ? "Running..." : "Run scan"}
          </button>
        </form>

        <section className="panel results-panel">
          <h2>Results</h2>
          {!scan && <p className="muted">Run a sample scan to see analyzer output.</p>}
          {scan && (
            <div className="result-stack">
              <div className="summary-grid">
                <div>
                  <span>Scan status</span>
                  <strong className={`metric-badge ${badgeTone(scan.status)}`}>{scan.status}</strong>
                </div>
                <div>
                  <span>History ID</span>
                  <strong className="metric-badge neutral">{scan.history_id ?? "Not saved"}</strong>
                </div>
                <div>
                  <span>Severity</span>
                  <strong className={`metric-badge ${badgeTone(primaryFinding?.severity)}`}>
                    {primaryFinding?.severity ?? "None"}
                  </strong>
                </div>
                <div>
                  <span>Confidence</span>
                  <strong className={`metric-badge ${badgeTone(primaryFinding?.confidence ?? scan.analysis?.confidence)}`}>
                    {primaryFinding?.confidence ?? scan.analysis?.confidence ?? "Unknown"}
                  </strong>
                </div>
              </div>

              {scan.error && (
                <div className="alert">
                  {scan.error.code}: {scan.error.message}
                </div>
              )}

              {scan.analysis && (
                <>
                  <section className="finding-card">
                    <span className="eyebrow">Primary finding</span>
                    <h3>{primaryFinding?.rule_id ?? "No blocking evidence"}</h3>
                    <p>{primaryFinding?.likely_cause ?? scan.analysis.summary}</p>
                  </section>
                  <DetailList title="Evidence" items={primaryFinding?.evidence} />
                  <DetailList title="Next steps" items={primaryFinding?.next_steps} />
                  <DetailList title="What not to change yet" items={primaryFinding?.what_not_to_change_yet} />
                  <DetailList title="Limitations" items={primaryFinding?.limitations ?? scan.analysis.limitations} />
                </>
              )}

              {reportLinks && (
                <div className="report-links">
                  <a href={reportLinks.json} target="_blank" rel="noreferrer">
                    JSON report
                  </a>
                  <a href={reportLinks.html} target="_blank" rel="noreferrer">
                    HTML report
                  </a>
                </div>
              )}
            </div>
          )}
        </section>
      </section>

      <section className="panel history-panel">
        <div className="section-heading">
          <h2>Recent History</h2>
          <button type="button" className="secondary" onClick={refreshHistory}>
            Refresh
          </button>
        </div>
        {history.length === 0 ? (
          <p className="muted">No scan history yet.</p>
        ) : (
          <div className="history-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>User</th>
                  <th>Service</th>
                  <th>Scenario</th>
                  <th>Status</th>
                  <th>Reports</th>
                </tr>
              </thead>
              <tbody>
                {history.map((record) => (
                  <tr key={record.id}>
                    <td>{record.id}</td>
                    <td>{record.user_principal_name}</td>
                    <td>{record.affected_service}</td>
                    <td>{record.scenario}</td>
                    <td>
                      <span className={`table-status ${badgeTone(record.status)}`}>{record.status}</span>
                    </td>
                    <td className="table-links">
                      <a href={jsonReportUrl(record.id)} target="_blank" rel="noreferrer">
                        JSON
                      </a>
                      <a href={htmlReportUrl(record.id)} target="_blank" rel="noreferrer">
                        HTML
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}

export default App;
