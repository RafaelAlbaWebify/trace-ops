export type ModuleMaturity = "Evidence";

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
    id: "access-evidence",
    group: "Identity",
    label: "Access evidence",
    maturity: "Evidence",
    description: "Analyzes redacted IAM access evidence from logs, Entra sign-in exports, guided forms, and resource assignment notes."
  },
  {
    id: "history",
    group: "Evidence",
    label: "History",
    maturity: "Evidence",
    description: "Shows previous IAM evidence runs and report links."
  }
];

export const moduleGroups = ["Identity", "Evidence"].map((group) => ({
  name: group,
  defaultOpen: true,
  modules: modules.filter((module) => module.group === group)
}));

export function findModule(id: string): ModuleDefinition | undefined {
  return modules.find((module) => module.id === id);
}
