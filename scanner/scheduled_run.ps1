# EGX Scanner — Scheduled Run
# Runs the scanner with proper env loading + logging.
# Triggered by Windows Task Scheduler.

$ErrorActionPreference = "Continue"
$scannerDir = "D:\General Projects\stock-market\scanner"
$logsDir = Join-Path $scannerDir "logs"
$logFile = Join-Path $logsDir ("scanner_{0}.log" -f (Get-Date -Format "yyyy-MM-dd"))

# Ensure logs dir exists
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

# Force UTF-8 for Arabic output
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$startTime = Get-Date
$header = @"

================================================================
 EGX Scanner started at: $($startTime.ToString("yyyy-MM-dd HH:mm:ss"))
================================================================
"@

Add-Content -Path $logFile -Value $header -Encoding utf8

# Run the scanner — output goes both to console (if visible) and log file
Set-Location $scannerDir
$pythonExe = Join-Path $scannerDir ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Add-Content -Path $logFile -Value "ERROR: venv not found at $pythonExe" -Encoding utf8
    exit 1
}

# Stream output to log file
& $pythonExe "main.py" "--min-score" "20" 2>&1 | Tee-Object -FilePath $logFile -Append

$exitCode = $LASTEXITCODE
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

$footer = @"
----------------------------------------------------------------
 Finished at: $($endTime.ToString("yyyy-MM-dd HH:mm:ss"))
 Duration:    $([int]$duration) seconds
 Exit code:   $exitCode
================================================================

"@
Add-Content -Path $logFile -Value $footer -Encoding utf8

# Cleanup: keep only last 30 log files
Get-ChildItem -Path $logsDir -Filter "scanner_*.log" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip 30 |
    Remove-Item -Force -ErrorAction SilentlyContinue

exit $exitCode
