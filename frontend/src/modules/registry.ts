export type ModuleMaturity = "Validated lab diagnostic" | "Readiness check" | "Sample" | "Evidence";

export type ModuleDefinition = {
  id: string;
  group: string;
  label: string;
  maturity: ModuleMaturity;
  description: string;
};

export type BackendHealth = {
  ok: boolean;
  endpoint?: string;
};

export const modules: ModuleDefinition[] = [
  {
    id: "share-access",
    group: "FactoryOps",
    label: "Share access",
    maturity: "Validated lab diagnostic",
    description: "Diagnoses DNS, SMB reachability, AD user state, required group membership, and observed access denial."
  },
  {
    id: "access-evidence",
    group: "Identity",
    label: "Access evidence",
    maturity: "Evidence",
    description: "Analyzes redacted access evidence from logs, Entra sign-in exports, or resource assignment notes."
  },
  {
    id: "ad-user-access",
    group: "Identity",
    label: "AD user access",
    maturity: "Sample",
    description: "Fixture-mode AD user access scenario."
  },
  {
    id: "ad-readiness",
    group: "Identity",
    label: "AD readiness",
    maturity: "Readiness check",
    description: "Shows whether the local machine context is ready for AD diagnostics."
  },
  {
    id: "dns-lookup",
    group: "Network",
    label: "DNS lookup",
    maturity: "Readiness check",
    description: "Collects read-only DNS resolution evidence."
  },
  {
    id: "local-readiness",
    group: "Endpoint",
    label: "Local readiness",
    maturity: "Readiness check",
    description: "Summarizes local operator-machine readiness."
  },
  {
    id: "cloud-readiness",
    group: "Cloud / M365",
    label: "Cloud readiness",
    maturity: "Readiness check",
    description: "Shows whether the local context is ready for Microsoft Graph diagnostics."
  },
  {
    id: "m365-sample",
    group: "Cloud / M365",
    label: "M365 sample",
    maturity: "Sample",
    description: "Synthetic access-path analyzer sample."
  },
  {
    id: "history",
    group: "Evidence",
    label: "History",
    maturity: "Evidence",
    description: "Shows previous diagnostic runs and report links."
  }
];

export const moduleGroups = ["FactoryOps", "Identity", "Network", "Endpoint", "Cloud / M365", "Evidence"].map((group) => ({
  name: group,
  defaultOpen: group === "FactoryOps" || group === "Identity",
  modules: modules.filter((module) => module.group === group)
}));

export function findModule(id: string): ModuleDefinition | undefined {
  return modules.find((module) => module.id === id);
}
