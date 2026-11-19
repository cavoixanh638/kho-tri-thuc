$ErrorActionPreference = 'Stop'
$ktRuntimeRoot = Join-Path $env:LOCALAPPDATA 'KhoTriThuc'
$ktConfigPath = Join-Path $ktRuntimeRoot 'runtime\config.json'
if (-not (Test-Path -LiteralPath $ktConfigPath)) { throw 'Run launch.py setup first.' }
$ktToolRoot = Join-Path $ktRuntimeRoot 'tools'
$ktArchive = Join-Path $ktToolRoot 'ffmpeg-9.0.2-essentials.zip'
$ktInstall = Join-Path $ktToolRoot 'ffmpeg-9.0.2'
$ktHash = '60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba'
$ktUri = 'https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.zip'
New-Item -ItemType Directory -Path $ktToolRoot -Force | Out-Null
if (-not (Test-Path -LiteralPath $ktArchive)) {
    Invoke-WebRequest -Uri $ktUri -OutFile $ktArchive -TimeoutSec 180
}
if ((Get-FileHash -LiteralPath $ktArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ktHash) {
    throw 'FFmpeg archive checksum mismatch. The archive was not executed.'
}
if (-not (Test-Path -LiteralPath $ktInstall)) {
    Expand-Archive -LiteralPath $ktArchive -DestinationPath $ktInstall
}
$ktBin = Join-Path $ktInstall 'ffmpeg-9.0.2-essentials_build\bin'
$ktFfmpeg = Join-Path $ktBin 'ffmpeg.exe'
$ktFfprobe = Join-Path $ktBin 'ffprobe.exe'
foreach ($ktBinary in @($ktFfmpeg, $ktFfprobe)) {
    if (-not (Test-Path -LiteralPath $ktBinary)) { throw 'FFmpeg package layout was unexpected.' }
}
$ktVersionOutput = & $ktFfprobe -v error -version
if ($LASTEXITCODE -ne 0) { throw 'ffprobe did not start.' }
Write-Output ($ktVersionOutput | Select-Object -First 1)
$ktConfig = Get-Content -LiteralPath $ktConfigPath -Raw | ConvertFrom-Json
$ktConfig.environment | Add-Member -NotePropertyName FFMPEG_BINARY -NotePropertyValue $ktFfmpeg -Force
$ktConfig.environment | Add-Member -NotePropertyName FFPROBE_BINARY -NotePropertyValue $ktFfprobe -Force
$ktPending = Join-Path $ktRuntimeRoot 'runtime\config.ffmpeg-pending'
$ktJson = $ktConfig | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($ktPending, $ktJson, [System.Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $ktPending -Destination $ktConfigPath -Force
Write-Output 'FFmpeg and ffprobe configured. Restart the API and worker.'
