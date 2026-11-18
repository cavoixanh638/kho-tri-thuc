$ErrorActionPreference = 'Stop'
$ktRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'KhoTriThuc'))
$ktRuntime = Join-Path $ktRoot 'runtime'
$ktState = Join-Path $ktRuntime 'processes.json'
$ktPython = Join-Path $ktRoot 'venv/Scripts/python.exe'
if (Test-Path -LiteralPath $ktState) {
    $ktProcesses = Get-Content -LiteralPath $ktState -Raw | ConvertFrom-Json
    foreach ($ktEntry in $ktProcesses) {
        $ktProcess = Get-CimInstance Win32_Process -Filter ("ProcessId = " + [int]$ktEntry.pid)
        if (-not $ktProcess) { continue }
        if ($ktProcess.ExecutablePath -ine $ktPython) {
            throw "Process identity changed. Inspect PID $($ktEntry.pid) before stopping."
        }
        $ktMarker = if ($ktEntry.name -eq 'worker') { 'manage.py run_worker' } else { '-m waitress ' }
        if (-not $ktProcess.CommandLine.Contains($ktMarker)) {
            throw "Unexpected process command for PID $($ktEntry.pid)."
        }
        Stop-Process -Id ([int]$ktEntry.pid) -ErrorAction Stop
    }
    $ktResolved = (Resolve-Path -LiteralPath $ktState).Path
    if ([IO.Path]::GetDirectoryName($ktResolved) -ine $ktRuntime) { throw 'Unexpected process-state path' }
    Remove-Item -LiteralPath $ktResolved -Force
}
$ktPgData = Join-Path $ktRuntime 'pgdata'
if (Test-Path -LiteralPath (Join-Path $ktPgData 'PG_VERSION')) {
    if ((Get-Content -LiteralPath (Join-Path $ktPgData 'PG_VERSION') -Raw).Trim() -ne '18') {
        throw 'Expected the application PostgreSQL 18 cluster.'
    }
    & 'C:/Program Files/PostgreSQL/18/bin/pg_ctl.exe' -D $ktPgData status | Out-Null
    if ($LASTEXITCODE -eq 0) {
        & 'C:/Program Files/PostgreSQL/18/bin/pg_ctl.exe' -D $ktPgData -w -t 30 stop -m fast
        if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL did not stop successfully' }
    }
}
Write-Output 'Kho Tri Thuc stopped.'
