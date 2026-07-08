param(
    [ValidateSet("All", "Backend", "Frontend", "Check")]
    [string]$Mode = "All",

    [switch]$NoInstall
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
$RunStore = Join-Path $RepoRoot ".trace-runs\access-evidence"
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"

function Write-Step {
    param([string]$Message)
    Write-Host "[TRACE] $Message" -ForegroundColor Cyan
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[TRACE] WARNING: $Message" -ForegroundColor Yellow
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

function Ensure-BackendReady {
    if (-not (Test-Path $BackendDir)) {
        throw "Backend folder not found: $BackendDir"
    }

    if (-not (Test-Path $VenvPython)) {
        Write-Step "Creating backend virtual environment"
        Push-Location $BackendDir
        try {
            Invoke-SystemPython @("-m", "venv", ".venv")
        }
        finally {
            Pop-Location
        }
    }

    if (-not $NoInstall) {
        Write-Step "Installing backend dependencies"
        Push-Location $BackendDir
        try {
            & $VenvPython -m pip install --upgrade pip
            if (Test-Path (Join-Path $BackendDir "requirements.txt")) {
                & $VenvPython -m pip install -r requirements.txt
            }
        }
        finally {
            Pop-Location
        }
    }
}

function Ensure-FrontendReady {
    if (-not (Test-Path $FrontendDir)) {
        throw "Frontend folder not found: $FrontendDir"
    }

    if (-not (Test-CommandExists "npm")) {
        throw "npm was not found. Install Node.js or make sure npm is available in PATH."
    }

    if (-not $NoInstall -and -not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
        Write-Step "Installing frontend dependencies"
        Push-Location $FrontendDir
        try {
            npm install
        }
        finally {
            Pop-Location
        }
    }
}

function Start-Backend {
    Ensure-BackendReady
    New-Item -ItemType Directory -Force -Path $RunStore | Out-Null
    $env:TRACE_ACCESS_RUN_STORE = $RunStore

    Write-Step "Starting backend at http://127.0.0.1:8000"
    Write-Step "API docs: http://127.0.0.1:8000/docs"
    Push-Location $BackendDir
    try {
        & $VenvPython -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    }
    finally {
        Pop-Location
    }
}

function Start-Frontend {
    Ensure-FrontendReady

    Write-Step "Starting frontend at http://127.0.0.1:5173"
    Push-Location $FrontendDir
    try {
        npm run dev -- --host 127.0.0.1 --port 5173
    }
    finally {
        Pop-Location
    }
}

function Test-LocalSetup {
    Write-Step "Repo root: $RepoRoot"
    Write-Step "Backend: $BackendDir"
    Write-Step "Frontend: $FrontendDir"

    if (Test-CommandExists "py") {
        Write-Step "Python launcher found: py"
    }
    elseif (Test-CommandExists "python") {
        Write-Step "Python found: python"
    }
    else {
        Write-Warn "Python was not found in PATH."
    }

    if (Test-CommandExists "npm") {
        Write-Step "npm found"
    }
    else {
        Write-Warn "npm was not found in PATH."
    }

    if (Test-Path $VenvPython) {
        Write-Step "Backend virtual environment exists"
    }
    else {
        Write-Warn "Backend virtual environment does not exist yet. It will be created when starting the backend."
    }

    if (Test-Path (Join-Path $FrontendDir "node_modules")) {
        Write-Step "Frontend node_modules exists"
    }
    else {
        Write-Warn "Frontend dependencies are not installed yet. They will be installed when starting the frontend."
    }
}

switch ($Mode) {
    "Check" {
        Test-LocalSetup
    }
    "Backend" {
        Start-Backend
    }
    "Frontend" {
        Start-Frontend
    }
    "All" {
        Test-LocalSetup
        Write-Step "Opening backend and frontend in separate PowerShell windows"
        Start-Process powershell.exe -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-File", $ScriptPath, "-Mode", "Backend")
        Start-Process powershell.exe -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-File", $ScriptPath, "-Mode", "Frontend")
        Write-Step "Open the app at http://127.0.0.1:5173"
        Write-Step "Open backend docs at http://127.0.0.1:8000/docs"
    }
}
