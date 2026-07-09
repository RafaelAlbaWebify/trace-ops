import { BackendHealth } from "../modules/registry";

type TopBarProps = {
  health: BackendHealth;
};

export function TopBar({ health }: TopBarProps) {
  return (
    <header className="trace-topbar" role="banner">
      <div className="trace-brand" aria-label="TRACE home">
        <span className="trace-brand-mark" aria-hidden="true">◆</span>
        <div>
          <strong>TRACE</strong>
          <span>Troubleshooting Reports Across Cloud &amp; Endpoints</span>
        </div>
      </div>
      <div className="trace-status-pills" aria-label="TRACE runtime status">
        <span className={`trace-pill ${health.ok ? "success" : "warning"}`}>
          {health.ok ? "Backend ok" : "Backend unknown"}
        </span>
        <span className="trace-pill success">Read-only</span>
      </div>
    </header>
  );
}
