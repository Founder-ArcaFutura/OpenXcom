[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Save,
    [ValidateSet('UFO','TFTD')][string]$Game = 'UFO',
    [switch]$Launch,
    [switch]$NormalVision,
    [switch]$Defend
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $repoRoot 'build\local\runtime'
$source = Get-Item -LiteralPath $Save
$before = (Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash
$runRoot = Join-Path $repoRoot ('build\local\tactical-session-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
$master = if ($Game -eq 'TFTD') { 'xcom2' } else { 'xcom1' }
$masterRoot = Join-Path $runRoot $master
New-Item -ItemType Directory -Path $runRoot | Out-Null
New-Item -ItemType Directory -Path $masterRoot | Out-Null
Copy-Item -LiteralPath $source.FullName -Destination (Join-Path $masterRoot 'inspection-start.sav')
$manifest = @{ source=$source.FullName; sourceSha256=$before; master=$master; observer=(-not [bool]$NormalVision); telemetry=$true; defend=[bool]$Defend; originalUnchanged=$true }
$manifest | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runRoot 'manifest.json') -Encoding utf8
# A reviewable launch script lets a prepared session be reopened without copying again.
function Quote-PS([string]$Value) { return "'" + $Value.Replace("'", "''") + "'" }
$exe = Join-Path $runtime 'OpenXcom.exe'
$observer = if ($NormalVision) { 'false' } else { 'true' }
$arguments = @('-data',$runtime,'-user',$runRoot,'-config',$runRoot,'-master',$master,
    '-playIntro','false','-fullscreen','false','-tacticalTelemetry','true','-tacticalObserver',$observer,
    '-debug','false','-traceAI','false','-alienCommandAudit','false','-alienCommandModelPort','0',
    '-alienCommandModelExecute','false','-alienCommandPortfolio','false','-newSeedOnLoad','false')
$arguments += @('-load','inspection-start.sav')
$arguments += @('-tacticalDefend',$(if ($Defend) { 'true' } else { 'false' }))
$quotedArguments = @($arguments | ForEach-Object { Quote-PS ('"' + $_ + '"') })
$launchText = '$taskGameProcess = Start-Process -FilePath ' + (Quote-PS $exe) + ' -ArgumentList @(' + ($quotedArguments -join ',') + ') -Wait -PassThru' + "`r`n" +
    'if ($taskGameProcess.ExitCode -ne 0) { throw "Game exited with code $($taskGameProcess.ExitCode)" }'
Set-Content -LiteralPath (Join-Path $runRoot 'launch.ps1') -Value $launchText -Encoding utf8
Write-Output "Inspection session: $runRoot"
Write-Output 'Load inspection-start in the game. Original saves are outside this session.'
Write-Output 'Observer display reveals terrain and units. Debug/manual alien control stays disabled.'
Write-Output 'Monthly model execution is disabled in this isolated tactical session.'
if ($Defend) { Write-Output 'EXPERIMENT: persistent UFO guard/screen orders enabled. Contact, injury and hazards return control to native AI.' }
Write-Output "Launch later: & '$runRoot\launch.ps1'"
if ($Launch) {
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw 'Build/stage the native engine first with scripts/setup-local.ps1.' }
    try {
        & (Join-Path $runRoot 'launch.ps1')
    }
    finally {
        $manifest.originalUnchanged = (Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash -eq $before
        $manifest | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runRoot 'manifest.json') -Encoding utf8
        if (-not $manifest.originalUnchanged) { throw 'Original save hash changed during the inspection session.' }
    }
    $captures = @(Get-ChildItem -LiteralPath $masterRoot -Filter 'tactical-*.jsonl')
    if ($captures.Count) {
        & (Join-Path $repoRoot 'build\local\laya-venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'view-tactical-telemetry.py') --capture-dir $masterRoot --out (Join-Path $runRoot 'review')
        if ($LASTEXITCODE -ne 0) { throw 'Capture viewer generation failed; native logs are retained.' }
    }
}
if ((Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash -ne $before) { throw 'Original save changed.' }
