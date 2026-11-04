$ErrorActionPreference = "Stop"
& python (Join-Path $PSScriptRoot "replay_518.py") @args
exit $LASTEXITCODE
