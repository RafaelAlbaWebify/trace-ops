param(
    [switch]$NoInstall,
    [switch]$SkipFrontend,
    [switch]$SkipBackend
)

$ErrorActionPreference = "Stop"

$ScriptPath = $PSCommandPath
if (-not $ScriptPath) {
    $ScriptPath = $MyInvocation.MyCommand.Path
}

$ScriptDir = Split-Path -Parent $ScriptPath
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$BackendDir = Join-Path $RepoRoot "backend"
$FrontendDir = Join-Path $RepoRoot "frontend"
$CollectorDir = Join-Path $RepoRoot "collector"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Downloads = Join-Path $HOME "Downloads"
$AuditRoot = Join-Path $Downloads "TRACE_LOCAL_CODE_AUDIT_$Timestamp"
$ZipPath = "$AuditRoot.zip"
$ReportPath = Join-Path $AuditRoot "audit-report.md"
$SummaryPath = Join-Path $AuditRoot "audit-summary.json"
$Findings = New-Object System.Collections.Generic.List[object]
$Checks = New-Object System.Collections.Generic.List[object]

function Write-Step {
    param([string]$Message)
    Write-Host "[TRACE AUDIT] $Message" -ForegroundColor Cyan
}

function Add-Check {
    param(
        [string]$Name,
        [string]$Status,
        [string]$Detail = ""
    )
    $Checks.Add([pscustomobject]@{ name = $Name; status = $Status; detail = $Detail }) | Out-Null
}

function Add-Finding {
    param(
        [string]$Severity,
        [string]$Area,
        [string]$Message,
        [string]$Recommendation
    )
    $Findings.Add([pscustomobject]@{ severity = $Severity; area = $Area; message = $Message; recommendation = $Recommendation }) | Out-Null
}

function Invoke-Captured {
    param(
        [string]$Name,
        [scriptblock]$Script,
        [string]$LogFile
    )

    Write-Step $Name
    $fullLog = Join-Path $AuditRoot $LogFile
    try {
        $output = & $Script 2>&1 | Out-String
        $output | Set-Content -LiteralPath $fullLog -Encoding UTF8
        Add-Check -Name $Name -Status "PASS" -Detail $LogFile
        return $true
    }
    catch {
        ($_ | Out-String) | Set-Content -LiteralPath $fullLog -Encoding UTF8
        Add-Check -Name $Name -Status "FAIL" -Detail $LogFile
        Add-Finding -Severity "high" -Area $Name -Message $_.Exception.Message -Recommendation "Open $LogFile in the audit ZIP and fix the failing check."
        return $false
    }
}

