# Portable convenience launcher; no installation or environment changes.
$ErrorActionPreference = 'Stop'
foreach ($dockerBin in @((Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin'), 'C:\Program Files\Docker\Docker\resources\bin')) {
    if (Test-Path (Join-Path $dockerBin 'docker.exe')) {
        $env:PATH = "$dockerBin;$env:PATH"
        break
    }
}
$candidates = @('python', 'python3', (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'))
foreach ($candidate in $candidates) {
    try {
        $null = & $candidate --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            & $candidate (Join-Path $PSScriptRoot 'ghostmaintainer.py') @args
            exit $LASTEXITCODE
        }
    } catch { continue }
}
throw 'Python 3.11+ is required.'
