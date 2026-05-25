# TRACE Tasks

## Phase 0: Spec foundation

- [x] Create repository structure.
- [x] Add AGENTS.md.
- [x] Add README.md.
- [x] Add product spec.
- [x] Add technical plan.
- [x] Add modules spec.
- [x] Add permissions model.
- [x] Add test plan.
- [x] Add synthetic sample JSON files.
- [x] Add .gitignore.

## Phase 1: Collector MVP with sample mode

- [ ] Create PowerShell script: Connect-TraceM365Graph.ps1.
- [x] Create PowerShell script: Get-TraceUserIdentitySnapshot.ps1.
- [x] Create PowerShell script: Get-TraceLicenseSnapshot.ps1.
- [x] Create PowerShell script: Get-TraceSignInSnapshot.ps1.
- [x] Create PowerShell script: Get-TraceConditionalAccessSnapshot.ps1.
- [x] Create PowerShell script: Get-TraceDeviceComplianceSnapshot.ps1.
- [x] Add -UseSampleData support for collector scripts.
- [x] Add Pester tests validating JSON output shape.
- [x] Do not add real remediation scripts.

## Phase 2: Backend MVP

- [x] Create FastAPI app.
- [x] Add endpoint: GET /api/health.
- [x] Add endpoint: GET /api/modules.
- [x] Add endpoint: POST /api/scan/user-access.
- [x] Add Pydantic models for scan request and scan result.
- [x] Add collector subprocess runner.
- [x] Add validation for collector JSON.
- [x] Add graceful collector error handling.
- [x] Add SQLite scan history.
- [x] Add Pytest tests.

## Phase 3: Analyzer rules

- [x] Implement USER_ACCOUNT_DISABLED.
- [x] Implement MISSING_RELEVANT_LICENSE.
- [x] Implement CONDITIONAL_ACCESS_DETAILS_MISSING.
- [x] Implement CA_DEVICE_COMPLIANCE_BLOCK.
- [x] Implement NO_RECENT_SIGNIN_EVIDENCE.
- [x] Add tests using synthetic sample JSON.

## Phase 4: Frontend MVP

- [x] Create React + TypeScript + Vite frontend.
- [x] Add TRACE landing/dashboard page.
- [x] Add module selector.
- [x] Add M365 Access Path Analyzer scan form.
- [x] Add results page.
- [x] Add evidence cards.
- [x] Add confidence labels.
- [x] Add limitations section.
- [x] Add local scan history view.
- [x] Add Vitest tests for core components.

## Phase 5: Reporting

- [x] Generate HTML report.
- [x] Generate JSON export.
- [x] Add support summary.
- [x] Add technical evidence section.
- [ ] Add manager-friendly explanation.
- [x] Add what-not-to-change-yet section.
- [ ] Add frontend export buttons.

## Phase 5A: Operational read-only Graph diagnostics

- [x] Add Phase 5A operational Graph diagnostics plan.
- [x] Add read-only Microsoft Graph readiness preflight script.
- [x] Verify proposed Graph permissions against current Microsoft documentation.
- [x] Update Graph readiness preflight to check LicenseAssignment.Read.All instead of Directory.Read.All.
- [ ] Add standalone operational collector script: Invoke-TraceM365AccessGraphScan.ps1.
- [ ] Add user lookup by UPN in operational collector.
- [ ] Add recent sign-in log retrieval with time window filtering.
- [ ] Normalize live evidence into the TRACE collector contract.
- [ ] Add controlled operational collector errors.
- [ ] Add mocked Graph response fixtures.
- [ ] Add Pester tests for operational collector with mocked Graph responses.
- [ ] Add backend runner support for operational mode.
- [ ] Add backend tests for operational runner controlled errors.
- [ ] Add frontend mode selector later.
- [ ] Keep sample mode as the default.
- [ ] Do not add remediation or tenant write actions.

## Phase 5B: User Access Health Scanner

- [x] Add Phase 5B User Access Health Scanner plan.
- [ ] Finish Phase 5A single-user operational collector first.
- [ ] Add synthetic CSV fixtures for multi-user scans.
- [ ] Add CSV parser and validation for user_principal_name and optional affected_service.
- [ ] Add mocked Graph response fixtures for multi-user scan tests.
- [ ] Add CSV-based multi-user scan runner.
- [ ] Reuse per-user analyzer logic for grouped scan results.
- [ ] Add grouped issue category summary.
- [ ] Add local JSON/HTML group health report.
- [ ] Add frontend health summary view later.
- [ ] Add Entra ID group input later.
- [ ] Add visual access map later.
- [ ] Consider on-prem AD OU scanner later for hybrid/on-prem environments only.
- [ ] Keep scanner read-only and scoped by explicit input.
- [ ] Do not add remediation or tenant write actions.

## Phase 6: Real Microsoft Graph integration

- [ ] Implement delegated Microsoft Graph authentication.
- [ ] Add permission checks.
- [ ] Add missing-permission warnings.
- [ ] Add real user identity lookup.
- [ ] Add real license lookup.
- [ ] Add real sign-in log lookup.
- [ ] Add Conditional Access evidence extraction when available.
- [ ] Add device evidence extraction when available.
- [ ] Keep sample mode available.

## Phase 7: Portfolio polish

- [x] Add screenshots using synthetic data.
- [x] Add architecture diagram.
- [ ] Add demo GIF or short video script.
- [ ] Add limitations section to README.
- [ ] Add future roadmap.
- [ ] Add LinkedIn post draft.