function Test-CommandExists {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-SystemPython {
    param([string[]]$Arguments)
    if (Test-CommandExists "py") {
        & py @Arguments
        return
    }
    if (Test-CommandExists "python") {
        & python @Arguments
        return
    }
    throw "Python was not found. Install Python or make sure 'py' or 'python' is available in PATH."
}

function ConvertTo-RelativePath {
    param([string]$Path)
    return $Path.Substring($RepoRoot.Length).TrimStart('\', '/')
}

New-Item -ItemType Directory -Force -Path $AuditRoot | Out-Null
Write-Step "Repository: $RepoRoot"
Write-Step "Audit folder: $AuditRoot"

# Repository identity
Invoke-Captured -Name "Git status" -LogFile "git-status.txt" -Script {
    git -C $RepoRoot status --short
    git -C $RepoRoot branch --show-current
    git -C $RepoRoot log -1 --oneline
    git -C $RepoRoot tag --points-at HEAD
} | Out-Null

# Required path inventory
Write-Step "Checking required paths"
$requiredPaths = @(
    "README.md",
    ".gitignore",
    ".github\workflows\ci.yml",
    "START_TRACE_LOCAL.bat",
    "AUDIT_TRACE_LOCAL.bat",
    "scripts\start-trace-local.ps1",
    "scripts\audit-trace-local.ps1",
    "backend\app\main.py",
    "backend\app\logs.py",
    "backend\app\log_models.py",
    "backend\app\log_analyzer.py",
    "backend\app\entra_signin_analyzer.py",
    "backend\app\resource_assignment_analyzer.py",
    "backend\app\access_run_store.py",
    "frontend\src\App.tsx",
    "frontend\src\api\traceApi.ts",
    "frontend\src\modules\accessEvidence\AccessEvidencePage.tsx",
    "docs\v1-release-checklist.md",
    "docs\releases\trace-v1.0.0-access-evidence-analyzer.md"
)

$missing = @()
foreach ($path in $requiredPaths) {
    if (-not (Test-Path (Join-Path $RepoRoot $path))) {
        $missing += $path
    }
}
if ($missing.Count -eq 0) {
    Add-Check -Name "Required paths" -Status "PASS" -Detail "All required paths found"
}
else {
    Add-Check -Name "Required paths" -Status "FAIL" -Detail ($missing -join ", ")
    Add-Finding -Severity "high" -Area "Repo structure" -Message "Missing required paths: $($missing -join ', ')" -Recommendation "Restore or regenerate the missing release files."
}

# File inventory
Write-Step "Collecting file inventory"
$files = Get-ChildItem -LiteralPath $RepoRoot -Recurse -File -Force |
    Where-Object {
        $_.FullName -notmatch "\\\.git\\" -and
        $_.FullName -notmatch "\\node_modules\\" -and
        $_.FullName -notmatch "\\\.venv\\" -and
        $_.FullName -notmatch "\\dist\\" -and
        $_.FullName -notmatch "\\\.trace-runs\\"
    }
$inventory = $files | Select-Object @{Name="path";Expression={ConvertTo-RelativePath $_.FullName}}, Length, LastWriteTimeUtc
$inventory | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $AuditRoot "file-inventory.json") -Encoding UTF8
Add-Check -Name "File inventory" -Status "PASS" -Detail "$($files.Count) files inventoried"

# PowerShell parse checks
Invoke-Captured -Name "PowerShell parse check" -LogFile "powershell-parse.txt" -Script {
    $parseErrors = @()
    Get-ChildItem -LiteralPath $RepoRoot -Filter "*.ps1" -Recurse -File |
        Where-Object { $_.FullName -notmatch "\\\.git\\|\\node_modules\\|\\\.venv\\|\\dist\\" } |
        ForEach-Object {
            $tokens = $null
            $errors = $null
            [System.Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$tokens, [ref]$errors) | Out-Null
            if ($errors -and $errors.Count -gt 0) {
                $parseErrors += [pscustomobject]@{ file = ConvertTo-RelativePath $_.FullName; errors = ($errors | ForEach-Object { $_.Message }) }
            }
        }
    if ($parseErrors.Count -gt 0) {
        $parseErrors | ConvertTo-Json -Depth 5
        throw "PowerShell parse errors detected."
    }
    "No PowerShell parse errors detected."
} | Out-Null

# JSON validity
Invoke-Captured -Name "JSON validity check" -LogFile "json-validity.txt" -Script {
    $jsonErrors = @()
    Get-ChildItem -LiteralPath $RepoRoot -Filter "*.json" -Recurse -File |
        Where-Object { $_.FullName -notmatch "\\\.git\\|\\node_modules\\|\\\.venv\\|\\dist\\|\\\.trace-runs\\" } |
        ForEach-Object {
            try {
                Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null
            }
            catch {
                $jsonErrors += [pscustomobject]@{ file = ConvertTo-RelativePath $_.FullName; error = $_.Exception.Message }
            }
        }
    if ($jsonErrors.Count -gt 0) {
        $jsonErrors | ConvertTo-Json -Depth 5
        throw "Invalid JSON files detected."
    }
    "All JSON files parsed successfully."
} | Out-Null

# Secret-ish scan
Write-Step "Running lightweight secret-pattern scan"
$secretPatterns = @(
    "BEGIN RSA PRIVATE KEY",
    "BEGIN OPENSSH PRIVATE KEY",
    "ghp_[A-Za-z0-9_]{20,}",
    "xox[baprs]-[A-Za-z0-9-]{10,}",
    "AKIA[0-9A-Z]{16}",
    "(?i)client_secret\s*[:=]\s*['\""].{8,}",
    "(?i)password\s*[:=]\s*['\""].{8,}",
    "(?i)token\s*[:=]\s*['\""].{12,}"
)
$secretHits = @()
$textFiles = $files | Where-Object { $_.Length -lt 1MB -and $_.Extension -notin @(".png", ".jpg", ".jpeg", ".gif", ".ico", ".zip") }
foreach ($file in $textFiles) {
    $text = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction SilentlyContinue
    foreach ($pattern in $secretPatterns) {
        if ($text -match $pattern) {
            $secretHits += [pscustomobject]@{ file = ConvertTo-RelativePath $file.FullName; pattern = $pattern }
        }
    }
}
$secretHits | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $AuditRoot "secret-scan.json") -Encoding UTF8
if ($secretHits.Count -eq 0) {
    Add-Check -Name "Secret-pattern scan" -Status "PASS" -Detail "No obvious secret patterns found"
}
else {
    Add-Check -Name "Secret-pattern scan" -Status "WARN" -Detail "$($secretHits.Count) potential hits"
    Add-Finding -Severity "medium" -Area "Secret scan" -Message "$($secretHits.Count) potential secret-pattern hits were found." -Recommendation "Review secret-scan.json manually before publishing or tagging."
}

