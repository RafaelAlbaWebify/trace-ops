param(
    [switch]$NoInstall,
    [switch]$SkipFrontend,
    [switch]$SkipBackend
)

$ErrorActionPreference = "Stop"

$ScriptPath = $PSCommandPath
if (-not $ScriptPath) { $ScriptPath = $MyInvocation.MyCommand.Path }

$ScriptDir = Split-Path -Parent $ScriptPath
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$BackendDir = Join-Path $RepoRoot "backend"
$FrontendDir = Join-Path $RepoRoot "frontend"
$CollectorDir = Join-Path $RepoRoot "collector"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$AuditRoot = Join-Path (Join-Path $HOME "Downloads") "TRACE_LOCAL_CODE_AUDIT_$Timestamp"
$ZipPath = "$AuditRoot.zip"
$Checks = @()
$Findings = @()

function Write-Step { param([string]$Message) Write-Host "[TRACE AUDIT] $Message" -ForegroundColor Cyan }

function Add-Check {
    param([string]$Name, [string]$Status, [string]$Detail)
    $script:Checks += [pscustomobject]@{ name = $Name; status = $Status; detail = $Detail }
}

function Add-Finding {
    param([string]$Severity, [string]$Area, [string]$Message, [string]$Recommendation)
    $script:Findings += [pscustomobject]@{ severity = $Severity; area = $Area; message = $Message; recommendation = $Recommendation }
}

function Command-Exists { param([string]$Name) return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue) }
function Get-PythonCommand { if (Command-Exists "py") { return "py" }; if (Command-Exists "python") { return "python" }; return $null }
function Get-NpmCommand { if (Command-Exists "npm.cmd") { return "npm.cmd" }; if (Command-Exists "npm") { return "npm" }; return $null }

function Get-RepoFiles {
    Get-ChildItem -LiteralPath $RepoRoot -Recurse -File -Force |
        Where-Object {
            $_.FullName -notlike "*\.git\*" -and
            $_.FullName -notlike "*\node_modules\*" -and
            $_.FullName -notlike "*\.venv\*" -and
            $_.FullName -notlike "*\dist\*" -and
            $_.FullName -notlike "*\.trace-runs\*"
        }
}

function Run-External {
    param([string]$Name, [string]$WorkingDirectory, [string]$Executable, [string[]]$Arguments, [string]$LogFile)
    Write-Step $Name
    $LogPath = Join-Path $AuditRoot $LogFile
    $Output = @()
    Push-Location $WorkingDirectory
    try {
        $Output = & $Executable @Arguments 2>&1
        $Exit = $LASTEXITCODE
        $Output | Out-String | Set-Content -LiteralPath $LogPath -Encoding UTF8
        if ($Exit -ne 0) {
            Add-Check -Name $Name -Status "FAIL" -Detail $LogFile
            Add-Finding -Severity "high" -Area $Name -Message "$Executable exited with code $Exit" -Recommendation "Review $LogFile in the audit ZIP."
        } else {
            Add-Check -Name $Name -Status "PASS" -Detail $LogFile
        }
    } catch {
        (($Output | Out-String) + [Environment]::NewLine + ($_ | Out-String)) | Set-Content -LiteralPath $LogPath -Encoding UTF8
        Add-Check -Name $Name -Status "FAIL" -Detail $LogFile
        Add-Finding -Severity "high" -Area $Name -Message $_.Exception.Message -Recommendation "Review $LogFile in the audit ZIP."
    } finally {
        Pop-Location
    }
}

function Test-JsonWithPython {
    param([string]$PythonCommand, [string]$JsonPath)
    $Code = "import json,sys; json.load(open(sys.argv[1], encoding='utf-8-sig'))"
    $Output = & $PythonCommand -c $Code $JsonPath 2>&1
    $Exit = $LASTEXITCODE
    if ($Exit -ne 0) { return ($Output | Out-String).Trim() }
    return $null
}

