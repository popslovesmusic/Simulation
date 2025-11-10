# Run DASE mission from JSON file
# Usage: .\run_mission.ps1 mission_short_fixed.json

param(
    [Parameter(Mandatory=$true)]
    [string]$JsonFile
)

if (-not (Test-Path $JsonFile)) {
    Write-Error "File not found: $JsonFile"
    exit 1
}

Get-Content $JsonFile -Raw | .\dase_cli.exe
