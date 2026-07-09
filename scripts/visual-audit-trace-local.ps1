param(
    [switch]$NoInstall,
    [switch]$SkipBackendStart,
    [switch]$SkipFrontendStart
)

$ErrorActionPreference = "Stop"

$ScriptPath = $PSCommandPath
if (-not $ScriptPath) { $ScriptPath = $MyInvocation.MyCommand.Path }
$ScriptDir = Split-Path -Parent $ScriptPath
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$BackendDir = Join-Path $RepoRoot "backend"
$FrontendDir = Join-Path $RepoRoot "frontend"
$RunnerSource = Join-Path $RepoRoot "scripts\trace-visual-audit-runner.mjs"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$AuditRoot = Join-Path (Join-Path $HOME "Downloads") "TRACE_UI_VISUAL_AUDIT_$Timestamp"
$ZipPath = "$AuditRoot.zip"
$BackendUrl = "http://127.0.0.1:8000/api/health"
$FrontendUrl = "http://127.0.0.1:5173"
$Checks = @()
$Findings = @()
$BackendProcess = $null
$FrontendProcess = $null
$ExitCode = 0

function Write-Step { param([string]$Message) Write-Host "[TRACE VISUAL AUDIT] $Message" -ForegroundColor Cyan }
function Add-Check { param([string]$Name, [string]$Status, [string]$Detail) $script:Checks += [pscustomobject]@{ name = $Name; status = $Status; detail = $Detail } }
function Add-Finding { param([string]$Severity, [string]$Area, [string]$Message, [string]$Recommendation) $script:Findings += [pscustomobject]@{ severity = $Severity; area = $Area; message = $Message; recommendation = $Recommendation } }
function Command-Exists { param([string]$Name) return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue) }
function Get-PythonCommand { if (Command-Exists "py") { return "py" }; if (Command-Exists "python") { return "python" }; return $null }

function Test-Url {
    param([string]$Url)
    try {
        Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3 | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Wait-Url {
    param([string]$Name, [string]$Url, [int]$Attempts = 45)
    for ($i = 1; $i -le $Attempts; $i++) {
        if (Test-Url -Url $Url) {
            Add-Check -Name "$Name reachable" -Status "PASS" -Detail $Url
            return $true
        }
        Start-Sleep -Seconds 2
    }
    Add-Check -Name "$Name reachable" -Status "FAIL" -Detail $Url
    Add-Finding -Severity "high" -Area $Name -Message "$Url did not become reachable." -Recommendation "Review backend/frontend process logs in the visual audit ZIP."
    return $false
}

function Run-CommandLog {
    param([string]$Name, [string]$WorkingDirectory, [string]$Executable, [string[]]$Arguments, [string]$LogFile)
    Write-Step $Name
    $LogPath = Join-Path $AuditRoot $LogFile
    Push-Location $WorkingDirectory
    try {
        $Output = & $Executable @Arguments 2>&1
        $Code = $LASTEXITCODE
        $Output | Out-String | Set-Content -LiteralPath $LogPath -Encoding UTF8
        if ($Code -ne 0) {
            Add-Check -Name $Name -Status "FAIL" -Detail $LogFile
            Add-Finding -Severity "high" -Area $Name -Message "$Executable exited with code $Code." -Recommendation "Review $LogFile."
            return $false
        }
        Add-Check -Name $Name -Status "PASS" -Detail $LogFile
        return $true
    } catch {
        ($_ | Out-String) | Set-Content -LiteralPath $LogPath -Encoding UTF8
        Add-Check -Name $Name -Status "FAIL" -Detail $LogFile
        Add-Finding -Severity "high" -Area $Name -Message $_.Exception.Message -Recommendation "Review $LogFile."
        return $false
    } finally {
        Pop-Location
    }
}

function Start-OwnedProcess {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$StdOutFile,
        [string]$StdErrFile
    )
    Write-Step "Starting $Name process"
    $StdOutPath = Join-Path $AuditRoot $StdOutFile
    $StdErrPath = Join-Path $AuditRoot $StdErrFile
    $Process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory -RedirectStandardOutput $StdOutPath -RedirectStandardError $StdErrPath -PassThru -WindowStyle Hidden
    Add-Check -Name "$Name start" -Status "PASS" -Detail "Started PID $($Process.Id)"
    return $Process
}

function Stop-ProcessTree {
    param([System.Diagnostics.Process]$Process, [string]$Name)
    if ($null -eq $Process) { return }
    try {
        $Fresh = Get-Process -Id $Process.Id -ErrorAction SilentlyContinue
        if ($null -eq $Fresh) {
            Add-Check -Name "$Name cleanup" -Status "PASS" -Detail "Process already exited"
            return
        }
        Write-Step "Stopping $Name process tree PID $($Process.Id)"
        & taskkill.exe /PID $Process.Id /T /F | Out-String | Set-Content -LiteralPath (Join-Path $AuditRoot "$Name-cleanup.txt") -Encoding UTF8
        Add-Check -Name "$Name cleanup" -Status "PASS" -Detail "$Name-cleanup.txt"
    } catch {
        Add-Check -Name "$Name cleanup" -Status "WARN" -Detail $_.Exception.Message
        Add-Finding -Severity "medium" -Area "$Name cleanup" -Message $_.Exception.Message -Recommendation "Run STOP_TRACE_LOCAL.bat to clean local TRACE processes."
    }
}

function Write-SummaryFiles {
    $FailCount = @($Checks | Where-Object { $_.status -eq "FAIL" }).Count
    $WarnCount = @($Checks | Where-Object { $_.status -eq "WARN" }).Count
    $Summary = [pscustomobject]@{
        generated_at = (Get-Date).ToString("o")
        repo_root = $RepoRoot
        frontend_url = $FrontendUrl
        backend_url = $BackendUrl
        fail_count = $FailCount
        warn_count = $WarnCount
        checks = $Checks
        findings = $Findings
    }
    $Summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $AuditRoot "visual-orchestrator-summary.json") -Encoding UTF8

    $Report = @("# TRACE Visual Audit Orchestrator", "", "- Generated: $($Summary.generated_at)", "- Repository: $RepoRoot", "- Frontend URL: $FrontendUrl", "- Backend URL: $BackendUrl", "- Failures: $FailCount", "- Warnings: $WarnCount", "", "## Checks")
    foreach ($Check in $Checks) { $Report += "- $($Check.status) - $($Check.name): $($Check.detail)" }
    $Report += ""; $Report += "## Findings"
    if ($Findings.Count -eq 0) { $Report += "No findings were recorded by the visual audit orchestrator." } else { foreach ($Finding in $Findings) { $Report += "### $($Finding.severity) - $($Finding.area)"; $Report += $Finding.message; $Report += "Recommendation: $($Finding.recommendation)" } }
    $Report | Set-Content -LiteralPath (Join-Path $AuditRoot "visual-orchestrator-report.md") -Encoding UTF8
    return $FailCount
}