function Complete-AuditArchive {
    param([string]$FolderPath, [string]$ArchivePath)
    if (Test-Path -LiteralPath $ArchivePath) { Remove-Item -LiteralPath $ArchivePath -Force }
    try {
        Compress-Archive -LiteralPath (Join-Path $FolderPath "*") -DestinationPath $ArchivePath -Force -ErrorAction Stop
    } catch {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        if (Test-Path -LiteralPath $ArchivePath) { Remove-Item -LiteralPath $ArchivePath -Force }
        [System.IO.Compression.ZipFile]::CreateFromDirectory($FolderPath, $ArchivePath)
    }
    if (-not (Test-Path -LiteralPath $ArchivePath)) { throw "Audit ZIP was not created: $ArchivePath" }
    $ZipItem = Get-Item -LiteralPath $ArchivePath
    if ($ZipItem.Length -le 0) { throw "Audit ZIP is empty: $ArchivePath" }
}

New-Item -ItemType Directory -Force -Path $AuditRoot | Out-Null
Write-Step "Repository: $RepoRoot"
Write-Step "Audit folder: $AuditRoot"

try {
    $GitLog = @()
    $GitLog += git -C $RepoRoot status --short
    $GitLog += git -C $RepoRoot branch --show-current
    $GitLog += git -C $RepoRoot log -1 --oneline
    $GitLog += git -C $RepoRoot tag --points-at HEAD
    $GitLog | Set-Content -LiteralPath (Join-Path $AuditRoot "git-status.txt") -Encoding UTF8
    Add-Check -Name "Git status" -Status "PASS" -Detail "git-status.txt"
} catch {
    Add-Check -Name "Git status" -Status "FAIL" -Detail $_.Exception.Message
    Add-Finding -Severity "high" -Area "Git" -Message $_.Exception.Message -Recommendation "Confirm Git is installed and the repo is valid."
}

$RequiredPaths = @("README.md", ".gitignore", ".github\workflows\ci.yml", "START_TRACE_LOCAL.bat", "AUDIT_TRACE_LOCAL.bat", "scripts\start-trace-local.ps1", "scripts\audit-trace-local.ps1", "backend\app\main.py", "backend\app\logs.py", "backend\app\log_models.py", "backend\app\log_analyzer.py", "backend\app\entra_signin_analyzer.py", "backend\app\resource_assignment_analyzer.py", "backend\app\access_run_store.py", "frontend\src\App.tsx", "frontend\src\api\traceApi.ts", "frontend\src\modules\accessEvidence\AccessEvidencePage.tsx", "docs\v1-release-checklist.md", "docs\releases\trace-v1.0.0-access-evidence-analyzer.md")
$Missing = @()
foreach ($Item in $RequiredPaths) { if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot $Item))) { $Missing += $Item } }
if ($Missing.Count -eq 0) { Add-Check -Name "Required paths" -Status "PASS" -Detail "All required paths found" } else { Add-Check -Name "Required paths" -Status "FAIL" -Detail ($Missing -join ", "); Add-Finding -Severity "high" -Area "Repo structure" -Message "Missing required paths: $($Missing -join ', ')" -Recommendation "Restore missing files." }

$Files = Get-RepoFiles
$Files | Select-Object FullName, Length, LastWriteTimeUtc | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $AuditRoot "file-inventory.json") -Encoding UTF8
Add-Check -Name "File inventory" -Status "PASS" -Detail "$($Files.Count) files inventoried"

