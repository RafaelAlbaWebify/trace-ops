import { ReactNode } from "react";
import { StandardDiagnosticResult } from "../api/traceApi";
import { BackendHealth } from "../modules/registry";
import { ResultPanel } from "./ResultPanel";
import { SidebarNav } from "./SidebarNav";
import { TopBar } from "./TopBar";

type AppShellProps = {
  activeId: string;
  onSelect: (id: string) => void;
  health: BackendHealth;
  result: StandardDiagnosticResult;
  children: ReactNode;
};

export function AppShell({ activeId, onSelect, health, result, children }: AppShellProps) {
  return (
    <div className="trace-shell">
      <TopBar health={health} />
      <div className="trace-layout">
        <SidebarNav activeId={activeId} onSelect={onSelect} />
        <main className="trace-workspace" role="main">
          {children}
        </main>
        <ResultPanel result={result} />
      </div>
    </div>
  );
}
