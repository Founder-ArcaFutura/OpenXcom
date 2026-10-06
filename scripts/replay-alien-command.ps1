[CmdletBinding()]
param(
    [string]$Save = 'G:\OpenXcom\build\local\user\xcom1\Testing.sav',
    [ValidateSet('UFO','TFTD')][string]$Game = 'UFO',
    [int]$ModelPort = 0
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$localRoot = Join-Path $repoRoot 'build\local'
$runtimeRoot = Join-Path $localRoot 'runtime'
$master = if ($Game -eq 'TFTD') { 'xcom2' } else { 'xcom1' }
$source = Get-Item -LiteralPath $Save
$before = (Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash
$runRoot = Join-Path $localRoot ('replay-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
$masterRoot = Join-Path $runRoot $master
New-Item -ItemType Directory -Path $masterRoot -Force | Out-Null
Copy-Item -LiteralPath $source.FullName -Destination (Join-Path $masterRoot 'source.sav')
$previousVideo = $env:SDL_VIDEODRIVER
$previousAudio = $env:SDL_AUDIODRIVER
$previousReplay = $env:OPENXCOM_ALIEN_REPLAY
try {
    $env:SDL_VIDEODRIVER = 'dummy'; $env:SDL_AUDIODRIVER = 'dummy'; $env:OPENXCOM_ALIEN_REPLAY = '1'
    $log = Join-Path $runRoot 'replay.log'
    & (Join-Path $runtimeRoot 'AlienCommandTests.exe') -data $runtimeRoot -user $runRoot -config $runRoot -master $master -playIntro false -useOpenGL false -fullscreen false -alienCommandModelPort $ModelPort *> $log
    if ($LASTEXITCODE -ne 0) { Get-Content -LiteralPath $log -Tail 8; throw "Replay failed: $log" }
    Select-String -LiteralPath $log -Pattern '^REPLAY:' | ForEach-Object { $_.Line }
}
finally { $env:SDL_VIDEODRIVER = $previousVideo; $env:SDL_AUDIODRIVER = $previousAudio; $env:OPENXCOM_ALIEN_REPLAY = $previousReplay }
$after = (Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash
if ($before -ne $after) { throw 'Original save changed during replay.' }
$receipt = @{ sourceSave=$source.FullName; sourceSha256=$before; originalUnchanged=$true; master=$master; modelPort=$ModelPort; audit=(Join-Path $masterRoot 'recon-replay.jsonl') }
$receipt | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runRoot 'manifest.json') -Encoding utf8
Write-Output "Original save unchanged (SHA-256). Replay manifest: $runRoot\manifest.json"
