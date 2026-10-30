$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
foreach ($dockerBin in @((Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin'), 'C:\Program Files\Docker\Docker\resources\bin')) {
    if (Test-Path (Join-Path $dockerBin 'docker.exe')) { $env:PATH = "$dockerBin;$env:PATH"; break }
}
foreach ($candidate in @('python', 'python3', (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'))) {
    try { $null = & $candidate --version 2>&1 } catch { continue }
    if ($LASTEXITCODE -eq 0) {
        Write-Host 'Open http://127.0.0.1:8765 in your browser. Press Ctrl+C to stop.'
        & $candidate (Join-Path $PSScriptRoot 'app.py')
        exit $LASTEXITCODE
    }
}
throw 'Install Python 3.11+ first.'
