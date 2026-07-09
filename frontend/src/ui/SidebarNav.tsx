import { ModuleDefinition, moduleGroups } from "../modules/registry";

type SidebarNavProps = {
  activeId: string;
  onSelect: (id: string) => void;
};

export function SidebarNav({ activeId, onSelect }: SidebarNavProps) {
  return (
    <nav className="trace-sidebar" aria-label="diagnostic navigation">
      <button
        className={`trace-nav-item ${activeId === "overview" ? "active" : ""}`}
        data-module-id="overview"
        data-nav-label="Overview"
        aria-label="Overview"
        onClick={() => onSelect("overview")}
      >
        <span>Overview</span>
      </button>

      {moduleGroups.map((group) => (
        <details key={group.name} open={group.defaultOpen}>
          <summary>{group.name}</summary>
          <div className="trace-nav-group">
            {group.modules.map((module: ModuleDefinition) => (
              <button
                key={module.id}
                className={`trace-nav-item ${activeId === module.id ? "active" : ""}`}
                data-module-id={module.id}
                data-nav-label={module.label}
                aria-label={module.label}
                onClick={() => onSelect(module.id)}
              >
                <span>{module.label}</span>
                <small aria-hidden="true">{module.maturity}</small>
              </button>
            ))}
          </div>
        </details>
      ))}
    </nav>
  );
}
