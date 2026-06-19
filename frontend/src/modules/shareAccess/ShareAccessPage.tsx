import { useState } from "react";
import { runShareAccessDiagnostic, ShareAccessInput, StandardDiagnosticResult } from "../../api/traceApi";

type ShareAccessPageProps = {
  onResult: (result: StandardDiagnosticResult) => void;
};

export function ShareAccessPage({ onResult }: ShareAccessPageProps) {
  const [form, setForm] = useState<ShareAccessInput>({
    shareHost: "filesrv01",
    shareName: "Finance",
    userSam: "finance.noaccess",
    requiredGroup: "GG_FINANCE_SHARE_READ",
    domain: "factory.local",
    dnsServer: "10.40.10.10",
    observedAccessDenied: true
  });
  const [running, setRunning] = useState(false);

  function update<K extends keyof ShareAccessInput>(key: K, value: ShareAccessInput[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function run() {
    setRunning(true);
    try {
      const result = await runShareAccessDiagnostic(form);
      onResult(result);
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="trace-page">
      <div className="trace-page-header">
        <span className="trace-eyebrow">FactoryOps diagnostic</span>
        <h1>Share access</h1>
        <p>Diagnose whether a file-share access issue looks like DNS, SMB reachability, AD user state, missing group membership, or observed access denial.</p>
      </div>

      <section className="trace-help-card compact">
        <div>
          <span className="trace-eyebrow">Guidance</span>
          <h2>When to use this</h2>
          <p>Use this when a user reports that a share is unavailable or access is denied. TRACE collects read-only evidence and does not modify AD or file-server permissions.</p>
        </div>
        <ul>
          <li>Confirms name resolution and SMB reachability.</li>
          <li>Checks affected AD user and required group context.</li>
          <li>Separates missing evidence from confirmed findings.</li>
          <li>Produces safe next steps for tickets and escalation.</li>
        </ul>
      </section>

      <form className="trace-form" onSubmit={(event) => { event.preventDefault(); void run(); }}>
        <fieldset>
          <legend>Target share</legend>
          <label>
            <span>Share host</span>
            <input value={form.shareHost} onChange={(event) => update("shareHost", event.target.value)} />
          </label>
          <label>
            <span>Share name</span>
            <input value={form.shareName} onChange={(event) => update("shareName", event.target.value)} />
          </label>
          <label>
            <span>Domain</span>
            <input value={form.domain} onChange={(event) => update("domain", event.target.value)} />
          </label>
        </fieldset>

        <fieldset>
          <legend>Affected user</legend>
          <label>
            <span>User SAM account</span>
            <input value={form.userSam} onChange={(event) => update("userSam", event.target.value)} />
          </label>
          <label>
            <span>Required group</span>
            <input value={form.requiredGroup} onChange={(event) => update("requiredGroup", event.target.value)} />
          </label>
        </fieldset>

        <fieldset>
          <legend>Evidence context</legend>
          <label>
            <span>DNS server optional</span>
            <input value={form.dnsServer ?? ""} onChange={(event) => update("dnsServer", event.target.value)} />
          </label>
          <label>
            <span>Observed access denied</span>
            <select value={String(form.observedAccessDenied)} onChange={(event) => update("observedAccessDenied", event.target.value === "true")}>
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          </label>
        </fieldset>

        <div className="trace-check-row" aria-label="What TRACE checks">
          <span>DNS resolution</span>
          <span>SMB reachability</span>
          <span>AD user state</span>
          <span>Group membership</span>
          <span>Access denial evidence</span>
        </div>

        <div className="trace-form-footer">
          <p>TRACE runs this diagnostic in read-only mode. It does not change AD groups, passwords, share permissions, or NTFS ACLs.</p>
          <button className="trace-primary-button" type="submit" disabled={running}>{running ? "Running..." : "Run diagnostic"}</button>
        </div>
      </form>
    </section>
  );
}
