[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Save)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
& (Join-Path $repoRoot 'build\local\laya-venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'alien-command-budget.py') --save $Save
if ($LASTEXITCODE -ne 0) { throw 'Budget audit failed.' }