try {
    $ParseErrors = @()
    $PowerShellFiles = Get-ChildItem -LiteralPath $RepoRoot -Filter "*.ps1" -Recurse -File | Where-Object { $_.FullName -notlike "*\.git\*" -and $_.FullName -notlike "*\node_modules\*" -and $_.FullName -notlike "*\.venv\*" -and $_.FullName -notlike "*\dist\*" }
    foreach ($File in $PowerShellFiles) {
        $Tokens = $null; $Errors = $null
        [System.Management.Automation.Language.Parser]::ParseFile($File.FullName, [ref]$Tokens, [ref]$Errors) | Out-Null
        if ($Errors -and $Errors.Count -gt 0) { $ParseErrors += [pscustomobject]@{ file = $File.FullName; errors = ($Errors | ForEach-Object { $_.Message }) } }
    }
    $ParseErrors | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $AuditRoot "powershell-parse.json") -Encoding UTF8
    if ($ParseErrors.Count -gt 0) { throw "PowerShell parse errors detected" }
    Add-Check -Name "PowerShell parse" -Status "PASS" -Detail "No parse errors"
} catch {
    Add-Check -Name "PowerShell parse" -Status "FAIL" -Detail "powershell-parse.json"
    Add-Finding -Severity "high" -Area "PowerShell" -Message $_.Exception.Message -Recommendation "Review powershell-parse.json."
}

$PythonForJson = Get-PythonCommand
if ($null -eq $PythonForJson) {
    Add-Check -Name "JSON validity" -Status "WARN" -Detail "Python not found; JSON validity skipped"
    Add-Finding -Severity "medium" -Area "JSON" -Message "Python was not available for robust JSON validation." -Recommendation "Install Python or run backend setup before auditing."
} else {
    $JsonErrors = @()
    $JsonFiles = Get-ChildItem -LiteralPath $RepoRoot -Filter "*.json" -Recurse -File | Where-Object { $_.FullName -notlike "*\.git\*" -and $_.FullName -notlike "*\node_modules\*" -and $_.FullName -notlike "*\.venv\*" -and $_.FullName -notlike "*\dist\*" -and $_.FullName -notlike "*\.trace-runs\*" }
    foreach ($File in $JsonFiles) { $ErrorText = Test-JsonWithPython -PythonCommand $PythonForJson -JsonPath $File.FullName; if ($ErrorText) { $JsonErrors += [pscustomobject]@{ file = $File.FullName; error = $ErrorText } } }
    $JsonErrors | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $AuditRoot "json-validity.json") -Encoding UTF8
    if ($JsonErrors.Count -eq 0) { Add-Check -Name "JSON validity" -Status "PASS" -Detail "All JSON parsed" } else { Add-Check -Name "JSON validity" -Status "FAIL" -Detail "json-validity.json"; Add-Finding -Severity "high" -Area "JSON" -Message "Invalid JSON files detected" -Recommendation "Review json-validity.json." }
}

$SecretHits = @()
$SecretPatterns = @("BEGIN RSA PRIVATE KEY", "BEGIN OPENSSH PRIVATE KEY", "ghp_", "xoxb-", "xoxa-", "AKIA", "client_secret", "password=", "token=")
foreach ($File in $Files) {
    if ($File.FullName -eq $ScriptPath) { continue }
    if ($File.Length -gt 1048576) { continue }
    if ($File.Extension -in @(".png", ".jpg", ".jpeg", ".gif", ".ico", ".zip")) { continue }
    $Text = Get-Content -LiteralPath $File.FullName -Raw -ErrorAction SilentlyContinue
    foreach ($Pattern in $SecretPatterns) { if ($Text -like "*$Pattern*") { $SecretHits += [pscustomobject]@{ file = $File.FullName; pattern = $Pattern } } }
}
$SecretHits | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $AuditRoot "secret-scan.json") -Encoding UTF8
if ($SecretHits.Count -eq 0) { Add-Check -Name "Secret scan" -Status "PASS" -Detail "No obvious patterns" } else { Add-Check -Name "Secret scan" -Status "WARN" -Detail "$($SecretHits.Count) potential hits"; Add-Finding -Severity "medium" -Area "Secret scan" -Message "$($SecretHits.Count) potential hits found." -Recommendation "Review secret-scan.json manually." }

