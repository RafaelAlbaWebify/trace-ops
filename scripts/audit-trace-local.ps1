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
$AuditRoot = Join-Path (Join-Path $HOME "Downloads") "TRACE_LOCAL_CODE_AUDIT_$Timestamp"
$ZipPath = "$AuditRoot.zip"
$Checks = New-Object System.Collections.Generic.List[object]
$Findings = New-Object System.Collections.Generic.List[object]

function Write-Step {
    param([string]$Message)
    Write-Host "[TRACE AUDIT] $Message" -ForegroundColor Cyan
}

function Add-Check {
    param([string]$Name, [string]$Status, [string]$Detail = "")
    $Checks.Add([pscustomobject]@{ name = $Name; status = $Status; detail = $Detail }) | Out-Null
}

function Add-Finding {
    param([string]$Severity, [string]$Area, [string]$Message, [string]$Recommendation)
    $Findings.Add([pscustomobject]@{
        severity = $Severity
        area = $Area
        message = $Message
        recommendation = $Recommendation
    }) | Out-Null
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
    throw "Python was not found. Install Python or make sure py or python is available in PATH."
}

function ConvertTo-RelativePath {
    param([string]$Path)
    return $Path.Substring($RepoRoot.Length).TrimStart('\', '/')
}

function Invoke-Captured {
    param([string]$Name, [scriptblock]$Script, [string]$LogFile)
    Write-Step $Name
    $FullLog = Join-Path $AuditRoot $LogFile
    try {
        $Output = & $Script 2>&1 | Out-String
        $Output | Set-Content -LiteralPath $FullLog -Encoding UTF8
        Add-Check -Name $Name -Status "PASS" -Detail $LogFile
        return $true
    }
    catch {
        ($_ | Out-String) | Set-Content -LiteralPath $FullLog -Encoding UTF8
        Add-Check -Name $Name -Status "FAIL" -Detail $LogFile
        Add-Finding -Severity "high" -Area $Name -Message $_.Exception.Message -Recommendation "Open $LogFile in the audit ZIP and fix the failing check."
        return $false
    }
}

function Get-AuditFiles {
    Get-ChildItem -LiteralPath $RepoRoot -Recurse -File -Force |
        Where-Object {
            $_.FullName -notmatch "\\\.git\\" -and
            $_.FullName -notmatch "\\node_modules\\" -and
            $_.FullName -notmatch "\\\.venv\\" -and
            $_.FullName -notmatch "\\dist\\" -and
            $_.FullName -notmatch "\\\.trace-runs\\"
        }
}

New-Item -ItemType Directory -Force -Path $AuditRoot | Out-Null
Write-Step "Repository: $RepoRoot"
Write-Step "Audit folder: $AuditRoot"

Invoke-Captured -Name "Git status" -LogFile "git-status.txt" -Script {
    git -C $RepoRoot status --short
    git -C $RepoRoot branch --show-current
    git -C $RepoRoot log -1 --oneline
    git -C $RepoRoot tag --points-at HEAD
} | Out-Null

Write-Step "Checking required paths"
$RequiredPaths = @(
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
$Missing = @()
foreach ($Path in $RequiredPaths) {
    if (-not (Test-Path (Join-Path $RepoRoot $Path))) {
        $Missing += $Path
    }
}
if ($Missing.Count -eq 0) {
    Add-Check -Name "Required paths" -Status "PASS" -Detail "All required paths found"
}
else {
    Add-Check -Name "Required paths" -Status "FAIL" -Detail ($Missing -join ", ")
    Add-Finding -Severity "high" -Area "Repo structure" -Message "Missing required paths: $($Missing -join ', ')" -Recommendation "Restore the missing release files."
}

Write-Step "Collecting file inventory"
$Files = Get-AuditFiles
$Files | Select-Object @{Name="path";Expression={ConvertTo-RelativePath $_.FullName}}, Length, LastWriteTimeUtc |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $AuditRoot "file-inventory.json") -Encoding UTF8
Add-Check -Name "File inventory" -Status "PASS" -Detail "$($Files.Count) files inventoried"

Invoke-Captured -Name "PowerShell parse check" -LogFile "powershell-parse.txt" -Script {
    $ParseErrors = @()
    Get-ChildItem -LiteralPath $RepoRoot -Filter "*.ps1" -Recurse -File |
        Where-Object { $_.FullName -notmatch "\\\.git\\|\\node_modules\\|\\\.venv\\|\\dist\\" } |
        ForEach-Object {
            $Tokens = $null
            $Errors = $null
            [System.Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$Tokens, [ref]$Errors) | Out-Null
            if ($Errors -and $Errors.Count -gt 0) {
                $ParseErrors += [pscustomobject]@{ file = ConvertTo-RelativePath $_.FullName; errors = ($Errors | ForEach-Object { $_.Message }) }
            }
        }
    if ($ParseErrors.Count -gt 0) {
        $ParseErrors | ConvertTo-Json -Depth 5
        throw "PowerShell parse errors detected."
    }
    "No PowerShell parse errors detected."
} | Out-Null

Invoke-Captured -Name "JSON validity check" -LogFile "json-validity.txt" -Script {
    $JsonErrors = @()
    Get-ChildItem -LiteralPath $RepoRoot -Filter "*.json" -Recurse -File |
        Where-Object { $_.FullName -notmatch "\\\.git\\|\\node_modules\\|\\\.venv\\|\\dist\\|\\\.trace-runs\\" } |
        ForEach-Object {
            try {
                Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null
            }
            catch {
                $JsonErrors += [pscustomobject]@{ file = ConvertTo-RelativePath $_.FullName; error = $_.Exception.Message }
            }
        }
    if ($JsonErrors.Count -gt 0) {
        $JsonErrors | ConvertTo-Json -Depth 5
        throw "Invalid JSON files detected."
    }
    "All JSON files parsed successfully."
} | Out-Null

Write-Step "Running lightweight secret-pattern scan"
$SecretPatterns = @(
    "BEGIN RSA PRIVATE KEY",
    "BEGIN OPENSSH PRIVATE KEY",
    "ghp_[A-Za-z0-9_]{20,}",
    "xox[baprs]-[A-Za-z0-9-]{10,}",
    "AKIA[0-9A-Z]{16}",
    "(?i)client_secret\s*[:=]\s*\S{8,}",
    "(?i)password\s*[:=]\s*\S{8,}",
    "(?i)token\s*[:=]\s*\S{12,}"
)
$SecretHits = @()
$TextFiles = $Files | Where-Object { $_.Length -lt 1MB -and $_.Extension -notin @(".png", ".jpg", ".jpeg", ".gif", ".ico", ".zip") }
foreach ($File in $TextFiles) {
    $Text = Get-Content -LiteralPath $File.FullName -Raw -ErrorAction SilentlyContinue
    foreach ($Pattern in $SecretPatterns) {
        if ($Text -match $Pattern) {
            $SecretHits += [pscustomobject]@{ file = ConvertTo-RelativePath $File.FullName; pattern = $Pattern }
        }
    }
}
$SecretHits | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $AuditRoot "secret-scan.json") -Encoding UTF8
if ($SecretHits.Count -eq 0) {
    Add-Check -Name "Secret-pattern scan" -Status "PASS" -Detail "No obvious secret patterns found"
}
else {
    Add-Check -Name "Secret-pattern scan" -Status "WARN" -Detail "$($SecretHits.Count) potential hits"
    Add-Finding -Severity "medium" -Area "Secret scan" -Message "$($SecretHits.Count) potential secret-pattern hits were found." -Recommendation "Review secret-scan.json manually."
}