function New-AuditZip {
    if (Test-Path -LiteralPath $ZipPath) { Remove-Item -LiteralPath $ZipPath -Force }
    Compress-Archive -Path (Join-Path $AuditRoot "*") -DestinationPath $ZipPath -Force -ErrorAction Stop
    if (-not (Test-Path -LiteralPath $ZipPath)) { throw "Visual audit ZIP was not created: $ZipPath" }
    $ZipItem = Get-Item -LiteralPath $ZipPath
    if ($ZipItem.Length -le 0) { throw "Visual audit ZIP is empty: $ZipPath" }
}

try {
    New-Item -ItemType Directory -Force -Path $AuditRoot | Out-Null
    Write-Step "Repository: $RepoRoot"
    Write-Step "Audit folder: $AuditRoot"

    if (-not (Command-Exists "node")) {
        Add-Check -Name "Node.js" -Status "FAIL" -Detail "node not found"
        Add-Finding -Severity "high" -Area "Node.js" -Message "Node.js is required for the Playwright visual audit." -Recommendation "Install Node.js or add node to PATH."
        throw "Node.js not found."
    }
    Add-Check -Name "Node.js" -Status "PASS" -Detail "node found"

    if (-not (Command-Exists "npm")) {
        Add-Check -Name "npm" -Status "FAIL" -Detail "npm not found"
        Add-Finding -Severity "high" -Area "npm" -Message "npm is required for the Playwright visual audit." -Recommendation "Install Node.js/npm or add npm to PATH."
        throw "npm not found."
    }
    Add-Check -Name "npm" -Status "PASS" -Detail "npm found"

    $Python = Get-PythonCommand
    if ($null -eq $Python) {
        Add-Check -Name "Python" -Status "FAIL" -Detail "python not found"
        Add-Finding -Severity "high" -Area "Python" -Message "Python is required for the TRACE backend." -Recommendation "Install Python or add py/python to PATH."
        throw "Python not found."
    }
    Add-Check -Name "Python" -Status "PASS" -Detail $Python

    $VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        Run-CommandLog -Name "Create backend venv" -WorkingDirectory $BackendDir -Executable $Python -Arguments @("-m", "venv", ".venv") -LogFile "backend-venv.txt" | Out-Null
    }
    if (-not (Test-Path -LiteralPath $VenvPython)) { throw "Backend venv was not created." }

    if (-not $NoInstall) {
        Run-CommandLog -Name "Install backend requirements" -WorkingDirectory $BackendDir -Executable $VenvPython -Arguments @("-m", "pip", "install", "-r", "requirements.txt") -LogFile "backend-install.txt" | Out-Null
        if (-not (Test-Path -LiteralPath (Join-Path $FrontendDir "node_modules"))) {
            Run-CommandLog -Name "Install frontend dependencies" -WorkingDirectory $FrontendDir -Executable "cmd.exe" -Arguments @("/c", "npm", "install") -LogFile "frontend-install.txt" | Out-Null
        }
    }

    $BackendAlreadyRunning = Test-Url -Url $BackendUrl
    if ($BackendAlreadyRunning) {
        Add-Check -Name "Backend start" -Status "PASS" -Detail "Already running at $BackendUrl; visual audit will not stop operator-owned process"
    } elseif (-not $SkipBackendStart) {
        $BackendProcess = Start-OwnedProcess -Name "Backend" -WorkingDirectory $BackendDir -FilePath $VenvPython -Arguments @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") -StdOutFile "backend-process.out.log" -StdErrFile "backend-process.err.log"
    }

    $FrontendAlreadyRunning = Test-Url -Url $FrontendUrl
    if ($FrontendAlreadyRunning) {
        Add-Check -Name "Frontend start" -Status "PASS" -Detail "Already running at $FrontendUrl; visual audit will not stop operator-owned process"
    } elseif (-not $SkipFrontendStart) {
        $FrontendProcess = Start-OwnedProcess -Name "Frontend" -WorkingDirectory $FrontendDir -FilePath "cmd.exe" -Arguments @("/c", "npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173") -StdOutFile "frontend-process.out.log" -StdErrFile "frontend-process.err.log"
    }

    $BackendReady = Wait-Url -Name "Backend" -Url $BackendUrl
    $FrontendReady = Wait-Url -Name "Frontend" -Url $FrontendUrl
    if (-not ($BackendReady -and $FrontendReady)) { throw "Backend or frontend was not reachable." }

    $RunnerDir = Join-Path $AuditRoot "playwright-runner"
    New-Item -ItemType Directory -Force -Path $RunnerDir | Out-Null
    Copy-Item -LiteralPath $RunnerSource -Destination (Join-Path $RunnerDir "trace-visual-audit-runner.mjs") -Force
    '{"type":"module","dependencies":{"playwright":"^1.55.0"}}' | Set-Content -LiteralPath (Join-Path $RunnerDir "package.json") -Encoding UTF8

    if (-not $NoInstall) {
        Run-CommandLog -Name "Install Playwright package" -WorkingDirectory $RunnerDir -Executable "cmd.exe" -Arguments @("/c", "npm", "install", "--silent") -LogFile "playwright-install.txt" | Out-Null
        Run-CommandLog -Name "Install Playwright Chromium" -WorkingDirectory $RunnerDir -Executable "cmd.exe" -Arguments @("/c", "npx", "playwright", "install", "chromium") -LogFile "playwright-install-chromium.txt" | Out-Null
    }

    Write-Step "Running Playwright visual audit"
    $env:TRACE_UI_AUDIT_ROOT = $AuditRoot
    $env:TRACE_FRONTEND_URL = $FrontendUrl
    $PlaywrightOk = Run-CommandLog -Name "Run Playwright visual audit" -WorkingDirectory $RunnerDir -Executable "node" -Arguments @("trace-visual-audit-runner.mjs") -LogFile "playwright-run.txt"
    if (-not $PlaywrightOk) { $ExitCode = 1 }
} catch {
    $ExitCode = 1
    Add-Check -Name "Visual audit fatal error" -Status "FAIL" -Detail "fatal-error.txt"
    Add-Finding -Severity "high" -Area "Visual audit" -Message $_.Exception.Message -Recommendation "Review fatal-error.txt and service logs."
    $_ | Out-String | Set-Content -LiteralPath (Join-Path $AuditRoot "fatal-error.txt") -Encoding UTF8
} finally {
    Stop-ProcessTree -Process $BackendProcess -Name "Backend"
    Stop-ProcessTree -Process $FrontendProcess -Name "Frontend"

    $FailCount = Write-SummaryFiles
    if ($FailCount -gt 0) { $ExitCode = 1 }

    try {
        New-AuditZip
        Write-Host ""
        Write-Host "TRACE visual UI audit complete." -ForegroundColor Green
        Write-Host "Audit folder: $AuditRoot"
        Write-Host "Audit ZIP:    $ZipPath"
        Write-Host "Failures:     $FailCount"
    } catch {
        Write-Host "Visual audit ZIP creation failed: $($_.Exception.Message)" -ForegroundColor Red
        $ExitCode = 1
    }
}

exit $ExitCode