# Gitignore protection checks
Write-Step "Checking local artifact ignore rules"
$gitignoreText = Get-Content -LiteralPath (Join-Path $RepoRoot ".gitignore") -Raw -Encoding UTF8
$requiredIgnorePatterns = @(".trace-runs/", "backend/.trace-runs/", "node_modules/", "frontend/dist/", "*.zip")
$missingIgnores = $requiredIgnorePatterns | Where-Object { $gitignoreText -notmatch [regex]::Escape($_) }
if ($missingIgnores.Count -eq 0) {
    Add-Check -Name "Gitignore protections" -Status "PASS" -Detail "Required local artifact patterns found"
}
else {
    Add-Check -Name "Gitignore protections" -Status "FAIL" -Detail ($missingIgnores -join ", ")
    Add-Finding -Severity "high" -Area "Git hygiene" -Message "Missing .gitignore protections: $($missingIgnores -join ', ')" -Recommendation "Add missing ignore patterns before running local demos."
}

# Backend checks
if (-not $SkipBackend) {
    $VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
    if (-not (Test-Path $VenvPython)) {
        Invoke-Captured -Name "Create backend venv" -LogFile "backend-venv.txt" -Script {
            Push-Location $BackendDir
            try { Invoke-SystemPython @("-m", "venv", ".venv") }
            finally { Pop-Location }
        } | Out-Null
    }

    if (-not $NoInstall) {
        Invoke-Captured -Name "Install backend dependencies" -LogFile "backend-install.txt" -Script {
            Push-Location $BackendDir
            try {
                & $VenvPython -m pip install --upgrade pip
                & $VenvPython -m pip install -r requirements.txt
            }
            finally { Pop-Location }
        } | Out-Null
    }

    Invoke-Captured -Name "Backend compileall" -LogFile "backend-compileall.txt" -Script {
        Push-Location $BackendDir
        try { & $VenvPython -m compileall app tests }
        finally { Pop-Location }
    } | Out-Null

    Invoke-Captured -Name "Backend pytest" -LogFile "backend-pytest.txt" -Script {
        Push-Location $BackendDir
        try { & $VenvPython -m pytest }
        finally { Pop-Location }
    } | Out-Null
}
else {
    Add-Check -Name "Backend checks" -Status "SKIP" -Detail "Skipped by -SkipBackend"
}

# Frontend checks
if (-not $SkipFrontend) {
    if (-not (Test-CommandExists "npm")) {
        Add-Check -Name "Frontend prerequisites" -Status "FAIL" -Detail "npm not found"
        Add-Finding -Severity "high" -Area "Frontend" -Message "npm was not found in PATH." -Recommendation "Install Node.js or make sure npm is available before running frontend checks."
    }
    else {
        if (-not $NoInstall -and -not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
            Invoke-Captured -Name "Install frontend dependencies" -LogFile "frontend-install.txt" -Script {
                Push-Location $FrontendDir
                try { npm install }
                finally { Pop-Location }
            } | Out-Null
        }

        Invoke-Captured -Name "Frontend test/typecheck" -LogFile "frontend-test.txt" -Script {
            Push-Location $FrontendDir
            try { npm test }
            finally { Pop-Location }
        } | Out-Null

        Invoke-Captured -Name "Frontend build" -LogFile "frontend-build.txt" -Script {
            Push-Location $FrontendDir
            try { npm run build }
            finally { Pop-Location }
        } | Out-Null
    }
}
else {
    Add-Check -Name "Frontend checks" -Status "SKIP" -Detail "Skipped by -SkipFrontend"
}

