param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$ScriptPath = $PSCommandPath
if (-not $ScriptPath) { $ScriptPath = $MyInvocation.MyCommand.Path }
$ScriptDir = Split-Path -Parent $ScriptPath
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$Ports = @(8000, 5173)
$ExitCode = 0

function Write-Step {
    param([string]$Message)
    Write-Host "[TRACE STOP] $Message" -ForegroundColor Cyan
}

function Get-ListeningPidForPort {
    param([int]$Port)
    $Rows = netstat -ano -p tcp | Select-String -Pattern ":$Port\s+.*LISTENING\s+(\d+)"
    $Pids = @()
    foreach ($Row in $Rows) {
        if ($Row.Matches.Count -gt 0) {
            $Pids += [int]$Row.Matches[0].Groups[1].Value
        }
    }
    return @($Pids | Sort-Object -Unique)
}

function Get-ProcessCommandLine {
    param([int]$Pid)
    try {
        $Proc = Get-CimInstance Win32_Process -Filter "ProcessId=$Pid" -ErrorAction Stop
        return [string]$Proc.CommandLine
    } catch {
        return ""
    }
}

function Test-TraceOwnedProcess {
    param([int]$Pid)
    $CommandLine = Get-ProcessCommandLine -Pid $Pid
    $Lower = $CommandLine.ToLowerInvariant()
    $RepoLower = $RepoRoot.ToLowerInvariant()
    if ($Force) { return $true }
    if ($Lower.Contains($RepoLower)) { return $true }
    if ($Lower.Contains("uvicorn") -and $Lower.Contains("app.main:app")) { return $true }
    if ($Lower.Contains("vite") -and $Lower.Contains("5173")) { return $true }
    if ($Lower.Contains("npm") -and $Lower.Contains("run") -and $Lower.Contains("dev")) { return $true }
    return $false
}

function Stop-ProcessTree {
    param([int]$Pid)
    Write-Step "Stopping PID $Pid and child process tree"
    & taskkill.exe /PID $Pid /T /F | Out-String | Write-Host
}

Write-Step "Repository: $RepoRoot"
foreach ($Port in $Ports) {
    $Pids = @(Get-ListeningPidForPort -Port $Port)
    if ($Pids.Count -eq 0) {
        Write-Step "No process is listening on port $Port"
        continue
    }

    foreach ($Pid in $Pids) {
        $CommandLine = Get-ProcessCommandLine -Pid $Pid
        Write-Step "Port $Port is owned by PID $Pid"
        if ($CommandLine) {
            Write-Host "Command line: $CommandLine"
        } else {
            Write-Host "Command line: unavailable"
        }

        if (Test-TraceOwnedProcess -Pid $Pid) {
            try {
                Stop-ProcessTree -Pid $Pid
            } catch {
                Write-Host "Failed to stop PID $Pid: $($_.Exception.Message)" -ForegroundColor Red
                $ExitCode = 1
            }
        } else {
            Write-Host "Skipped PID $Pid because it does not look TRACE-owned. Re-run with -Force to stop it anyway." -ForegroundColor Yellow
            $ExitCode = 1
        }
    }
}

Start-Sleep -Milliseconds 500
foreach ($Port in $Ports) {
    $Remaining = @(Get-ListeningPidForPort -Port $Port)
    if ($Remaining.Count -eq 0) {
        Write-Step "Port $Port is clear"
    } else {
        Write-Host "Port $Port is still in use by PID(s): $($Remaining -join ', ')" -ForegroundColor Yellow
        $ExitCode = 1
    }
}

exit $ExitCode
