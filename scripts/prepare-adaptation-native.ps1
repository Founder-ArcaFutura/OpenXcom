$ErrorActionPreference='Stop'
$repoRoot=Split-Path -Parent $PSScriptRoot
$python=Join-Path $repoRoot 'build/local/laya-venv/Scripts/python.exe'
$runtimeRoot=Join-Path $repoRoot 'build/local/runtime'
$fixtureRoot=Join-Path $repoRoot 'build/local/adaptation-native-v1'
$baseUser=Join-Path $fixtureRoot 'transition'
New-Item -ItemType Directory -Path $baseUser -Force | Out-Null
& $python (Join-Path $PSScriptRoot 'prepare-adaptation-native.py') --source (Join-Path $repoRoot 'build/local/user/xcom1/Pre-Junes.sav') --out (Join-Path $baseUser 'xcom1/source.sav')
if ($LASTEXITCODE) { throw 'Cannot prepare isolated source' }
$oldVideo=$env:SDL_VIDEODRIVER; $oldAudio=$env:SDL_AUDIODRIVER
$oldReplay=$env:OPENXCOM_ALIEN_REPLAY; $oldTransition=$env:OPENXCOM_MONTH_TRANSITION; $oldStrategy=$env:OPENXCOM_STRATEGY_REPLAY
$service=$null
try {
 $env:SDL_VIDEODRIVER='dummy';$env:SDL_AUDIODRIVER='dummy';$env:OPENXCOM_ALIEN_REPLAY='1';$env:OPENXCOM_MONTH_TRANSITION='1';$env:OPENXCOM_STRATEGY_REPLAY=$null
 $service=Start-Process -FilePath $python -ArgumentList @('-u',('"'+(Join-Path $repoRoot 'tests/alien-command-portfolio-fixture.py')+'"'),'--port','18879','--mode','save') -WindowStyle Hidden -PassThru
 Start-Sleep -Milliseconds 500
 if ($service.HasExited) { throw 'Owned SAVE transport fixture failed' }
 $exe=Join-Path $runtimeRoot 'AlienCommandTests.exe'
 & $exe -data $runtimeRoot -user $baseUser -config $baseUser -master xcom1 -playIntro false -useOpenGL false -fullscreen false -alienCommandPortfolio true -alienCommandModelPort 18879 *> (Join-Path $fixtureRoot 'transition.log')
 if ($LASTEXITCODE) { Get-Content (Join-Path $fixtureRoot 'transition.log') -Tail 8; throw 'Isolated transition failed' }
 $env:OPENXCOM_MONTH_TRANSITION=$null;$env:OPENXCOM_STRATEGY_REPLAY='1'
 foreach ($level in @(1,2)) {
  $testUser=Join-Path $fixtureRoot "logistics-$level"
  New-Item -ItemType Directory -Path $testUser -Force | Out-Null
  & $python (Join-Path $PSScriptRoot 'prepare-adaptation-native.py') --source (Join-Path $baseUser 'xcom1/transition-result.sav') --out (Join-Path $testUser 'xcom1/source.sav') --logistics $level
  if ($LASTEXITCODE) { throw 'Cannot prepare capability fixture' }
  & $exe -data $runtimeRoot -user $testUser -config $testUser -master xcom1 -playIntro false -useOpenGL false -fullscreen false -alienCommandPortfolio true -alienCommandModelPort 18879 *> (Join-Path $fixtureRoot "logistics-$level.log")
  if ($LASTEXITCODE) { Get-Content (Join-Path $fixtureRoot "logistics-$level.log") -Tail 8; throw 'Native capability inspection failed' }
 }
} finally {
 $env:SDL_VIDEODRIVER=$oldVideo;$env:SDL_AUDIODRIVER=$oldAudio;$env:OPENXCOM_ALIEN_REPLAY=$oldReplay;$env:OPENXCOM_MONTH_TRANSITION=$oldTransition;$env:OPENXCOM_STRATEGY_REPLAY=$oldStrategy
 if ($service -and -not $service.HasExited) {
  Get-CimInstance Win32_Process -Filter "ParentProcessId=$($service.Id)" -ErrorAction SilentlyContinue | ForEach-Object {Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue}
  Stop-Process -Id $service.Id -ErrorAction SilentlyContinue
 }
}
Write-Output 'Native capability inputs exported in build/local/adaptation-native-v1; original saves untouched.'