$GitignoreText = Get-Content -LiteralPath (Join-Path $RepoRoot ".gitignore") -Raw -Encoding UTF8
$MissingIgnore = @()
foreach ($Pattern in @(".trace-runs/", "backend/.trace-runs/", "node_modules/", "frontend/dist/", "*.zip")) { if ($GitignoreText -notlike "*$Pattern*") { $MissingIgnore += $Pattern } }
if ($MissingIgnore.Count -eq 0) { Add-Check -Name "Gitignore protections" -Status "PASS" -Detail "Required patterns found" } else { Add-Check -Name "Gitignore protections" -Status "FAIL" -Detail ($MissingIgnore -join ", "); Add-Finding -Severity "high" -Area "Git hygiene" -Message "Missing ignore patterns: $($MissingIgnore -join ', ')" -Recommendation "Update .gitignore." }

if (-not $SkipBackend) {
    $VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $VenvPython)) { $Python = Get-PythonCommand; if ($null -eq $Python) { Add-Check -Name "Create backend venv" -Status "FAIL" -Detail "Python not found"; Add-Finding -Severity "high" -Area "Backend" -Message "Python was not found." -Recommendation "Install Python or add it to PATH." } else { Run-External -Name "Create backend venv" -WorkingDirectory $BackendDir -Executable $Python -Arguments @("-m", "venv", ".venv") -LogFile "backend-venv.txt" } }
    if (Test-Path -LiteralPath $VenvPython) {
        if (-not $NoInstall) { Run-External -Name "Install backend dependencies" -WorkingDirectory $BackendDir -Executable $VenvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip") -LogFile "backend-pip-upgrade.txt"; Run-External -Name "Install backend requirements" -WorkingDirectory $BackendDir -Executable $VenvPython -Arguments @("-m", "pip", "install", "-r", "requirements.txt") -LogFile "backend-install.txt" }
        Run-External -Name "Backend compileall" -WorkingDirectory $BackendDir -Executable $VenvPython -Arguments @("-m", "compileall", "app", "tests") -LogFile "backend-compileall.txt"
        Run-External -Name "Backend pytest" -WorkingDirectory $BackendDir -Executable $VenvPython -Arguments @("-m", "pytest") -LogFile "backend-pytest.txt"
    }
} else { Add-Check -Name "Backend checks" -Status "SKIP" -Detail "Skipped by parameter" }

if (-not $SkipFrontend) {
    $NpmCommand = Get-NpmCommand
    if ($null -eq $NpmCommand) { Add-Check -Name "Frontend prerequisites" -Status "FAIL" -Detail "npm not found"; Add-Finding -Severity "high" -Area "Frontend" -Message "npm was not found." -Recommendation "Install Node.js or add npm to PATH." }
    else {
        if (-not $NoInstall -and -not (Test-Path -LiteralPath (Join-Path $FrontendDir "node_modules"))) { Run-External -Name "Install frontend dependencies" -WorkingDirectory $FrontendDir -Executable "cmd.exe" -Arguments @("/c", "npm", "install") -LogFile "frontend-install.txt" }
        Run-External -Name "Frontend test/typecheck" -WorkingDirectory $FrontendDir -Executable "cmd.exe" -Arguments @("/c", "npm", "test") -LogFile "frontend-test.txt"
        Run-External -Name "Frontend build" -WorkingDirectory $FrontendDir -Executable "cmd.exe" -Arguments @("/c", "npm", "run", "build") -LogFile "frontend-build.txt"
    }
} else { Add-Check -Name "Frontend checks" -Status "SKIP" -Detail "Skipped by parameter" }