Write-Step "Checking local artifact ignore rules"
$GitignoreText = Get-Content -LiteralPath (Join-Path $RepoRoot ".gitignore") -Raw -Encoding UTF8
$RequiredIgnorePatterns = @(".trace-runs/", "backend/.trace-runs/", "node_modules/", "frontend/dist/", "*.zip")
$MissingIgnores = $RequiredIgnorePatterns | Where-Object { $GitignoreText -notmatch [regex]::Escape($_) }
if ($MissingIgnores.Count -eq 0) {
    Add-Check -Name "Gitignore protections" -Status "PASS" -Detail "Required local artifact patterns found"
}
else {
    Add-Check -Name "Gitignore protections" -Status "FAIL" -Detail ($MissingIgnores -join ", ")
    Add-Finding -Severity "high" -Area "Git hygiene" -Message "Missing .gitignore protections: $($MissingIgnores -join ', ')" -Recommendation "Add missing ignore patterns."
}

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

if (-not $SkipFrontend) {
    if (-not (Test-CommandExists "npm")) {
        Add-Check -Name "Frontend prerequisites" -Status "FAIL" -Detail "npm not found"
        Add-Finding -Severity "high" -Area "Frontend" -Message "npm was not found in PATH." -Recommendation "Install Node.js or make sure npm is available."
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

Invoke-Captured -Name "Collector sample contract smoke" -LogFile "collector-sample-smoke.txt" -Script {
    $Scenarios = @("account-disabled", "missing-license", "service-plan-disabled", "guest-b2b-access-failure", "ca-details-missing", "ca-device-noncompliant", "mfa-requirement-not-satisfied", "no-recent-signin-evidence", "successful-access-baseline")
    foreach ($Scenario in $Scenarios) {
        $JsonText = (& (Join-Path $CollectorDir "Invoke-TraceM365AccessScan.ps1") -UserPrincipalName "sample.user@contoso.invalid" -AffectedService "Microsoft 365 general access" -Scenario $Scenario -UseSampleData:$true | Out-String)
        $Result = $JsonText | ConvertFrom-Json -ErrorAction Stop
        if ($Result.scenario_id -ne $Scenario) { throw "Scenario $Scenario returned scenario_id '$($Result.scenario_id)'" }
        if ($Result.module -ne "m365-access-path-analyzer") { throw "Scenario $Scenario returned unexpected module '$($Result.module)'" }
        "$Scenario OK"
    }
} | Out-Null

Write-Step "Checking README consistency"
$Readme = Get-Content -LiteralPath (Join-Path $RepoRoot "README.md") -Raw -Encoding UTF8
$RequiredReadmeTerms = @("Access Evidence Analyzer", "generic_access_log_text", "entra_signin_csv", "resource_assignment_json", "POST /api/logs/analyze", "not a SIEM")
$MissingTerms = $RequiredReadmeTerms | Where-Object { $Readme -notmatch [regex]::Escape($_) }
if ($MissingTerms.Count -eq 0) {
    Add-Check -Name "README consistency" -Status "PASS" -Detail "Current v1 terms found"
}
else {
    Add-Check -Name "README consistency" -Status "WARN" -Detail ($MissingTerms -join ", ")
    Add-Finding -Severity "medium" -Area "Documentation" -Message "README is missing expected v1 terms: $($MissingTerms -join ', ')" -Recommendation "Refresh README to match current scope."
}

$FailCount = ($Checks | Where-Object { $_.status -eq "FAIL" }).Count
$WarnCount = ($Checks | Where-Object { $_.status -eq "WARN" }).Count
$Head = git -C $RepoRoot rev-parse HEAD
$Branch = git -C $RepoRoot branch --show-current
$Summary = [pscustomobject]@{
    generated_at = (Get-Date).ToString("o")
    repo_root = $RepoRoot
    head = $Head
    branch = $Branch
    checks = $Checks
    findings = $Findings
    fail_count = $FailCount
    warn_count = $WarnCount
}
$Summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $AuditRoot "audit-summary.json") -Encoding UTF8

$Report = @()
$Report += "# TRACE Local Code Audit"
$Report += ""
$Report += "- Generated: $($Summary.generated_at)"
$Report += "- Repository: `$RepoRoot`"
$Report += "- Branch: `$Branch`"
$Report += "- HEAD: `$Head`"
$Report += "- Failures: $FailCount"
$Report += "- Warnings: $WarnCount"
$Report += ""
$Report += "## Checks"
$Report += ""
foreach ($Check in $Checks) {
    $Report += "- **$($Check.status)** - $($Check.name): $($Check.detail)"
}
$Report += ""
$Report += "## Findings"
$Report += ""
if ($Findings.Count -eq 0) {
    $Report += "No findings were recorded by the audit script."
}
else {
    foreach ($Finding in $Findings) {
        $Report += "### $($Finding.severity.ToUpper()) - $($Finding.area)"
        $Report += ""
        $Report += $Finding.message
        $Report += ""
        $Report += "Recommendation: $($Finding.recommendation)"
        $Report += ""
    }
}
$Report | Set-Content -LiteralPath (Join-Path $AuditRoot "audit-report.md") -Encoding UTF8

if (Test-Path $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}
Compress-Archive -LiteralPath (Join-Path $AuditRoot "*") -DestinationPath $ZipPath -Force

Write-Host ""
Write-Host "TRACE local code audit complete." -ForegroundColor Green
Write-Host "Audit folder: $AuditRoot"
Write-Host "Audit ZIP:    $ZipPath"
Write-Host "Failures:     $FailCount"
Write-Host "Warnings:     $WarnCount"

if ($FailCount -gt 0) {
    exit 1
}
exit 0
