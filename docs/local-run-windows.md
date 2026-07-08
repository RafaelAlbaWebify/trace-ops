# TRACE Windows Local Run

Use this flow to run TRACE locally with the fewest manual steps.

## Start everything

After the repo is updated, start TRACE from any folder with:

```powershell
& "$HOME\trace-ops\START_TRACE_LOCAL.bat"
```

You can also double-click `START_TRACE_LOCAL.bat` in the repo root.

The launcher opens separate PowerShell windows for:

- Backend: http://127.0.0.1:8000
- Backend API docs: http://127.0.0.1:8000/docs
- Frontend: http://127.0.0.1:5173

## One-time update and start

If your local clone does not have the launcher yet, use this single PowerShell command:

```powershell
git -C "$HOME\trace-ops" pull --ff-only origin main; & "$HOME\trace-ops\START_TRACE_LOCAL.bat"
```

## Check prerequisites

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\trace-ops\scripts\start-trace-local.ps1" -Mode Check
```

The check reports the detected repo root, backend folder, frontend folder, Python availability, npm availability, and whether local dependencies already exist.

## Start services separately

Backend only:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\trace-ops\scripts\start-trace-local.ps1" -Mode Backend
```

Frontend only:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\trace-ops\scripts\start-trace-local.ps1" -Mode Frontend
```

## Operator notes

- Do not paste previous PowerShell prompt text such as `PS C:\Users\name>` into the terminal.
- Do not paste command output such as `remote: Enumerating objects` back into PowerShell.
- If the repo is cloned somewhere else, change only the path before `START_TRACE_LOCAL.bat`.
- The scripts resolve the repo root from their own location, so they do not depend on the current terminal folder.
- Local access-evidence run outputs are written to `.trace-runs\access-evidence`, which is ignored by Git.

## Demo sample

Use the Access Evidence screen with:

```text
2026-07-07T09:22:11Z user=sample.user@contoso.invalid app=SharePoint result=failure reason=ca-policy
2026-07-07T09:23:02Z user=sample.user@contoso.invalid app=SharePoint result=failure reason=mfa-required
```

Expected result:

- The result panel shows an access evidence finding.
- Markdown report content is generated.
- The History page shows the new run.
- Backend docs load at `/docs`.