try {
    $SmokeLog = Join-Path $AuditRoot "collector-sample-smoke.txt"
    $Scenarios = @("account-disabled", "missing-license", "service-plan-disabled", "guest-b2b-access-failure", "ca-details-missing", "ca-device-noncompliant", "mfa-requirement-not-satisfied", "no-recent-signin-evidence", "successful-access-baseline")
    $SmokeOutput = @()
    foreach ($Scenario in $Scenarios) { $JsonText = (& (Join-Path $CollectorDir "Invoke-TraceM365AccessScan.ps1") -UserPrincipalName "sample.user@contoso.invalid" -AffectedService "Microsoft 365 general access" -Scenario $Scenario -UseSampleData:$true | Out-String); $Result = $JsonText | ConvertFrom-Json -ErrorAction Stop; if ($Result.scenario_id -ne $Scenario) { throw "Scenario $Scenario returned scenario_id '$($Result.scenario_id)'" }; if ($Result.module -ne "m365-access-path-analyzer") { throw "Scenario $Scenario returned unexpected module '$($Result.module)'" }; $SmokeOutput += "$Scenario OK" }
    $SmokeOutput | Set-Content -LiteralPath $SmokeLog -Encoding UTF8
    Add-Check -Name "Collector sample smoke" -Status "PASS" -Detail "collector-sample-smoke.txt"
} catch { Add-Check -Name "Collector sample smoke" -Status "FAIL" -Detail $_.Exception.Message; Add-Finding -Severity "high" -Area "Collector" -Message $_.Exception.Message -Recommendation "Review collector sample scenarios." }

$Readme = Get-Content -LiteralPath (Join-Path $RepoRoot "README.md") -Raw -Encoding UTF8
$MissingTerms = @()
foreach ($Term in @("Access Evidence Analyzer", "generic_access_log_text", "entra_signin_csv", "resource_assignment_json", "POST /api/logs/analyze", "not a SIEM")) { if ($Readme -notlike "*$Term*") { $MissingTerms += $Term } }
if ($MissingTerms.Count -eq 0) { Add-Check -Name "README consistency" -Status "PASS" -Detail "Expected terms found" } else { Add-Check -Name "README consistency" -Status "WARN" -Detail ($MissingTerms -join ", "); Add-Finding -Severity "medium" -Area "Documentation" -Message "README is missing expected terms." -Recommendation "Refresh README." }

$FailCount = @($Checks | Where-Object { $_.status -eq "FAIL" }).Count
$WarnCount = @($Checks | Where-Object { $_.status -eq "WARN" }).Count
$Head = git -C $RepoRoot rev-parse HEAD
$Branch = git -C $RepoRoot branch --show-current
$Summary = [pscustomobject]@{ generated_at = (Get-Date).ToString("o"); repo_root = $RepoRoot; branch = $Branch; head = $Head; fail_count = $FailCount; warn_count = $WarnCount; checks = $Checks; findings = $Findings }
$Summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $AuditRoot "audit-summary.json") -Encoding UTF8

$Report = @("# TRACE Local Code Audit", "", "- Generated: $($Summary.generated_at)", "- Repository: $RepoRoot", "- Branch: $Branch", "- HEAD: $Head", "- Failures: $FailCount", "- Warnings: $WarnCount", "", "## Checks")
foreach ($Check in $Checks) { $Report += "- $($Check.status) - $($Check.name): $($Check.detail)" }
$Report += ""; $Report += "## Findings"
if ($Findings.Count -eq 0) { $Report += "No findings were recorded by the audit script." } else { foreach ($Finding in $Findings) { $Report += "### $($Finding.severity) - $($Finding.area)"; $Report += $Finding.message; $Report += "Recommendation: $($Finding.recommendation)" } }
$Report | Set-Content -LiteralPath (Join-Path $AuditRoot "audit-report.md") -Encoding UTF8

Complete-AuditArchive -FolderPath $AuditRoot -ArchivePath $ZipPath

Write-Host ""
Write-Host "TRACE local code audit complete." -ForegroundColor Green
Write-Host "Audit folder: $AuditRoot"
Write-Host "Audit ZIP:    $ZipPath"
Write-Host "Failures:     $FailCount"
Write-Host "Warnings:     $WarnCount"

if ($FailCount -gt 0) { exit 1 }
exit 0
