[CmdletBinding()]
param(
    [ValidateSet('UFO', 'TFTD')][string]$Game = 'UFO',
    [switch]$Audit,
    [switch]$ModelAudit,
    [switch]$ModelExecute,
    [switch]$Portfolio,
    [string]$Checkpoint = 'C:\Users\Main PC 2\AppData\Local\Temp\uppward-v4',
    [ValidateRange(1,65535)][int]$ModelPort = 18867
)
$ErrorActionPreference = 'Stop'
if ($ModelExecute) { $ModelAudit = $true }
if ($Portfolio) { $ModelAudit = $true; $ModelExecute = $false }
$repoRoot = Split-Path -Parent $PSScriptRoot
$localRoot = Join-Path $repoRoot 'build\local'
$runtimeRoot = Join-Path $localRoot 'runtime'
$executable = Join-Path $runtimeRoot 'OpenXcom.exe'
$userRoot = Join-Path $localRoot 'user'
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    throw 'Run scripts\setup-local.ps1 first to build and stage the development runtime.'
}
New-Item -ItemType Directory -Path $userRoot -Force | Out-Null
$master = if ($Game -eq 'TFTD') { 'xcom2' } else { 'xcom1' }
$auditEnabled = if ($Audit -or $ModelAudit) { 'true' } else { 'false' }
$service = $null
try {
    if ($ModelAudit) {
        $health = $null
        try { $health = Invoke-RestMethod "http://127.0.0.1:$ModelPort/healthz" -TimeoutSec 2 } catch {}
        if ($health -and ($health.protocol -ne 'alien-recon-laya-v2' -or $health.checkpointSha256 -ne 'bcbb891d21cf081a9d7a941b97f8b0f10cf3dac7473b4b9450fab0d07b885175')) {
            throw 'The selected port is occupied by a different model service.'
        }
        if (-not $health) {
            $python = Join-Path $localRoot 'laya-venv\Scripts\python.exe'
            if (-not (Test-Path -LiteralPath $python)) { throw 'Run scripts\setup-alien-command-model.ps1 first.' }
            $modelScript = Join-Path $PSScriptRoot 'alien-command-model.py'
            $modelArguments = @('-u', ('"' + $modelScript + '"'), '--checkpoint', ('"' + $Checkpoint + '"'), '--port', "$ModelPort")
            $service = Start-Process -FilePath $python -ArgumentList $modelArguments -WindowStyle Hidden -RedirectStandardOutput (Join-Path $localRoot 'model-service-launch.log') -RedirectStandardError (Join-Path $localRoot 'model-service-launch-errors.log') -PassThru
            Write-Output 'Loading the local career-trained classifier for shadow comparison...'
            $deadline = (Get-Date).AddSeconds(120)
            while ((Get-Date) -lt $deadline) {
                if ($service.HasExited) { throw 'Model startup failed. See build\local\model-service-launch-errors.log.' }
                try { $health = Invoke-RestMethod "http://127.0.0.1:$ModelPort/healthz" -TimeoutSec 1; break } catch {}
                Start-Sleep -Milliseconds 500
            }
            if (-not $health) { throw 'Model startup timed out.' }
        }
        if ($Portfolio -and ($health.portfolioProtocol -ne 'alien-strategy-laya-v2' -or $health.portfolioPromptVersion -ne 'search-evidence-v5')) { throw 'Portfolio mode needs the updated search-evidence service. Close the earlier game/service session and launch again.' }
        if ($Portfolio) { Write-Output 'Monthly commander enabled: previous-month sitrep, strategy, then up to three funded operations or saved resources. Routine monthly scripts are replaced; searches do not auto-assault.' }
        elseif ($ModelExecute) { Write-Output "Model execution enabled for monthly recon: contact gathering or retaliation base search. Discovery can lead to a base assault." }
        else { Write-Output "Model ready on $($health.device); learned proposals remain shadow-only." }
    }
    $port = if ($ModelAudit) { $ModelPort } else { 0 }
    $gameArguments = @('-data', ('"' + $runtimeRoot + '"'), '-user', ('"' + $userRoot + '"'), '-config', ('"' + $userRoot + '"'),
        '-master', $master, '-alienCommandAudit', $auditEnabled, '-alienCommandModelPort', "$port",
        '-alienCommandModelExecute', $(if ($ModelExecute) { 'true' } else { 'false' }),
        '-alienCommandPortfolio', $(if ($Portfolio) { 'true' } else { 'false' }))
    # Explicitly wait for the GUI process so its owned classifier lives for the game session.
    $gameProcess = Start-Process -FilePath $executable -ArgumentList $gameArguments -Wait -PassThru
    if ($gameProcess.ExitCode -ne 0) { throw "Game exited with code $($gameProcess.ExitCode)." }
}
finally {
    if ($service -and -not $service.HasExited) {
        # The Windows venv launcher can spawn a Python child. Stop only this owned tree.
        $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$($service.Id)" -ErrorAction SilentlyContinue)
        foreach ($child in $children) { Stop-Process -Id $child.ProcessId -ErrorAction SilentlyContinue }
        if (-not $service.HasExited) { Stop-Process -Id $service.Id -ErrorAction SilentlyContinue }
    }
}
