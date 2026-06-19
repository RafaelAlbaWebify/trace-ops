import { BackendHealth } from "../modules/registry";

type TopBarProps = {
  health: BackendHealth;
};

export function TopBar({ health }: TopBarProps) {
  return (
    <header className="trace-topbar" role="banner">
      <div className="trace-brand">
        <span>TRACE</span>
        <strong>TRACE</strong>
      </div>
      <div className="trace-status-pills" aria-label="TRACE runtime status">
        <span className={`trace-pill ${health.ok ? "success" : "warning"}`}>
          {health.ok ? "Backend ok" : "Backend unknown"}
        </span>
        <span className="trace-pill success">Read-only</span>
        <span className="trace-pill neutral">FactoryOps Lab</span>
      </div>
    </header>
  );
}