# Collector sample smoke
Invoke-Captured -Name "Collector sample contract smoke" -LogFile "collector-sample-smoke.txt" -Script {
    $scenarios = @("account-disabled", "missing-license", "service-plan-disabled", "guest-b2b-access-failure", "ca-details-missing", "ca-device-noncompliant", "mfa-requirement-not-satisfied", "no-recent-signin-evidence", "successful-access-baseline")
    foreach ($scenario in $scenarios) {
        $jsonText = (& (Join-Path $CollectorDir "Invoke-TraceM365AccessScan.ps1") -UserPrincipalName "sample.user@contoso.invalid" -AffectedService "Microsoft 365 general access" -Scenario $scenario -UseSampleData:$true | Out-String)
        $result = $jsonText | ConvertFrom-Json -ErrorAction Stop
        if ($result.scenario_id -ne $scenario) { throw "Scenario $scenario returned scenario_id '$($result.scenario_id)'" }
        if ($result.module -ne "m365-access-path-analyzer") { throw "Scenario $scenario returned unexpected module '$($result.module)'" }
        "$scenario OK"
    }
} | Out-Null

# Documentation consistency checks
Write-Step "Checking documentation consistency"
$readme = Get-Content -LiteralPath (Join-Path $RepoRoot "README.md") -Raw -Encoding UTF8
$requiredReadmeTerms = @("Access Evidence Analyzer", "generic_access_log_text", "entra_signin_csv", "resource_assignment_json", "POST /api/logs/analyze", "not a SIEM")
$missingTerms = $requiredReadmeTerms | Where-Object { $readme -notmatch [regex]::Escape($_) }
if ($missingTerms.Count -eq 0) {
    Add-Check -Name "README consistency" -Status "PASS" -Detail "Current v1 terms found"
}
else {
    Add-Check -Name "README consistency" -Status "WARN" -Detail ($missingTerms -join ", ")
    Add-Finding -Severity "medium" -Area "Documentation" -Message "README is missing expected v1 terms: $($missingTerms -join ', ')" -Recommendation "Refresh README to match current v1 scope."
}

# Summary and report
$failCount = ($Checks | Where-Object { $_.status -eq "FAIL" }).Count
$warnCount = ($Checks | Where-Object { $_.status -eq "WARN" }).Count
$summary = [pscustomobject]@{
    generated_at = (Get-Date).ToString("o")
    repo_root = $RepoRoot
    head = (git -C $RepoRoot rev-parse HEAD)
    branch = (git -C $RepoRoot branch --show-current)
    checks = $Checks
    findings = $Findings
    fail_count = $failCount
    warn_count = $warnCount
}
$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $SummaryPath -Encoding UTF8

$report = @()
$report += "# TRACE Local Code Audit"
$report += ""
$report += "- Generated: $($summary.generated_at)"
$report += "- Repository: `$RepoRoot`"
$report += "- Branch: `$($summary.branch)`"
$report += "- HEAD: `$($summary.head)`"
$report += "- Failures: $failCount"
$report += "- Warnings: $warnCount"
$report += ""
$report += "## Checks"
$report += ""
foreach ($check in $Checks) {
    $report += "- **$($check.status)** - $($check.name): $($check.detail)"
}
$report += ""
$report += "## Findings"
$report += ""
if ($Findings.Count -eq 0) {
    $report += "No findings were recorded by the audit script."
}
else {
    foreach ($finding in $Findings) {
        $report += "### $($finding.severity.ToUpper()) - $($finding.area)"
        $report += ""
        $report += $finding.message
        $report += ""
        $report += "Recommendation: $($finding.recommendation)"
        $report += ""
    }
}
$report | Set-Content -LiteralPath $ReportPath -Encoding UTF8

if (Test-Path $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}
Compress-Archive -LiteralPath (Join-Path $AuditRoot "*") -DestinationPath $ZipPath -Force

Write-Host ""
Write-Host "TRACE local code audit complete." -ForegroundColor Green
Write-Host "Audit folder: $AuditRoot"
Write-Host "Audit ZIP:    $ZipPath"
Write-Host "Failures:     $failCount"
Write-Host "Warnings:     $warnCount"

if ($failCount -gt 0) {
    exit 1
}
exit 0
