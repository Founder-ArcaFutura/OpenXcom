[CmdletBinding()]
param([switch]$Learned,[int]$Port=18884,[string]$SourceSave='')
$ErrorActionPreference='Stop'
$repoRoot=Split-Path -Parent $PSScriptRoot
$python=Join-Path $repoRoot 'build/local/laya-venv/Scripts/python.exe'
$runtime=Join-Path $repoRoot 'build/local/runtime'
if (-not $SourceSave) { $SourceSave=Join-Path $repoRoot 'build/local/user/xcom1/Pre-Junes.sav' }
$sourcePath=(Resolve-Path -LiteralPath $SourceSave).Path
$sourceHash=(Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash
$mode=if($Learned){'learned'}else{'scripted'}
$testRoot=Join-Path $repoRoot "build/local/operation-ledger-replay-$mode"
New-Item -ItemType Directory -Path (Join-Path $testRoot 'xcom1') -Force | Out-Null
Copy-Item -LiteralPath $sourcePath -Destination (Join-Path $testRoot 'xcom1/source.sav') -Force
$names=@('SDL_VIDEODRIVER','SDL_AUDIODRIVER','OPENXCOM_ALIEN_REPLAY','OPENXCOM_MONTH_TRANSITION','OPENXCOM_STRATEGY_REPLAY')
$previous=@{};foreach($name in $names){$previous[$name]=[Environment]::GetEnvironmentVariable($name,'Process')}
$service=$null
try {
 if($Learned){
  $argsList=@('-u',('"'+(Join-Path $PSScriptRoot 'alien-command-model.py')+'"'),'--checkpoint','"C:\Users\Main PC 2\AppData\Local\Temp\uppward-v4"','--port',"$Port")
 } else {
  $argsList=@('-u',('"'+(Join-Path $repoRoot 'tests/alien-command-portfolio-fixture.py')+'"'),'--mode','valid','--port',"$Port")
 }
 # Bind only an unused test port; never stop or reuse the user's model service.
 $listener=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,$Port)
 $listener.Start();$listener.Stop()
 $service=Start-Process -FilePath $python -ArgumentList $argsList -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $testRoot 'service.log') -RedirectStandardError (Join-Path $testRoot 'service-errors.log')
 if($Learned){
  $ready=$false;$deadline=(Get-Date).AddMinutes(3)
  while((Get-Date)-lt $deadline){
   if($service.HasExited){throw 'Owned model service failed to start; inspect service-errors.log'}
   try{$health=Invoke-RestMethod "http://127.0.0.1:$Port/healthz" -TimeoutSec 1;if($health.portfolioPromptVersion -eq 'progressive-portfolio-v10'){$ready=$true;break}}catch{}
   Start-Sleep -Milliseconds 500
  }
  if(-not $ready){throw 'Owned model service did not become ready'}
 } else {Start-Sleep -Milliseconds 500;if($service.HasExited){throw 'Owned scripted fixture failed to start'}}
 $env:SDL_VIDEODRIVER='dummy';$env:SDL_AUDIODRIVER='dummy'
 $env:OPENXCOM_ALIEN_REPLAY='1';$env:OPENXCOM_MONTH_TRANSITION='1';$env:OPENXCOM_STRATEGY_REPLAY=$null
 & (Join-Path $runtime 'AlienCommandTests.exe') -data $runtime -user $testRoot -config $testRoot -master xcom1 -playIntro false -useOpenGL false -fullscreen false -alienCommandPortfolio true -alienCommandModelPort $Port *> (Join-Path $testRoot 'transition.log')
 if($LASTEXITCODE){Get-Content (Join-Path $testRoot 'transition.log') -Tail 8;throw 'Copied-save transition failed'}
 & $python (Join-Path $PSScriptRoot 'audit-alien-operations.py') --save (Join-Path $testRoot 'xcom1/transition-result.sav') --out (Join-Path $testRoot 'review')
 if($LASTEXITCODE){throw 'Monthly review export failed'}
 $checkArgs=@((Join-Path $PSScriptRoot 'check-operation-ledger-replay.py'),'--root',$testRoot)
 if($Learned){$checkArgs+='--learned'}
 & $python @checkArgs
 if($LASTEXITCODE){throw 'Native ledger/model contract verification failed'}
 if((Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash -ne $sourceHash){throw 'Original source save changed'}
 Write-Output "PASS: $mode native monthly transition, persistence and review export; source unchanged. $testRoot"
} finally {
 foreach($name in $names){[Environment]::SetEnvironmentVariable($name,$previous[$name],'Process')}
 if($service){
  Get-CimInstance Win32_Process -Filter "ParentProcessId=$($service.Id)" -ErrorAction SilentlyContinue | ForEach-Object {Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue}
  if(-not $service.HasExited){Stop-Process -Id $service.Id -ErrorAction SilentlyContinue}
 }
}
